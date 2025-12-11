# Phase 9.2: GitHub Integration - Implementation Plan

**Phase:** 9.2
**Name:** GitHub Integration
**Dependencies:** Phase 9.1 (Git Integration), Phase 8.2 (Web Tools)

---

## Overview

This document provides the complete implementation plan for GitHub integration, enabling Code-Forge to interact with GitHub repositories, issues, pull requests, and other GitHub features.

---

## Implementation Order

1. Authentication (auth.py)
2. API Client (client.py)
3. Repository Service (repository.py)
4. Issue Service (issues.py)
5. Pull Request Service (pull_requests.py)
6. Actions Service (actions.py)
7. GitHub Context (context.py)
8. Package exports (__init__.py)

---

## File Implementations

### 1. auth.py - GitHub Authentication

```python
"""GitHub authentication handling."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

import aiohttp

if TYPE_CHECKING:
    pass


class GitHubAuthError(Exception):
    """GitHub authentication error."""
    pass


@dataclass
class GitHubAuth:
    """GitHub authentication information."""
    token: str
    username: str
    scopes: list[str] = field(default_factory=list)
    rate_limit: int = 5000
    rate_remaining: int = 5000
    rate_reset: int = 0

    @property
    def rate_reset_time(self) -> datetime:
        """Get rate limit reset time."""
        return datetime.fromtimestamp(self.rate_reset)

    @property
    def is_rate_limited(self) -> bool:
        """Check if rate limited."""
        return self.rate_remaining == 0


class GitHubAuthenticator:
    """Handle GitHub authentication."""

    ENV_TOKEN_KEY = "GITHUB_TOKEN"
    ENV_TOKEN_ALT = "GH_TOKEN"

    def __init__(self, token: str | None = None):
        """
        Initialize with token or from environment.

        Args:
            token: GitHub personal access token.
                   If None, reads from GITHUB_TOKEN or GH_TOKEN env var.
        """
        self._token = token or self._get_token_from_env()
        self._auth_info: GitHubAuth | None = None
        self._validated = False

    def _get_token_from_env(self) -> str | None:
        """Get token from environment variables."""
        return os.environ.get(self.ENV_TOKEN_KEY) or os.environ.get(
            self.ENV_TOKEN_ALT
        )

    @property
    def has_token(self) -> bool:
        """Check if token is available."""
        return self._token is not None

    @property
    def is_authenticated(self) -> bool:
        """Check if authenticated and validated."""
        return self._validated and self._auth_info is not None

    def get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def validate(self) -> GitHubAuth:
        """
        Validate token and get auth info.

        Returns:
            GitHubAuth with user info and rate limits.

        Raises:
            GitHubAuthError: If token is invalid or missing.
        """
        if not self._token:
            raise GitHubAuthError(
                "No GitHub token found. Set GITHUB_TOKEN environment variable "
                "or provide token in configuration."
            )

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.github.com/user",
                headers=self.get_headers(),
            ) as response:
                if response.status == 401:
                    raise GitHubAuthError(
                        "Invalid GitHub token. Please check your token."
                    )
                if response.status == 403:
                    raise GitHubAuthError(
                        "GitHub token has insufficient permissions."
                    )
                if response.status != 200:
                    raise GitHubAuthError(
                        f"GitHub API error: {response.status}"
                    )

                data = await response.json()

                # Parse scopes from header
                scopes_header = response.headers.get("X-OAuth-Scopes", "")
                scopes = [
                    s.strip() for s in scopes_header.split(",") if s.strip()
                ]

                self._auth_info = GitHubAuth(
                    token=self._token,
                    username=data["login"],
                    scopes=scopes,
                    rate_limit=int(
                        response.headers.get("X-RateLimit-Limit", 5000)
                    ),
                    rate_remaining=int(
                        response.headers.get("X-RateLimit-Remaining", 5000)
                    ),
                    rate_reset=int(
                        response.headers.get("X-RateLimit-Reset", 0)
                    ),
                )
                self._validated = True
                return self._auth_info

    def update_rate_limit(
        self,
        limit: int,
        remaining: int,
        reset: int
    ) -> None:
        """Update rate limit info from response headers."""
        if self._auth_info:
            self._auth_info.rate_limit = limit
            self._auth_info.rate_remaining = remaining
            self._auth_info.rate_reset = reset

    def get_auth_info(self) -> GitHubAuth | None:
        """Get current auth info."""
        return self._auth_info
```

### 2. client.py - GitHub API Client

