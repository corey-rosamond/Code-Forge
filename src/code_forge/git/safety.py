"""Safety guards for Git operations."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import ClassVar

from .repository import GitError, GitRepository

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
    PROTECTED_BRANCHES: ClassVar[set[str]] = {"main", "master", "develop", "production", "release"}

    def __init__(self, repo: GitRepository) -> None:
        """Initialize safety checker.

        Args:
            repo: Git repository instance
        """
        self.repo = repo

    async def check_amend(self) -> SafetyCheck:
        """Check if amend is safe.

        Safe if:
        - HEAD commit is not pushed
        - HEAD commit is authored by current user (warning only)

        Returns:
            SafetyCheck result
        """
        warnings: list[str] = []

        # Check if pushed
        is_pushed = await self.is_pushed("HEAD")
        if is_pushed:
            return SafetyCheck(
                safe=False,
                reason="HEAD commit has been pushed to remote",
                warnings=["Amending pushed commits can cause issues for others"],
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
        branch: str | None = None,
    ) -> SafetyCheck:
        """Check if force push is safe.

        Args:
            branch: Branch to check (default: current branch)

        Returns:
            SafetyCheck result
        """
        branch = branch or self.repo.current_branch

        if branch and branch in self.PROTECTED_BRANCHES:
            return SafetyCheck(
                safe=False,
                reason=f"Force push to protected branch '{branch}' is not allowed",
            )

        return SafetyCheck(
            safe=True,
            warnings=[
                "Force push will rewrite remote history",
                "Other users may be affected",
            ],
        )

    async def check_branch_delete(self, branch: str) -> SafetyCheck:
        """Check if branch delete is safe.

        Args:
            branch: Branch to delete

        Returns:
            SafetyCheck result
        """
        warnings: list[str] = []

        # Check if it's current branch
        if branch == self.repo.current_branch:
            return SafetyCheck(
                safe=False,
                reason="Cannot delete current branch",
            )

        # Check if protected
        if branch in self.PROTECTED_BRANCHES:
            return SafetyCheck(
                safe=False,
                reason=f"Cannot delete protected branch '{branch}'",
            )

        # Check if merged
        try:
            out, _, _ = await self.repo.run_git(
                "branch", "--merged", "HEAD", check=False
            )
            merged_branches = [b.strip().lstrip("* ") for b in out.split("\n")]
            if branch not in merged_branches:
                warnings.append(f"Branch '{branch}' is not merged into HEAD")
        except GitError:
            pass

        return SafetyCheck(safe=True, warnings=warnings)

    async def check_hard_reset(self) -> SafetyCheck:
        """Check if hard reset is safe.

        Returns:
            SafetyCheck result
        """
        # Check for uncommitted changes
        out, _, _ = await self.repo.run_git("status", "--porcelain")
        if out:
            return SafetyCheck(
                safe=False,
                reason="Uncommitted changes would be lost",
                warnings=["Commit or stash changes first"],
            )

        return SafetyCheck(
            safe=True,
            warnings=["Hard reset cannot be undone easily"],
        )

    async def check_checkout(self, target: str) -> SafetyCheck:
        """Check if checkout is safe.

        Args:
            target: Branch or commit to checkout

        Returns:
            SafetyCheck result
        """
        # Check for uncommitted changes that would be overwritten
        out, _, _ = await self.repo.run_git("status", "--porcelain")
        if out:
            # Check if the changes would conflict
            try:
                await self.repo.run_git(
                    "checkout", "--dry-run", target, check=True
                )
            except GitError:
                return SafetyCheck(
                    safe=False,
                    reason="Uncommitted changes would be overwritten",
                    warnings=[
                        "Commit, stash, or discard changes first",
                        f"Changed files: {len(out.split(chr(10)))}",
                    ],
                )

        return SafetyCheck(safe=True)

    async def get_head_authorship(self) -> tuple[str, str]:
        """Get author name and email of HEAD commit.

        Returns:
            Tuple of (author name, author email)
        """
        out, _, _ = await self.repo.run_git("log", "-1", "--format=%an%n%ae")
        lines = out.split("\n")
        return lines[0], lines[1] if len(lines) > 1 else ""

    async def is_pushed(self, ref: str = "HEAD") -> bool:
        """Check if commit is pushed to remote.

        A commit is considered pushed if it exists on any remote
        tracking branch.

        Args:
            ref: Commit reference

        Returns:
            True if pushed to any remote
        """
        try:
            # Get the commit hash
            hash_out, _, _ = await self.repo.run_git("rev-parse", ref)
            commit_hash = hash_out.strip()

            # Check if any remote has this commit
            out, _, _ = await self.repo.run_git(
                "branch", "-r", "--contains", commit_hash, check=False
            )
            return bool(out.strip())
        except GitError:
            return False

    async def validate_commit_message(self, message: str) -> SafetyCheck:
        """Validate commit message format.

        Args:
            message: Commit message to validate

        Returns:
            SafetyCheck result
        """
        warnings: list[str] = []

        lines = message.split("\n")
        subject = lines[0] if lines else ""

        # Check subject length
        if len(subject) > 72:
            warnings.append("Subject line exceeds 72 characters")

        # Check for empty message
        if not subject.strip():
            return SafetyCheck(
                safe=False,
                reason="Commit message cannot be empty",
            )

        # Check second line should be blank
        if len(lines) > 1 and lines[1].strip():
            warnings.append("Second line should be blank (separates subject from body)")

        # Check for conventional format (informational)
        conventional_prefixes = [
            "feat",
            "fix",
            "docs",
            "style",
            "refactor",
            "test",
            "chore",
            "build",
            "ci",
            "perf",
            "revert",
        ]
        if not any(subject.lower().startswith(p) for p in conventional_prefixes):
            warnings.append("Consider using conventional commit format")

        return SafetyCheck(safe=True, warnings=warnings)

    async def check_rebase(self, onto: str | None = None) -> SafetyCheck:
        """Check if rebase is safe.

        Args:
            onto: Target branch for rebase

        Returns:
            SafetyCheck result
        """
        warnings: list[str] = []

        # Check for uncommitted changes
        out, _, _ = await self.repo.run_git("status", "--porcelain")
        if out:
            return SafetyCheck(
                safe=False,
                reason="Cannot rebase with uncommitted changes",
                warnings=["Commit or stash changes first"],
            )

        # Check if current branch is pushed
        current_branch = self.repo.current_branch
        if current_branch:
            is_pushed = await self.is_pushed("HEAD")
            if is_pushed:
                warnings.append(
                    f"Branch '{current_branch}' has pushed commits - "
                    "rebase will rewrite history"
                )

        # Check if rebasing onto protected branch
        if onto and onto in self.PROTECTED_BRANCHES:
            warnings.append(f"Rebasing onto protected branch '{onto}'")

        return SafetyCheck(safe=True, warnings=warnings)

    async def check_merge(self, branch: str) -> SafetyCheck:
        """Check if merge is safe.

        Args:
            branch: Branch to merge

        Returns:
            SafetyCheck result
        """
        # Check for uncommitted changes
        out, _, _ = await self.repo.run_git("status", "--porcelain")
        if out:
            return SafetyCheck(
                safe=False,
                reason="Cannot merge with uncommitted changes",
                warnings=["Commit or stash changes first"],
            )

        # Check for potential conflicts (dry run)
        try:
            await self.repo.run_git("merge", "--no-commit", "--no-ff", branch)
            # Abort the merge
            await self.repo.run_git("merge", "--abort", check=False)
            return SafetyCheck(safe=True)
        except GitError as e:
            # Abort the merge
            await self.repo.run_git("merge", "--abort", check=False)
            if "conflict" in e.stderr.lower():
                return SafetyCheck(
                    safe=True,
                    warnings=[f"Merge will have conflicts with branch '{branch}'"],
                )
            return SafetyCheck(
                safe=False,
                reason=f"Merge check failed: {e.stderr}",
            )
