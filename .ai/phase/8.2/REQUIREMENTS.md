# Phase 8.2: Web Tools - Requirements

**Phase:** 8.2
**Name:** Web Tools (WebSearch, WebFetch)
**Dependencies:** Phase 2.1 (Tool System), Phase 3.2 (LangChain Integration)

---

## Overview

Phase 8.2 implements web tools for Code-Forge, enabling the assistant to search the web and fetch content from URLs. These tools provide access to real-time information beyond the model's training cutoff and allow retrieval of documentation, APIs, and other web resources.

---

## Goals

1. Implement WebSearch tool for web queries
2. Implement WebFetch tool for URL content retrieval
3. Support multiple search provider backends
4. Handle HTML-to-text conversion
5. Implement caching for repeated requests
6. Provide content summarization for large pages

---

## Non-Goals (This Phase)

- Browser automation (Playwright, Selenium)
- JavaScript rendering for SPAs
- Image/video content extraction
- Web scraping frameworks
- Rate limit management across providers
- Proxy rotation

---

## Functional Requirements

### FR-1: WebSearch Tool

**FR-1.1:** Search execution
- Query search engines with user query
- Return structured search results
- Support result count limits

**FR-1.2:** Search results
- Title and URL
- Snippet/description
- Optional metadata (date, source)

**FR-1.3:** Search options
- Domain filtering (include/exclude)
- Date range filtering
- Result count (default 10)

**FR-1.4:** Provider abstraction
- Support multiple search providers
- Configurable default provider
- Fallback on provider failure

### FR-2: WebFetch Tool

**FR-2.1:** URL fetching
- Fetch content from URLs
- Follow redirects (configurable)
- Handle various content types

**FR-2.2:** Content processing
- HTML to Markdown/text conversion
- Remove scripts and styles
- Extract main content
- Handle encodings

**FR-2.3:** Content options
- Raw HTML mode
- Text-only mode
- Markdown conversion mode
- Content summarization

**FR-2.4:** Fetch constraints
- Timeout configuration
- Maximum content size
- User-agent setting
- Header customization

### FR-3: Search Providers

**FR-3.1:** Built-in providers
- DuckDuckGo (no API key needed)
- Google Custom Search (API key)
- Bing Search (API key)
- Brave Search (API key)

**FR-3.2:** Provider interface
- Common search interface
- Result normalization
- Error handling

**FR-3.3:** Provider configuration
- API keys in config
- Per-provider settings
- Rate limit awareness

### FR-4: Content Processing

**FR-4.1:** HTML processing
- Parse HTML documents
- Extract text content
- Handle malformed HTML
- Remove boilerplate

**FR-4.2:** Content extraction
- Identify main content
- Remove navigation/ads
- Extract article text
- Handle pagination

**FR-4.3:** Format conversion
- HTML to Markdown
- HTML to plain text
- Preserve structure

### FR-5: Caching

**FR-5.1:** Response caching
- Cache fetch responses
- Configurable TTL
- Cache key generation

**FR-5.2:** Cache management
- Maximum cache size
- LRU eviction
- Manual cache clear

**FR-5.3:** Cache bypass
- Force refresh option
- Cache-control headers
- Dynamic content detection

### FR-6: Error Handling

**FR-6.1:** Network errors
- Connection timeouts
- DNS failures
- SSL errors

**FR-6.2:** HTTP errors
- 4xx client errors
- 5xx server errors
- Redirect loops

**FR-6.3:** Content errors
- Invalid HTML
- Encoding issues
- Size limits exceeded

---

## Non-Functional Requirements

### NFR-1: Performance
- Search response < 3s
- Fetch response < 5s
- Cache hit < 10ms

### NFR-2: Reliability
- Graceful degradation
- Provider fallback
- Retry logic

### NFR-3: Privacy
- No tracking
- Minimal data collection
- Respect robots.txt (optional)

---

## Technical Specifications

### Package Structure