```python
"""GitHub API client."""
from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlencode

import aiohttp

from .auth import GitHubAuthenticator, GitHubAuthError


class GitHubAPIError(Exception):
    """GitHub API error."""

    def __init__(
        self,
        message: str,
        status: int | None = None,
        response: dict | None = None
    ):
        super().__init__(message)
        self.status = status
        self.response = response


class GitHubRateLimitError(GitHubAPIError):
    """Rate limit exceeded error."""
    pass


class GitHubNotFoundError(GitHubAPIError):
    """Resource not found error."""
    pass


class GitHubClient:
    """GitHub API client."""

    BASE_URL = "https://api.github.com"

    def __init__(
        self,
        auth: GitHubAuthenticator,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize GitHub client.

        Args:
            auth: GitHub authenticator.
            timeout: Request timeout in seconds.
            max_retries: Maximum retries for failed requests.
        """
        self.auth = auth
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers=self.auth.get_headers(),
            )
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def _build_url(self, path: str, **params) -> str:
        """Build full URL with query parameters."""
        url = f"{self.BASE_URL}{path}"
        if params:
            # Filter out None values
            filtered = {k: v for k, v in params.items() if v is not None}
            if filtered:
                url = f"{url}?{urlencode(filtered)}"
        return url

    def _update_rate_limit(self, headers: dict) -> None:
        """Update rate limit from response headers."""
        try:
            self.auth.update_rate_limit(
                limit=int(headers.get("X-RateLimit-Limit", 5000)),
                remaining=int(headers.get("X-RateLimit-Remaining", 5000)),
                reset=int(headers.get("X-RateLimit-Reset", 0)),
            )
        except (ValueError, TypeError):
            pass

    async def _request(
        self,
        method: str,
        path: str,
        data: dict | None = None,
        accept: str | None = None,
        **params
    ) -> tuple[Any, dict]:
        """
        Make HTTP request.

        Returns:
            Tuple of (response_data, headers).
        """
        session = await self._get_session()
        url = self._build_url(path, **params)

        headers = {}
        if accept:
            headers["Accept"] = accept

        for attempt in range(self.max_retries):
            try:
                async with session.request(
                    method,
                    url,
                    json=data,
                    headers=headers,
                ) as response:
                    self._update_rate_limit(response.headers)

                    if response.status == 204:
                        return None, dict(response.headers)

                    if response.status == 404:
                        raise GitHubNotFoundError(
                            f"Resource not found: {path}",
                            status=404,
                        )

                    if response.status == 403:
                        # Check if rate limited
                        remaining = response.headers.get(
                            "X-RateLimit-Remaining"
                        )
                        if remaining == "0":
                            raise GitHubRateLimitError(
                                "GitHub API rate limit exceeded",
                                status=403,
                            )
                        raise GitHubAPIError(
                            "Access forbidden",
                            status=403,
                        )

                    if response.status == 401:
                        raise GitHubAuthError("Authentication failed")

                    if response.status >= 400:
                        error_data = await response.json()
                        message = error_data.get("message", "Unknown error")
                        raise GitHubAPIError(
                            f"GitHub API error: {message}",
                            status=response.status,
                            response=error_data,
                        )

                    # Handle different content types
                    content_type = response.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        result = await response.json()
                    else:
                        result = await response.text()

                    return result, dict(response.headers)

            except aiohttp.ClientError as e:
                if attempt < self.max_retries - 1:
                    # Exponential backoff with jitter: base * 2^attempt + random jitter
                    # attempt 0: 1-1.5s, attempt 1: 2-3s, attempt 2: 4-6s
                    import random
                    base_delay = 1.0  # Base delay in seconds
                    max_delay = 60.0  # Cap at 60 seconds
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = delay * random.uniform(0, 0.5)  # 0-50% jitter
                    await asyncio.sleep(delay + jitter)
                    continue
                raise GitHubAPIError(f"Request failed: {e}")

        raise GitHubAPIError("Max retries exceeded")

    async def get(self, path: str, **params) -> dict[str, Any]:
        """Make GET request."""
        result, _ = await self._request("GET", path, **params)
        return result

    async def get_raw(
        self,
        path: str,
        accept: str = "application/vnd.github.raw",
        **params
    ) -> str:
        """Get raw content."""
        result, _ = await self._request(
            "GET", path, accept=accept, **params
        )
        return result

    async def post(self, path: str, data: dict) -> dict[str, Any]:
        """Make POST request."""
        result, _ = await self._request("POST", path, data=data)
        return result

    async def patch(self, path: str, data: dict) -> dict[str, Any]:
        """Make PATCH request."""
        result, _ = await self._request("PATCH", path, data=data)
        return result

    async def put(self, path: str, data: dict | None = None) -> dict[str, Any]:
        """Make PUT request."""
        result, _ = await self._request("PUT", path, data=data)
        return result

    async def delete(self, path: str) -> None:
        """Make DELETE request."""
        await self._request("DELETE", path)

    async def get_paginated(
        self,
        path: str,
        per_page: int = 30,
        max_pages: int | None = None,
        **params
    ) -> list[dict[str, Any]]:
        """
        Get paginated results.

        Args:
            path: API path.
            per_page: Items per page (max 100).
            max_pages: Maximum pages to fetch (None for all).
            **params: Additional query parameters.

        Returns:
            List of all items.
        """
        all_items = []
        page = 1
        per_page = min(per_page, 100)

        while True:
            result, headers = await self._request(
                "GET",
                path,
                page=page,
                per_page=per_page,
                **params
            )

            if isinstance(result, list):
                all_items.extend(result)
                if len(result) < per_page:
                    break
            else:
                # Some endpoints return objects with items array
                items = result.get("items", [])
                all_items.extend(items)
                if len(items) < per_page:
                    break

            page += 1
            if max_pages and page > max_pages:
                break

            # Check for Link header to see if more pages
            link_header = headers.get("Link", "")
            if 'rel="next"' not in link_header:
                break

        return all_items
```

### 3. repository.py - Repository Service

