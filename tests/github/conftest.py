"""Shared fixtures for GitHub integration tests."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opencode.github.auth import GitHubAuth, GitHubAuthenticator
from opencode.github.client import GitHubClient
from opencode.github.repository import RepositoryService
from opencode.github.issues import IssueService
from opencode.github.pull_requests import PullRequestService
from opencode.github.actions import ActionsService
from opencode.github.context import GitHubContext


@pytest.fixture
def mock_token() -> str:
    """Test token."""
    return "ghp_test_token_12345"


@pytest.fixture
def github_auth(mock_token: str) -> GitHubAuth:
    """Create a GitHubAuth instance."""
    return GitHubAuth(
        token=mock_token,
        username="testuser",
        scopes=["repo", "workflow"],
        rate_limit=5000,
        rate_remaining=4999,
        rate_reset=1700000000,
    )


@pytest.fixture
def authenticator(mock_token: str) -> GitHubAuthenticator:
    """Create a GitHubAuthenticator instance."""
    return GitHubAuthenticator(token=mock_token)


@pytest.fixture
def authenticated_authenticator(
    mock_token: str, github_auth: GitHubAuth
) -> GitHubAuthenticator:
    """Create an authenticated GitHubAuthenticator instance."""
    auth = GitHubAuthenticator(token=mock_token)
    auth._auth_info = github_auth
    auth._validated = True
    return auth


@pytest.fixture
def client(authenticated_authenticator: GitHubAuthenticator) -> GitHubClient:
    """Create a GitHubClient instance."""
    return GitHubClient(auth=authenticated_authenticator)


@pytest.fixture
def repo_service(client: GitHubClient) -> RepositoryService:
    """Create a RepositoryService instance."""
    return RepositoryService(client=client)


@pytest.fixture
def issue_service(client: GitHubClient) -> IssueService:
    """Create an IssueService instance."""
    return IssueService(client=client)


@pytest.fixture
def pr_service(client: GitHubClient) -> PullRequestService:
    """Create a PullRequestService instance."""
    return PullRequestService(client=client)


@pytest.fixture
def actions_service(client: GitHubClient) -> ActionsService:
    """Create an ActionsService instance."""
    return ActionsService(client=client)


@pytest.fixture
def github_context(
    client: GitHubClient,
    repo_service: RepositoryService,
    issue_service: IssueService,
    pr_service: PullRequestService,
) -> GitHubContext:
    """Create a GitHubContext instance."""
    return GitHubContext(
        client=client,
        repo_service=repo_service,
        issue_service=issue_service,
        pr_service=pr_service,
    )


# Sample API response data fixtures

@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Sample GitHub user data."""
    return {
        "login": "testuser",
        "id": 12345,
        "avatar_url": "https://avatars.githubusercontent.com/u/12345",
        "html_url": "https://github.com/testuser",
        "type": "User",
    }


@pytest.fixture
def sample_repository_data() -> dict[str, Any]:
    """Sample GitHub repository data."""
    return {
        "name": "test-repo",
        "full_name": "testuser/test-repo",
        "owner": {"login": "testuser"},
        "description": "A test repository",
        "private": False,
        "default_branch": "main",
        "html_url": "https://github.com/testuser/test-repo",
        "clone_url": "https://github.com/testuser/test-repo.git",
        "ssh_url": "git@github.com:testuser/test-repo.git",
        "language": "Python",
        "stargazers_count": 100,
        "forks_count": 25,
        "open_issues_count": 10,
        "archived": False,
        "disabled": False,
        "topics": ["python", "testing"],
    }


@pytest.fixture
def sample_branch_data() -> dict[str, Any]:
    """Sample GitHub branch data."""
    return {
        "name": "main",
        "commit": {"sha": "abc123def456"},
        "protected": True,
    }


@pytest.fixture
def sample_tag_data() -> dict[str, Any]:
    """Sample GitHub tag data."""
    return {
        "name": "v1.0.0",
        "commit": {"sha": "abc123def456"},
        "zipball_url": "https://api.github.com/repos/testuser/test-repo/zipball/v1.0.0",
        "tarball_url": "https://api.github.com/repos/testuser/test-repo/tarball/v1.0.0",
    }


@pytest.fixture
def sample_label_data() -> dict[str, Any]:
    """Sample GitHub label data."""
    return {
        "name": "bug",
        "color": "d73a4a",
        "description": "Something isn't working",
    }


