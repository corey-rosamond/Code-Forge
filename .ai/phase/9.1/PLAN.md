# Phase 9.1: Git Integration - Implementation Plan

**Phase:** 9.1
**Name:** Git Integration
**Dependencies:** Phase 2.3 (Execution Tools), Phase 2.1 (Tool System)

---

## Implementation Order

1. Repository detection and information
2. Status parsing and display
3. History and log operations
4. Diff operations
5. Safety guards
6. Git operations (commit, branch, etc.)
7. Context integration
8. Commands and tools

---

## Step 1: Repository Interface (repository.py)

```python
# src/opencode/git/repository.py
"""Git repository interface."""

import asyncio
import logging
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
    def __init__(self, message: str, returncode: int = 1, stderr: str = ""):
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr


class GitRepository:
    """Interface to a Git repository."""

    def __init__(self, path: Path | str | None = None):
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
        cwd: Path | None = None
    ) -> tuple[str, str, int]:
        """Run git command.

        Args:
            *args: Git command arguments
            check: Raise error on non-zero exit
            cwd: Working directory (default: repo root)

        Returns:
            Tuple of (stdout, stderr, returncode)
        """
        cmd = ["git"] + list(args)
        work_dir = cwd or self.root

        logger.debug(f"Running: {' '.join(cmd)}")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=work_dir
        )
        stdout, stderr = await proc.communicate()

        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()

        if check and proc.returncode != 0:
            raise GitError(
                f"Git command failed: {' '.join(args)}",
                proc.returncode,
                stderr_str
            )

        return stdout_str, stderr_str, proc.returncode

    def _run_git_sync(self, *args: str) -> str:
        """Run git command synchronously for property access.

        Uses subprocess.run instead of os.popen for better security
        (no shell injection) and error handling.

        Args:
            *args: Git command arguments

        Returns:
            stdout as string, empty string on error
        """
        import subprocess
        try:
            result = subprocess.run(
                ["git", "-C", str(self._path)] + list(args),
                capture_output=True,
                text=True,
                timeout=10,  # Prevent hanging
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
                is_dirty=False
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
            remotes=remotes
        )

    async def _get_head_commit(self) -> GitCommit | None:
        """Get HEAD commit info."""
        try:
            format_str = "%H%n%h%n%an%n%ae%n%ai%n%s%n%P"
            out, _, _ = await self.run_git(
                "log", "-1", f"--format={format_str}"
            )
            lines = out.split("\n")
            if len(lines) >= 6:
                return GitCommit(
                    hash=lines[0],
                    short_hash=lines[1],
                    author=lines[2],
                    author_email=lines[3],
                    date=lines[4],
                    message=lines[5],
                    parent_hashes=lines[6].split() if len(lines) > 6 else []
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
        remote: bool = False
    ) -> list[GitBranch]:
        """Get list of branches."""
        args = ["branch", "-v"]
        if all:
            args.append("-a")
        elif remote:
            args.append("-r")

        out, _, _ = await self.run_git(*args)
        branches = []

        for line in out.split("\n"):
            if not line.strip():
                continue

            is_current = line.startswith("*")
            line = line.lstrip("* ")

            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                commit = parts[1] if len(parts) > 1 else None

                branches.append(GitBranch(
                    name=name,
                    is_current=is_current,
                    commit=commit
                ))

        return branches
```

---

## Step 2: Status Operations (status.py)

