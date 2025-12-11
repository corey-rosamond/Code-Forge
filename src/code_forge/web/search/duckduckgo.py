"""DuckDuckGo search provider."""

import asyncio
import logging
import time
from typing import Any

from ..types import SearchResponse, SearchResult
from .base import SearchError, SearchProvider

logger = logging.getLogger(__name__)


class DuckDuckGoProvider(SearchProvider):
    """DuckDuckGo search provider (no API key needed)."""

    @property
    def name(self) -> str:
        """Provider name."""
        return "duckduckgo"

    async def search(
        self,
        query: str,
        num_results: int = 10,
        region: str = "wt-wt",
        safe_search: str = "moderate",
        **kwargs: Any,  # noqa: ARG002
    ) -> SearchResponse:
        """Search using DuckDuckGo.

        Args:
            query: Search query
            num_results: Max results
            region: Region code (default: worldwide)
            safe_search: off, moderate, strict

        Returns:
            SearchResponse
        """
        try:
            from duckduckgo_search import DDGS
        except ImportError as err:
            raise SearchError(
                "duckduckgo-search package not installed. "
                "Install with: pip install duckduckgo-search"
            ) from err

        def _do_search() -> list[dict[str, Any]]:
            """Synchronous search function to run in thread."""
            with DDGS() as ddgs:
                results = ddgs.text(
                    query,
                    region=region,
                    safesearch=safe_search,
                    max_results=num_results,
                )
                return list(results)

        try:
            start_time = time.time()

            # Run synchronous DDGS in thread pool
            raw_results = await asyncio.to_thread(_do_search)

            results_list: list[SearchResult] = []
            for r in raw_results:
                results_list.append(
                    SearchResult(
                        title=r.get("title", ""),
                        url=r.get("href", ""),
                        snippet=r.get("body", ""),
                        source=r.get("source"),
                    )
                )

            search_time = time.time() - start_time

            return SearchResponse(
                query=query,
                results=results_list,
                provider=self.name,
                total_results=len(results_list),
                search_time=search_time,
            )

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            raise SearchError(f"Search failed: {e}") from e