@pytest.fixture
def sample_milestone_data() -> dict[str, Any]:
    """Sample GitHub milestone data."""
    return {
        "number": 1,
        "title": "v1.0",
        "description": "First release",
        "state": "open",
        "due_on": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_issue_data(
    sample_user_data: dict[str, Any],
    sample_label_data: dict[str, Any],
    sample_milestone_data: dict[str, Any],
) -> dict[str, Any]:
    """Sample GitHub issue data."""
    return {
        "number": 42,
        "title": "Test issue",
        "body": "This is a test issue",
        "state": "open",
        "state_reason": None,
        "user": sample_user_data,
        "assignees": [sample_user_data],
        "labels": [sample_label_data],
        "milestone": sample_milestone_data,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
        "closed_at": None,
        "comments": 5,
        "url": "https://api.github.com/repos/testuser/test-repo/issues/42",
        "html_url": "https://github.com/testuser/test-repo/issues/42",
    }


@pytest.fixture
def sample_comment_data(sample_user_data: dict[str, Any]) -> dict[str, Any]:
    """Sample GitHub comment data."""
    return {
        "id": 12345,
        "body": "This is a test comment",
        "user": sample_user_data,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "html_url": "https://github.com/testuser/test-repo/issues/42#issuecomment-12345",
    }


@pytest.fixture
def sample_pr_data(
    sample_user_data: dict[str, Any],
    sample_label_data: dict[str, Any],
) -> dict[str, Any]:
    """Sample GitHub pull request data."""
    return {
        "number": 123,
        "title": "Test PR",
        "body": "This is a test PR",
        "state": "open",
        "draft": False,
        "merged": False,
        "mergeable": True,
        "mergeable_state": "clean",
        "user": sample_user_data,
        "assignees": [sample_user_data],
        "requested_reviewers": [sample_user_data],
        "labels": [sample_label_data],
        "head": {
            "ref": "feature-branch",
            "sha": "abc123",
            "repo": {"full_name": "testuser/test-repo"},
        },
        "base": {
            "ref": "main",
            "sha": "def456",
        },
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
        "merged_at": None,
        "merged_by": None,
        "additions": 100,
        "deletions": 50,
        "changed_files": 5,
        "commits": 3,
        "comments": 2,
        "review_comments": 1,
        "url": "https://api.github.com/repos/testuser/test-repo/pulls/123",
        "html_url": "https://github.com/testuser/test-repo/pull/123",
        "diff_url": "https://github.com/testuser/test-repo/pull/123.diff",
    }


@pytest.fixture
def sample_review_data(sample_user_data: dict[str, Any]) -> dict[str, Any]:
    """Sample GitHub review data."""
    return {
        "id": 456,
        "user": sample_user_data,
        "body": "LGTM!",
        "state": "APPROVED",
        "submitted_at": "2024-01-01T00:00:00Z",
        "html_url": "https://github.com/testuser/test-repo/pull/123#pullrequestreview-456",
    }


@pytest.fixture
def sample_review_comment_data(
    sample_user_data: dict[str, Any],
) -> dict[str, Any]:
    """Sample GitHub review comment data."""
    return {
        "id": 789,
        "body": "Consider changing this",
        "user": sample_user_data,
        "path": "src/main.py",
        "position": 10,
        "line": 15,
        "commit_id": "abc123",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "html_url": "https://github.com/testuser/test-repo/pull/123#discussion_r789",
    }


@pytest.fixture
def sample_check_run_data() -> dict[str, Any]:
    """Sample GitHub check run data."""
    return {
        "id": 999,
        "name": "CI",
        "status": "completed",
        "conclusion": "success",
        "started_at": "2024-01-01T00:00:00Z",
        "completed_at": "2024-01-01T00:10:00Z",
        "url": "https://api.github.com/repos/testuser/test-repo/check-runs/999",
        "html_url": "https://github.com/testuser/test-repo/runs/999",
        "app": {"name": "GitHub Actions"},
    }


@pytest.fixture
def sample_pr_file_data() -> dict[str, Any]:
    """Sample GitHub PR file data."""
    return {
        "filename": "src/main.py",
        "status": "modified",
        "additions": 10,
        "deletions": 5,
        "changes": 15,
        "patch": "@@ -1,5 +1,10 @@...",
        "blob_url": "https://github.com/testuser/test-repo/blob/abc123/src/main.py",
        "raw_url": "https://github.com/testuser/test-repo/raw/abc123/src/main.py",
    }


@pytest.fixture
def sample_workflow_data() -> dict[str, Any]:
    """Sample GitHub workflow data."""
    return {
        "id": 111,
        "name": "CI",
        "path": ".github/workflows/ci.yml",
        "state": "active",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "url": "https://api.github.com/repos/testuser/test-repo/actions/workflows/111",
        "html_url": "https://github.com/testuser/test-repo/actions/workflows/ci.yml",
    }


@pytest.fixture
def sample_workflow_run_data() -> dict[str, Any]:
    """Sample GitHub workflow run data."""
    return {
        "id": 222,
        "name": "CI",
        "workflow_id": 111,
        "status": "completed",
        "conclusion": "success",
        "event": "push",
        "head_branch": "main",
        "head_sha": "abc123",
        "run_number": 42,
        "run_attempt": 1,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:10:00Z",
        "url": "https://api.github.com/repos/testuser/test-repo/actions/runs/222",
        "html_url": "https://github.com/testuser/test-repo/actions/runs/222",
        "jobs_url": "https://api.github.com/repos/testuser/test-repo/actions/runs/222/jobs",
        "logs_url": "https://api.github.com/repos/testuser/test-repo/actions/runs/222/logs",
    }


@pytest.fixture
def sample_workflow_job_data() -> dict[str, Any]:
    """Sample GitHub workflow job data."""
    return {
        "id": 333,
        "name": "build",
        "status": "completed",
        "conclusion": "success",
        "started_at": "2024-01-01T00:00:00Z",
        "completed_at": "2024-01-01T00:05:00Z",
        "run_id": 222,
        "html_url": "https://github.com/testuser/test-repo/actions/runs/222/job/333",
        "steps": [
            {"name": "Checkout", "status": "completed", "conclusion": "success"},
            {"name": "Build", "status": "completed", "conclusion": "success"},
        ],
    }