```python
# src/opencode/git/status.py
"""Git status operations."""

from dataclasses import dataclass, field
import re

from .repository import GitRepository, GitError


@dataclass
class FileStatus:
    """Status of a single file."""
    path: str
    status: str  # M, A, D, R, C, U, ?
    staged: bool
    original_path: str | None = None

    @property
    def status_name(self) -> str:
        """Human-readable status name."""
        names = {
            "M": "modified",
            "A": "added",
            "D": "deleted",
            "R": "renamed",
            "C": "copied",
            "U": "unmerged",
            "?": "untracked"
        }
        return names.get(self.status, "unknown")


@dataclass
class GitStatus:
    """Complete git status."""
    branch: str | None = None
    tracking: str | None = None
    ahead: int = 0
    behind: int = 0
    staged: list[FileStatus] = field(default_factory=list)
    unstaged: list[FileStatus] = field(default_factory=list)
    untracked: list[FileStatus] = field(default_factory=list)
    conflicts: list[FileStatus] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        """Check if working tree is clean."""
        return not (
            self.staged or self.unstaged or
            self.untracked or self.conflicts
        )

    @property
    def total_changes(self) -> int:
        """Total number of changed files."""
        return (
            len(self.staged) + len(self.unstaged) +
            len(self.untracked) + len(self.conflicts)
        )

    def to_string(self) -> str:
        """Format as human-readable string."""
        lines = []

        # Branch info
        if self.branch:
            branch_line = f"On branch {self.branch}"
            if self.tracking:
                if self.ahead and self.behind:
                    branch_line += f" (ahead {self.ahead}, behind {self.behind})"
                elif self.ahead:
                    branch_line += f" (ahead {self.ahead})"
                elif self.behind:
                    branch_line += f" (behind {self.behind})"
            lines.append(branch_line)
            lines.append("")

        # Staged changes
        if self.staged:
            lines.append("Changes to be committed:")
            for f in self.staged:
                lines.append(f"  {f.status_name}: {f.path}")
            lines.append("")

        # Unstaged changes
        if self.unstaged:
            lines.append("Changes not staged for commit:")
            for f in self.unstaged:
                lines.append(f"  {f.status_name}: {f.path}")
            lines.append("")

        # Untracked files
        if self.untracked:
            lines.append("Untracked files:")
            for f in self.untracked:
                lines.append(f"  {f.path}")
            lines.append("")

        # Conflicts
        if self.conflicts:
            lines.append("Unmerged paths:")
            for f in self.conflicts:
                lines.append(f"  {f.path}")
            lines.append("")

        if self.is_clean:
            lines.append("Nothing to commit, working tree clean")

        return "\n".join(lines)


class GitStatusTool:
    """Git status operations."""

    def __init__(self, repo: GitRepository):
        self.repo = repo

    async def get_status(self) -> GitStatus:
        """Get current git status."""
        # Get branch info
        branch_out, _, _ = await self.repo.run_git(
            "status", "-b", "--porcelain=v2"
        )

        status = GitStatus()

        # Parse porcelain v2 output
        for line in branch_out.split("\n"):
            if line.startswith("# branch.head "):
                status.branch = line.split(" ", 2)[2]
            elif line.startswith("# branch.upstream "):
                status.tracking = line.split(" ", 2)[2]
            elif line.startswith("# branch.ab "):
                parts = line.split(" ")
                for part in parts[2:]:
                    if part.startswith("+"):
                        status.ahead = int(part[1:])
                    elif part.startswith("-"):
                        status.behind = int(part[1:])
            elif line.startswith("1 ") or line.startswith("2 "):
                # Changed files
                self._parse_changed_file(line, status)
            elif line.startswith("? "):
                # Untracked file
                path = line[2:]
                status.untracked.append(FileStatus(
                    path=path, status="?", staged=False
                ))
            elif line.startswith("u "):
                # Unmerged file
                path = line.split("\t")[-1]
                status.conflicts.append(FileStatus(
                    path=path, status="U", staged=False
                ))

        return status

    def _parse_changed_file(self, line: str, status: GitStatus) -> None:
        """Parse a changed file line from porcelain v2."""
        parts = line.split(" ", 8)
        if len(parts) < 9:
            return

        xy = parts[1]
        path = parts[8].split("\t")[-1]

        # Check staged changes (index vs HEAD)
        if xy[0] != ".":
            status.staged.append(FileStatus(
                path=path, status=xy[0], staged=True
            ))

        # Check unstaged changes (worktree vs index)
        if xy[1] != ".":
            status.unstaged.append(FileStatus(
                path=path, status=xy[1], staged=False
            ))

    async def get_staged_diff(self) -> str:
        """Get diff of staged changes."""
        out, _, _ = await self.repo.run_git("diff", "--cached")
        return out

    async def get_unstaged_diff(self) -> str:
        """Get diff of unstaged changes."""
        out, _, _ = await self.repo.run_git("diff")
        return out

    async def get_short_status(self) -> str:
        """Get short status summary."""
        status = await self.get_status()

        parts = []
        if status.staged:
            parts.append(f"{len(status.staged)} staged")
        if status.unstaged:
            parts.append(f"{len(status.unstaged)} modified")
        if status.untracked:
            parts.append(f"{len(status.untracked)} untracked")

        if not parts:
            return "clean"
        return ", ".join(parts)
```

