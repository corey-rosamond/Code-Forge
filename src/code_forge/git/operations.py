"""Git operations with safety guards."""

from __future__ import annotations

import logging

from .repository import GitBranch, GitCommit, GitError, GitRepository
from .safety import GitSafety

logger = logging.getLogger(__name__)


class UnsafeOperationError(GitError):
    """Raised when an unsafe operation is attempted."""

    pass


class GitOperations:
    """Git operations with safety guards."""

    def __init__(self, repo: GitRepository) -> None:
        """Initialize operations.

        Args:
            repo: Git repository instance
        """
        self.repo = repo
        self.safety = GitSafety(repo)

    # === Staging ===

    async def stage(self, paths: list[str]) -> None:
        """Stage files for commit.

        Args:
            paths: Files to stage
        """
        if not paths:
            return
        await self.repo.run_git("add", "--", *paths)
        self.repo.invalidate_cache()
        logger.info(f"Staged {len(paths)} file(s)")

    async def unstage(self, paths: list[str]) -> None:
        """Unstage files.

        Args:
            paths: Files to unstage
        """
        if not paths:
            return
        await self.repo.run_git("restore", "--staged", "--", *paths)
        self.repo.invalidate_cache()
        logger.info(f"Unstaged {len(paths)} file(s)")

    async def stage_all(self) -> None:
        """Stage all changes."""
        await self.repo.run_git("add", "-A")
        self.repo.invalidate_cache()
        logger.info("Staged all changes")

    async def discard(self, paths: list[str]) -> None:
        """Discard changes in working tree.

        Args:
            paths: Files to discard changes for
        """
        if not paths:
            return
        await self.repo.run_git("restore", "--", *paths)
        self.repo.invalidate_cache()
        logger.info(f"Discarded changes in {len(paths)} file(s)")

    # === Commits ===

    async def commit(
        self,
        message: str,
        amend: bool = False,
        allow_empty: bool = False,
    ) -> GitCommit:
        """Create a commit.

        Args:
            message: Commit message
            amend: Amend previous commit
            allow_empty: Allow empty commits

        Returns:
            Created commit

        Raises:
            GitError: If commit fails
            UnsafeOperationError: If amend is unsafe
        """
        # Validate message
        check = await self.safety.validate_commit_message(message)
        if not check.safe:
            raise GitError(f"Invalid commit message: {check.reason}")

        # Check amend safety
        if amend:
            check = await self.safety.check_amend()
            if not check.safe:
                raise UnsafeOperationError(f"Cannot amend: {check.reason}")

        args = ["commit", "-m", message]
        if amend:
            args.append("--amend")
        if allow_empty:
            args.append("--allow-empty")

        await self.repo.run_git(*args)
        self.repo.invalidate_cache()

        # Get new commit
        format_str = "%H%n%h%n%an%n%ae%n%ai%n%s"
        out, _, _ = await self.repo.run_git("log", "-1", f"--format={format_str}")
        lines = out.split("\n")

        commit = GitCommit(
            hash=lines[0],
            short_hash=lines[1],
            author=lines[2],
            author_email=lines[3],
            date=lines[4],
            message=message,
        )

        logger.info(f"Created commit {commit.short_hash}")
        return commit

    # === Branches ===

    async def create_branch(
        self,
        name: str,
        start_point: str | None = None,
    ) -> GitBranch:
        """Create a branch.

        Args:
            name: Branch name
            start_point: Starting commit/branch

        Returns:
            Created branch
        """
        args = ["branch", name]
        if start_point:
            args.append(start_point)

        await self.repo.run_git(*args)
        logger.info(f"Created branch {name}")

        return GitBranch(name=name, is_current=False)

    async def switch_branch(self, name: str) -> None:
        """Switch to a branch.

        Args:
            name: Branch name

        Raises:
            GitError: If switch fails
        """
        check = await self.safety.check_checkout(name)
        if not check.safe:
            raise UnsafeOperationError(f"Cannot switch: {check.reason}")

        await self.repo.run_git("switch", name)
        self.repo.invalidate_cache()
        logger.info(f"Switched to branch {name}")

    async def checkout(self, target: str, create: bool = False) -> None:
        """Checkout branch or commit.

        Args:
            target: Branch or commit to checkout
            create: Create new branch

        Raises:
            GitError: If checkout fails
            UnsafeOperationError: If checkout is unsafe
        """
        check = await self.safety.check_checkout(target)
        if not check.safe:
            raise UnsafeOperationError(f"Cannot checkout: {check.reason}")

        args = ["checkout"]
        if create:
            args.append("-b")
        args.append(target)

        await self.repo.run_git(*args)
        self.repo.invalidate_cache()
        logger.info(f"Checked out {target}")

    async def delete_branch(
        self,
        name: str,
        force: bool = False,
    ) -> None:
        """Delete a branch.

        Args:
            name: Branch name
            force: Force delete even if not merged

        Raises:
            GitError: If delete fails
            UnsafeOperationError: If delete is unsafe
        """
        check = await self.safety.check_branch_delete(name)
        if not check.safe:
            raise UnsafeOperationError(f"Cannot delete branch: {check.reason}")

        args = ["branch", "-D" if force else "-d", name]
        await self.repo.run_git(*args)
        logger.info(f"Deleted branch {name}")

    # === Remote Operations ===

    async def fetch(
        self,
        remote: str = "origin",
        prune: bool = False,
    ) -> None:
        """Fetch from remote.

        Args:
            remote: Remote name
            prune: Remove deleted remote branches
        """
        args = ["fetch", remote]
        if prune:
            args.append("--prune")

        await self.repo.run_git(*args)
        self.repo.invalidate_cache()
        logger.info(f"Fetched from {remote}")

    async def pull(
        self,
        remote: str = "origin",
        branch: str | None = None,
        rebase: bool = False,
    ) -> None:
        """Pull from remote.

        Args:
            remote: Remote name
            branch: Branch to pull
            rebase: Use rebase instead of merge

        Raises:
            GitError: If pull fails
        """
        args = ["pull"]
        if rebase:
            args.append("--rebase")
        args.append(remote)
        if branch:
            args.append(branch)

        await self.repo.run_git(*args)
        self.repo.invalidate_cache()
        logger.info(f"Pulled from {remote}")

    async def push(
        self,
        remote: str = "origin",
        branch: str | None = None,
        set_upstream: bool = False,
        force: bool = False,
        force_with_lease: bool = False,
    ) -> None:
        """Push to remote.

        Args:
            remote: Remote name
            branch: Branch to push
            set_upstream: Set upstream tracking
            force: Force push (dangerous!)
            force_with_lease: Force with lease (safer)

        Raises:
            GitError: If push fails
            UnsafeOperationError: If force push to protected branch
        """
        if force or force_with_lease:
            check = await self.safety.check_force_push(branch)
            if not check.safe:
                raise UnsafeOperationError(f"Cannot force push: {check.reason}")

        args = ["push"]
        if set_upstream:
            args.append("-u")
        if force_with_lease:
            args.append("--force-with-lease")
        elif force:
            args.append("--force")
        args.append(remote)
        if branch:
            args.append(branch)

        await self.repo.run_git(*args)
        logger.info(f"Pushed to {remote}")

    # === Stash ===

    async def stash(self, message: str | None = None) -> None:
        """Stash changes.

        Args:
            message: Stash message
        """
        args = ["stash", "push"]
        if message:
            args.extend(["-m", message])

        await self.repo.run_git(*args)
        self.repo.invalidate_cache()
        logger.info("Stashed changes")

    async def stash_pop(self, index: int = 0) -> None:
        """Pop stashed changes.

        Args:
            index: Stash index to pop
        """
        await self.repo.run_git("stash", "pop", f"stash@{{{index}}}")
        self.repo.invalidate_cache()
        logger.info("Popped stashed changes")

    async def stash_list(self) -> list[str]:
        """List stashes.

        Returns:
            List of stash descriptions
        """
        out, _, _ = await self.repo.run_git("stash", "list", check=False)
        if not out:
            return []
        return [line for line in out.split("\n") if line.strip()]

    async def stash_drop(self, index: int = 0) -> None:
        """Drop a stash.

        Args:
            index: Stash index to drop
        """
        await self.repo.run_git("stash", "drop", f"stash@{{{index}}}")
        logger.info(f"Dropped stash@{{{index}}}")

    # === Tags ===

    async def create_tag(
        self,
        name: str,
        message: str | None = None,
        ref: str = "HEAD",
    ) -> None:
        """Create a tag.

        Args:
            name: Tag name
            message: Tag message (creates annotated tag)
            ref: Commit to tag
        """
        args = ["tag"]
        if message:
            args.extend(["-a", "-m", message])
        args.extend([name, ref])

        await self.repo.run_git(*args)
        logger.info(f"Created tag {name}")

    async def delete_tag(self, name: str) -> None:
        """Delete a tag.

        Args:
            name: Tag name
        """
        await self.repo.run_git("tag", "-d", name)
        logger.info(f"Deleted tag {name}")

    async def list_tags(self) -> list[str]:
        """List tags.

        Returns:
            List of tag names
        """
        out, _, _ = await self.repo.run_git("tag", "-l", check=False)
        if not out:
            return []
        return [line for line in out.split("\n") if line.strip()]

    # === Reset ===

    async def reset_soft(self, ref: str = "HEAD~1") -> None:
        """Soft reset (keep changes staged).

        Args:
            ref: Reference to reset to
        """
        await self.repo.run_git("reset", "--soft", ref)
        self.repo.invalidate_cache()
        logger.info(f"Soft reset to {ref}")

    async def reset_mixed(self, ref: str = "HEAD") -> None:
        """Mixed reset (keep changes unstaged).

        Args:
            ref: Reference to reset to
        """
        await self.repo.run_git("reset", "--mixed", ref)
        self.repo.invalidate_cache()
        logger.info(f"Mixed reset to {ref}")

    async def reset_hard(self, ref: str = "HEAD") -> None:
        """Hard reset (discard all changes).

        Args:
            ref: Reference to reset to

        Raises:
            UnsafeOperationError: If reset is unsafe
        """
        check = await self.safety.check_hard_reset()
        if not check.safe:
            raise UnsafeOperationError(f"Cannot hard reset: {check.reason}")

        await self.repo.run_git("reset", "--hard", ref)
        self.repo.invalidate_cache()
        logger.info(f"Hard reset to {ref}")

    # === Clean ===

    async def clean(
        self,
        directories: bool = False,
        force: bool = True,
        dry_run: bool = False,
    ) -> list[str]:
        """Clean untracked files.

        Args:
            directories: Also remove directories
            force: Required for actual removal
            dry_run: Only show what would be removed

        Returns:
            List of removed/would-be-removed files
        """
        args = ["clean"]
        if directories:
            args.append("-d")
        if force and not dry_run:
            args.append("-f")
        if dry_run:
            args.append("-n")

        out, _, _ = await self.repo.run_git(*args)
        self.repo.invalidate_cache()

        # Parse output
        files = []
        for line in out.split("\n"):
            if line.startswith("Would remove ") or line.startswith("Removing "):
                files.append(line.split(" ", 2)[-1])

        return files