```python
"""GitHub repository operations."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .client import GitHubClient


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
    archived: bool
    disabled: bool
    topics: list[str]

    @classmethod
    def from_api(cls, data: dict) -> GitHubRepository:
        """Create from API response."""
        return cls(
            owner=data["owner"]["login"],
            name=data["name"],
            full_name=data["full_name"],
            description=data.get("description"),
            private=data["private"],
            default_branch=data["default_branch"],
            url=data["html_url"],
            clone_url=data["clone_url"],
            ssh_url=data["ssh_url"],
            language=data.get("language"),
            stars=data["stargazers_count"],
            forks=data["forks_count"],
            open_issues=data["open_issues_count"],
            archived=data.get("archived", False),
            disabled=data.get("disabled", False),
            topics=data.get("topics", []),
        )


@dataclass
class GitHubBranch:
    """GitHub branch information."""
    name: str
    commit_sha: str
    protected: bool

    @classmethod
    def from_api(cls, data: dict) -> GitHubBranch:
        """Create from API response."""
        return cls(
            name=data["name"],
            commit_sha=data["commit"]["sha"],
            protected=data.get("protected", False),
        )


@dataclass
class GitHubTag:
    """GitHub tag information."""
    name: str
    commit_sha: str
    zipball_url: str
    tarball_url: str

    @classmethod
    def from_api(cls, data: dict) -> GitHubTag:
        """Create from API response."""
        return cls(
            name=data["name"],
            commit_sha=data["commit"]["sha"],
            zipball_url=data["zipball_url"],
            tarball_url=data["tarball_url"],
        )


class RepositoryService:
    """Repository operations."""

    # Patterns for parsing remote URLs
    HTTPS_PATTERN = re.compile(
        r"https?://(?:www\.)?github\.com/([^/]+)/([^/]+?)(?:\.git)?$"
    )
    SSH_PATTERN = re.compile(
        r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$"
    )

    def __init__(self, client: GitHubClient):
        """Initialize repository service."""
        self.client = client

    async def get(self, owner: str, repo: str) -> GitHubRepository:
        """
        Get repository information.

        Args:
            owner: Repository owner.
            repo: Repository name.

        Returns:
            GitHubRepository with details.
        """
        data = await self.client.get(f"/repos/{owner}/{repo}")
        return GitHubRepository.from_api(data)

    async def list_branches(
        self,
        owner: str,
        repo: str,
        protected: bool | None = None
    ) -> list[GitHubBranch]:
        """
        List repository branches.

        Args:
            owner: Repository owner.
            repo: Repository name.
            protected: Filter by protected status.

        Returns:
            List of branches.
        """
        params = {}
        if protected is not None:
            params["protected"] = str(protected).lower()

        data = await self.client.get_paginated(
            f"/repos/{owner}/{repo}/branches",
            **params
        )
        return [GitHubBranch.from_api(b) for b in data]

    async def get_branch(
        self,
        owner: str,
        repo: str,
        branch: str
    ) -> GitHubBranch:
        """Get single branch."""
        data = await self.client.get(
            f"/repos/{owner}/{repo}/branches/{branch}"
        )
        return GitHubBranch.from_api(data)

    async def list_tags(
        self,
        owner: str,
        repo: str
    ) -> list[GitHubTag]:
        """List repository tags."""
        data = await self.client.get_paginated(
            f"/repos/{owner}/{repo}/tags"
        )
        return [GitHubTag.from_api(t) for t in data]

    async def get_readme(
        self,
        owner: str,
        repo: str,
        ref: str | None = None
    ) -> str:
        """Get repository README content."""
        params = {}
        if ref:
            params["ref"] = ref

        return await self.client.get_raw(
            f"/repos/{owner}/{repo}/readme",
            **params
        )

    async def get_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str | None = None
    ) -> str | list[dict]:
        """
        Get repository content.

        Returns file content or directory listing.
        """
        params = {}
        if ref:
            params["ref"] = ref

        return await self.client.get(
            f"/repos/{owner}/{repo}/contents/{path}",
            **params
        )

    @classmethod
    def parse_remote_url(cls, url: str) -> tuple[str, str] | None:
        """
        Parse owner/repo from remote URL.

        Args:
            url: Git remote URL (HTTPS or SSH).

        Returns:
            Tuple of (owner, repo) or None if not a GitHub URL.
        """
        # Try HTTPS pattern
        match = cls.HTTPS_PATTERN.match(url)
        if match:
            return match.group(1), match.group(2)

        # Try SSH pattern
        match = cls.SSH_PATTERN.match(url)
        if match:
            return match.group(1), match.group(2)

        return None
```

### 4. issues.py - Issue Service

