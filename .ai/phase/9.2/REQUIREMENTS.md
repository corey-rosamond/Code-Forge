# Phase 9.2: GitHub Integration - Requirements

**Phase:** 9.2
**Name:** GitHub Integration
**Dependencies:** Phase 9.1 (Git Integration), Phase 8.2 (Web Tools)

---

## Overview

Phase 9.2 implements GitHub integration for Code-Forge, enabling the assistant to interact with GitHub repositories, issues, pull requests, and other GitHub features. This builds on Git integration to provide full GitHub workflow support.

---

## Goals

1. Authenticate with GitHub API
2. Work with GitHub Issues
3. Work with Pull Requests
4. Access repository information
5. Support GitHub Actions status
6. Enable code review workflows
7. Handle GitHub notifications

---

## Non-Goals (This Phase)

- GitHub Enterprise Server (focus on github.com)
- GitHub Apps authentication
- Webhooks handling
- Repository creation/deletion
- Team management
- Organization management
- GitHub Packages

---

## Functional Requirements

### FR-1: Authentication

**FR-1.1:** Token-based authentication
- Personal Access Token (PAT)
- Fine-grained PAT support
- Token from environment variable
- Token from config file

**FR-1.2:** Authentication validation
- Validate token on startup
- Check token scopes
- Graceful handling of expired tokens
- Clear error messages

**FR-1.3:** Rate limiting
- Track API rate limits
- Warn when approaching limits
- Handle rate limit errors
- Support conditional requests

### FR-2: Repository Information

**FR-2.1:** Repository details
- Get repository metadata
- List branches
- List tags
- Get default branch
- Check repository visibility

**FR-2.2:** Repository detection
- Detect GitHub remote from git config
- Parse remote URL (HTTPS and SSH)
- Extract owner and repo name
- Handle multiple remotes

**FR-2.3:** Repository context
- Provide repo info to LLM
- Include in system prompt
- Track current repository

### FR-3: Issues

**FR-3.1:** Issue listing
- List repository issues
- Filter by state (open/closed/all)
- Filter by labels
- Filter by assignee
- Filter by milestone

**FR-3.2:** Issue details
- Get single issue
- Get issue comments
- Get issue timeline
- Get linked PRs

**FR-3.3:** Issue operations
- Create issues
- Update issues
- Close/reopen issues
- Add comments
- Add labels
- Assign users

### FR-4: Pull Requests

**FR-4.1:** PR listing
- List repository PRs
- Filter by state
- Filter by head/base branch
- Filter by author

**FR-4.2:** PR details
- Get single PR
- Get PR diff
- Get PR commits
- Get PR files
- Get PR comments
- Get review comments
- Get PR checks/status

**FR-4.3:** PR operations
- Create PRs
- Update PRs
- Close/merge PRs
- Add comments
- Request reviewers
- Add labels

**FR-4.4:** PR reviews
- Get reviews
- Create review
- Submit review (approve/request changes/comment)
- Reply to review comments

### FR-5: GitHub Actions

**FR-5.1:** Workflow runs
- List workflow runs
- Get run status
- Get run logs
- Re-run failed jobs

**FR-5.2:** Check status
- Get commit check status
- Get PR check status
- List check runs

### FR-6: Notifications

**FR-6.1:** Notification listing
- List notifications
- Filter by repository
- Filter by reason
- Mark as read

---

## Non-Functional Requirements

### NFR-1: Performance
- API calls cached where appropriate
- Conditional requests to reduce rate limit usage
- Parallel API calls where possible
- Response time < 2s for most operations

### NFR-2: Security
- Tokens never logged
- Tokens never included in error messages
- Secure token storage
- Minimal required scopes

### NFR-3: Reliability
- Graceful degradation without auth
- Retry on transient failures
- Clear error messages
- Offline operation where possible

---

## Technical Specifications

### Package Structure

```
src/forge/github/
├── __init__.py           # Package exports
├── client.py             # GitHub API client
├── auth.py               # Authentication
├── repository.py         # Repository operations
├── issues.py             # Issue operations
├── pull_requests.py      # PR operations
├── actions.py            # GitHub Actions
├── notifications.py      # Notifications
└── context.py            # GitHub context for LLM
```

### Class Signatures

