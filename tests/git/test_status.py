"""Tests for git status module."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from code_forge.git.repository import GitRepository
from code_forge.git.status import FileStatus, GitStatus, GitStatusTool


class TestFileStatus:
    """Tests for FileStatus dataclass."""

    def test_basic_creation(self) -> None:
        """Test basic file status creation."""
        status = FileStatus(path="file.py", status="M", staged=True)
        assert status.path == "file.py"
        assert status.status == "M"
        assert status.staged is True
        assert status.original_path is None

    def test_with_original_path(self) -> None:
        """Test file status with original path (rename)."""
        status = FileStatus(
            path="new_name.py",
            status="R",
            staged=True,
            original_path="old_name.py",
        )
        assert status.original_path == "old_name.py"

    def test_status_name_modified(self) -> None:
        """Test status_name for modified."""
        status = FileStatus(path="file.py", status="M", staged=True)
        assert status.status_name == "modified"

    def test_status_name_added(self) -> None:
        """Test status_name for added."""
        status = FileStatus(path="file.py", status="A", staged=True)
        assert status.status_name == "added"

    def test_status_name_deleted(self) -> None:
        """Test status_name for deleted."""
        status = FileStatus(path="file.py", status="D", staged=True)
        assert status.status_name == "deleted"

    def test_status_name_renamed(self) -> None:
        """Test status_name for renamed."""
        status = FileStatus(path="file.py", status="R", staged=True)
        assert status.status_name == "renamed"

    def test_status_name_copied(self) -> None:
        """Test status_name for copied."""
        status = FileStatus(path="file.py", status="C", staged=True)
        assert status.status_name == "copied"

    def test_status_name_unmerged(self) -> None:
        """Test status_name for unmerged."""
        status = FileStatus(path="file.py", status="U", staged=False)
        assert status.status_name == "unmerged"

    def test_status_name_untracked(self) -> None:
        """Test status_name for untracked."""
        status = FileStatus(path="file.py", status="?", staged=False)
        assert status.status_name == "untracked"

    def test_status_name_unknown(self) -> None:
        """Test status_name for unknown status."""
        status = FileStatus(path="file.py", status="X", staged=False)
        assert status.status_name == "unknown"


class TestGitStatus:
    """Tests for GitStatus dataclass."""

    def test_empty_status(self) -> None:
        """Test empty status (clean repo)."""
        status = GitStatus()
        assert status.branch is None
        assert status.tracking is None
        assert status.ahead == 0
        assert status.behind == 0
        assert status.staged == []
        assert status.unstaged == []
        assert status.untracked == []
        assert status.conflicts == []

    def test_is_clean_true(self) -> None:
        """Test is_clean when repo is clean."""
        status = GitStatus(branch="main")
        assert status.is_clean is True

    def test_is_clean_false_staged(self) -> None:
        """Test is_clean with staged files."""
        status = GitStatus(
            staged=[FileStatus(path="file.py", status="A", staged=True)]
        )
        assert status.is_clean is False

    def test_is_clean_false_unstaged(self) -> None:
        """Test is_clean with unstaged files."""
        status = GitStatus(
            unstaged=[FileStatus(path="file.py", status="M", staged=False)]
        )
        assert status.is_clean is False

    def test_is_clean_false_untracked(self) -> None:
        """Test is_clean with untracked files."""
        status = GitStatus(
            untracked=[FileStatus(path="file.py", status="?", staged=False)]
        )
        assert status.is_clean is False

    def test_is_clean_false_conflicts(self) -> None:
        """Test is_clean with conflicts."""
        status = GitStatus(
            conflicts=[FileStatus(path="file.py", status="U", staged=False)]
        )
        assert status.is_clean is False

    def test_total_changes(self) -> None:
        """Test total_changes calculation."""
        status = GitStatus(
            staged=[FileStatus(path="a.py", status="A", staged=True)],
            unstaged=[
                FileStatus(path="b.py", status="M", staged=False),
                FileStatus(path="c.py", status="M", staged=False),
            ],
            untracked=[FileStatus(path="d.py", status="?", staged=False)],
            conflicts=[FileStatus(path="e.py", status="U", staged=False)],
        )
        assert status.total_changes == 5

    def test_to_string_clean(self) -> None:
        """Test to_string for clean repo."""
        status = GitStatus(branch="main")
        output = status.to_string()
        assert "On branch main" in output
        assert "Nothing to commit, working tree clean" in output

    def test_to_string_with_tracking(self) -> None:
        """Test to_string with tracking info."""
        status = GitStatus(
            branch="main",
            tracking="origin/main",
            ahead=2,
            behind=1,
        )
        output = status.to_string()
        assert "ahead 2" in output
        assert "behind 1" in output

    def test_to_string_ahead_only(self) -> None:
        """Test to_string with ahead only."""
        status = GitStatus(
            branch="main",
            tracking="origin/main",
            ahead=3,
        )
        output = status.to_string()
        assert "ahead 3" in output
        assert "behind" not in output

    def test_to_string_behind_only(self) -> None:
        """Test to_string with behind only."""
        status = GitStatus(
            branch="main",
            tracking="origin/main",
            behind=2,
        )
        output = status.to_string()
        assert "behind 2" in output
        assert "ahead" not in output

    def test_to_string_with_staged(self) -> None:
        """Test to_string with staged files."""
        status = GitStatus(
            branch="main",
            staged=[FileStatus(path="file.py", status="A", staged=True)],
        )
        output = status.to_string()
        assert "Changes to be committed" in output
        assert "added: file.py" in output

    def test_to_string_with_unstaged(self) -> None:
        """Test to_string with unstaged files."""
        status = GitStatus(
            branch="main",
            unstaged=[FileStatus(path="file.py", status="M", staged=False)],
        )
        output = status.to_string()
        assert "Changes not staged for commit" in output
        assert "modified: file.py" in output

    def test_to_string_with_untracked(self) -> None:
        """Test to_string with untracked files."""
        status = GitStatus(
            branch="main",
            untracked=[FileStatus(path="new.py", status="?", staged=False)],
        )
        output = status.to_string()
        assert "Untracked files" in output
        assert "new.py" in output

    def test_to_string_with_conflicts(self) -> None:
        """Test to_string with conflicts."""
        status = GitStatus(
            branch="main",
            conflicts=[FileStatus(path="conflict.py", status="U", staged=False)],
        )
        output = status.to_string()
        assert "Unmerged paths" in output
        assert "conflict.py" in output


class TestGitStatusTool:
    """Tests for GitStatusTool class."""

    @pytest.fixture
    def mock_repo(self) -> GitRepository:
        """Create mock repository."""
        repo = GitRepository("/project")
        repo._root = "/project"
        return repo

    @pytest.mark.asyncio
    async def test_get_status_clean(self, mock_repo: GitRepository) -> None:
        """Test get_status for clean repo."""
        porcelain_output = "# branch.head main\n# branch.upstream origin/main\n# branch.ab +0 -0"

        async def mock_run_git(*args, **kwargs):
            return (porcelain_output, "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitStatusTool(mock_repo)
            status = await tool.get_status()

        assert status.branch == "main"
        assert status.tracking == "origin/main"
        assert status.is_clean is True

    @pytest.mark.asyncio
    async def test_get_status_with_staged(self, mock_repo: GitRepository) -> None:
        """Test get_status with staged files."""
        porcelain_output = (
            "# branch.head main\n"
            "1 A. N... 000000 100644 100644 0000000000000000000000000000000000000000 abc123 new_file.py"
        )

        async def mock_run_git(*args, **kwargs):
            return (porcelain_output, "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitStatusTool(mock_repo)
            status = await tool.get_status()

        assert len(status.staged) == 1
        assert status.staged[0].path == "new_file.py"
        assert status.staged[0].status == "A"

    @pytest.mark.asyncio
    async def test_get_status_with_modified(self, mock_repo: GitRepository) -> None:
        """Test get_status with modified files."""
        porcelain_output = (
            "# branch.head main\n"
            "1 .M N... 100644 100644 100644 abc123 def456 modified_file.py"
        )

        async def mock_run_git(*args, **kwargs):
            return (porcelain_output, "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitStatusTool(mock_repo)
            status = await tool.get_status()

        assert len(status.unstaged) == 1
        assert status.unstaged[0].path == "modified_file.py"
        assert status.unstaged[0].status == "M"

    @pytest.mark.asyncio
    async def test_get_status_with_untracked(self, mock_repo: GitRepository) -> None:
        """Test get_status with untracked files."""
        porcelain_output = "# branch.head main\n? untracked_file.py"

        async def mock_run_git(*args, **kwargs):
            return (porcelain_output, "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitStatusTool(mock_repo)
            status = await tool.get_status()

        assert len(status.untracked) == 1
        assert status.untracked[0].path == "untracked_file.py"

    @pytest.mark.asyncio
    async def test_get_status_with_conflict(self, mock_repo: GitRepository) -> None:
        """Test get_status with conflict."""
        porcelain_output = "# branch.head main\nu UU N... 100644 100644 100644 100644 abc def ghi\tconflict.py"

        async def mock_run_git(*args, **kwargs):
            return (porcelain_output, "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitStatusTool(mock_repo)
            status = await tool.get_status()

        assert len(status.conflicts) == 1
        assert status.conflicts[0].path == "conflict.py"

    @pytest.mark.asyncio
    async def test_get_status_ahead_behind(self, mock_repo: GitRepository) -> None:
        """Test get_status with ahead/behind."""
        porcelain_output = "# branch.head feature\n# branch.upstream origin/feature\n# branch.ab +3 -2"

        async def mock_run_git(*args, **kwargs):
            return (porcelain_output, "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitStatusTool(mock_repo)
            status = await tool.get_status()

        assert status.ahead == 3
        assert status.behind == 2

    @pytest.mark.asyncio
    async def test_get_staged_diff(self, mock_repo: GitRepository) -> None:
        """Test get_staged_diff."""
        diff_output = "diff --git a/file.py b/file.py\n+new line"

        async def mock_run_git(*args, **kwargs):
            return (diff_output, "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitStatusTool(mock_repo)
            diff = await tool.get_staged_diff()

        assert "diff --git" in diff

    @pytest.mark.asyncio
    async def test_get_unstaged_diff(self, mock_repo: GitRepository) -> None:
        """Test get_unstaged_diff."""
        diff_output = "diff --git a/file.py b/file.py\n-old line\n+new line"

        async def mock_run_git(*args, **kwargs):
            return (diff_output, "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitStatusTool(mock_repo)
            diff = await tool.get_unstaged_diff()

        assert "diff --git" in diff

    @pytest.mark.asyncio
    async def test_get_short_status_clean(self, mock_repo: GitRepository) -> None:
        """Test get_short_status for clean repo."""
        porcelain_output = "# branch.head main"

        async def mock_run_git(*args, **kwargs):
            return (porcelain_output, "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitStatusTool(mock_repo)
            short = await tool.get_short_status()

        assert short == "clean"

    @pytest.mark.asyncio
    async def test_get_short_status_with_changes(self, mock_repo: GitRepository) -> None:
        """Test get_short_status with changes."""
        porcelain_output = (
            "# branch.head main\n"
            "1 A. N... 000000 100644 100644 000000 abc123 staged.py\n"
            "1 .M N... 100644 100644 100644 abc123 def456 modified.py\n"
            "? untracked.py"
        )

        async def mock_run_git(*args, **kwargs):
            return (porcelain_output, "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitStatusTool(mock_repo)
            short = await tool.get_short_status()

        assert "1 staged" in short
        assert "1 modified" in short
        assert "1 untracked" in short

    @pytest.mark.asyncio
    async def test_parse_renamed_file(self, mock_repo: GitRepository) -> None:
        """Test parsing renamed file."""
        # Porcelain v2 format for rename: "2 R. ... score path\told_path"
        porcelain_output = (
            "# branch.head main\n"
            "2 R. N... 100644 100644 100644 abc123 def456 R100 new_name.py\told_name.py"
        )

        async def mock_run_git(*args, **kwargs):
            return (porcelain_output, "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitStatusTool(mock_repo)
            status = await tool.get_status()

        assert len(status.staged) == 1
        assert status.staged[0].path == "new_name.py"
        assert status.staged[0].original_path == "old_name.py"
