"""Tests for git diff module."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from opencode.git.diff import DiffFile, GitDiff, GitDiffTool
from opencode.git.repository import GitRepository


class TestDiffFile:
    """Tests for DiffFile dataclass."""

    def test_basic_creation(self) -> None:
        """Test basic diff file creation."""
        diff_file = DiffFile(path="file.py")
        assert diff_file.path == "file.py"
        assert diff_file.old_path is None
        assert diff_file.status == "M"
        assert diff_file.additions == 0
        assert diff_file.deletions == 0
        assert diff_file.content is None

    def test_with_stats(self) -> None:
        """Test diff file with stats."""
        diff_file = DiffFile(
            path="file.py",
            status="A",
            additions=10,
            deletions=0,
        )
        assert diff_file.additions == 10
        assert diff_file.deletions == 0

    def test_is_rename_true(self) -> None:
        """Test is_rename for rename."""
        diff_file = DiffFile(
            path="new_name.py",
            old_path="old_name.py",
            status="R",
        )
        assert diff_file.is_rename is True

    def test_is_rename_false_no_old_path(self) -> None:
        """Test is_rename when no old path."""
        diff_file = DiffFile(path="file.py", status="R")
        assert diff_file.is_rename is False

    def test_is_rename_false_not_rename(self) -> None:
        """Test is_rename for non-rename."""
        diff_file = DiffFile(path="file.py", status="M")
        assert diff_file.is_rename is False


class TestGitDiff:
    """Tests for GitDiff dataclass."""

    def test_empty_diff(self) -> None:
        """Test empty diff."""
        diff = GitDiff()
        assert diff.files == []
        assert diff.total_additions == 0
        assert diff.total_deletions == 0
        assert diff.stat == ""

    def test_total_files(self) -> None:
        """Test total_files property."""
        diff = GitDiff(
            files=[
                DiffFile(path="a.py"),
                DiffFile(path="b.py"),
                DiffFile(path="c.py"),
            ]
        )
        assert diff.total_files == 3

    def test_to_string_empty(self) -> None:
        """Test to_string for empty diff."""
        diff = GitDiff()
        output = diff.to_string()
        assert output == ""

    def test_to_string_with_stat(self) -> None:
        """Test to_string with stat."""
        diff = GitDiff(stat=" file.py | 5 +++--")
        output = diff.to_string()
        assert "file.py | 5" in output

    def test_to_string_with_content(self) -> None:
        """Test to_string with file content."""
        diff = GitDiff(
            files=[
                DiffFile(path="file.py", content="diff content here"),
            ]
        )
        output = diff.to_string(include_content=True)
        assert "diff content here" in output

    def test_to_string_without_content(self) -> None:
        """Test to_string without file content."""
        diff = GitDiff(
            stat=" file.py | 5 +++--",
            files=[
                DiffFile(path="file.py", content="diff content here"),
            ],
        )
        output = diff.to_string(include_content=False)
        assert "diff content here" not in output

    def test_get_stat_summary(self) -> None:
        """Test get_stat_summary."""
        diff = GitDiff(
            files=[DiffFile(path="a.py"), DiffFile(path="b.py")],
            total_additions=15,
            total_deletions=5,
        )
        summary = diff.get_stat_summary()
        assert "2 file(s) changed" in summary
        assert "15 insertion(s)" in summary
        assert "5 deletion(s)" in summary


class TestGitDiffTool:
    """Tests for GitDiffTool class."""

    @pytest.fixture
    def mock_repo(self) -> GitRepository:
        """Create mock repository."""
        repo = GitRepository("/project")
        repo._root = "/project"
        return repo

    @pytest.mark.asyncio
    async def test_diff_working(self, mock_repo: GitRepository) -> None:
        """Test diff_working basic."""
        stat_output = " file.py | 5 +++--\n 1 file changed, 3 insertions(+), 2 deletions(-)"
        diff_output = (
            "diff --git a/file.py b/file.py\n"
            "index abc123..def456 100644\n"
            "--- a/file.py\n"
            "+++ b/file.py\n"
            "@@ -1,3 +1,4 @@\n"
            "+new line\n"
            " existing line\n"
            "-old line\n"
        )

        calls = []

        async def mock_run_git(*args, **kwargs):
            calls.append(args)
            if "--stat" in args:
                return (stat_output, "", 0)
            return (diff_output, "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitDiffTool(mock_repo)
            diff = await tool.diff_working()

        assert len(diff.files) >= 1
        assert diff.total_additions == 3
        assert diff.total_deletions == 2

    @pytest.mark.asyncio
    async def test_diff_working_staged(self, mock_repo: GitRepository) -> None:
        """Test diff_working with staged=True."""
        calls = []

        async def mock_run_git(*args, **kwargs):
            calls.append(args)
            return ("", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitDiffTool(mock_repo)
            await tool.diff_working(staged=True)

        assert any("--cached" in c for c in calls)

    @pytest.mark.asyncio
    async def test_diff_working_with_path(self, mock_repo: GitRepository) -> None:
        """Test diff_working with path filter."""
        calls = []

        async def mock_run_git(*args, **kwargs):
            calls.append(args)
            return ("", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitDiffTool(mock_repo)
            await tool.diff_working(path="src/file.py")

        assert any("src/file.py" in str(c) for c in calls)

    @pytest.mark.asyncio
    async def test_diff_commits(self, mock_repo: GitRepository) -> None:
        """Test diff_commits."""
        calls = []

        async def mock_run_git(*args, **kwargs):
            calls.append(args)
            return ("", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitDiffTool(mock_repo)
            await tool.diff_commits("abc123", "def456")

        assert "abc123" in calls[0]
        assert "def456" in calls[0]

    @pytest.mark.asyncio
    async def test_diff_branches(self, mock_repo: GitRepository) -> None:
        """Test diff_branches."""
        calls = []

        async def mock_run_git(*args, **kwargs):
            calls.append(args)
            return ("", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitDiffTool(mock_repo)
            await tool.diff_branches("main", "feature")

        assert "main" in calls[0]
        assert "feature" in calls[0]

    @pytest.mark.asyncio
    async def test_get_stat(self, mock_repo: GitRepository) -> None:
        """Test get_stat."""
        stat_output = " file.py | 5 +++--\n 1 file changed, 3 insertions(+), 2 deletions(-)"

        async def mock_run_git(*args, **kwargs):
            return (stat_output, "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitDiffTool(mock_repo)
            stat = await tool.get_stat()

        assert "file.py" in stat

    @pytest.mark.asyncio
    async def test_get_stat_with_refs(self, mock_repo: GitRepository) -> None:
        """Test get_stat with refs."""
        calls = []

        async def mock_run_git(*args, **kwargs):
            calls.append(args)
            return ("", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitDiffTool(mock_repo)
            await tool.get_stat(from_ref="abc123", to_ref="def456")

        assert "abc123" in calls[0]
        assert "def456" in calls[0]

    @pytest.mark.asyncio
    async def test_get_name_only(self, mock_repo: GitRepository) -> None:
        """Test get_name_only."""
        async def mock_run_git(*args, **kwargs):
            return ("file1.py\nfile2.py\ndir/file3.py", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitDiffTool(mock_repo)
            files = await tool.get_name_only()

        assert len(files) == 3
        assert "file1.py" in files

    @pytest.mark.asyncio
    async def test_get_name_status(self, mock_repo: GitRepository) -> None:
        """Test get_name_status."""
        async def mock_run_git(*args, **kwargs):
            return ("M\tfile1.py\nA\tfile2.py\nD\tfile3.py", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            tool = GitDiffTool(mock_repo)
            files = await tool.get_name_status()

        assert len(files) == 3
        assert ("M", "file1.py") in files
        assert ("A", "file2.py") in files
        assert ("D", "file3.py") in files

    def test_parse_stat(self, mock_repo: GitRepository) -> None:
        """Test _parse_stat."""
        tool = GitDiffTool(mock_repo)
        diff = GitDiff()

        stat = (
            " file1.py | 10 +++++++---\n"
            " file2.py |  5 +++++\n"
            " 2 files changed, 12 insertions(+), 3 deletions(-)"
        )
        tool._parse_stat(stat, diff)

        assert len(diff.files) == 2
        assert diff.total_additions == 12
        assert diff.total_deletions == 3

    def test_parse_stat_insertions_only(self, mock_repo: GitRepository) -> None:
        """Test _parse_stat with insertions only."""
        tool = GitDiffTool(mock_repo)
        diff = GitDiff()

        stat = " file.py | 5 +++++\n 1 file changed, 5 insertions(+)"
        tool._parse_stat(stat, diff)

        assert diff.total_additions == 5
        assert diff.total_deletions == 0

    def test_parse_stat_deletions_only(self, mock_repo: GitRepository) -> None:
        """Test _parse_stat with deletions only."""
        tool = GitDiffTool(mock_repo)
        diff = GitDiff()

        stat = " file.py | 3 ---\n 1 file changed, 3 deletions(-)"
        tool._parse_stat(stat, diff)

        assert diff.total_additions == 0
        assert diff.total_deletions == 3

    def test_parse_diff_content(self, mock_repo: GitRepository) -> None:
        """Test _parse_diff_content."""
        tool = GitDiffTool(mock_repo)
        diff = GitDiff()

        content = (
            "diff --git a/file.py b/file.py\n"
            "index abc..def 100644\n"
            "--- a/file.py\n"
            "+++ b/file.py\n"
            "@@ -1,3 +1,4 @@\n"
            "+new line\n"
            " existing\n"
            "-old line\n"
        )
        tool._parse_diff_content(content, diff)

        assert len(diff.files) == 1
        assert diff.files[0].path == "file.py"
        assert diff.files[0].additions == 1
        assert diff.files[0].deletions == 1

    def test_parse_diff_content_new_file(self, mock_repo: GitRepository) -> None:
        """Test _parse_diff_content for new file."""
        tool = GitDiffTool(mock_repo)
        diff = GitDiff()

        content = (
            "diff --git a/new.py b/new.py\n"
            "new file mode 100644\n"
            "index 000..abc\n"
            "--- /dev/null\n"
            "+++ b/new.py\n"
            "@@ -0,0 +1,3 @@\n"
            "+line 1\n"
            "+line 2\n"
        )
        tool._parse_diff_content(content, diff)

        assert len(diff.files) == 1
        assert diff.files[0].status == "A"
        assert diff.files[0].additions == 2

    def test_parse_diff_content_deleted_file(self, mock_repo: GitRepository) -> None:
        """Test _parse_diff_content for deleted file."""
        tool = GitDiffTool(mock_repo)
        diff = GitDiff()

        content = (
            "diff --git a/old.py b/old.py\n"
            "deleted file mode 100644\n"
            "index abc..000\n"
            "--- a/old.py\n"
            "+++ /dev/null\n"
            "@@ -1,2 +0,0 @@\n"
            "-line 1\n"
            "-line 2\n"
        )
        tool._parse_diff_content(content, diff)

        assert len(diff.files) == 1
        assert diff.files[0].status == "D"
        assert diff.files[0].deletions == 2

    def test_parse_diff_content_renamed_file(self, mock_repo: GitRepository) -> None:
        """Test _parse_diff_content for renamed file."""
        tool = GitDiffTool(mock_repo)
        diff = GitDiff()

        content = (
            "diff --git a/old_name.py b/new_name.py\n"
            "similarity index 95%\n"
            "rename from old_name.py\n"
            "rename to new_name.py\n"
        )
        tool._parse_diff_content(content, diff)

        assert len(diff.files) == 1
        assert diff.files[0].path == "new_name.py"
        assert diff.files[0].old_path == "old_name.py"
        assert diff.files[0].status == "R"

    def test_parse_diff_content_multiple_files(self, mock_repo: GitRepository) -> None:
        """Test _parse_diff_content with multiple files."""
        tool = GitDiffTool(mock_repo)
        diff = GitDiff()

        content = (
            "diff --git a/file1.py b/file1.py\n"
            "+line\n"
            "diff --git a/file2.py b/file2.py\n"
            "-line\n"
        )
        tool._parse_diff_content(content, diff)

        assert len(diff.files) == 2