```python
# auth.py
from dataclasses import dataclass


@dataclass
class GitHubAuth:
    """GitHub authentication information."""
    token: str
    username: str
    scopes: list[str]
    rate_limit: int
    rate_remaining: int
    rate_reset: int


class GitHubAuthenticator:
    """Handle GitHub authentication."""

    def __init__(self, token: str | None = None):
        """Initialize with token or from environment."""
        ...

    async def validate(self) -> GitHubAuth:
        """Validate token and get auth info."""
        ...

    @property
    def is_authenticated(self) -> bool:
        """Check if authenticated."""
        ...

    def get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        ...


# client.py
from typing import Any


class GitHubClient:
    """GitHub API client."""

    def __init__(self, auth: GitHubAuthenticator):
        self.auth = auth
        self.base_url = "https://api.github.com"

    async def get(self, path: str, **params) -> dict[str, Any]:
        """Make GET request."""
        ...

    async def post(self, path: str, data: dict) -> dict[str, Any]:
        """Make POST request."""
        ...

    async def patch(self, path: str, data: dict) -> dict[str, Any]:
        """Make PATCH request."""
        ...

    async def delete(self, path: str) -> None:
        """Make DELETE request."""
        ...

    async def get_paginated(
        self,
        path: str,
        per_page: int = 30,
        max_pages: int | None = None,
        **params
    ) -> list[dict[str, Any]]:
        """Get paginated results."""
        ...


# repository.py
@dataclass
class GitHubRepository:
    """GitHub repository information."""
    owner: str
    name: str
    full_name: str
    description: str | None
    private: bool
    default_branch: str
    url: str
    clone_url: str
    ssh_url: str
    language: str | None
    stars: int
    forks: int
    open_issues: int


@dataclass
class GitHubBranch:
    """GitHub branch information."""
    name: str
    commit_sha: str
    protected: bool


class RepositoryService:
    """Repository operations."""

    def __init__(self, client: GitHubClient):
        self.client = client

    async def get(self, owner: str, repo: str) -> GitHubRepository:
        """Get repository information."""
        ...

    async def list_branches(
        self,
        owner: str,
        repo: str
    ) -> list[GitHubBranch]:
        """List repository branches."""
        ...

    async def list_tags(
        self,
        owner: str,
        repo: str
    ) -> list[dict]:
        """List repository tags."""
        ...

    @staticmethod
    def parse_remote_url(url: str) -> tuple[str, str] | None:
        """Parse owner/repo from remote URL."""
        ...


# issues.py
@dataclass
class GitHubUser:
    """GitHub user information."""
    login: str
    id: int
    avatar_url: str
    url: str


@dataclass
class GitHubLabel:
    """GitHub label."""
    name: str
    color: str
    description: str | None


@dataclass
class GitHubIssue:
    """GitHub issue."""
    number: int
    title: str
    body: str | None
    state: str  # open, closed
    author: GitHubUser
    assignees: list[GitHubUser]
    labels: list[GitHubLabel]
    created_at: str
    updated_at: str
    closed_at: str | None
    comments_count: int
    url: str
    html_url: str


@dataclass
class GitHubComment:
    """GitHub issue/PR comment."""
    id: int
    body: str
    author: GitHubUser
    created_at: str
    updated_at: str


class IssueService:
    """Issue operations."""

    def __init__(self, client: GitHubClient):
        self.client = client

    async def list(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: list[str] | None = None,
        assignee: str | None = None,
        creator: str | None = None,
        sort: str = "created",
        direction: str = "desc"
    ) -> list[GitHubIssue]:
        """List issues."""
        ...

    async def get(
        self,
        owner: str,
        repo: str,
        issue_number: int
    ) -> GitHubIssue:
        """Get single issue."""
        ...

    async def create(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None
    ) -> GitHubIssue:
        """Create issue."""
        ...

    async def update(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        **updates
    ) -> GitHubIssue:
        """Update issue."""
        ...

    async def close(
        self,
        owner: str,
        repo: str,
        issue_number: int
    ) -> GitHubIssue:
        """Close issue."""
        ...

    async def list_comments(
        self,
        owner: str,
        repo: str,
        issue_number: int
    ) -> list[GitHubComment]:
        """List issue comments."""
        ...

    async def add_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        body: str
    ) -> GitHubComment:
        """Add comment to issue."""
        ...


# pull_requests.py
@dataclass
class GitHubPullRequest:
    """GitHub pull request."""
    number: int
    title: str
    body: str | None
    state: str  # open, closed
    draft: bool
    merged: bool
    mergeable: bool | None
    author: GitHubUser
    assignees: list[GitHubUser]
    reviewers: list[GitHubUser]
    labels: list[GitHubLabel]
    head_ref: str
    head_sha: str
    base_ref: str
    created_at: str
    updated_at: str
    merged_at: str | None
    additions: int
    deletions: int
    changed_files: int
    url: str
    html_url: str
    diff_url: str


@dataclass
class GitHubReview:
    """GitHub PR review."""
    id: int
    author: GitHubUser
    body: str | None
    state: str  # APPROVED, CHANGES_REQUESTED, COMMENTED, PENDING
    submitted_at: str | None


@dataclass
class GitHubCheckRun:
    """GitHub check run."""
    id: int
    name: str
    status: str  # queued, in_progress, completed
    conclusion: str | None  # success, failure, etc.
    started_at: str | None
    completed_at: str | None
    url: str


class PullRequestService:
    """Pull request operations."""

    def __init__(self, client: GitHubClient):
        self.client = client

    async def list(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        head: str | None = None,
        base: str | None = None,
        sort: str = "created",
        direction: str = "desc"
    ) -> list[GitHubPullRequest]:
        """List pull requests."""
        ...

    async def get(
        self,
        owner: str,
        repo: str,
        pr_number: int
    ) -> GitHubPullRequest:
        """Get single pull request."""
        ...

    async def create(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str,
        body: str | None = None,
        draft: bool = False
    ) -> GitHubPullRequest:
        """Create pull request."""
        ...

    async def update(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        **updates
    ) -> GitHubPullRequest:
        """Update pull request."""
        ...

    async def get_diff(
        self,
        owner: str,
        repo: str,
        pr_number: int
    ) -> str:
        """Get PR diff."""
        ...

    async def get_files(
        self,
        owner: str,
        repo: str,
        pr_number: int
    ) -> list[dict]:
        """Get PR files."""
        ...

    async def get_commits(
        self,
        owner: str,
        repo: str,
        pr_number: int
    ) -> list[dict]:
        """Get PR commits."""
        ...

    async def list_reviews(
        self,
        owner: str,
        repo: str,
        pr_number: int
    ) -> list[GitHubReview]:
        """List PR reviews."""
        ...

    async def create_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str | None = None,
        event: str = "COMMENT",  # APPROVE, REQUEST_CHANGES, COMMENT
        comments: list[dict] | None = None
    ) -> GitHubReview:
        """Create PR review."""
        ...

    async def get_checks(
        self,
        owner: str,
        repo: str,
        ref: str
    ) -> list[GitHubCheckRun]:
        """Get check runs for ref."""
        ...

    async def merge(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        merge_method: str = "merge",  # merge, squash, rebase
        commit_title: str | None = None,
        commit_message: str | None = None
    ) -> bool:
        """Merge pull request."""
        ...


# actions.py
@dataclass
class WorkflowRun:
    """GitHub Actions workflow run."""
    id: int
    name: str
    workflow_id: int
    status: str  # queued, in_progress, completed
    conclusion: str | None
    event: str
    head_branch: str
    head_sha: str
    created_at: str
    updated_at: str
    url: str
    html_url: str


class ActionsService:
    """GitHub Actions operations."""

    def __init__(self, client: GitHubClient):
        self.client = client

    async def list_runs(
        self,
        owner: str,
        repo: str,
        workflow_id: int | str | None = None,
        branch: str | None = None,
        event: str | None = None,
        status: str | None = None
    ) -> list[WorkflowRun]:
        """List workflow runs."""
        ...

    async def get_run(
        self,
        owner: str,
        repo: str,
        run_id: int
    ) -> WorkflowRun:
        """Get workflow run."""
        ...

    async def get_run_logs(
        self,
        owner: str,
        repo: str,
        run_id: int
    ) -> str:
        """Get workflow run logs."""
        ...

    async def rerun(
        self,
        owner: str,
        repo: str,
        run_id: int
    ) -> None:
        """Re-run workflow."""
        ...

    async def cancel(
        self,
        owner: str,
        repo: str,
        run_id: int
    ) -> None:
        """Cancel workflow run."""
        ...


# context.py
class GitHubContext:
    """GitHub context for LLM."""

    def __init__(
        self,
        client: GitHubClient,
        repo_service: RepositoryService
    ):
        self.client = client
        self.repo_service = repo_service

    async def get_context_summary(
        self,
        owner: str,
        repo: str
    ) -> str:
        """Get GitHub context summary for system prompt."""
        ...

    async def format_issue(self, issue: GitHubIssue) -> str:
        """Format issue for LLM context."""
        ...

    async def format_pr(self, pr: GitHubPullRequest) -> str:
        """Format PR for LLM context."""
        ...
```