---

## Step 3: History Operations (history.py)

```python
# src/opencode/git/history.py
"""Git history and log operations."""

from dataclasses import dataclass, field
from typing import Any

from .repository import GitCommit, GitRepository


@dataclass
class LogEntry:
    """Single log entry with stats."""
    commit: GitCommit
    files_changed: int | None = None
    insertions: int | None = None
    deletions: int | None = None

    def to_string(self, verbose: bool = False) -> str:
        """Format as string."""
        lines = [
            f"commit {self.commit.short_hash}",
            f"Author: {self.commit.author} <{self.commit.author_email}>",
            f"Date:   {self.commit.date}",
            "",
            f"    {self.commit.subject}"
        ]

        if verbose and self.commit.message != self.commit.subject:
            for line in self.commit.message.split("\n")[1:]:
                lines.append(f"    {line}")

        if self.files_changed is not None:
            stats = f" {self.files_changed} file(s) changed"
            if self.insertions:
                stats += f", {self.insertions} insertion(s)"
            if self.deletions:
                stats += f", {self.deletions} deletion(s)"
            lines.append(stats)

        return "\n".join(lines)


class GitHistory:
    """Git history operations."""

    def __init__(self, repo: GitRepository):
        self.repo = repo

    async def get_log(
        self,
        count: int = 10,
        path: str | None = None,
        author: str | None = None,
        since: str | None = None,
        until: str | None = None,
        branch: str | None = None,
        all_branches: bool = False
    ) -> list[LogEntry]:
        """Get commit log.

        Args:
            count: Number of commits
            path: Filter by file path
            author: Filter by author
            since: Commits since date
            until: Commits until date
            branch: Specific branch
            all_branches: Show all branches

        Returns:
            List of log entries
        """
        format_str = "%H%n%h%n%an%n%ae%n%ai%n%s%n%b%n---COMMIT---"

        args = [
            "log",
            f"-{count}",
            f"--format={format_str}",
            "--shortstat"
        ]

        if author:
            args.append(f"--author={author}")
        if since:
            args.append(f"--since={since}")
        if until:
            args.append(f"--until={until}")
        if all_branches:
            args.append("--all")
        if branch:
            args.append(branch)
        if path:
            args.append("--")
            args.append(path)

        out, _, _ = await self.repo.run_git(*args)

        entries = []
        commits = out.split("---COMMIT---")

        for commit_text in commits:
            if not commit_text.strip():
                continue

            entry = self._parse_commit(commit_text)
            if entry:
                entries.append(entry)

        return entries

    def _parse_commit(self, text: str) -> LogEntry | None:
        """Parse commit text into LogEntry."""
        lines = text.strip().split("\n")
        if len(lines) < 6:
            return None

        # Parse commit info
        commit = GitCommit(
            hash=lines[0],
            short_hash=lines[1],
            author=lines[2],
            author_email=lines[3],
            date=lines[4],
            message="\n".join(lines[5:]).strip()
        )

        # Parse stats from last line if present
        entry = LogEntry(commit=commit)
        for line in reversed(lines):
            if "file" in line and "changed" in line:
                self._parse_stats(line, entry)
                break

        return entry

    def _parse_stats(self, line: str, entry: LogEntry) -> None:
        """Parse stat line."""
        import re

        files_match = re.search(r"(\d+) file", line)
        if files_match:
            entry.files_changed = int(files_match.group(1))

        insert_match = re.search(r"(\d+) insertion", line)
        if insert_match:
            entry.insertions = int(insert_match.group(1))

        delete_match = re.search(r"(\d+) deletion", line)
        if delete_match:
            entry.deletions = int(delete_match.group(1))

    async def get_commit(self, ref: str) -> GitCommit:
        """Get single commit details."""
        format_str = "%H%n%h%n%an%n%ae%n%ai%n%B%n%P"
        out, _, _ = await self.repo.run_git(
            "show", "-s", f"--format={format_str}", ref
        )

        lines = out.split("\n")
        return GitCommit(
            hash=lines[0],
            short_hash=lines[1],
            author=lines[2],
            author_email=lines[3],
            date=lines[4],
            message="\n".join(lines[5:-1]).strip(),
            parent_hashes=lines[-1].split() if lines[-1] else []
        )

    async def get_commit_files(self, ref: str) -> list[str]:
        """Get files changed in commit."""
        out, _, _ = await self.repo.run_git(
            "show", "--name-only", "--format=", ref
        )
        return [f for f in out.split("\n") if f.strip()]

    async def get_commit_diff(
        self,
        ref: str,
        path: str | None = None
    ) -> str:
        """Get diff for commit."""
        args = ["show", "--patch", ref]
        if path:
            args.extend(["--", path])

        out, _, _ = await self.repo.run_git(*args)
        return out

    async def get_recent_commits(
        self,
        count: int = 5
    ) -> str:
        """Get formatted recent commits for context."""
        entries = await self.get_log(count=count)

        lines = ["Recent commits:"]
        for entry in entries:
            lines.append(
                f"  {entry.commit.short_hash} {entry.commit.subject}"
            )

        return "\n".join(lines)
```