```python
"""GitHub issue operations."""
from __future__ import annotations

from dataclasses import dataclass, field

from .client import GitHubClient


@dataclass
class GitHubUser:
    """GitHub user information."""
    login: str
    id: int
    avatar_url: str
    url: str
    type: str  # User, Bot, Organization

    @classmethod
    def from_api(cls, data: dict) -> GitHubUser:
        """Create from API response."""
        return cls(
            login=data["login"],
            id=data["id"],
            avatar_url=data["avatar_url"],
            url=data["html_url"],
            type=data.get("type", "User"),
        )


@dataclass
class GitHubLabel:
    """GitHub label."""
    name: str
    color: str
    description: str | None

    @classmethod
    def from_api(cls, data: dict) -> GitHubLabel:
        """Create from API response."""
        return cls(
            name=data["name"],
            color=data["color"],
            description=data.get("description"),
        )


@dataclass
class GitHubMilestone:
    """GitHub milestone."""
    number: int
    title: str
    description: str | None
    state: str
    due_on: str | None

    @classmethod
    def from_api(cls, data: dict) -> GitHubMilestone:
        """Create from API response."""
        return cls(
            number=data["number"],
            title=data["title"],
            description=data.get("description"),
            state=data["state"],
            due_on=data.get("due_on"),
        )


@dataclass
class GitHubIssue:
    """GitHub issue."""
    number: int
    title: str
    body: str | None
    state: str
    state_reason: str | None
    author: GitHubUser
    assignees: list[GitHubUser]
    labels: list[GitHubLabel]
    milestone: GitHubMilestone | None
    created_at: str
    updated_at: str
    closed_at: str | None
    comments_count: int
    url: str
    html_url: str
    is_pull_request: bool

    @classmethod
    def from_api(cls, data: dict) -> GitHubIssue:
        """Create from API response."""
        milestone = None
        if data.get("milestone"):
            milestone = GitHubMilestone.from_api(data["milestone"])

        return cls(
            number=data["number"],
            title=data["title"],
            body=data.get("body"),
            state=data["state"],
            state_reason=data.get("state_reason"),
            author=GitHubUser.from_api(data["user"]),
            assignees=[
                GitHubUser.from_api(a) for a in data.get("assignees", [])
            ],
            labels=[
                GitHubLabel.from_api(l) for l in data.get("labels", [])
            ],
            milestone=milestone,
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            closed_at=data.get("closed_at"),
            comments_count=data.get("comments", 0),
            url=data["url"],
            html_url=data["html_url"],
            is_pull_request="pull_request" in data,
        )


@dataclass
class GitHubComment:
    """GitHub issue/PR comment."""
    id: int
    body: str
    author: GitHubUser
    created_at: str
    updated_at: str
    html_url: str

    @classmethod
    def from_api(cls, data: dict) -> GitHubComment:
        """Create from API response."""
        return cls(
            id=data["id"],
            body=data["body"],
            author=GitHubUser.from_api(data["user"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            html_url=data["html_url"],
        )


class IssueService:
    """Issue operations."""

    def __init__(self, client: GitHubClient):
        """Initialize issue service."""
        self.client = client

    async def list(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: list[str] | None = None,
        assignee: str | None = None,
        creator: str | None = None,
        mentioned: str | None = None,
        milestone: str | int | None = None,
        sort: str = "created",
        direction: str = "desc",
        since: str | None = None
    ) -> list[GitHubIssue]:
        """
        List issues.

        Args:
            owner: Repository owner.
            repo: Repository name.
            state: Issue state (open, closed, all).
            labels: Filter by labels.
            assignee: Filter by assignee.
            creator: Filter by creator.
            mentioned: Filter by mentioned user.
            milestone: Filter by milestone number or "*"/"none".
            sort: Sort by (created, updated, comments).
            direction: Sort direction (asc, desc).
            since: Only issues updated after this time.

        Returns:
            List of issues.
        """
        params = {
            "state": state,
            "sort": sort,
            "direction": direction,
        }
        if labels:
            params["labels"] = ",".join(labels)
        if assignee:
            params["assignee"] = assignee
        if creator:
            params["creator"] = creator
        if mentioned:
            params["mentioned"] = mentioned
        if milestone:
            params["milestone"] = str(milestone)
        if since:
            params["since"] = since

        data = await self.client.get_paginated(
            f"/repos/{owner}/{repo}/issues",
            **params
        )

        # Filter out PRs (they appear in issues endpoint)
        issues = [
            GitHubIssue.from_api(d) for d in data
            if "pull_request" not in d
        ]
        return issues

    async def get(
        self,
        owner: str,
        repo: str,
        issue_number: int
    ) -> GitHubIssue:
        """Get single issue."""
        data = await self.client.get(
            f"/repos/{owner}/{repo}/issues/{issue_number}"
        )
        return GitHubIssue.from_api(data)

    async def create(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
        milestone: int | None = None
    ) -> GitHubIssue:
        """Create issue."""
        payload = {"title": title}
        if body:
            payload["body"] = body
        if labels:
            payload["labels"] = labels
        if assignees:
            payload["assignees"] = assignees
        if milestone:
            payload["milestone"] = milestone

        data = await self.client.post(
            f"/repos/{owner}/{repo}/issues",
            payload
        )
        return GitHubIssue.from_api(data)

    async def update(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
        state_reason: str | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
        milestone: int | None = None
    ) -> GitHubIssue:
        """Update issue."""
        payload = {}
        if title is not None:
            payload["title"] = title
        if body is not None:
            payload["body"] = body
        if state is not None:
            payload["state"] = state
        if state_reason is not None:
            payload["state_reason"] = state_reason
        if labels is not None:
            payload["labels"] = labels
        if assignees is not None:
            payload["assignees"] = assignees
        if milestone is not None:
            payload["milestone"] = milestone

        data = await self.client.patch(
            f"/repos/{owner}/{repo}/issues/{issue_number}",
            payload
        )
        return GitHubIssue.from_api(data)

    async def close(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        reason: str = "completed"
    ) -> GitHubIssue:
        """Close issue."""
        return await self.update(
            owner, repo, issue_number,
            state="closed",
            state_reason=reason
        )

    async def reopen(
        self,
        owner: str,
        repo: str,
        issue_number: int
    ) -> GitHubIssue:
        """Reopen issue."""
        return await self.update(
            owner, repo, issue_number,
            state="open"
        )

    async def list_comments(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        since: str | None = None
    ) -> list[GitHubComment]:
        """List issue comments."""
        params = {}
        if since:
            params["since"] = since

        data = await self.client.get_paginated(
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            **params
        )
        return [GitHubComment.from_api(c) for c in data]

    async def add_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        body: str
    ) -> GitHubComment:
        """Add comment to issue."""
        data = await self.client.post(
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            {"body": body}
        )
        return GitHubComment.from_api(data)

    async def update_comment(
        self,
        owner: str,
        repo: str,
        comment_id: int,
        body: str
    ) -> GitHubComment:
        """Update issue comment."""
        data = await self.client.patch(
            f"/repos/{owner}/{repo}/issues/comments/{comment_id}",
            {"body": body}
        )
        return GitHubComment.from_api(data)

    async def delete_comment(
        self,
        owner: str,
        repo: str,
        comment_id: int
    ) -> None:
        """Delete issue comment."""
        await self.client.delete(
            f"/repos/{owner}/{repo}/issues/comments/{comment_id}"
        )

    async def add_labels(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        labels: list[str]
    ) -> list[GitHubLabel]:
        """Add labels to issue."""
        data = await self.client.post(
            f"/repos/{owner}/{repo}/issues/{issue_number}/labels",
            {"labels": labels}
        )
        return [GitHubLabel.from_api(l) for l in data]

    async def remove_label(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        label: str
    ) -> None:
        """Remove label from issue."""
        await self.client.delete(
            f"/repos/{owner}/{repo}/issues/{issue_number}/labels/{label}"
        )
```