```
src/forge/web/
├── __init__.py           # Package exports
├── search/
│   ├── __init__.py
│   ├── base.py           # Search provider interface
│   ├── duckduckgo.py     # DuckDuckGo provider
│   ├── google.py         # Google Custom Search
│   ├── bing.py           # Bing Search
│   └── brave.py          # Brave Search
├── fetch/
│   ├── __init__.py
│   ├── fetcher.py        # URL fetcher
│   ├── parser.py         # HTML parser
│   └── converter.py      # Format converter
├── cache.py              # Response caching
├── config.py             # Web tools configuration
└── tools.py              # Tool implementations
```

### Configuration Format

```yaml
# ~/.src/forge/config.yaml
web:
  search:
    default_provider: duckduckgo
    default_results: 10
    timeout: 10

    providers:
      google:
        api_key: "${GOOGLE_API_KEY}"
        cx: "${GOOGLE_CX}"

      bing:
        api_key: "${BING_API_KEY}"

      brave:
        api_key: "${BRAVE_API_KEY}"

  fetch:
    timeout: 30
    max_size: 5242880  # 5MB
    user_agent: "src/forge/1.0"
    follow_redirects: true
    max_redirects: 5

  cache:
    enabled: true
    ttl: 900  # 15 minutes
    max_size: 104857600  # 100MB
```

### Class Signatures

```python
# search/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class SearchResult:
    """Single search result."""
    title: str
    url: str
    snippet: str
    date: str | None = None
    source: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class SearchResponse:
    """Search response with multiple results."""
    query: str
    results: list[SearchResult]
    provider: str
    total_results: int | None = None
    search_time: float | None = None


class SearchProvider(ABC):
    """Abstract search provider interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        ...

    @abstractmethod
    async def search(
        self,
        query: str,
        num_results: int = 10,
        **kwargs
    ) -> SearchResponse:
        """Execute search query."""
        ...


# search/duckduckgo.py
class DuckDuckGoProvider(SearchProvider):
    """DuckDuckGo search provider (no API key needed)."""

    @property
    def name(self) -> str:
        return "duckduckgo"

    async def search(
        self,
        query: str,
        num_results: int = 10,
        region: str = "wt-wt",
        **kwargs
    ) -> SearchResponse:
        ...


# search/google.py
class GoogleSearchProvider(SearchProvider):
    """Google Custom Search provider."""

    def __init__(self, api_key: str, cx: str):
        self.api_key = api_key
        self.cx = cx

    @property
    def name(self) -> str:
        return "google"

    async def search(
        self,
        query: str,
        num_results: int = 10,
        date_restrict: str | None = None,
        site_search: str | None = None,
        **kwargs
    ) -> SearchResponse:
        ...


# fetch/fetcher.py
@dataclass
class FetchResponse:
    """Response from URL fetch."""
    url: str
    final_url: str  # After redirects
    status_code: int
    content_type: str
    content: str | bytes
    headers: dict[str, str]
    encoding: str
    fetch_time: float
    from_cache: bool = False


@dataclass
class FetchOptions:
    """Options for URL fetching."""
    timeout: int = 30
    max_size: int = 5 * 1024 * 1024  # 5MB
    user_agent: str = "src/forge/1.0"
    follow_redirects: bool = True
    max_redirects: int = 5
    headers: dict[str, str] | None = None
    verify_ssl: bool = True


class URLFetcher:
    """Fetches content from URLs."""

    def __init__(self, options: FetchOptions | None = None):
        self.options = options or FetchOptions()
        self._session: aiohttp.ClientSession | None = None

    async def fetch(
        self,
        url: str,
        options: FetchOptions | None = None
    ) -> FetchResponse:
        """Fetch URL content."""
        ...

    async def fetch_multiple(
        self,
        urls: list[str],
        options: FetchOptions | None = None
    ) -> list[FetchResponse]:
        """Fetch multiple URLs concurrently."""
        ...


# fetch/parser.py
@dataclass
class ParsedContent:
    """Parsed HTML content."""
    title: str | None
    text: str
    markdown: str
    links: list[dict[str, str]]
    images: list[dict[str, str]]
    metadata: dict[str, str]


class HTMLParser:
    """Parses HTML content."""

    def parse(self, html: str, base_url: str | None = None) -> ParsedContent:
        """Parse HTML to structured content."""
        ...

    def extract_main_content(self, html: str) -> str:
        """Extract main content, removing boilerplate."""
        ...

    def to_markdown(self, html: str) -> str:
        """Convert HTML to Markdown."""
        ...

    def to_text(self, html: str) -> str:
        """Convert HTML to plain text."""
        ...


# cache.py
class WebCache:
    """Cache for web responses."""

    def __init__(
        self,
        max_size: int = 100 * 1024 * 1024,  # 100MB
        ttl: int = 900,  # 15 minutes
        cache_dir: Path | None = None
    ):
        ...

    def get(self, key: str) -> FetchResponse | None:
        """Get cached response."""
        ...

    def set(self, key: str, response: FetchResponse) -> None:
        """Cache a response."""
        ...

    def delete(self, key: str) -> bool:
        """Delete cached entry."""
        ...

    def clear(self) -> int:
        """Clear all cache entries."""
        ...

    def generate_key(self, url: str, options: FetchOptions) -> str:
        """Generate cache key for URL and options."""
        ...


# tools.py
class WebSearchTool(Tool):
    """Web search tool."""

    name = "web_search"
    description = "Search the web for information"

    def __init__(self, providers: dict[str, SearchProvider], default: str):
        self.providers = providers
        self.default = default

    async def execute(
        self,
        query: str,
        num_results: int = 10,
        provider: str | None = None,
        allowed_domains: list[str] | None = None,
        blocked_domains: list[str] | None = None,
        **kwargs
    ) -> str:
        """Execute web search."""
        ...


class WebFetchTool(Tool):
    """URL fetch tool."""

    name = "web_fetch"
    description = "Fetch and process content from a URL"

    def __init__(self, fetcher: URLFetcher, parser: HTMLParser, cache: WebCache):
        self.fetcher = fetcher
        self.parser = parser
        self.cache = cache

    async def execute(
        self,
        url: str,
        prompt: str | None = None,
        format: str = "markdown",  # markdown, text, raw
        use_cache: bool = True,
        timeout: int | None = None,
        **kwargs
    ) -> str:
        """Fetch URL content."""
        ...
```