---

## Step 4: Diff Operations (diff.py)

```python
# src/opencode/git/diff.py
"""Git diff operations."""

from dataclasses import dataclass, field
import re

from .repository import GitRepository


@dataclass
class DiffFile:
    """Diff for a single file."""
    path: str
    old_path: str | None = None
    status: str = "M"  # A, M, D, R
    additions: int = 0
    deletions: int = 0
    content: str | None = None

    @property
    def is_rename(self) -> bool:
        """Check if this is a rename."""
        return self.status == "R" and self.old_path is not None


@dataclass
class GitDiff:
    """Complete diff result."""
    files: list[DiffFile] = field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0
    stat: str = ""

    @property
    def total_files(self) -> int:
        """Total number of files."""
        return len(self.files)

    def to_string(self, include_content: bool = True) -> str:
        """Format as string."""
        lines = []

        # Summary
        lines.append(self.stat)
        lines.append("")

        if include_content:
            for file in self.files:
                if file.content:
                    lines.append(file.content)
                    lines.append("")

        return "\n".join(lines)

    def get_stat_summary(self) -> str:
        """Get short stat summary."""
        return (
            f"{self.total_files} file(s) changed, "
            f"{self.total_additions} insertion(s)(+), "
            f"{self.total_deletions} deletion(s)(-)"
        )


class GitDiffTool:
    """Git diff operations."""

    def __init__(self, repo: GitRepository):
        self.repo = repo

    async def diff_working(
        self,
        path: str | None = None,
        staged: bool = False,
        context_lines: int = 3
    ) -> GitDiff:
        """Diff working tree vs HEAD.

        Args:
            path: Filter by path
            staged: Diff staged changes only
            context_lines: Number of context lines

        Returns:
            GitDiff result
        """
        args = ["diff", f"-U{context_lines}"]
        if staged:
            args.append("--cached")
        if path:
            args.extend(["--", path])

        return await self._run_diff(args)

    async def diff_commits(
        self,
        from_ref: str,
        to_ref: str,
        path: str | None = None
    ) -> GitDiff:
        """Diff between commits.

        Args:
            from_ref: Start commit
            to_ref: End commit
            path: Filter by path

        Returns:
            GitDiff result
        """
        args = ["diff", from_ref, to_ref]
        if path:
            args.extend(["--", path])

        return await self._run_diff(args)

    async def diff_branches(
        self,
        from_branch: str,
        to_branch: str
    ) -> GitDiff:
        """Diff between branches.

        Args:
            from_branch: Source branch
            to_branch: Target branch

        Returns:
            GitDiff result
        """
        return await self.diff_commits(from_branch, to_branch)

    async def get_stat(
        self,
        from_ref: str = "HEAD",
        to_ref: str | None = None
    ) -> str:
        """Get diff stat.

        Args:
            from_ref: Start reference
            to_ref: End reference (working tree if None)

        Returns:
            Stat output
        """
        args = ["diff", "--stat", from_ref]
        if to_ref:
            args.append(to_ref)

        out, _, _ = await self.repo.run_git(*args)
        return out

    async def _run_diff(self, args: list[str]) -> GitDiff:
        """Run diff command and parse output."""
        # Get stat
        stat_args = args.copy()
        stat_args.insert(1, "--stat")
        stat_out, _, _ = await self.repo.run_git(*stat_args)

        # Get full diff
        diff_out, _, _ = await self.repo.run_git(*args)

        # Parse results
        diff = GitDiff(stat=stat_out)
        self._parse_stat(stat_out, diff)
        self._parse_diff_content(diff_out, diff)

        return diff

    def _parse_stat(self, stat: str, diff: GitDiff) -> None:
        """Parse stat output."""
        for line in stat.split("\n"):
            # Match file stat line
            match = re.match(r"\s*(.+?)\s*\|\s*(\d+)", line)
            if match:
                path = match.group(1).strip()
                # Find or create file entry
                file_entry = None
                for f in diff.files:
                    if f.path == path:
                        file_entry = f
                        break
                if not file_entry:
                    file_entry = DiffFile(path=path)
                    diff.files.append(file_entry)

            # Match summary line
            summary = re.search(
                r"(\d+) insertion.*?(\d+) deletion",
                line
            )
            if summary:
                diff.total_additions = int(summary.group(1))
                diff.total_deletions = int(summary.group(2))

    def _parse_diff_content(self, content: str, diff: GitDiff) -> None:
        """Parse diff content and attach to files."""
        current_file: DiffFile | None = None
        current_content: list[str] = []

        for line in content.split("\n"):
            if line.startswith("diff --git"):
                # Save previous file content
                if current_file and current_content:
                    current_file.content = "\n".join(current_content)

                # Extract file path
                match = re.search(r"diff --git a/(.+) b/(.+)", line)
                if match:
                    path = match.group(2)
                    # Find existing entry or create new
                    current_file = None
                    for f in diff.files:
                        if f.path == path:
                            current_file = f
                            break
                    if not current_file:
                        current_file = DiffFile(path=path)
                        diff.files.append(current_file)

                    current_content = [line]
            else:
                current_content.append(line)

        # Save last file
        if current_file and current_content:
            current_file.content = "\n".join(current_content)
```

