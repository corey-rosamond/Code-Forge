"""Google Custom Search provider."""

import logging
import time
from typing import Any

import aiohttp

from ..types import SearchResponse, SearchResult
from .base import SearchError, SearchProvider

logger = logging.getLogger(__name__)


class GoogleSearchProvider(SearchProvider):
    """Google Custom Search API provider."""

    API_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, api_key: str, cx: str):
        """Initialize with API credentials.

        Args:
            api_key: Google API key
            cx: Custom Search Engine ID
        """
        self.api_key = api_key
        self.cx = cx

    @property
    def name(self) -> str:
        """Provider name."""
        return "google"

    @property
    def requires_api_key(self) -> bool:
        """Whether this provider requires an API key."""
        return True

    async def search(
        self,
        query: str,
        num_results: int = 10,
        date_restrict: str | None = None,
        site_search: str | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> SearchResponse:
        """Search using Google Custom Search.

        Args:
            query: Search query
            num_results: Max results (max 10 per request)
            date_restrict: Date restriction (e.g., 'd7' for past week)
            site_search: Limit to specific site

        Returns:
            SearchResponse
        """
        if not self.api_key:
            raise SearchError("Google API key not configured")

        start_time = time.time()
        results: list[SearchResult] = []

        # Google CSE max 10 results per request
        num_results = min(num_results, 10)

        params: dict[str, Any] = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": num_results,
        }

        if date_restrict:
            params["dateRestrict"] = date_restrict
        if site_search:
            params["siteSearch"] = site_search

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(self.API_URL, params=params) as resp,
            ):
                if resp.status != 200:
                    error = await resp.text()
                    raise SearchError(f"Google API error: {error}")

                data = await resp.json()

                for item in data.get("items", []):
                    results.append(
                        SearchResult(
                            title=item.get("title", ""),
                            url=item.get("link", ""),
                            snippet=item.get("snippet", ""),
                            metadata={
                                "displayLink": item.get("displayLink"),
                                "formattedUrl": item.get("formattedUrl"),
                            },
                        )
                    )

                search_time = time.time() - start_time
                total = data.get("searchInformation", {}).get("totalResults")

                return SearchResponse(
                    query=query,
                    results=results,
                    provider=self.name,
                    total_results=int(total) if total else len(results),
                    search_time=search_time,
                )

        except aiohttp.ClientError as e:
            raise SearchError(f"Network error: {e}") from e
