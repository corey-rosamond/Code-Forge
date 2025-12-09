"""Git context for LLM integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .status import GitStatusTool

if TYPE_CHECKING:
    from .repository import GitRepository


class GitContext:
    """Git context provider for LLM system prompt."""

    def __init__(self, repo: GitRepository) -> None:
        """Initialize context provider.

        Args:
            repo: Git repository instance
        """
        self.repo = repo
        self._status_tool = GitStatusTool(repo)

    def get_context_summary(self) -> str:
        """Get Git context summary for system prompt.

        Returns:
            Formatted context string
        """
        if not self.repo.is_git_repo:
            return "Working directory is not a Git repository."

        lines = []
        lines.append("Git Repository Context:")

        # Branch info
        branch = self.repo.current_branch
        if branch:
            lines.append(f"  Branch: {branch}")
        else:
            lines.append("  Branch: (detached HEAD)")

        # Dirty state
        if self.repo.is_dirty:
            lines.append("  Status: Has uncommitted changes")
        else:
            lines.append("  Status: Clean")

        return "\n".join(lines)

    async def get_detailed_context(self) -> str:
        """Get detailed Git context.

        Returns:
            Detailed context string
        """
        if not self.repo.is_git_repo:
            return "Working directory is not a Git repository."

        lines = []
        lines.append("Git Repository Context:")

        # Get full info
        info = await self.repo.get_info()

        lines.append(f"  Root: {info.root}")
        lines.append(f"  Branch: {info.current_branch or '(detached HEAD)'}")

        if info.head_commit:
            lines.append(f"  HEAD: {info.head_commit.short_hash} - {info.head_commit.subject}")

        if info.remotes:
            remote_names = [r.name for r in info.remotes]
            lines.append(f"  Remotes: {', '.join(remote_names)}")

        # Get status
        status = await self._status_tool.get_status()

        if status.is_clean:
            lines.append("  Status: Clean")
        else:
            status_parts = []
            if status.staged:
                status_parts.append(f"{len(status.staged)} staged")
            if status.unstaged:
                status_parts.append(f"{len(status.unstaged)} modified")
            if status.untracked:
                status_parts.append(f"{len(status.untracked)} untracked")
            if status.conflicts:
                status_parts.append(f"{len(status.conflicts)} conflicts")
            lines.append(f"  Status: {', '.join(status_parts)}")

        if status.tracking:
            tracking_info = f"Tracking: {status.tracking}"
            if status.ahead or status.behind:
                tracking_info += f" (ahead {status.ahead}, behind {status.behind})"
            lines.append(f"  {tracking_info}")

        return "\n".join(lines)

    async def get_status_summary(self) -> str:
        """Get brief status summary.

        Returns:
            Short status line
        """
        if not self.repo.is_git_repo:
            return "Not a git repository"

        return await self._status_tool.get_short_status()

    async def format_for_commit(self, staged_diff: str) -> str:
        """Format staged changes for commit message generation.

        Args:
            staged_diff: Diff of staged changes

        Returns:
            Formatted context for LLM commit message generation
        """
        lines = []
        lines.append("## Staged Changes for Commit")
        lines.append("")

        # Get status
        status = await self._status_tool.get_status()

        if not status.staged:
            lines.append("No changes staged for commit.")
            return "\n".join(lines)

        # List staged files
        lines.append("### Files to be committed:")
        for f in status.staged:
            lines.append(f"- {f.status_name}: {f.path}")
            if f.original_path:
                lines.append(f"  (renamed from {f.original_path})")

        lines.append("")
        lines.append("### Diff:")
        lines.append("```diff")
        # Truncate diff if too long
        max_diff_lines = 200
        diff_lines = staged_diff.split("\n")
        if len(diff_lines) > max_diff_lines:
            lines.extend(diff_lines[:max_diff_lines])
            lines.append(f"... ({len(diff_lines) - max_diff_lines} more lines)")
        else:
            lines.append(staged_diff)
        lines.append("```")

        return "\n".join(lines)

    async def format_for_review(self) -> str:
        """Format repository state for code review context.

        Returns:
            Formatted context for code review
        """
        lines = []
        lines.append("## Repository State for Review")
        lines.append("")

        if not self.repo.is_git_repo:
            lines.append("Not a git repository.")
            return "\n".join(lines)

        info = await self.repo.get_info()

        lines.append(f"**Branch:** {info.current_branch or 'detached HEAD'}")

        if info.head_commit:
            lines.append(f"**Latest Commit:** {info.head_commit.short_hash}")
            lines.append(f"**Author:** {info.head_commit.author}")
            lines.append(f"**Date:** {info.head_commit.date}")
            lines.append(f"**Message:** {info.head_commit.subject}")

        lines.append("")

        # Get status
        status = await self._status_tool.get_status()

        if not status.is_clean:
            lines.append("### Uncommitted Changes:")
            if status.staged:
                lines.append(f"- {len(status.staged)} file(s) staged")
            if status.unstaged:
                lines.append(f"- {len(status.unstaged)} file(s) modified")
            if status.untracked:
                lines.append(f"- {len(status.untracked)} file(s) untracked")
        else:
            lines.append("Working tree is clean.")

        return "\n".join(lines)

    def get_branch_for_prompt(self) -> str:
        """Get branch info formatted for system prompt.

        Returns:
            Branch info string or empty if not a repo
        """
        if not self.repo.is_git_repo:
            return ""

        branch = self.repo.current_branch
        dirty = " (dirty)" if self.repo.is_dirty else ""

        return f"[{branch or 'detached'}{dirty}]"