---

## Step 5: Safety Guards (safety.py)

```python
# src/opencode/git/safety.py
"""Safety guards for Git operations."""

from dataclasses import dataclass, field
import logging

from .repository import GitRepository, GitError

logger = logging.getLogger(__name__)


@dataclass
class SafetyCheck:
    """Result of safety check."""
    safe: bool
    reason: str | None = None
    warnings: list[str] = field(default_factory=list)


class GitSafety:
    """Safety guards for Git operations."""

    # Protected branches that should never be force-pushed
    PROTECTED_BRANCHES = {"main", "master", "develop", "production"}

    def __init__(self, repo: GitRepository):
        self.repo = repo

    async def check_amend(self) -> SafetyCheck:
        """Check if amend is safe.

        Safe if:
        - HEAD commit is not pushed
        - HEAD commit is authored by current user
        """
        warnings = []

        # Check if pushed
        is_pushed = await self.is_pushed("HEAD")
        if is_pushed:
            return SafetyCheck(
                safe=False,
                reason="HEAD commit has been pushed to remote",
                warnings=["Amending pushed commits can cause issues for others"]
            )

        # Check authorship (informational)
        try:
            author, email = await self.get_head_authorship()
            warnings.append(f"Will amend commit by: {author} <{email}>")
        except GitError:
            pass

        return SafetyCheck(safe=True, warnings=warnings)

    async def check_force_push(
        self,
        branch: str | None = None
    ) -> SafetyCheck:
        """Check if force push is safe."""
        branch = branch or self.repo.current_branch

        if branch in self.PROTECTED_BRANCHES:
            return SafetyCheck(
                safe=False,
                reason=f"Force push to protected branch '{branch}' is not allowed"
            )

        return SafetyCheck(
            safe=True,
            warnings=[
                "Force push will rewrite remote history",
                "Other users may be affected"
            ]
        )

    async def check_branch_delete(self, branch: str) -> SafetyCheck:
        """Check if branch delete is safe."""
        warnings = []

        # Check if it's current branch
        if branch == self.repo.current_branch:
            return SafetyCheck(
                safe=False,
                reason="Cannot delete current branch"
            )

        # Check if protected
        if branch in self.PROTECTED_BRANCHES:
            return SafetyCheck(
                safe=False,
                reason=f"Cannot delete protected branch '{branch}'"
            )

        # Check if merged
        try:
            out, _, code = await self.repo.run_git(
                "branch", "--merged", "HEAD", check=False
            )
            if branch not in out:
                warnings.append(f"Branch '{branch}' is not merged into HEAD")
        except GitError:
            pass

        return SafetyCheck(safe=True, warnings=warnings)

    async def check_hard_reset(self) -> SafetyCheck:
        """Check if hard reset is safe."""
        # Check for uncommitted changes
        out, _, _ = await self.repo.run_git("status", "--porcelain")
        if out:
            return SafetyCheck(
                safe=False,
                reason="Uncommitted changes would be lost",
                warnings=["Commit or stash changes first"]
            )

        return SafetyCheck(
            safe=True,
            warnings=["Hard reset cannot be undone easily"]
        )

    async def get_head_authorship(self) -> tuple[str, str]:
        """Get author name and email of HEAD commit."""
        out, _, _ = await self.repo.run_git(
            "log", "-1", "--format=%an%n%ae"
        )
        lines = out.split("\n")
        return lines[0], lines[1] if len(lines) > 1 else ""

    async def is_pushed(self, ref: str = "HEAD") -> bool:
        """Check if commit is pushed to remote.

        A commit is considered pushed if it exists on any remote
        tracking branch.
        """
        try:
            # Get the commit hash
            hash_out, _, _ = await self.repo.run_git("rev-parse", ref)
            commit_hash = hash_out.strip()

            # Check if any remote has this commit
            out, _, code = await self.repo.run_git(
                "branch", "-r", "--contains", commit_hash,
                check=False
            )
            return bool(out.strip())
        except GitError:
            return False

    async def validate_commit_message(self, message: str) -> SafetyCheck:
        """Validate commit message format."""
        warnings = []

        lines = message.split("\n")
        subject = lines[0] if lines else ""

        # Check subject length
        if len(subject) > 72:
            warnings.append("Subject line exceeds 72 characters")

        # Check for empty message
        if not subject.strip():
            return SafetyCheck(
                safe=False,
                reason="Commit message cannot be empty"
            )

        # Check for conventional format (informational)
        if not any(subject.lower().startswith(p) for p in
                   ["feat", "fix", "docs", "style", "refactor",
                    "test", "chore", "build", "ci"]):
            warnings.append("Consider using conventional commit format")

        return SafetyCheck(safe=True, warnings=warnings)
```