### 5. pull_requests.py - Pull Request Service

```python
"""GitHub pull request operations."""
from __future__ import annotations

from dataclasses import dataclass

from .client import GitHubClient
from .issues import GitHubUser, GitHubLabel


@dataclass
class GitHubPullRequest:
    """GitHub pull request."""
    number: int
    title: str
    body: str | None
    state: str
    draft: bool
    merged: bool
    mergeable: bool | None
    mergeable_state: str | None
    author: GitHubUser
    assignees: list[GitHubUser]
    requested_reviewers: list[GitHubUser]
    labels: list[GitHubLabel]
    head_ref: str
    head_sha: str
    head_repo: str | None
    base_ref: str
    base_sha: str
    created_at: str
    updated_at: str
    merged_at: str | None
    merged_by: GitHubUser | None
    additions: int
    deletions: int
    changed_files: int
    commits: int
    comments: int
    review_comments: int
    url: str
    html_url: str
    diff_url: str

    @classmethod
    def from_api(cls, data: dict) -> GitHubPullRequest:
        """Create from API response."""
        merged_by = None
        if data.get("merged_by"):
            merged_by = GitHubUser.from_api(data["merged_by"])

        head_repo = None
        if data.get("head", {}).get("repo"):
            head_repo = data["head"]["repo"]["full_name"]

        return cls(
            number=data["number"],
            title=data["title"],
            body=data.get("body"),
            state=data["state"],
            draft=data.get("draft", False),
            merged=data.get("merged", False),
            mergeable=data.get("mergeable"),
            mergeable_state=data.get("mergeable_state"),
            author=GitHubUser.from_api(data["user"]),
            assignees=[
                GitHubUser.from_api(a) for a in data.get("assignees", [])
            ],
            requested_reviewers=[
                GitHubUser.from_api(r)
                for r in data.get("requested_reviewers", [])
            ],
            labels=[
                GitHubLabel.from_api(l) for l in data.get("labels", [])
            ],
            head_ref=data["head"]["ref"],
            head_sha=data["head"]["sha"],
            head_repo=head_repo,
            base_ref=data["base"]["ref"],
            base_sha=data["base"]["sha"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            merged_at=data.get("merged_at"),
            merged_by=merged_by,
            additions=data.get("additions", 0),
            deletions=data.get("deletions", 0),
            changed_files=data.get("changed_files", 0),
            commits=data.get("commits", 0),
            comments=data.get("comments", 0),
            review_comments=data.get("review_comments", 0),
            url=data["url"],
            html_url=data["html_url"],
            diff_url=data["diff_url"],
        )


@dataclass
class GitHubReview:
    """GitHub PR review."""
    id: int
    author: GitHubUser
    body: str | None
    state: str
    submitted_at: str | None
    html_url: str

    @classmethod
    def from_api(cls, data: dict) -> GitHubReview:
        """Create from API response."""
        return cls(
            id=data["id"],
            author=GitHubUser.from_api(data["user"]),
            body=data.get("body"),
            state=data["state"],
            submitted_at=data.get("submitted_at"),
            html_url=data["html_url"],
        )


@dataclass
class GitHubReviewComment:
    """GitHub PR review comment."""
    id: int
    body: str
    author: GitHubUser
    path: str
    position: int | None
    line: int | None
    commit_id: str
    created_at: str
    updated_at: str
    html_url: str

    @classmethod
    def from_api(cls, data: dict) -> GitHubReviewComment:
        """Create from API response."""
        return cls(
            id=data["id"],
            body=data["body"],
            author=GitHubUser.from_api(data["user"]),
            path=data["path"],
            position=data.get("position"),
            line=data.get("line"),
            commit_id=data["commit_id"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            html_url=data["html_url"],
        )


@dataclass
class GitHubCheckRun:
    """GitHub check run."""
    id: int
    name: str
    status: str
    conclusion: str | None
    started_at: str | None
    completed_at: str | None
    url: str
    html_url: str | None
    app_name: str | None

    @classmethod
    def from_api(cls, data: dict) -> GitHubCheckRun:
        """Create from API response."""
        app_name = None
        if data.get("app"):
            app_name = data["app"].get("name")

        return cls(
            id=data["id"],
            name=data["name"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            url=data["url"],
            html_url=data.get("html_url"),
            app_name=app_name,
        )


@dataclass
class GitHubPRFile:
    """GitHub PR file change."""
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: str | None
    blob_url: str
    raw_url: str

    @classmethod
    def from_api(cls, data: dict) -> GitHubPRFile:
        """Create from API response."""
        return cls(
            filename=data["filename"],
            status=data["status"],
            additions=data["additions"],
            deletions=data["deletions"],
            changes=data["changes"],
            patch=data.get("patch"),
            blob_url=data["blob_url"],
            raw_url=data["raw_url"],
        )


class PullRequestService:
    """Pull request operations."""

    def __init__(self, client: GitHubClient):
        """Initialize PR service."""
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
        params = {
            "state": state,
            "sort": sort,
            "direction": direction,
        }
        if head:
            params["head"] = head
        if base:
            params["base"] = base

        data = await self.client.get_paginated(
            f"/repos/{owner}/{repo}/pulls",
            **params
        )
        return [GitHubPullRequest.from_api(pr) for pr in data]

    async def get(
        self,
        owner: str,
        repo: str,
        pr_number: int
    ) -> GitHubPullRequest:
        """Get single pull request."""
        data = await self.client.get(
            f"/repos/{owner}/{repo}/pulls/{pr_number}"
        )
        return GitHubPullRequest.from_api(data)

    async def create(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str,
        body: str | None = None,
        draft: bool = False,
        maintainer_can_modify: bool = True
    ) -> GitHubPullRequest:
        """Create pull request."""
        payload = {
            "title": title,
            "head": head,
            "base": base,
            "draft": draft,
            "maintainer_can_modify": maintainer_can_modify,
        }
        if body:
            payload["body"] = body

        data = await self.client.post(
            f"/repos/{owner}/{repo}/pulls",
            payload
        )
        return GitHubPullRequest.from_api(data)

    async def update(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
        base: str | None = None
    ) -> GitHubPullRequest:
        """Update pull request."""
        payload = {}
        if title is not None:
            payload["title"] = title
        if body is not None:
            payload["body"] = body
        if state is not None:
            payload["state"] = state
        if base is not None:
            payload["base"] = base

        data = await self.client.patch(
            f"/repos/{owner}/{repo}/pulls/{pr_number}",
            payload
        )
        return GitHubPullRequest.from_api(data)

    async def get_diff(
        self,
        owner: str,
        repo: str,
        pr_number: int
    ) -> str:
        """Get PR diff."""
        return await self.client.get_raw(
            f"/repos/{owner}/{repo}/pulls/{pr_number}",
            accept="application/vnd.github.diff"
        )

    async def get_files(
        self,
        owner: str,
        repo: str,
        pr_number: int
    ) -> list[GitHubPRFile]:
        """Get PR files."""
        data = await self.client.get_paginated(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/files"
        )
        return [GitHubPRFile.from_api(f) for f in data]

    async def get_commits(
        self,
        owner: str,
        repo: str,
        pr_number: int
    ) -> list[dict]:
        """Get PR commits."""
        return await self.client.get_paginated(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/commits"
        )

    async def list_reviews(
        self,
        owner: str,
        repo: str,
        pr_number: int
    ) -> list[GitHubReview]:
        """List PR reviews."""
        data = await self.client.get_paginated(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        )
        return [GitHubReview.from_api(r) for r in data]

    async def create_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str | None = None,
        event: str = "COMMENT",
        comments: list[dict] | None = None,
        commit_id: str | None = None
    ) -> GitHubReview:
        """
        Create PR review.

        Args:
            event: APPROVE, REQUEST_CHANGES, or COMMENT
            comments: List of review comments with path, position, body
        """
        payload = {"event": event}
        if body:
            payload["body"] = body
        if comments:
            payload["comments"] = comments
        if commit_id:
            payload["commit_id"] = commit_id

        data = await self.client.post(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
            payload
        )
        return GitHubReview.from_api(data)

    async def list_review_comments(
        self,
        owner: str,
        repo: str,
        pr_number: int
    ) -> list[GitHubReviewComment]:
        """List review comments on PR."""
        data = await self.client.get_paginated(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        )
        return [GitHubReviewComment.from_api(c) for c in data]

    async def get_checks(
        self,
        owner: str,
        repo: str,
        ref: str
    ) -> list[GitHubCheckRun]:
        """Get check runs for ref."""
        data = await self.client.get(
            f"/repos/{owner}/{repo}/commits/{ref}/check-runs"
        )
        return [GitHubCheckRun.from_api(c) for c in data.get("check_runs", [])]

    async def get_combined_status(
        self,
        owner: str,
        repo: str,
        ref: str
    ) -> dict:
        """Get combined commit status."""
        return await self.client.get(
            f"/repos/{owner}/{repo}/commits/{ref}/status"
        )

    async def merge(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        merge_method: str = "merge",
        commit_title: str | None = None,
        commit_message: str | None = None,
        sha: str | None = None
    ) -> dict:
        """
        Merge pull request.

        Args:
            merge_method: merge, squash, or rebase
        """
        payload = {"merge_method": merge_method}
        if commit_title:
            payload["commit_title"] = commit_title
        if commit_message:
            payload["commit_message"] = commit_message
        if sha:
            payload["sha"] = sha

        return await self.client.put(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/merge",
            payload
        )

    async def request_reviewers(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        reviewers: list[str] | None = None,
        team_reviewers: list[str] | None = None
    ) -> GitHubPullRequest:
        """Request reviewers for PR."""
        payload = {}
        if reviewers:
            payload["reviewers"] = reviewers
        if team_reviewers:
            payload["team_reviewers"] = team_reviewers

        data = await self.client.post(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/requested_reviewers",
            payload
        )
        return GitHubPullRequest.from_api(data)
```

