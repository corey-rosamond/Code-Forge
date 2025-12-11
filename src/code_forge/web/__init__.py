"""Web tools for Code-Forge."""

from .cache import WebCache
from .config import (
    CacheConfig,
    FetchConfig,
    SearchConfig,
    SearchProviderConfig,
    WebConfig,
)
from .fetch.fetcher import FetchError, URLFetcher
from .fetch.parser import HTMLParser
from .search.base import SearchError, SearchProvider
from .search.brave import BraveSearchProvider
from .search.duckduckgo import DuckDuckGoProvider
from .search.google import GoogleSearchProvider
from .tools import WebFetchTool, WebSearchTool
from .types import (
    FetchOptions,
    FetchResponse,
    ParsedContent,
    SearchResponse,
    SearchResult,
)

__all__ = [
    "BraveSearchProvider",
    "CacheConfig",
    "DuckDuckGoProvider",
    "FetchConfig",
    "FetchError",
    "FetchOptions",
    "FetchResponse",
    "GoogleSearchProvider",
    "HTMLParser",
    "ParsedContent",
    "SearchConfig",
    "SearchError",
    "SearchProvider",
    "SearchProviderConfig",
    "SearchResponse",
    "SearchResult",
    "URLFetcher",
    "WebCache",
    "WebConfig",
    "WebFetchTool",
    "WebSearchTool",
]
