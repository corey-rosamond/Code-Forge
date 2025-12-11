"""GitHub authentication handling."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime

import aiohttp
from pydantic import SecretStr


class GitHubAuthError(Exception):
    """GitHub authentication error."""

    pass


@dataclass
class GitHubAuth:
    """GitHub authentication information."""

    token: SecretStr
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

    def __init__(self, token: str | SecretStr | None = None):
        """
        Initialize with token or from environment.

        Args:
            token: GitHub personal access token.
                   If None, reads from GITHUB_TOKEN or GH_TOKEN env var.
        """
        raw_token = token or self._get_token_from_env()
        if isinstance(raw_token, SecretStr):
            self._token = raw_token
        elif raw_token:
            self._token = SecretStr(raw_token)
        else:
            self._token = None
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
            headers["Authorization"] = f"Bearer {self._token.get_secret_value()}"
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

        async with aiohttp.ClientSession() as session, session.get(
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
        reset: int,
    ) -> None:
        """Update rate limit info from response headers."""
        if self._auth_info:
            self._auth_info.rate_limit = limit
            self._auth_info.rate_remaining = remaining
            self._auth_info.rate_reset = reset

    def get_auth_info(self) -> GitHubAuth | None:
        """Get current auth info."""
        return self._auth_info
