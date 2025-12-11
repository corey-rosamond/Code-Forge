"""Git repository interface."""

from __future__ import annotations

import asyncio
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class GitRemote:
    """Git remote information."""

    name: str
    url: str
    fetch_url: str | None = None
    push_url: str | None = None


@dataclass
class GitBranch:
    """Git branch information."""

    name: str
    is_current: bool = False
    tracking: str | None = None
    ahead: int = 0
    behind: int = 0
    commit: str | None = None


@dataclass
class GitCommit:
    """Git commit information."""

    hash: str
    short_hash: str
    author: str
    author_email: str
    date: str
    message: str
    parent_hashes: list[str] = field(default_factory=list)

    @property
    def subject(self) -> str:
        """Get commit subject (first line)."""
        return self.message.split("\n")[0]


@dataclass
class RepositoryInfo:
    """Git repository information."""

    root: Path
    is_git_repo: bool
    current_branch: str | None
    head_commit: GitCommit | None
    is_dirty: bool
    remotes: list[GitRemote] = field(default_factory=list)


class GitError(Exception):
    """Git operation error."""

    def __init__(self, message: str, returncode: int = 1, stderr: str = "") -> None:
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr


class GitRepository:
    """Interface to a Git repository."""

    def __init__(self, path: Path | str | None = None) -> None:
        """Initialize repository.

        Args:
            path: Repository path or current directory
        """
        self._path = Path(path) if path else Path.cwd()
        self._root: Path | None = None
        self._is_git_repo: bool | None = None
        self._current_branch_cache: str | None = None
        self._dirty_cache: bool | None = None

    def invalidate_cache(self) -> None:
        """Invalidate cached repository state.

        Call this after operations that might change the repository state
        (commits, checkouts, etc.) to ensure fresh values are fetched.
        """
        self._current_branch_cache = None
        self._dirty_cache = None

    async def run_git(
        self,
        *args: str,
        check: bool = True,
        cwd: Path | None = None,
    ) -> tuple[str, str, int]:
        """Run git command.

        Args:
            *args: Git command arguments
            check: Raise error on non-zero exit
            cwd: Working directory (default: repo root)

        Returns:
            Tuple of (stdout, stderr, returncode)
        """
        cmd = ["git", *list(args)]
        work_dir = cwd or self._get_work_dir()

        logger.debug(f"Running: {' '.join(cmd)}")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=work_dir,
        )
        stdout, stderr = await proc.communicate()

        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()

        if check and proc.returncode != 0:
            raise GitError(
                f"Git command failed: {' '.join(args)}",
                proc.returncode or 1,
                stderr_str,
            )

        return stdout_str, stderr_str, proc.returncode or 0

    def _get_work_dir(self) -> Path:
        """Get working directory for git commands."""
        if self._root is not None:
            return self._root
        return self._path

    def _run_git_sync(self, *args: str) -> str:
        """Run git command synchronously for property access.

        Uses subprocess.run instead of os.popen for better security
        (no shell injection) and error handling.

        Args:
            *args: Git command arguments

        Returns:
            stdout as string, empty string on error
        """
        try:
            result = subprocess.run(
                ["git", "-C", str(self._path), *list(args)],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            return result.stdout.strip()
        except (subprocess.SubprocessError, OSError):
            return ""

    @property
    def is_git_repo(self) -> bool:
        """Check if path is a Git repository."""
        if self._is_git_repo is None:
            result = self._run_git_sync("rev-parse", "--git-dir")
            self._is_git_repo = bool(result)
        return self._is_git_repo

    @property
    def root(self) -> Path:
        """Get repository root directory."""
        if self._root is None:
            if not self.is_git_repo:
                raise GitError("Not a git repository")
            result = self._run_git_sync("rev-parse", "--show-toplevel")
            if not result:
                raise GitError("Could not determine repository root")
            self._root = Path(result)
        return self._root

    @property
    def current_branch(self) -> str | None:
        """Get current branch name (cached until invalidated)."""
        if not self.is_git_repo:
            return None
        if self._current_branch_cache is None:
            result = self._run_git_sync("branch", "--show-current")
            self._current_branch_cache = result or None
        return self._current_branch_cache

    @property
    def is_dirty(self) -> bool:
        """Check if working tree has uncommitted changes (cached until invalidated)."""
        if not self.is_git_repo:
            return False
        if self._dirty_cache is None:
            result = self._run_git_sync("status", "--porcelain")
            self._dirty_cache = bool(result)
        return self._dirty_cache

    async def get_info(self) -> RepositoryInfo:
        """Get repository information."""
        if not self.is_git_repo:
            return RepositoryInfo(
                root=self._path,
                is_git_repo=False,
                current_branch=None,
                head_commit=None,
                is_dirty=False,
            )

        # Get current branch
        branch_out, _, _ = await self.run_git("branch", "--show-current")
        current_branch = branch_out or None

        # Get HEAD commit
        head_commit = await self._get_head_commit()

        # Check dirty state
        status_out, _, _ = await self.run_git("status", "--porcelain")
        is_dirty = bool(status_out)

        # Get remotes
        remotes = await self.get_remotes()

        return RepositoryInfo(
            root=self.root,
            is_git_repo=True,
            current_branch=current_branch,
            head_commit=head_commit,
            is_dirty=is_dirty,
            remotes=remotes,
        )

    async def _get_head_commit(self) -> GitCommit | None:
        """Get HEAD commit info."""
        try:
            format_str = "%H%n%h%n%an%n%ae%n%ai%n%s%n%P"
            out, _, _ = await self.run_git("log", "-1", f"--format={format_str}")
            lines = out.split("\n")
            if len(lines) >= 6:
                return GitCommit(
                    hash=lines[0],
                    short_hash=lines[1],
                    author=lines[2],
                    author_email=lines[3],
                    date=lines[4],
                    message=lines[5],
                    parent_hashes=lines[6].split() if len(lines) > 6 else [],
                )
        except GitError:
            pass
        return None

    async def get_remotes(self) -> list[GitRemote]:
        """Get list of remotes."""
        out, _, _ = await self.run_git("remote", "-v", check=False)
        if not out:
            return []

        remotes: dict[str, GitRemote] = {}
        for line in out.split("\n"):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                url = parts[1]
                if name not in remotes:
                    remotes[name] = GitRemote(name=name, url=url)
                if "(fetch)" in line:
                    remotes[name].fetch_url = url
                elif "(push)" in line:
                    remotes[name].push_url = url

        return list(remotes.values())

    async def get_branches(
        self,
        all: bool = False,
        remote: bool = False,
    ) -> list[GitBranch]:
        """Get list of branches.

        Args:
            all: Include all branches (local and remote)
            remote: Only remote branches

        Returns:
            List of branches
        """
        args = ["branch", "-v"]
        if all:
            args.append("-a")
        elif remote:
            args.append("-r")

        out, _, _ = await self.run_git(*args)
        branches = []

        for raw_line in out.split("\n"):
            if not raw_line.strip():
                continue

            is_current = raw_line.startswith("*")
            line = raw_line.lstrip("* ")

            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                commit = parts[1] if len(parts) > 1 else None

                branches.append(
                    GitBranch(
                        name=name,
                        is_current=is_current,
                        commit=commit,
                    )
                )

        return branches
