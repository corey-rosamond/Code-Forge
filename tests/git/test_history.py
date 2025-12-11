"""Tests for git history module."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from code_forge.git.history import GitHistory, LogEntry
from code_forge.git.repository import GitCommit, GitError, GitRepository


class TestLogEntry:
    """Tests for LogEntry dataclass."""

    def test_basic_creation(self) -> None:
        """Test basic log entry creation."""
        commit = GitCommit(
            hash="abc123def456",
            short_hash="abc123",
            author="Test Author",
            author_email="test@example.com",
            date="2024-01-15 10:30:00",
            message="Test commit",
        )
        entry = LogEntry(commit=commit)

        assert entry.commit == commit
        assert entry.files_changed is None
        assert entry.insertions is None
        assert entry.deletions is None

    def test_with_stats(self) -> None:
        """Test log entry with stats."""
        commit = GitCommit(
            hash="abc",
            short_hash="abc",
            author="Test",
            author_email="test@test.com",
            date="2024-01-01",
            message="Test",
        )
        entry = LogEntry(
            commit=commit,
            files_changed=3,
            insertions=10,
            deletions=5,
        )

        assert entry.files_changed == 3
        assert entry.insertions == 10
        assert entry.deletions == 5

    def test_to_string_basic(self) -> None:
        """Test to_string basic output."""
        commit = GitCommit(
            hash="abc123",
            short_hash="abc",
            author="Test Author",
            author_email="test@example.com",
            date="2024-01-15 10:30:00",
            message="Test commit message",
        )
        entry = LogEntry(commit=commit)
        output = entry.to_string()

        assert "commit abc" in output
        assert "Author: Test Author" in output
        assert "Date:   2024-01-15" in output
        assert "Test commit message" in output

    def test_to_string_with_stats(self) -> None:
        """Test to_string with stats."""
        commit = GitCommit(
            hash="abc",
            short_hash="abc",
            author="Test",
            author_email="test@test.com",
            date="2024-01-01",
            message="Test",
        )
        entry = LogEntry(
            commit=commit,
            files_changed=2,
            insertions=10,
            deletions=3,
        )
        output = entry.to_string()

        assert "2 file(s) changed" in output
        assert "10 insertion(s)" in output
        assert "3 deletion(s)" in output

    def test_to_string_verbose(self) -> None:
        """Test to_string verbose mode."""
        commit = GitCommit(
            hash="abc",
            short_hash="abc",
            author="Test",
            author_email="test@test.com",
            date="2024-01-01",
            message="Subject line\n\nBody paragraph here.",
        )
        entry = LogEntry(commit=commit)
        output = entry.to_string(verbose=True)

        assert "Body paragraph here." in output


class TestGitHistory:
    """Tests for GitHistory class."""

    @pytest.fixture
    def mock_repo(self) -> GitRepository:
        """Create mock repository."""
        repo = GitRepository("/project")
        repo._root = "/project"
        return repo

    @pytest.mark.asyncio
    async def test_get_log_basic(self, mock_repo: GitRepository) -> None:
        """Test basic log retrieval."""
        log_output = (
            "abc123def456\x00abc123\x00Test Author\x00test@example.com\x00"
            "2024-01-15 10:30:00\x00Test commit\x00\x00parent1\x00\n"
            "\n 1 file changed, 5 insertions(+), 2 deletions(-)\n"
        )

        async def mock_run_git(*args, **kwargs):
            return (log_output, "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            history = GitHistory(mock_repo)
            entries = await history.get_log(count=5)

        assert len(entries) >= 1
        assert entries[0].commit.author == "Test Author"

    @pytest.mark.asyncio
    async def test_get_log_with_path(self, mock_repo: GitRepository) -> None:
        """Test log with path filter."""
        calls = []

        async def mock_run_git(*args, **kwargs):
            calls.append(args)
            return ("", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            history = GitHistory(mock_repo)
            await history.get_log(path="src/file.py")

        assert "--" in calls[0]
        assert "src/file.py" in calls[0]

    @pytest.mark.asyncio
    async def test_get_log_with_author(self, mock_repo: GitRepository) -> None:
        """Test log with author filter."""
        calls = []

        async def mock_run_git(*args, **kwargs):
            calls.append(args)
            return ("", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            history = GitHistory(mock_repo)
            await history.get_log(author="test@example.com")

        assert any("--author=test@example.com" in str(c) for c in calls)

    @pytest.mark.asyncio
    async def test_get_log_with_date_range(self, mock_repo: GitRepository) -> None:
        """Test log with date range."""
        calls = []

        async def mock_run_git(*args, **kwargs):
            calls.append(args)
            return ("", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            history = GitHistory(mock_repo)
            await history.get_log(since="2024-01-01", until="2024-01-31")

        assert any("--since=2024-01-01" in str(c) for c in calls)
        assert any("--until=2024-01-31" in str(c) for c in calls)

    @pytest.mark.asyncio
    async def test_get_log_with_branch(self, mock_repo: GitRepository) -> None:
        """Test log with branch filter."""
        calls = []

        async def mock_run_git(*args, **kwargs):
            calls.append(args)
            return ("", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            history = GitHistory(mock_repo)
            await history.get_log(branch="feature")

        assert "feature" in calls[0]

    @pytest.mark.asyncio
    async def test_get_log_all_branches(self, mock_repo: GitRepository) -> None:
        """Test log with all branches."""
        calls = []

        async def mock_run_git(*args, **kwargs):
            calls.append(args)
            return ("", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            history = GitHistory(mock_repo)
            await history.get_log(all_branches=True)

        assert "--all" in calls[0]

    @pytest.mark.asyncio
    async def test_get_commit(self, mock_repo: GitRepository) -> None:
        """Test get single commit."""
        commit_output = (
            "abc123def456\n"
            "abc123\n"
            "Test Author\n"
            "test@example.com\n"
            "2024-01-15 10:30:00\n"
            "Test commit message\n"
            "\n"
            "Extended body here.\n"
            "---PARENTS---\n"
            "parent1 parent2"
        )

        async def mock_run_git(*args, **kwargs):
            return (commit_output, "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            history = GitHistory(mock_repo)
            commit = await history.get_commit("abc123")

        assert commit.hash == "abc123def456"
        assert commit.author == "Test Author"
        assert "Extended body" in commit.message
        assert len(commit.parent_hashes) == 2

    @pytest.mark.asyncio
    async def test_get_commit_invalid(self, mock_repo: GitRepository) -> None:
        """Test get commit with invalid output."""
        async def mock_run_git(*args, **kwargs):
            return ("invalid\noutput", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            history = GitHistory(mock_repo)
            with pytest.raises(GitError):
                await history.get_commit("invalid")

    @pytest.mark.asyncio
    async def test_get_commit_files(self, mock_repo: GitRepository) -> None:
        """Test get files changed in commit."""
        async def mock_run_git(*args, **kwargs):
            return ("file1.py\nfile2.py\ndir/file3.py", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            history = GitHistory(mock_repo)
            files = await history.get_commit_files("abc123")

        assert len(files) == 3
        assert "file1.py" in files
        assert "dir/file3.py" in files

    @pytest.mark.asyncio
    async def test_get_commit_files_empty(self, mock_repo: GitRepository) -> None:
        """Test get files for empty commit."""
        async def mock_run_git(*args, **kwargs):
            return ("", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            history = GitHistory(mock_repo)
            files = await history.get_commit_files("abc123")

        assert files == []

    @pytest.mark.asyncio
    async def test_get_commit_diff(self, mock_repo: GitRepository) -> None:
        """Test get diff for commit."""
        diff_output = "diff --git a/file.py b/file.py\n+new line"

        async def mock_run_git(*args, **kwargs):
            return (diff_output, "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            history = GitHistory(mock_repo)
            diff = await history.get_commit_diff("abc123")

        assert "diff --git" in diff

    @pytest.mark.asyncio
    async def test_get_commit_diff_with_path(self, mock_repo: GitRepository) -> None:
        """Test get diff for commit with path filter."""
        calls = []

        async def mock_run_git(*args, **kwargs):
            calls.append(args)
            return ("diff content", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            history = GitHistory(mock_repo)
            await history.get_commit_diff("abc123", path="file.py")

        assert "--" in calls[0]
        assert "file.py" in calls[0]

    @pytest.mark.asyncio
    async def test_get_recent_commits(self, mock_repo: GitRepository) -> None:
        """Test get recent commits formatted."""
        log_output = (
            "abc123\x00abc\x00Author\x00a@test.com\x002024-01-01\x00First commit\x00\x00\x00\n\n"
            "def456\x00def\x00Author\x00a@test.com\x002024-01-02\x00Second commit\x00\x00\x00"
        )

        async def mock_run_git(*args, **kwargs):
            return (log_output, "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            history = GitHistory(mock_repo)
            output = await history.get_recent_commits(count=5)

        assert "Recent commits:" in output

    @pytest.mark.asyncio
    async def test_search_commits(self, mock_repo: GitRepository) -> None:
        """Test search commits by message."""
        calls = []

        async def mock_run_git(*args, **kwargs):
            calls.append(args)
            return ("", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            history = GitHistory(mock_repo)
            await history.search_commits("fix bug")

        assert any("--grep=fix bug" in str(c) for c in calls)
        assert "-i" in calls[0]  # Case insensitive

    def test_parse_stats(self, mock_repo: GitRepository) -> None:
        """Test stats parsing."""
        history = GitHistory(mock_repo)
        entry = LogEntry(
            commit=GitCommit(
                hash="abc",
                short_hash="abc",
                author="",
                author_email="",
                date="",
                message="",
            )
        )

        # Test various stat formats
        history._parse_stats(" 3 files changed, 10 insertions(+), 5 deletions(-)", entry)
        assert entry.files_changed == 3
        assert entry.insertions == 10
        assert entry.deletions == 5

    def test_parse_stats_single_file(self, mock_repo: GitRepository) -> None:
        """Test stats parsing for single file."""
        history = GitHistory(mock_repo)
        entry = LogEntry(
            commit=GitCommit(
                hash="abc",
                short_hash="abc",
                author="",
                author_email="",
                date="",
                message="",
            )
        )

        history._parse_stats(" 1 file changed, 1 insertion(+)", entry)
        assert entry.files_changed == 1
        assert entry.insertions == 1
        assert entry.deletions is None