### 6. actions.py - GitHub Actions Service

```python
"""GitHub Actions operations."""
from __future__ import annotations

from dataclasses import dataclass

from .client import GitHubClient


@dataclass
class WorkflowRun:
    """GitHub Actions workflow run."""
    id: int
    name: str
    workflow_id: int
    status: str
    conclusion: str | None
    event: str
    head_branch: str
    head_sha: str
    run_number: int
    run_attempt: int
    created_at: str
    updated_at: str
    url: str
    html_url: str
    jobs_url: str
    logs_url: str

    @classmethod
    def from_api(cls, data: dict) -> WorkflowRun:
        """Create from API response."""
        return cls(
            id=data["id"],
            name=data["name"],
            workflow_id=data["workflow_id"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            event=data["event"],
            head_branch=data["head_branch"],
            head_sha=data["head_sha"],
            run_number=data["run_number"],
            run_attempt=data["run_attempt"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            url=data["url"],
            html_url=data["html_url"],
            jobs_url=data["jobs_url"],
            logs_url=data["logs_url"],
        )


@dataclass
class WorkflowJob:
    """GitHub Actions workflow job."""
    id: int
    name: str
    status: str
    conclusion: str | None
    started_at: str | None
    completed_at: str | None
    run_id: int
    html_url: str
    steps: list[dict]

    @classmethod
    def from_api(cls, data: dict) -> WorkflowJob:
        """Create from API response."""
        return cls(
            id=data["id"],
            name=data["name"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            run_id=data["run_id"],
            html_url=data["html_url"],
            steps=data.get("steps", []),
        )


@dataclass
class Workflow:
    """GitHub Actions workflow."""
    id: int
    name: str
    path: str
    state: str
    created_at: str
    updated_at: str
    url: str
    html_url: str

    @classmethod
    def from_api(cls, data: dict) -> Workflow:
        """Create from API response."""
        return cls(
            id=data["id"],
            name=data["name"],
            path=data["path"],
            state=data["state"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            url=data["url"],
            html_url=data["html_url"],
        )


class ActionsService:
    """GitHub Actions operations."""

    def __init__(self, client: GitHubClient):
        """Initialize actions service."""
        self.client = client

    async def list_workflows(
        self,
        owner: str,
        repo: str
    ) -> list[Workflow]:
        """List repository workflows."""
        data = await self.client.get(
            f"/repos/{owner}/{repo}/actions/workflows"
        )
        return [Workflow.from_api(w) for w in data.get("workflows", [])]

    async def list_runs(
        self,
        owner: str,
        repo: str,
        workflow_id: int | str | None = None,
        branch: str | None = None,
        event: str | None = None,
        status: str | None = None,
        actor: str | None = None
    ) -> list[WorkflowRun]:
        """
        List workflow runs.

        Args:
            workflow_id: Filter by workflow ID or filename.
            branch: Filter by branch.
            event: Filter by event type (push, pull_request, etc).
            status: Filter by status (queued, in_progress, completed).
            actor: Filter by actor (user who triggered).
        """
        params = {}
        if branch:
            params["branch"] = branch
        if event:
            params["event"] = event
        if status:
            params["status"] = status
        if actor:
            params["actor"] = actor

        if workflow_id:
            path = f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
        else:
            path = f"/repos/{owner}/{repo}/actions/runs"

        data = await self.client.get(path, **params)
        return [WorkflowRun.from_api(r) for r in data.get("workflow_runs", [])]

    async def get_run(
        self,
        owner: str,
        repo: str,
        run_id: int
    ) -> WorkflowRun:
        """Get workflow run."""
        data = await self.client.get(
            f"/repos/{owner}/{repo}/actions/runs/{run_id}"
        )
        return WorkflowRun.from_api(data)

    async def list_run_jobs(
        self,
        owner: str,
        repo: str,
        run_id: int,
        filter: str = "latest"
    ) -> list[WorkflowJob]:
        """
        List jobs for a workflow run.

        Args:
            filter: latest or all
        """
        data = await self.client.get(
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/jobs",
            filter=filter
        )
        return [WorkflowJob.from_api(j) for j in data.get("jobs", [])]

    async def get_run_logs(
        self,
        owner: str,
        repo: str,
        run_id: int
    ) -> str:
        """
        Get workflow run logs.

        Returns URL to download logs (zip file).
        """
        # This endpoint redirects to download URL
        return await self.client.get_raw(
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/logs"
        )

    async def rerun(
        self,
        owner: str,
        repo: str,
        run_id: int
    ) -> None:
        """Re-run all jobs in workflow."""
        await self.client.post(
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/rerun",
            {}
        )

    async def rerun_failed(
        self,
        owner: str,
        repo: str,
        run_id: int
    ) -> None:
        """Re-run only failed jobs."""
        await self.client.post(
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/rerun-failed-jobs",
            {}
        )

    async def cancel(
        self,
        owner: str,
        repo: str,
        run_id: int
    ) -> None:
        """Cancel workflow run."""
        await self.client.post(
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/cancel",
            {}
        )

    async def get_job_logs(
        self,
        owner: str,
        repo: str,
        job_id: int
    ) -> str:
        """Get job logs."""
        return await self.client.get_raw(
            f"/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
        )
```

