"""GitHub API client."""
from __future__ import annotations

import asyncio
import contextlib
import random
from typing import Any, cast
from urllib.parse import urlencode

import aiohttp

from .auth import GitHubAuthenticator, GitHubAuthError


class GitHubAPIError(Exception):
    """GitHub API error."""

    def __init__(
        self,
        message: str,
        status: int | None = None,
        response: dict[str, Any] | None = None,
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
        max_retries: int = 3,
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

    def _build_url(self, path: str, **params: Any) -> str:
        """Build full URL with query parameters."""
        url = f"{self.BASE_URL}{path}"
        if params:
            # Filter out None values
            filtered = {k: v for k, v in params.items() if v is not None}
            if filtered:
                url = f"{url}?{urlencode(filtered)}"
        return url

    def _update_rate_limit(self, headers: dict[str, Any]) -> None:
        """Update rate limit from response headers."""
        with contextlib.suppress(ValueError, TypeError):
            self.auth.update_rate_limit(
                limit=int(headers.get("X-RateLimit-Limit", 5000)),
                remaining=int(headers.get("X-RateLimit-Remaining", 5000)),
                reset=int(headers.get("X-RateLimit-Reset", 0)),
            )

    async def _request(
        self,
        method: str,
        path: str,
        data: dict[str, Any] | None = None,
        accept: str | None = None,
        **params: Any,
    ) -> tuple[Any, dict[str, Any]]:
        """
        Make HTTP request.

        Returns:
            Tuple of (response_data, headers).
        """
        session = await self._get_session()
        url = self._build_url(path, **params)

        headers: dict[str, str] = {}
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
                    self._update_rate_limit(dict(response.headers))

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
                    # Exponential backoff with jitter
                    base_delay = 1.0
                    max_delay = 60.0
                    delay = min(base_delay * (2**attempt), max_delay)
                    jitter = delay * random.uniform(0, 0.5)
                    await asyncio.sleep(delay + jitter)
                    continue
                raise GitHubAPIError(f"Request failed: {e}") from e

        raise GitHubAPIError("Max retries exceeded")

    async def get(self, path: str, **params: Any) -> dict[str, Any]:
        """Make GET request."""
        result, _ = await self._request("GET", path, **params)
        return cast("dict[str, Any]", result)

    async def get_raw(
        self,
        path: str,
        accept: str = "application/vnd.github.raw",
        **params: Any,
    ) -> str:
        """Get raw content."""
        result, _ = await self._request(
            "GET", path, accept=accept, **params
        )
        return cast("str", result)

    async def post(
        self, path: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Make POST request."""
        result, _ = await self._request("POST", path, data=data)
        return cast("dict[str, Any]", result)

    async def patch(
        self, path: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Make PATCH request."""
        result, _ = await self._request("PATCH", path, data=data)
        return cast("dict[str, Any]", result)

    async def put(
        self, path: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Make PUT request."""
        result, _ = await self._request("PUT", path, data=data)
        return cast("dict[str, Any] | None", result)

    async def delete(self, path: str) -> None:
        """Make DELETE request."""
        await self._request("DELETE", path)

    async def get_paginated(
        self,
        path: str,
        per_page: int = 30,
        max_pages: int | None = None,
        **params: Any,
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
        all_items: list[dict[str, Any]] = []
        page = 1
        per_page = min(per_page, 100)

        while True:
            result, headers = await self._request(
                "GET",
                path,
                page=page,
                per_page=per_page,
                **params,
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
