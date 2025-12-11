"""Tests for git safety module."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from code_forge.git.repository import GitError, GitRepository
from code_forge.git.safety import GitSafety, SafetyCheck


class TestSafetyCheck:
    """Tests for SafetyCheck dataclass."""

    def test_safe_check(self) -> None:
        """Test safe check."""
        check = SafetyCheck(safe=True)
        assert check.safe is True
        assert check.reason is None
        assert check.warnings == []

    def test_unsafe_check(self) -> None:
        """Test unsafe check with reason."""
        check = SafetyCheck(safe=False, reason="Not allowed")
        assert check.safe is False
        assert check.reason == "Not allowed"

    def test_check_with_warnings(self) -> None:
        """Test check with warnings."""
        check = SafetyCheck(
            safe=True,
            warnings=["Warning 1", "Warning 2"],
        )
        assert len(check.warnings) == 2


class TestGitSafety:
    """Tests for GitSafety class."""

    @pytest.fixture
    def mock_repo(self) -> GitRepository:
        """Create mock repository."""
        repo = GitRepository("/project")
        repo._root = "/project"
        repo._is_git_repo = True
        return repo

    @pytest.mark.asyncio
    async def test_check_amend_safe(self, mock_repo: GitRepository) -> None:
        """Test check_amend when safe."""
        async def mock_run_git(*args, **kwargs):
            if "branch" in args and "-r" in args:
                return ("", "", 0)  # Not pushed
            elif "log" in args:
                return ("Author\nauthor@test.com", "", 0)
            return ("abc123", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            safety = GitSafety(mock_repo)
            check = await safety.check_amend()

        assert check.safe is True

    @pytest.mark.asyncio
    async def test_check_amend_pushed(self, mock_repo: GitRepository) -> None:
        """Test check_amend when pushed."""
        async def mock_run_git(*args, **kwargs):
            if "branch" in args and "-r" in args:
                return ("origin/main", "", 0)  # Is pushed
            return ("abc123", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            safety = GitSafety(mock_repo)
            check = await safety.check_amend()

        assert check.safe is False
        assert "pushed" in check.reason.lower()

    @pytest.mark.asyncio
    async def test_check_force_push_protected(self, mock_repo: GitRepository) -> None:
        """Test check_force_push for protected branch."""
        mock_repo._current_branch_cache = "main"

        safety = GitSafety(mock_repo)
        check = await safety.check_force_push()

        assert check.safe is False
        assert "protected" in check.reason.lower()

    @pytest.mark.asyncio
    async def test_check_force_push_safe(self, mock_repo: GitRepository) -> None:
        """Test check_force_push for non-protected branch."""
        mock_repo._current_branch_cache = "feature-branch"

        safety = GitSafety(mock_repo)
        check = await safety.check_force_push()

        assert check.safe is True
        assert len(check.warnings) >= 1

    @pytest.mark.asyncio
    async def test_check_force_push_explicit_branch(self, mock_repo: GitRepository) -> None:
        """Test check_force_push with explicit branch."""
        safety = GitSafety(mock_repo)
        check = await safety.check_force_push(branch="master")

        assert check.safe is False

    @pytest.mark.asyncio
    async def test_check_branch_delete_current(self, mock_repo: GitRepository) -> None:
        """Test check_branch_delete for current branch."""
        mock_repo._current_branch_cache = "feature"

        safety = GitSafety(mock_repo)
        check = await safety.check_branch_delete("feature")

        assert check.safe is False
        assert "current" in check.reason.lower()

    @pytest.mark.asyncio
    async def test_check_branch_delete_protected(self, mock_repo: GitRepository) -> None:
        """Test check_branch_delete for protected branch."""
        mock_repo._current_branch_cache = "feature"

        safety = GitSafety(mock_repo)
        check = await safety.check_branch_delete("main")

        assert check.safe is False
        assert "protected" in check.reason.lower()

    @pytest.mark.asyncio
    async def test_check_branch_delete_unmerged(self, mock_repo: GitRepository) -> None:
        """Test check_branch_delete for unmerged branch."""
        mock_repo._current_branch_cache = "main"

        async def mock_run_git(*args, **kwargs):
            return ("main\ndevelop", "", 0)  # feature not in list

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            safety = GitSafety(mock_repo)
            check = await safety.check_branch_delete("feature")

        assert check.safe is True
        assert any("not merged" in w.lower() for w in check.warnings)

    @pytest.mark.asyncio
    async def test_check_branch_delete_merged(self, mock_repo: GitRepository) -> None:
        """Test check_branch_delete for merged branch."""
        mock_repo._current_branch_cache = "main"

        async def mock_run_git(*args, **kwargs):
            return ("main\nfeature\ndevelop", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            safety = GitSafety(mock_repo)
            check = await safety.check_branch_delete("feature")

        assert check.safe is True

    @pytest.mark.asyncio
    async def test_check_hard_reset_with_changes(self, mock_repo: GitRepository) -> None:
        """Test check_hard_reset with uncommitted changes."""
        async def mock_run_git(*args, **kwargs):
            return (" M file.py", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            safety = GitSafety(mock_repo)
            check = await safety.check_hard_reset()

        assert check.safe is False
        assert "uncommitted" in check.reason.lower()

    @pytest.mark.asyncio
    async def test_check_hard_reset_clean(self, mock_repo: GitRepository) -> None:
        """Test check_hard_reset with clean tree."""
        async def mock_run_git(*args, **kwargs):
            return ("", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            safety = GitSafety(mock_repo)
            check = await safety.check_hard_reset()

        assert check.safe is True

    @pytest.mark.asyncio
    async def test_check_checkout_clean(self, mock_repo: GitRepository) -> None:
        """Test check_checkout with clean tree."""
        async def mock_run_git(*args, **kwargs):
            return ("", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            safety = GitSafety(mock_repo)
            check = await safety.check_checkout("feature")

        assert check.safe is True

    @pytest.mark.asyncio
    async def test_check_checkout_with_conflict(self, mock_repo: GitRepository) -> None:
        """Test check_checkout with conflicting changes."""
        call_count = [0]

        async def mock_run_git(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # status check
                return (" M file.py", "", 0)
            else:  # dry-run checkout
                raise GitError("error: would be overwritten")

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            safety = GitSafety(mock_repo)
            check = await safety.check_checkout("feature")

        assert check.safe is False
        assert "overwritten" in check.reason.lower()

    @pytest.mark.asyncio
    async def test_get_head_authorship(self, mock_repo: GitRepository) -> None:
        """Test get_head_authorship."""
        async def mock_run_git(*args, **kwargs):
            return ("Test Author\ntest@example.com", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            safety = GitSafety(mock_repo)
            author, email = await safety.get_head_authorship()

        assert author == "Test Author"
        assert email == "test@example.com"

    @pytest.mark.asyncio
    async def test_is_pushed_true(self, mock_repo: GitRepository) -> None:
        """Test is_pushed when pushed."""
        async def mock_run_git(*args, **kwargs):
            if "rev-parse" in args:
                return ("abc123", "", 0)
            return ("origin/main origin/feature", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            safety = GitSafety(mock_repo)
            result = await safety.is_pushed("HEAD")

        assert result is True

    @pytest.mark.asyncio
    async def test_is_pushed_false(self, mock_repo: GitRepository) -> None:
        """Test is_pushed when not pushed."""
        async def mock_run_git(*args, **kwargs):
            if "rev-parse" in args:
                return ("abc123", "", 0)
            return ("", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            safety = GitSafety(mock_repo)
            result = await safety.is_pushed("HEAD")

        assert result is False

    @pytest.mark.asyncio
    async def test_is_pushed_error(self, mock_repo: GitRepository) -> None:
        """Test is_pushed on error."""
        async def mock_run_git(*args, **kwargs):
            raise GitError("error")

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            safety = GitSafety(mock_repo)
            result = await safety.is_pushed("HEAD")

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_commit_message_valid(self, mock_repo: GitRepository) -> None:
        """Test validate_commit_message with valid message."""
        safety = GitSafety(mock_repo)
        check = await safety.validate_commit_message("feat: Add new feature")

        assert check.safe is True

    @pytest.mark.asyncio
    async def test_validate_commit_message_empty(self, mock_repo: GitRepository) -> None:
        """Test validate_commit_message with empty message."""
        safety = GitSafety(mock_repo)
        check = await safety.validate_commit_message("")

        assert check.safe is False
        assert "empty" in check.reason.lower()

    @pytest.mark.asyncio
    async def test_validate_commit_message_long_subject(self, mock_repo: GitRepository) -> None:
        """Test validate_commit_message with long subject."""
        safety = GitSafety(mock_repo)
        long_subject = "a" * 100
        check = await safety.validate_commit_message(long_subject)

        assert check.safe is True
        assert any("72" in w for w in check.warnings)

    @pytest.mark.asyncio
    async def test_validate_commit_message_no_blank_line(self, mock_repo: GitRepository) -> None:
        """Test validate_commit_message without blank line."""
        safety = GitSafety(mock_repo)
        check = await safety.validate_commit_message("Subject\nBody without blank line")

        assert check.safe is True
        assert any("blank" in w.lower() for w in check.warnings)

    @pytest.mark.asyncio
    async def test_validate_commit_message_non_conventional(self, mock_repo: GitRepository) -> None:
        """Test validate_commit_message with non-conventional format."""
        safety = GitSafety(mock_repo)
        check = await safety.validate_commit_message("Some random commit message")

        assert check.safe is True
        assert any("conventional" in w.lower() for w in check.warnings)

    @pytest.mark.asyncio
    async def test_check_rebase_with_changes(self, mock_repo: GitRepository) -> None:
        """Test check_rebase with uncommitted changes."""
        async def mock_run_git(*args, **kwargs):
            return (" M file.py", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            safety = GitSafety(mock_repo)
            check = await safety.check_rebase()

        assert check.safe is False
        assert "uncommitted" in check.reason.lower()

    @pytest.mark.asyncio
    async def test_check_rebase_pushed_branch(self, mock_repo: GitRepository) -> None:
        """Test check_rebase when branch is pushed."""
        mock_repo._current_branch_cache = "feature"

        call_count = [0]

        async def mock_run_git(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # status check
                return ("", "", 0)
            elif "rev-parse" in args:
                return ("abc123", "", 0)
            elif "branch" in args and "-r" in args:
                return ("origin/feature", "", 0)  # pushed
            return ("", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            safety = GitSafety(mock_repo)
            check = await safety.check_rebase()

        assert check.safe is True
        assert any("pushed" in w.lower() for w in check.warnings)

    @pytest.mark.asyncio
    async def test_check_rebase_onto_protected(self, mock_repo: GitRepository) -> None:
        """Test check_rebase onto protected branch."""
        mock_repo._current_branch_cache = "feature"

        async def mock_run_git(*args, **kwargs):
            if "branch" in args and "-r" in args:
                return ("", "", 0)
            return ("", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            safety = GitSafety(mock_repo)
            check = await safety.check_rebase(onto="main")

        assert check.safe is True
        assert any("main" in w for w in check.warnings)

    @pytest.mark.asyncio
    async def test_check_merge_with_changes(self, mock_repo: GitRepository) -> None:
        """Test check_merge with uncommitted changes."""
        async def mock_run_git(*args, **kwargs):
            return (" M file.py", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            safety = GitSafety(mock_repo)
            check = await safety.check_merge("feature")

        assert check.safe is False
        assert "uncommitted" in check.reason.lower()

    @pytest.mark.asyncio
    async def test_check_merge_clean(self, mock_repo: GitRepository) -> None:
        """Test check_merge with clean merge."""
        call_count = [0]

        async def mock_run_git(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # status check
                return ("", "", 0)
            elif "merge" in args and "--no-commit" in args:
                return ("", "", 0)
            elif "merge" in args and "--abort" in args:
                return ("", "", 0)
            return ("", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            safety = GitSafety(mock_repo)
            check = await safety.check_merge("feature")

        assert check.safe is True

    @pytest.mark.asyncio
    async def test_check_merge_with_conflict(self, mock_repo: GitRepository) -> None:
        """Test check_merge with conflict."""
        call_count = [0]

        async def mock_run_git(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # status check
                return ("", "", 0)
            elif "merge" in args and "--no-commit" in args:
                raise GitError("CONFLICT", stderr="conflict in file.py")
            return ("", "", 0)

        with patch.object(mock_repo, "run_git", side_effect=mock_run_git):
            safety = GitSafety(mock_repo)
            check = await safety.check_merge("feature")

        assert check.safe is True
        assert any("conflict" in w.lower() for w in check.warnings)

    def test_protected_branches(self, mock_repo: GitRepository) -> None:
        """Test protected branches list."""
        safety = GitSafety(mock_repo)

        assert "main" in safety.PROTECTED_BRANCHES
        assert "master" in safety.PROTECTED_BRANCHES
        assert "develop" in safety.PROTECTED_BRANCHES
        assert "production" in safety.PROTECTED_BRANCHES