### 7. context.py - GitHub Context for LLM

```python
"""GitHub context for LLM integration."""
from __future__ import annotations

from .client import GitHubClient
from .repository import RepositoryService, GitHubRepository
from .issues import GitHubIssue, IssueService
from .pull_requests import GitHubPullRequest, PullRequestService


class GitHubContext:
    """GitHub context for LLM."""

    def __init__(
        self,
        client: GitHubClient,
        repo_service: RepositoryService,
        issue_service: IssueService,
        pr_service: PullRequestService
    ):
        """Initialize GitHub context."""
        self.client = client
        self.repo_service = repo_service
        self.issue_service = issue_service
        self.pr_service = pr_service

    async def get_context_summary(
        self,
        owner: str,
        repo: str
    ) -> str:
        """Get GitHub context summary for system prompt."""
        try:
            repo_info = await self.repo_service.get(owner, repo)
            return self._format_repo_summary(repo_info)
        except Exception:
            return f"GitHub: {owner}/{repo} (unable to fetch details)"

    def _format_repo_summary(self, repo: GitHubRepository) -> str:
        """Format repository summary."""
        lines = [
            f"GitHub Repository: {repo.full_name}",
            f"  Description: {repo.description or 'No description'}",
            f"  Default branch: {repo.default_branch}",
            f"  Visibility: {'Private' if repo.private else 'Public'}",
            f"  Language: {repo.language or 'Not specified'}",
            f"  Open issues: {repo.open_issues}",
        ]
        if repo.archived:
            lines.append("  Status: ARCHIVED")
        return "\n".join(lines)

    def format_issue(self, issue: GitHubIssue) -> str:
        """Format issue for LLM context."""
        lines = [
            f"Issue #{issue.number}: {issue.title}",
            f"State: {issue.state}",
            f"Author: @{issue.author.login}",
            f"Created: {issue.created_at}",
        ]

        if issue.assignees:
            assignees = ", ".join(f"@{a.login}" for a in issue.assignees)
            lines.append(f"Assignees: {assignees}")

        if issue.labels:
            labels = ", ".join(l.name for l in issue.labels)
            lines.append(f"Labels: {labels}")

        if issue.body:
            lines.append("")
            lines.append("Description:")
            lines.append(issue.body)

        return "\n".join(lines)

    def format_pr(self, pr: GitHubPullRequest) -> str:
        """Format PR for LLM context."""
        lines = [
            f"Pull Request #{pr.number}: {pr.title}",
            f"State: {pr.state}",
            f"Author: @{pr.author.login}",
            f"Branch: {pr.head_ref} -> {pr.base_ref}",
            f"Created: {pr.created_at}",
        ]

        if pr.draft:
            lines.append("Status: DRAFT")
        if pr.merged:
            lines.append(f"Merged: {pr.merged_at}")

        lines.append(
            f"Changes: +{pr.additions} -{pr.deletions} "
            f"in {pr.changed_files} files"
        )

        if pr.assignees:
            assignees = ", ".join(f"@{a.login}" for a in pr.assignees)
            lines.append(f"Assignees: {assignees}")

        if pr.requested_reviewers:
            reviewers = ", ".join(
                f"@{r.login}" for r in pr.requested_reviewers
            )
            lines.append(f"Reviewers: {reviewers}")

        if pr.labels:
            labels = ", ".join(l.name for l in pr.labels)
            lines.append(f"Labels: {labels}")

        if pr.body:
            lines.append("")
            lines.append("Description:")
            lines.append(pr.body)

        return "\n".join(lines)

    def format_issue_list(self, issues: list[GitHubIssue]) -> str:
        """Format issue list for display."""
        if not issues:
            return "No issues found."

        lines = []
        for issue in issues:
            labels = ""
            if issue.labels:
                labels = f" [{', '.join(l.name for l in issue.labels)}]"

            lines.append(
                f"#{issue.number} {issue.title}{labels} "
                f"(@{issue.author.login})"
            )
        return "\n".join(lines)

    def format_pr_list(self, prs: list[GitHubPullRequest]) -> str:
        """Format PR list for display."""
        if not prs:
            return "No pull requests found."

        lines = []
        for pr in prs:
            status = ""
            if pr.draft:
                status = " [DRAFT]"
            elif pr.merged:
                status = " [MERGED]"

            lines.append(
                f"#{pr.number} {pr.title}{status} "
                f"({pr.head_ref} -> {pr.base_ref}) "
                f"@{pr.author.login}"
            )
        return "\n".join(lines)
```

