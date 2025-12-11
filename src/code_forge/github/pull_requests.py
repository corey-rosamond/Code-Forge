"""GitHub pull request operations."""
from __future__ import annotations

import builtins
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .issues import GitHubLabel, GitHubUser

if TYPE_CHECKING:
    from .client import GitHubClient


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
    def from_api(cls, data: dict[str, Any]) -> GitHubPullRequest:
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
                GitHubLabel.from_api(label) for label in data.get("labels", [])
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
    def from_api(cls, data: dict[str, Any]) -> GitHubReview:
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
    def from_api(cls, data: dict[str, Any]) -> GitHubReviewComment:
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
    def from_api(cls, data: dict[str, Any]) -> GitHubCheckRun:
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
    def from_api(cls, data: dict[str, Any]) -> GitHubPRFile:
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
        direction: str = "desc",
    ) -> builtins.list[GitHubPullRequest]:
        """List pull requests."""
        params: dict[str, Any] = {
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
            **params,
        )
        return [GitHubPullRequest.from_api(pr) for pr in data]

    async def get(
        self,
        owner: str,
        repo: str,
        pr_number: int,
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
        maintainer_can_modify: bool = True,
    ) -> GitHubPullRequest:
        """Create pull request."""
        payload: dict[str, Any] = {
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
            payload,
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
        base: str | None = None,
    ) -> GitHubPullRequest:
        """Update pull request."""
        payload: dict[str, Any] = {}
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
            payload,
        )
        return GitHubPullRequest.from_api(data)

    async def get_diff(
        self,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> str:
        """Get PR diff."""
        return await self.client.get_raw(
            f"/repos/{owner}/{repo}/pulls/{pr_number}",
            accept="application/vnd.github.diff",
        )

    async def get_files(
        self,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> builtins.list[GitHubPRFile]:
        """Get PR files."""
        data = await self.client.get_paginated(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/files"
        )
        return [GitHubPRFile.from_api(f) for f in data]

    async def get_commits(
        self,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> builtins.list[dict[str, Any]]:
        """Get PR commits."""
        return await self.client.get_paginated(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/commits"
        )

    async def list_reviews(
        self,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> builtins.list[GitHubReview]:
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
        comments: builtins.list[dict[str, Any]] | None = None,
        commit_id: str | None = None,
    ) -> GitHubReview:
        """
        Create PR review.

        Args:
            event: APPROVE, REQUEST_CHANGES, or COMMENT
            comments: List of review comments with path, position, body
        """
        payload: dict[str, Any] = {"event": event}
        if body:
            payload["body"] = body
        if comments:
            payload["comments"] = comments
        if commit_id:
            payload["commit_id"] = commit_id

        data = await self.client.post(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
            payload,
        )
        return GitHubReview.from_api(data)

    async def list_review_comments(
        self,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> builtins.list[GitHubReviewComment]:
        """List review comments on PR."""
        data = await self.client.get_paginated(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        )
        return [GitHubReviewComment.from_api(c) for c in data]

    async def get_checks(
        self,
        owner: str,
        repo: str,
        ref: str,
    ) -> builtins.list[GitHubCheckRun]:
        """Get check runs for ref."""
        data = await self.client.get(
            f"/repos/{owner}/{repo}/commits/{ref}/check-runs"
        )
        return [GitHubCheckRun.from_api(c) for c in data.get("check_runs", [])]

    async def get_combined_status(
        self,
        owner: str,
        repo: str,
        ref: str,
    ) -> dict[str, Any]:
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
        sha: str | None = None,
    ) -> dict[str, Any]:
        """
        Merge pull request.

        Args:
            merge_method: merge, squash, or rebase
        """
        payload: dict[str, Any] = {"merge_method": merge_method}
        if commit_title:
            payload["commit_title"] = commit_title
        if commit_message:
            payload["commit_message"] = commit_message
        if sha:
            payload["sha"] = sha

        result = await self.client.put(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/merge",
            payload,
        )
        return result or {}

    async def request_reviewers(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        reviewers: builtins.list[str] | None = None,
        team_reviewers: builtins.list[str] | None = None,
    ) -> GitHubPullRequest:
        """Request reviewers for PR."""
        payload: dict[str, Any] = {}
        if reviewers:
            payload["reviewers"] = reviewers
        if team_reviewers:
            payload["team_reviewers"] = team_reviewers

        data = await self.client.post(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/requested_reviewers",
            payload,
        )
        return GitHubPullRequest.from_api(data)
