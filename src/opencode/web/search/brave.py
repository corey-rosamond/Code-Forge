"""Brave Search provider."""

import logging
import time
from typing import Any

import aiohttp

from ..types import SearchResponse, SearchResult
from .base import SearchError, SearchProvider

logger = logging.getLogger(__name__)


class BraveSearchProvider(SearchProvider):
    """Brave Search API provider."""

    API_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, api_key: str):
        """Initialize with API key.

        Args:
            api_key: Brave Search API key
        """
        self.api_key = api_key

    @property
    def name(self) -> str:
        """Provider name."""
        return "brave"

    @property
    def requires_api_key(self) -> bool:
        """Whether this provider requires an API key."""
        return True

    async def search(
        self,
        query: str,
        num_results: int = 10,
        country: str = "us",
        search_lang: str = "en",
        **kwargs: Any,  # noqa: ARG002
    ) -> SearchResponse:
        """Search using Brave Search.

        Args:
            query: Search query
            num_results: Max results
            country: Country code
            search_lang: Language code

        Returns:
            SearchResponse
        """
        if not self.api_key:
            raise SearchError("Brave API key not configured")

        start_time = time.time()

        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key,
        }

        params: dict[str, str | int] = {
            "q": query,
            "count": num_results,
            "country": country,
            "search_lang": search_lang,
        }

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(self.API_URL, headers=headers, params=params) as resp,
            ):
                if resp.status != 200:
                    error = await resp.text()
                    raise SearchError(f"Brave API error: {error}")

                data = await resp.json()

                results: list[SearchResult] = []
                for item in data.get("web", {}).get("results", []):
                    results.append(
                        SearchResult(
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            snippet=item.get("description", ""),
                            date=item.get("page_age"),
                            metadata={
                                "language": item.get("language"),
                                "family_friendly": item.get("family_friendly"),
                            },
                        )
                    )

                search_time = time.time() - start_time

                return SearchResponse(
                    query=query,
                    results=results,
                    provider=self.name,
                    total_results=len(results),
                    search_time=search_time,
                )

        except aiohttp.ClientError as e:
            raise SearchError(f"Network error: {e}") from e