---

## Step 6: Git Operations (operations.py)

```python
# src/opencode/git/operations.py
"""Git operations with safety guards."""

import logging
from typing import Any

from .repository import GitBranch, GitCommit, GitRepository, GitError
from .safety import GitSafety

logger = logging.getLogger(__name__)


class UnsafeOperationError(GitError):
    """Raised when an unsafe operation is attempted."""
    pass


class GitOperations:
    """Git operations with safety guards."""

    def __init__(self, repo: GitRepository):
        self.repo = repo
        self.safety = GitSafety(repo)

    # === Staging ===

    async def stage(self, paths: list[str]) -> None:
        """Stage files for commit."""
        if not paths:
            return
        await self.repo.run_git("add", "--", *paths)
        logger.info(f"Staged {len(paths)} file(s)")

    async def unstage(self, paths: list[str]) -> None:
        """Unstage files."""
        if not paths:
            return
        await self.repo.run_git("restore", "--staged", "--", *paths)
        logger.info(f"Unstaged {len(paths)} file(s)")

    async def stage_all(self) -> None:
        """Stage all changes."""
        await self.repo.run_git("add", "-A")
        logger.info("Staged all changes")

    # === Commits ===

    async def commit(
        self,
        message: str,
        amend: bool = False,
        allow_empty: bool = False
    ) -> GitCommit:
        """Create a commit.

        Args:
            message: Commit message
            amend: Amend previous commit
            allow_empty: Allow empty commits

        Returns:
            Created commit
        """
        # Validate message
        check = await self.safety.validate_commit_message(message)
        if not check.safe:
            raise GitError(f"Invalid commit message: {check.reason}")

        # Check amend safety
        if amend:
            check = await self.safety.check_amend()
            if not check.safe:
                raise UnsafeOperationError(
                    f"Cannot amend: {check.reason}"
                )

        args = ["commit", "-m", message]
        if amend:
            args.append("--amend")
        if allow_empty:
            args.append("--allow-empty")

        await self.repo.run_git(*args)

        # Get new commit
        format_str = "%H%n%h%n%an%n%ae%n%ai%n%s"
        out, _, _ = await self.repo.run_git(
            "log", "-1", f"--format={format_str}"
        )
        lines = out.split("\n")

        commit = GitCommit(
            hash=lines[0],
            short_hash=lines[1],
            author=lines[2],
            author_email=lines[3],
            date=lines[4],
            message=message
        )

        logger.info(f"Created commit {commit.short_hash}")
        return commit

    # === Branches ===

    async def create_branch(
        self,
        name: str,
        start_point: str | None = None
    ) -> GitBranch:
        """Create a branch."""
        args = ["branch", name]
        if start_point:
            args.append(start_point)

        await self.repo.run_git(*args)
        logger.info(f"Created branch {name}")

        return GitBranch(name=name, is_current=False)

    async def switch_branch(self, name: str) -> None:
        """Switch to a branch."""
        await self.repo.run_git("switch", name)
        logger.info(f"Switched to branch {name}")

    async def delete_branch(
        self,
        name: str,
        force: bool = False
    ) -> None:
        """Delete a branch."""
        check = await self.safety.check_branch_delete(name)
        if not check.safe:
            raise UnsafeOperationError(
                f"Cannot delete branch: {check.reason}"
            )

        args = ["branch", "-D" if force else "-d", name]
        await self.repo.run_git(*args)
        logger.info(f"Deleted branch {name}")

    # === Remote Operations ===

    async def fetch(
        self,
        remote: str = "origin",
        prune: bool = False
    ) -> None:
        """Fetch from remote."""
        args = ["fetch", remote]
        if prune:
            args.append("--prune")

        await self.repo.run_git(*args)
        logger.info(f"Fetched from {remote}")

    async def pull(
        self,
        remote: str = "origin",
        branch: str | None = None
    ) -> None:
        """Pull from remote."""
        args = ["pull", remote]
        if branch:
            args.append(branch)

        await self.repo.run_git(*args)
        logger.info(f"Pulled from {remote}")

    async def push(
        self,
        remote: str = "origin",
        branch: str | None = None,
        set_upstream: bool = False,
        force: bool = False
    ) -> None:
        """Push to remote."""
        if force:
            check = await self.safety.check_force_push(branch)
            if not check.safe:
                raise UnsafeOperationError(
                    f"Cannot force push: {check.reason}"
                )

        args = ["push", remote]
        if branch:
            args.append(branch)
        if set_upstream:
            args.insert(1, "-u")
        if force:
            args.insert(1, "--force-with-lease")

        await self.repo.run_git(*args)
        logger.info(f"Pushed to {remote}")

    # === Utility ===

    async def stash(self, message: str | None = None) -> None:
        """Stash changes."""
        args = ["stash", "push"]
        if message:
            args.extend(["-m", message])

        await self.repo.run_git(*args)
        logger.info("Stashed changes")

    async def stash_pop(self) -> None:
        """Pop stashed changes."""
        await self.repo.run_git("stash", "pop")
        logger.info("Popped stashed changes")
```

