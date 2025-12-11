"""Tests for GitHub context."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from code_forge.github.context import GitHubContext
from code_forge.github.repository import GitHubRepository
from code_forge.github.issues import GitHubIssue, GitHubUser, GitHubLabel, GitHubMilestone
from code_forge.github.pull_requests import GitHubPullRequest


class TestGitHubContext:
    """Tests for GitHubContext class."""

    @pytest.mark.asyncio
    async def test_get_context_summary(
        self,
        github_context: GitHubContext,
        sample_repository_data: dict[str, Any],
    ) -> None:
        """Test getting context summary."""
        with patch.object(
            github_context.repo_service, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = GitHubRepository.from_api(sample_repository_data)

            summary = await github_context.get_context_summary(
                "testuser", "test-repo"
            )

        assert "testuser/test-repo" in summary
        assert "A test repository" in summary
        assert "main" in summary

    @pytest.mark.asyncio
    async def test_get_context_summary_error(
        self,
        github_context: GitHubContext,
    ) -> None:
        """Test context summary with error."""
        with patch.object(
            github_context.repo_service, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = Exception("API error")

            summary = await github_context.get_context_summary(
                "testuser", "test-repo"
            )

        assert "testuser/test-repo" in summary
        assert "unable to fetch" in summary

    @pytest.mark.asyncio
    async def test_get_context_summary_archived(
        self,
        github_context: GitHubContext,
        sample_repository_data: dict[str, Any],
    ) -> None:
        """Test context summary for archived repo."""
        archived_data = {**sample_repository_data, "archived": True}

        with patch.object(
            github_context.repo_service, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = GitHubRepository.from_api(archived_data)

            summary = await github_context.get_context_summary(
                "testuser", "test-repo"
            )

        assert "ARCHIVED" in summary

    def test_format_issue(
        self,
        github_context: GitHubContext,
        sample_issue_data: dict[str, Any],
    ) -> None:
        """Test formatting issue."""
        issue = GitHubIssue.from_api(sample_issue_data)

        formatted = github_context.format_issue(issue)

        assert "#42" in formatted
        assert "Test issue" in formatted
        assert "open" in formatted
        assert "@testuser" in formatted
        assert "bug" in formatted
        assert "This is a test issue" in formatted

    def test_format_issue_minimal(
        self,
        github_context: GitHubContext,
        sample_user_data: dict[str, Any],
    ) -> None:
        """Test formatting minimal issue."""
        data = {
            "number": 1,
            "title": "Simple issue",
            "body": None,
            "state": "open",
            "user": sample_user_data,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "url": "https://api.github.com/repos/test/test/issues/1",
            "html_url": "https://github.com/test/test/issues/1",
        }
        issue = GitHubIssue.from_api(data)

        formatted = github_context.format_issue(issue)

        assert "#1" in formatted
        assert "Simple issue" in formatted

    def test_format_pr(
        self,
        github_context: GitHubContext,
        sample_pr_data: dict[str, Any],
    ) -> None:
        """Test formatting PR."""
        pr = GitHubPullRequest.from_api(sample_pr_data)

        formatted = github_context.format_pr(pr)

        assert "#123" in formatted
        assert "Test PR" in formatted
        assert "feature-branch -> main" in formatted
        assert "+100 -50" in formatted
        assert "5 files" in formatted

    def test_format_pr_draft(
        self,
        github_context: GitHubContext,
        sample_pr_data: dict[str, Any],
    ) -> None:
        """Test formatting draft PR."""
        data = {**sample_pr_data, "draft": True}
        pr = GitHubPullRequest.from_api(data)

        formatted = github_context.format_pr(pr)

        assert "DRAFT" in formatted

    def test_format_pr_merged(
        self,
        github_context: GitHubContext,
        sample_pr_data: dict[str, Any],
    ) -> None:
        """Test formatting merged PR."""
        data = {
            **sample_pr_data,
            "merged": True,
            "merged_at": "2024-01-02T00:00:00Z",
        }
        pr = GitHubPullRequest.from_api(data)

        formatted = github_context.format_pr(pr)

        assert "Merged: 2024-01-02T00:00:00Z" in formatted

    def test_format_issue_list(
        self,
        github_context: GitHubContext,
        sample_issue_data: dict[str, Any],
    ) -> None:
        """Test formatting issue list."""
        issues = [GitHubIssue.from_api(sample_issue_data)]

        formatted = github_context.format_issue_list(issues)

        assert "#42" in formatted
        assert "Test issue" in formatted
        assert "bug" in formatted
        assert "@testuser" in formatted

    def test_format_issue_list_empty(
        self,
        github_context: GitHubContext,
    ) -> None:
        """Test formatting empty issue list."""
        formatted = github_context.format_issue_list([])

        assert "No issues found" in formatted

    def test_format_issue_list_multiple(
        self,
        github_context: GitHubContext,
        sample_issue_data: dict[str, Any],
    ) -> None:
        """Test formatting multiple issues."""
        issue1 = GitHubIssue.from_api(sample_issue_data)
        issue2_data = {**sample_issue_data, "number": 43, "title": "Second issue"}
        issue2 = GitHubIssue.from_api(issue2_data)

        formatted = github_context.format_issue_list([issue1, issue2])

        assert "#42" in formatted
        assert "#43" in formatted
        assert "Second issue" in formatted

    def test_format_pr_list(
        self,
        github_context: GitHubContext,
        sample_pr_data: dict[str, Any],
    ) -> None:
        """Test formatting PR list."""
        prs = [GitHubPullRequest.from_api(sample_pr_data)]

        formatted = github_context.format_pr_list(prs)

        assert "#123" in formatted
        assert "Test PR" in formatted
        assert "feature-branch -> main" in formatted

    def test_format_pr_list_empty(
        self,
        github_context: GitHubContext,
    ) -> None:
        """Test formatting empty PR list."""
        formatted = github_context.format_pr_list([])

        assert "No pull requests found" in formatted

    def test_format_pr_list_with_draft(
        self,
        github_context: GitHubContext,
        sample_pr_data: dict[str, Any],
    ) -> None:
        """Test formatting PR list with draft."""
        data = {**sample_pr_data, "draft": True}
        prs = [GitHubPullRequest.from_api(data)]

        formatted = github_context.format_pr_list(prs)

        assert "[DRAFT]" in formatted

    def test_format_pr_list_with_merged(
        self,
        github_context: GitHubContext,
        sample_pr_data: dict[str, Any],
    ) -> None:
        """Test formatting PR list with merged."""
        data = {**sample_pr_data, "merged": True}
        prs = [GitHubPullRequest.from_api(data)]

        formatted = github_context.format_pr_list(prs)

        assert "[MERGED]" in formatted
