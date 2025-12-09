"""GitHub repository operations."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
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
    topics: list[str] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> GitHubRepository:
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
    def from_api(cls, data: dict[str, Any]) -> GitHubBranch:
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
    def from_api(cls, data: dict[str, Any]) -> GitHubTag:
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
        protected: bool | None = None,
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
        params: dict[str, Any] = {}
        if protected is not None:
            params["protected"] = str(protected).lower()

        data = await self.client.get_paginated(
            f"/repos/{owner}/{repo}/branches",
            **params,
        )
        return [GitHubBranch.from_api(b) for b in data]

    async def get_branch(
        self,
        owner: str,
        repo: str,
        branch: str,
    ) -> GitHubBranch:
        """Get single branch."""
        data = await self.client.get(
            f"/repos/{owner}/{repo}/branches/{branch}"
        )
        return GitHubBranch.from_api(data)

    async def list_tags(
        self,
        owner: str,
        repo: str,
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
        ref: str | None = None,
    ) -> str:
        """Get repository README content."""
        params: dict[str, Any] = {}
        if ref:
            params["ref"] = ref

        return await self.client.get_raw(
            f"/repos/{owner}/{repo}/readme",
            **params,
        )

    async def get_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Get repository content.

        Returns file content or directory listing.
        """
        params: dict[str, Any] = {}
        if ref:
            params["ref"] = ref

        return await self.client.get(
            f"/repos/{owner}/{repo}/contents/{path}",
            **params,
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