---

## Tool Schemas

### WebSearch Schema

```json
{
  "name": "web_search",
  "description": "Search the web for information. Returns titles, URLs, and snippets.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The search query"
      },
      "num_results": {
        "type": "integer",
        "description": "Number of results to return (default: 10)",
        "default": 10
      },
      "allowed_domains": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Only include results from these domains"
      },
      "blocked_domains": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Exclude results from these domains"
      }
    },
    "required": ["query"]
  }
}
```

### WebFetch Schema

```json
{
  "name": "web_fetch",
  "description": "Fetch content from a URL and optionally process it with a prompt.",
  "parameters": {
    "type": "object",
    "properties": {
      "url": {
        "type": "string",
        "format": "uri",
        "description": "The URL to fetch"
      },
      "prompt": {
        "type": "string",
        "description": "Optional prompt to process the content"
      },
      "format": {
        "type": "string",
        "enum": ["markdown", "text", "raw"],
        "description": "Output format (default: markdown)"
      }
    },
    "required": ["url"]
  }
}
```

---

## Integration Points

### With Tool System (Phase 2.1)
- WebSearchTool and WebFetchTool implement Tool interface
- Registered in ToolRegistry
- Available to LLM agents

### With LangChain (Phase 3.2)
- Tools bound to LLM
- Tool schemas provided
- Results formatted for context

### With Configuration (Phase 1.2)
- Web config loaded from settings
- API keys from environment
- Provider configuration

### With Permission System (Phase 4.1)
- Web tools may require permission
- Domain allowlists/blocklists
- Rate limit awareness

---

## Testing Requirements

1. Unit tests for SearchProvider implementations
2. Unit tests for URLFetcher
3. Unit tests for HTMLParser
4. Unit tests for WebCache
5. Unit tests for tools
6. Integration tests with mock HTTP
7. Test coverage ≥ 90%

---

## Acceptance Criteria

1. WebSearch returns relevant results
2. Multiple search providers work
3. WebFetch retrieves page content
4. HTML correctly converted to Markdown
5. Caching reduces duplicate fetches
6. Large pages handled gracefully
7. Timeouts work correctly
8. Error handling is graceful
9. Domain filtering works
10. Configuration loads properly
