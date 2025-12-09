"""GitHub issue operations."""
from __future__ import annotations

import builtins
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
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
    def from_api(cls, data: dict[str, Any]) -> GitHubUser:
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
    def from_api(cls, data: dict[str, Any]) -> GitHubLabel:
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
    def from_api(cls, data: dict[str, Any]) -> GitHubMilestone:
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
    def from_api(cls, data: dict[str, Any]) -> GitHubIssue:
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
                GitHubLabel.from_api(label) for label in data.get("labels", [])
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
    def from_api(cls, data: dict[str, Any]) -> GitHubComment:
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
        labels: builtins.list[str] | None = None,
        assignee: str | None = None,
        creator: str | None = None,
        mentioned: str | None = None,
        milestone: str | int | None = None,
        sort: str = "created",
        direction: str = "desc",
        since: str | None = None,
    ) -> builtins.list[GitHubIssue]:
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
        params: dict[str, Any] = {
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
            **params,
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
        issue_number: int,
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
        labels: builtins.list[str] | None = None,
        assignees: builtins.list[str] | None = None,
        milestone: int | None = None,
    ) -> GitHubIssue:
        """Create issue."""
        payload: dict[str, Any] = {"title": title}
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
            payload,
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
        labels: builtins.list[str] | None = None,
        assignees: builtins.list[str] | None = None,
        milestone: int | None = None,
    ) -> GitHubIssue:
        """Update issue."""
        payload: dict[str, Any] = {}
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
            payload,
        )
        return GitHubIssue.from_api(data)

    async def close(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        reason: str = "completed",
    ) -> GitHubIssue:
        """Close issue."""
        return await self.update(
            owner, repo, issue_number,
            state="closed",
            state_reason=reason,
        )

    async def reopen(
        self,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> GitHubIssue:
        """Reopen issue."""
        return await self.update(
            owner, repo, issue_number,
            state="open",
        )

    async def list_comments(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        since: str | None = None,
    ) -> builtins.list[GitHubComment]:
        """List issue comments."""
        params: dict[str, Any] = {}
        if since:
            params["since"] = since

        data = await self.client.get_paginated(
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            **params,
        )
        return [GitHubComment.from_api(c) for c in data]

    async def add_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        body: str,
    ) -> GitHubComment:
        """Add comment to issue."""
        data = await self.client.post(
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            {"body": body},
        )
        return GitHubComment.from_api(data)

    async def update_comment(
        self,
        owner: str,
        repo: str,
        comment_id: int,
        body: str,
    ) -> GitHubComment:
        """Update issue comment."""
        data = await self.client.patch(
            f"/repos/{owner}/{repo}/issues/comments/{comment_id}",
            {"body": body},
        )
        return GitHubComment.from_api(data)

    async def delete_comment(
        self,
        owner: str,
        repo: str,
        comment_id: int,
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
        labels: builtins.list[str],
    ) -> builtins.list[GitHubLabel]:
        """Add labels to issue."""
        # The GitHub API returns a list of labels for this endpoint
        data: builtins.list[dict[str, Any]] = await self.client.post(  # type: ignore[assignment]
            f"/repos/{owner}/{repo}/issues/{issue_number}/labels",
            {"labels": labels},
        )
        return [GitHubLabel.from_api(label) for label in data]

    async def remove_label(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        label: str,
    ) -> None:
        """Remove label from issue."""
        await self.client.delete(
            f"/repos/{owner}/{repo}/issues/{issue_number}/labels/{label}"
        )