### 8. __init__.py - Package Exports

```python
"""GitHub integration for Code-Forge."""
from .auth import (
    GitHubAuth,
    GitHubAuthenticator,
    GitHubAuthError,
)
from .client import (
    GitHubClient,
    GitHubAPIError,
    GitHubRateLimitError,
    GitHubNotFoundError,
)
from .repository import (
    GitHubRepository,
    GitHubBranch,
    GitHubTag,
    RepositoryService,
)
from .issues import (
    GitHubUser,
    GitHubLabel,
    GitHubMilestone,
    GitHubIssue,
    GitHubComment,
    IssueService,
)
from .pull_requests import (
    GitHubPullRequest,
    GitHubReview,
    GitHubReviewComment,
    GitHubCheckRun,
    GitHubPRFile,
    PullRequestService,
)
from .actions import (
    Workflow,
    WorkflowRun,
    WorkflowJob,
    ActionsService,
)
from .context import GitHubContext

__all__ = [
    # Auth
    "GitHubAuth",
    "GitHubAuthenticator",
    "GitHubAuthError",
    # Client
    "GitHubClient",
    "GitHubAPIError",
    "GitHubRateLimitError",
    "GitHubNotFoundError",
    # Repository
    "GitHubRepository",
    "GitHubBranch",
    "GitHubTag",
    "RepositoryService",
    # Issues
    "GitHubUser",
    "GitHubLabel",
    "GitHubMilestone",
    "GitHubIssue",
    "GitHubComment",
    "IssueService",
    # Pull Requests
    "GitHubPullRequest",
    "GitHubReview",
    "GitHubReviewComment",
    "GitHubCheckRun",
    "GitHubPRFile",
    "PullRequestService",
    # Actions
    "Workflow",
    "WorkflowRun",
    "WorkflowJob",
    "ActionsService",
    # Context
    "GitHubContext",
]
```

---

## Integration Notes

### With Git Integration (Phase 9.1)

```python
# Detect GitHub remote from git config
from forge.git import GitRepository
from forge.github import RepositoryService

repo = GitRepository()
remotes = repo.get_remotes()

for remote in remotes:
    parsed = RepositoryService.parse_remote_url(remote.url)
    if parsed:
        owner, name = parsed
        # Use GitHub API with owner/name
```

### With Session System

```python
# Store GitHub context in session
session.metadata["github"] = {
    "owner": "user",
    "repo": "project",
    "authenticated": True,
}
```

---

## Testing Strategy

1. Mock aiohttp for API tests
2. Use pytest-asyncio for async tests
3. Test rate limiting handling
4. Test pagination
5. Test error handling
6. Integration tests with real API (optional, requires token)

---

## Notes

- All API calls are async
- Rate limiting is tracked and handled
- Tokens are never logged or included in errors
- Pagination is handled automatically
- Response parsing uses dataclasses for type safety