---

## Step 7: Package Exports (__init__.py)

```python
# src/opencode/git/__init__.py
"""Git integration for OpenCode."""

from .diff import DiffFile, GitDiff, GitDiffTool
from .history import GitHistory, LogEntry
from .operations import GitOperations, UnsafeOperationError
from .repository import (
    GitBranch,
    GitCommit,
    GitError,
    GitRemote,
    GitRepository,
    RepositoryInfo,
)
from .safety import GitSafety, SafetyCheck
from .status import FileStatus, GitStatus, GitStatusTool

__all__ = [
    # Repository
    "GitRepository",
    "RepositoryInfo",
    "GitRemote",
    "GitBranch",
    "GitCommit",
    "GitError",
    # Status
    "GitStatus",
    "GitStatusTool",
    "FileStatus",
    # History
    "GitHistory",
    "LogEntry",
    # Diff
    "GitDiff",
    "GitDiffTool",
    "DiffFile",
    # Operations
    "GitOperations",
    "UnsafeOperationError",
    # Safety
    "GitSafety",
    "SafetyCheck",
]
```

---

## Testing Strategy

1. **Repository tests**: Detect repo, get info
2. **Status tests**: Parse porcelain output
3. **History tests**: Parse log output
4. **Diff tests**: Parse diff output
5. **Safety tests**: Check all safety conditions
6. **Operations tests**: Stage, commit, branch
7. **Integration tests**: Real Git repository

---

## Notes

- All Git commands run asynchronously
- Safety guards prevent dangerous operations
- Commit authorship verified before amend
- Protected branches cannot be force-pushed
- Clear error messages for all failures
