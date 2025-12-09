"""Tests for git context module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from opencode.git.context import GitContext
from opencode.git.repository import GitCommit, GitRemote, GitRepository, RepositoryInfo
from opencode.git.status import FileStatus, GitStatus


class TestGitContext:
    """Tests for GitContext class."""

    @pytest.fixture
    def mock_repo(self) -> GitRepository:
        """Create mock repository."""
        repo = GitRepository("/project")
        repo._root = Path("/project")
        repo._is_git_repo = True
        repo._current_branch_cache = "main"
        repo._dirty_cache = False
        return repo

    def test_init(self, mock_repo: GitRepository) -> None:
        """Test context initialization."""
        context = GitContext(mock_repo)
        assert context.repo == mock_repo

    def test_get_context_summary_not_repo(self) -> None:
        """Test get_context_summary when not a repo."""
        repo = GitRepository("/project")
        repo._is_git_repo = False

        context = GitContext(repo)
        summary = context.get_context_summary()

        assert "not a Git repository" in summary

    def test_get_context_summary_clean(self, mock_repo: GitRepository) -> None:
        """Test get_context_summary for clean repo."""
        context = GitContext(mock_repo)
        summary = context.get_context_summary()

        assert "Git Repository Context" in summary
        assert "Branch: main" in summary
        assert "Clean" in summary

    def test_get_context_summary_dirty(self, mock_repo: GitRepository) -> None:
        """Test get_context_summary for dirty repo."""
        mock_repo._dirty_cache = True

        context = GitContext(mock_repo)
        summary = context.get_context_summary()

        assert "uncommitted changes" in summary

    def test_get_context_summary_detached(self, mock_repo: GitRepository) -> None:
        """Test get_context_summary in detached HEAD."""
        mock_repo._current_branch_cache = None

        context = GitContext(mock_repo)
        summary = context.get_context_summary()

        assert "detached HEAD" in summary

    @pytest.mark.asyncio
    async def test_get_detailed_context_not_repo(self) -> None:
        """Test get_detailed_context when not a repo."""
        repo = GitRepository("/project")
        repo._is_git_repo = False

        context = GitContext(repo)
        detailed = await context.get_detailed_context()

        assert "not a Git repository" in detailed

    @pytest.mark.asyncio
    async def test_get_detailed_context(self, mock_repo: GitRepository) -> None:
        """Test get_detailed_context."""
        commit = GitCommit(
            hash="abc123def456",
            short_hash="abc123",
            author="Test Author",
            author_email="test@example.com",
            date="2024-01-15",
            message="Test commit",
        )
        remote = GitRemote(name="origin", url="https://github.com/test/repo")

        info = RepositoryInfo(
            root=Path("/project"),
            is_git_repo=True,
            current_branch="main",
            head_commit=commit,
            is_dirty=False,
            remotes=[remote],
        )

        status = GitStatus(branch="main")

        async def mock_get_info():
            return info

        async def mock_get_status():
            return status

        with patch.object(mock_repo, "get_info", side_effect=mock_get_info):
            context = GitContext(mock_repo)
            with patch.object(context._status_tool, "get_status", side_effect=mock_get_status):
                detailed = await context.get_detailed_context()

        assert "Root:" in detailed
        assert "Branch: main" in detailed
        assert "HEAD: abc123" in detailed
        assert "origin" in detailed
        assert "Clean" in detailed

    @pytest.mark.asyncio
    async def test_get_detailed_context_with_changes(self, mock_repo: GitRepository) -> None:
        """Test get_detailed_context with changes."""
        info = RepositoryInfo(
            root=Path("/project"),
            is_git_repo=True,
            current_branch="feature",
            head_commit=None,
            is_dirty=True,
        )

        status = GitStatus(
            branch="feature",
            tracking="origin/feature",
            ahead=2,
            behind=1,
            staged=[FileStatus(path="a.py", status="A", staged=True)],
            unstaged=[FileStatus(path="b.py", status="M", staged=False)],
            untracked=[FileStatus(path="c.py", status="?", staged=False)],
        )

        async def mock_get_info():
            return info

        async def mock_get_status():
            return status

        with patch.object(mock_repo, "get_info", side_effect=mock_get_info):
            context = GitContext(mock_repo)
            with patch.object(context._status_tool, "get_status", side_effect=mock_get_status):
                detailed = await context.get_detailed_context()

        assert "1 staged" in detailed
        assert "1 modified" in detailed
        assert "1 untracked" in detailed
        assert "Tracking" in detailed
        assert "ahead 2" in detailed

    @pytest.mark.asyncio
    async def test_get_status_summary_not_repo(self) -> None:
        """Test get_status_summary when not a repo."""
        repo = GitRepository("/project")
        repo._is_git_repo = False

        context = GitContext(repo)
        summary = await context.get_status_summary()

        assert "Not a git repository" in summary

    @pytest.mark.asyncio
    async def test_get_status_summary(self, mock_repo: GitRepository) -> None:
        """Test get_status_summary."""
        async def mock_short_status():
            return "2 staged, 1 modified"

        context = GitContext(mock_repo)
        with patch.object(context._status_tool, "get_short_status", side_effect=mock_short_status):
            summary = await context.get_status_summary()

        assert "2 staged" in summary

    @pytest.mark.asyncio
    async def test_format_for_commit_no_staged(self, mock_repo: GitRepository) -> None:
        """Test format_for_commit with no staged changes."""
        status = GitStatus(branch="main")

        async def mock_get_status():
            return status

        context = GitContext(mock_repo)
        with patch.object(context._status_tool, "get_status", side_effect=mock_get_status):
            output = await context.format_for_commit("")

        assert "No changes staged" in output

    @pytest.mark.asyncio
    async def test_format_for_commit_with_staged(self, mock_repo: GitRepository) -> None:
        """Test format_for_commit with staged changes."""
        status = GitStatus(
            branch="main",
            staged=[
                FileStatus(path="new.py", status="A", staged=True),
                FileStatus(path="modified.py", status="M", staged=True),
            ],
        )

        diff = "+new line\n-old line"

        async def mock_get_status():
            return status

        context = GitContext(mock_repo)
        with patch.object(context._status_tool, "get_status", side_effect=mock_get_status):
            output = await context.format_for_commit(diff)

        assert "Staged Changes for Commit" in output
        assert "Files to be committed" in output
        assert "added: new.py" in output
        assert "modified: modified.py" in output
        assert "```diff" in output
        assert "+new line" in output

    @pytest.mark.asyncio
    async def test_format_for_commit_truncates_long_diff(self, mock_repo: GitRepository) -> None:
        """Test format_for_commit truncates long diff."""
        status = GitStatus(
            branch="main",
            staged=[FileStatus(path="big.py", status="M", staged=True)],
        )

        # Create a very long diff
        long_diff = "\n".join([f"+line {i}" for i in range(300)])

        async def mock_get_status():
            return status

        context = GitContext(mock_repo)
        with patch.object(context._status_tool, "get_status", side_effect=mock_get_status):
            output = await context.format_for_commit(long_diff)

        assert "more lines" in output

    @pytest.mark.asyncio
    async def test_format_for_commit_with_rename(self, mock_repo: GitRepository) -> None:
        """Test format_for_commit with renamed file."""
        status = GitStatus(
            branch="main",
            staged=[
                FileStatus(
                    path="new_name.py",
                    status="R",
                    staged=True,
                    original_path="old_name.py",
                ),
            ],
        )

        async def mock_get_status():
            return status

        context = GitContext(mock_repo)
        with patch.object(context._status_tool, "get_status", side_effect=mock_get_status):
            output = await context.format_for_commit("")

        assert "renamed from old_name.py" in output

    @pytest.mark.asyncio
    async def test_format_for_review(self, mock_repo: GitRepository) -> None:
        """Test format_for_review."""
        commit = GitCommit(
            hash="abc123",
            short_hash="abc",
            author="Test Author",
            author_email="test@test.com",
            date="2024-01-15",
            message="Test commit",
        )
        info = RepositoryInfo(
            root=Path("/project"),
            is_git_repo=True,
            current_branch="feature",
            head_commit=commit,
            is_dirty=True,
        )

        status = GitStatus(
            branch="feature",
            staged=[FileStatus(path="a.py", status="A", staged=True)],
            unstaged=[FileStatus(path="b.py", status="M", staged=False)],
        )

        async def mock_get_info():
            return info

        async def mock_get_status():
            return status

        with patch.object(mock_repo, "get_info", side_effect=mock_get_info):
            context = GitContext(mock_repo)
            with patch.object(context._status_tool, "get_status", side_effect=mock_get_status):
                output = await context.format_for_review()

        assert "Repository State for Review" in output
        assert "Branch:" in output
        assert "Latest Commit:" in output
        assert "Author:" in output
        assert "Uncommitted Changes" in output

    @pytest.mark.asyncio
    async def test_format_for_review_not_repo(self) -> None:
        """Test format_for_review when not a repo."""
        repo = GitRepository("/project")
        repo._is_git_repo = False

        context = GitContext(repo)
        output = await context.format_for_review()

        assert "Not a git repository" in output

    @pytest.mark.asyncio
    async def test_format_for_review_clean(self, mock_repo: GitRepository) -> None:
        """Test format_for_review when clean."""
        info = RepositoryInfo(
            root=Path("/project"),
            is_git_repo=True,
            current_branch="main",
            head_commit=None,
            is_dirty=False,
        )

        status = GitStatus(branch="main")

        async def mock_get_info():
            return info

        async def mock_get_status():
            return status

        with patch.object(mock_repo, "get_info", side_effect=mock_get_info):
            context = GitContext(mock_repo)
            with patch.object(context._status_tool, "get_status", side_effect=mock_get_status):
                output = await context.format_for_review()

        assert "clean" in output.lower()

    def test_get_branch_for_prompt_not_repo(self) -> None:
        """Test get_branch_for_prompt when not a repo."""
        repo = GitRepository("/project")
        repo._is_git_repo = False

        context = GitContext(repo)
        result = context.get_branch_for_prompt()

        assert result == ""

    def test_get_branch_for_prompt_clean(self, mock_repo: GitRepository) -> None:
        """Test get_branch_for_prompt for clean repo."""
        context = GitContext(mock_repo)
        result = context.get_branch_for_prompt()

        assert result == "[main]"

    def test_get_branch_for_prompt_dirty(self, mock_repo: GitRepository) -> None:
        """Test get_branch_for_prompt for dirty repo."""
        mock_repo._dirty_cache = True

        context = GitContext(mock_repo)
        result = context.get_branch_for_prompt()

        assert result == "[main (dirty)]"

    def test_get_branch_for_prompt_detached(self, mock_repo: GitRepository) -> None:
        """Test get_branch_for_prompt in detached HEAD."""
        mock_repo._current_branch_cache = None

        context = GitContext(mock_repo)
        result = context.get_branch_for_prompt()

        assert result == "[detached]"

    def test_get_branch_for_prompt_detached_dirty(self, mock_repo: GitRepository) -> None:
        """Test get_branch_for_prompt in detached HEAD with changes."""
        mock_repo._current_branch_cache = None
        mock_repo._dirty_cache = True

        context = GitContext(mock_repo)
        result = context.get_branch_for_prompt()

        assert result == "[detached (dirty)]"
