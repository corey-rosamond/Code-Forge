"""Web tool implementations."""

import logging
from typing import Any

from .cache import WebCache
from .fetch.fetcher import FetchError, URLFetcher
from .fetch.parser import HTMLParser
from .search.base import SearchError, SearchProvider
from .types import FetchOptions, FetchResponse

logger = logging.getLogger(__name__)


class WebSearchTool:
    """Web search tool implementation."""

    name = "web_search"
    description = "Search the web for information"

    def __init__(
        self,
        providers: dict[str, SearchProvider],
        default_provider: str = "duckduckgo",
    ):
        """Initialize search tool.

        Args:
            providers: Available search providers
            default_provider: Default provider name
        """
        self.providers = providers
        self.default_provider = default_provider

    async def execute(
        self,
        query: str,
        num_results: int = 10,
        provider: str | None = None,
        allowed_domains: list[str] | None = None,
        blocked_domains: list[str] | None = None,
        **kwargs: Any,
    ) -> str:
        """Execute web search.

        Args:
            query: Search query
            num_results: Number of results
            provider: Provider to use
            allowed_domains: Only include these domains
            blocked_domains: Exclude these domains

        Returns:
            Formatted search results
        """
        provider_name = provider or self.default_provider
        search_provider = self.providers.get(provider_name)

        if not search_provider:
            available = ", ".join(self.providers.keys())
            return f"Unknown provider: {provider_name}. Available: {available}"

        try:
            response = await search_provider.search(query, num_results, **kwargs)

            # Apply domain filtering
            response = search_provider.filter_results(
                response, allowed_domains, blocked_domains
            )

            if not response.results:
                return f"No results found for: {query}"

            return response.to_markdown()

        except SearchError as e:
            return f"Search error: {e}"


class WebFetchTool:
    """URL fetch tool implementation."""

    name = "web_fetch"
    description = "Fetch and process content from a URL"

    def __init__(
        self,
        fetcher: URLFetcher,
        parser: HTMLParser,
        cache: WebCache | None = None,
    ):
        """Initialize fetch tool.

        Args:
            fetcher: URL fetcher
            parser: HTML parser
            cache: Response cache
        """
        self.fetcher = fetcher
        self.parser = parser
        self.cache = cache

    async def execute(
        self,
        url: str,
        prompt: str | None = None,
        format: str = "markdown",
        use_cache: bool = True,
        timeout: int | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> str:
        """Fetch URL content.

        Args:
            url: URL to fetch
            prompt: Optional prompt for processing (reserved for future use)
            format: Output format (markdown, text, raw)
            use_cache: Whether to use cache
            timeout: Override timeout

        Returns:
            Fetched and processed content
        """
        # Check cache
        cache_key: str | None = None
        if use_cache and self.cache:
            cache_key = self.cache.generate_key(url)
            cached = self.cache.get(cache_key)
            if cached:
                return self._format_response(cached, format, prompt)

        # Fetch URL
        try:
            options = None
            if timeout:
                options = FetchOptions(timeout=timeout)

            response = await self.fetcher.fetch(url, options)

            # Cache response
            if use_cache and self.cache and cache_key:
                self.cache.set(cache_key, response)

            return self._format_response(response, format, prompt)

        except FetchError as e:
            return f"Fetch error: {e}"

    def _format_response(
        self,
        response: FetchResponse,
        format: str,
        prompt: str | None,  # noqa: ARG002 - reserved for future use
    ) -> str:
        """Format response based on format option."""
        if not isinstance(response.content, str):
            return f"Binary content ({response.content_type})"

        if format == "raw":
            return response.content

        if response.is_html:
            if format == "text":
                content = self.parser.to_text(response.content)
            else:
                content = self.parser.to_markdown(response.content)
        else:
            content = response.content

        # Truncate if too long
        max_len = 50000
        if len(content) > max_len:
            content = content[:max_len] + "\n\n[Content truncated...]"

        # Add source info
        result = f"**Source:** {response.final_url}\n\n{content}"

        if response.from_cache:
            result = "[From cache]\n\n" + result

        return result