---

## GitHub Commands

| Command | Description |
|---------|-------------|
| `/gh` | Show GitHub status |
| `/gh repo` | Repository information |
| `/gh issues` | List issues |
| `/gh issue <n>` | Show issue details |
| `/gh prs` | List pull requests |
| `/gh pr <n>` | Show PR details |
| `/gh pr create` | Create pull request |
| `/gh actions` | Show workflow runs |

---

## Integration Points

### With Git Integration (Phase 9.1)
- Detect GitHub remote from git config
- Link commits to GitHub
- Push/pull with GitHub

### With Web Tools (Phase 8.2)
- HTTP client for API calls
- Cache for API responses

### With Session (Phase 5.1)
- Store GitHub context
- Remember repository

### With Permission System (Phase 4.1)
- Confirm destructive operations
- Protect token access

---

## Testing Requirements

1. Unit tests for authentication
2. Unit tests for API client (mocked)
3. Unit tests for repository service
4. Unit tests for issue service
5. Unit tests for PR service
6. Unit tests for actions service
7. Integration tests with GitHub API (optional)
8. Test coverage >= 90%

---

## Acceptance Criteria

1. Token authentication works
2. Rate limiting handled properly
3. Repository info retrieved correctly
4. Issues can be listed and created
5. PRs can be listed and created
6. PR reviews work correctly
7. Actions status retrieved
8. Error handling is graceful
9. Context provided to LLM
10. Commands work correctly
