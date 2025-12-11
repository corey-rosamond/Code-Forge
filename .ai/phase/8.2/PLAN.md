# Phase 8.2: Web Tools - Implementation Plan

**Phase:** 8.2
**Name:** Web Tools (WebSearch, WebFetch)
**Dependencies:** Phase 2.1 (Tool System), Phase 3.2 (LangChain Integration)

---

## Implementation Order

1. Data types and configuration
2. Search provider interface and implementations
3. URL fetcher
4. HTML parser and converter
5. Response caching
6. Tool implementations
7. Integration and registration

---

## Step 1: Data Types and Configuration (types.py, config.py)

### Data Types

```python
# src/forge/web/types.py
"""Data types for web tools."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchResult:
    """Single search result."""
    title: str
    url: str
    snippet: str
    date: str | None = None
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "date": self.date,
            "source": self.source,
        }

    def to_markdown(self) -> str:
        """Format as Markdown."""
        md = f"**[{self.title}]({self.url})**\n"
        md += f"{self.snippet}\n"
        if self.date:
            md += f"*{self.date}*\n"
        return md


@dataclass
class SearchResponse:
    """Search response with multiple results."""
    query: str
    results: list[SearchResult]
    provider: str
    total_results: int | None = None
    search_time: float | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "provider": self.provider,
            "total_results": self.total_results,
            "search_time": self.search_time,
        }

    def to_markdown(self) -> str:
        """Format results as Markdown."""
        lines = [f"## Search Results for: {self.query}\n"]
        for i, result in enumerate(self.results, 1):
            lines.append(f"### {i}. [{result.title}]({result.url})")
            lines.append(f"{result.snippet}\n")
        return "\n".join(lines)


@dataclass
class FetchResponse:
    """Response from URL fetch."""
    url: str
    final_url: str
    status_code: int
    content_type: str
    content: str | bytes
    headers: dict[str, str]
    encoding: str
    fetch_time: float
    from_cache: bool = False

    @property
    def is_html(self) -> bool:
        """Check if content is HTML."""
        return "text/html" in self.content_type.lower()

    @property
    def is_text(self) -> bool:
        """Check if content is text."""
        ct = self.content_type.lower()
        return "text/" in ct or "json" in ct or "xml" in ct


@dataclass
class FetchOptions:
    """Options for URL fetching."""
    timeout: int = 30
    max_size: int = 5 * 1024 * 1024  # 5MB
    user_agent: str = "src/forge/1.0 (AI Assistant)"
    follow_redirects: bool = True
    max_redirects: int = 5
    headers: dict[str, str] = field(default_factory=dict)
    verify_ssl: bool = True


@dataclass
class ParsedContent:
    """Parsed HTML content."""
    title: str | None
    text: str
    markdown: str
    links: list[dict[str, str]] = field(default_factory=list)
    images: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
```

### Configuration

```python
# src/forge/web/config.py
"""Web tools configuration."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import os


@dataclass
class SearchProviderConfig:
    """Configuration for a search provider."""
    name: str
    api_key: str | None = None
    endpoint: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchConfig:
    """Search configuration."""
    default_provider: str = "duckduckgo"
    default_results: int = 10
    timeout: int = 10
    providers: dict[str, SearchProviderConfig] = field(default_factory=dict)


@dataclass
class FetchConfig:
    """Fetch configuration."""
    timeout: int = 30
    max_size: int = 5 * 1024 * 1024
    user_agent: str = "src/forge/1.0 (AI Assistant)"
    follow_redirects: bool = True
    max_redirects: int = 5


@dataclass
class CacheConfig:
    """Cache configuration."""
    enabled: bool = True
    ttl: int = 900  # 15 minutes
    max_size: int = 100 * 1024 * 1024  # 100MB
    directory: str | None = None


@dataclass
class WebConfig:
    """Complete web tools configuration."""
    search: SearchConfig = field(default_factory=SearchConfig)
    fetch: FetchConfig = field(default_factory=FetchConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)

    @classmethod
    def from_dict(cls, data: dict) -> "WebConfig":
        """Create from dictionary."""
        search_data = data.get("search", {})
        fetch_data = data.get("fetch", {})
        cache_data = data.get("cache", {})

        # Parse provider configs
        providers = {}
        for name, pdata in search_data.get("providers", {}).items():
            providers[name] = SearchProviderConfig(
                name=name,
                api_key=os.path.expandvars(pdata.get("api_key", "")),
                endpoint=pdata.get("endpoint"),
                extra={k: v for k, v in pdata.items()
                       if k not in ("api_key", "endpoint")}
            )

        search_config = SearchConfig(
            default_provider=search_data.get("default_provider", "duckduckgo"),
            default_results=search_data.get("default_results", 10),
            timeout=search_data.get("timeout", 10),
            providers=providers
        )

        fetch_config = FetchConfig(
            timeout=fetch_data.get("timeout", 30),
            max_size=fetch_data.get("max_size", 5 * 1024 * 1024),
            user_agent=fetch_data.get("user_agent", "src/forge/1.0"),
            follow_redirects=fetch_data.get("follow_redirects", True),
            max_redirects=fetch_data.get("max_redirects", 5)
        )

        cache_config = CacheConfig(
            enabled=cache_data.get("enabled", True),
            ttl=cache_data.get("ttl", 900),
            max_size=cache_data.get("max_size", 100 * 1024 * 1024),
            directory=cache_data.get("directory")
        )

        return cls(
            search=search_config,
            fetch=fetch_config,
            cache=cache_config
        )
```

---

## Step 2: Search Provider Interface (search/base.py)

```python
# src/forge/web/search/base.py
"""Search provider interface."""

from abc import ABC, abstractmethod
import logging

from ..types import SearchResponse

logger = logging.getLogger(__name__)


class SearchError(Exception):
    """Search provider error."""
    pass


class SearchProvider(ABC):
    """Abstract search provider interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        ...

    @property
    def requires_api_key(self) -> bool:
        """Whether this provider requires an API key."""
        return False

    @abstractmethod
    async def search(
        self,
        query: str,
        num_results: int = 10,
        **kwargs
    ) -> SearchResponse:
        """Execute search query.

        Args:
            query: Search query string
            num_results: Maximum results to return
            **kwargs: Provider-specific options

        Returns:
            SearchResponse with results
        """
        ...

    def filter_results(
        self,
        response: SearchResponse,
        allowed_domains: list[str] | None = None,
        blocked_domains: list[str] | None = None
    ) -> SearchResponse:
        """Filter results by domain.

        Args:
            response: Search response
            allowed_domains: Only include these domains
            blocked_domains: Exclude these domains

        Returns:
            Filtered SearchResponse
        """
        if not allowed_domains and not blocked_domains:
            return response

        filtered = []
        for result in response.results:
            from urllib.parse import urlparse
            domain = urlparse(result.url).netloc.lower()

            # Check blocked domains
            if blocked_domains:
                if any(d.lower() in domain for d in blocked_domains):
                    continue

            # Check allowed domains
            if allowed_domains:
                if not any(d.lower() in domain for d in allowed_domains):
                    continue

            filtered.append(result)

        return SearchResponse(
            query=response.query,
            results=filtered,
            provider=response.provider,
            total_results=len(filtered),
            search_time=response.search_time
        )
```

---

## Step 3: Search Provider Implementations

### DuckDuckGo Provider

```python
# src/forge/web/search/duckduckgo.py
"""DuckDuckGo search provider."""

import asyncio
import logging
import time
from typing import Any

from .base import SearchError, SearchProvider
from ..types import SearchResponse, SearchResult

logger = logging.getLogger(__name__)


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
        safe_search: str = "moderate",
        **kwargs
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
            # Use duckduckgo-search library
            from duckduckgo_search import AsyncDDGS

            start_time = time.time()

            async with AsyncDDGS() as ddgs:
                results_list = []
                async for r in ddgs.text(
                    query,
                    region=region,
                    safesearch=safe_search,
                    max_results=num_results
                ):
                    results_list.append(SearchResult(
                        title=r.get("title", ""),
                        url=r.get("href", ""),
                        snippet=r.get("body", ""),
                        source=r.get("source")
                    ))

            search_time = time.time() - start_time

            return SearchResponse(
                query=query,
                results=results_list,
                provider=self.name,
                total_results=len(results_list),
                search_time=search_time
            )

        except ImportError:
            raise SearchError(
                "duckduckgo-search package not installed. "
                "Install with: pip install duckduckgo-search"
            )
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            raise SearchError(f"Search failed: {e}")
```

### Google Custom Search Provider

```python
# src/forge/web/search/google.py
"""Google Custom Search provider."""

import logging
import time

import aiohttp

from .base import SearchError, SearchProvider
from ..types import SearchResponse, SearchResult

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
        return "google"

    @property
    def requires_api_key(self) -> bool:
        return True

    async def search(
        self,
        query: str,
        num_results: int = 10,
        date_restrict: str | None = None,
        site_search: str | None = None,
        **kwargs
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
        start_time = time.time()
        results = []

        # Google CSE max 10 results per request
        num_results = min(num_results, 10)

        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": num_results
        }

        if date_restrict:
            params["dateRestrict"] = date_restrict
        if site_search:
            params["siteSearch"] = site_search

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.API_URL, params=params) as resp:
                    if resp.status != 200:
                        error = await resp.text()
                        raise SearchError(f"Google API error: {error}")

                    data = await resp.json()

            for item in data.get("items", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    metadata={
                        "displayLink": item.get("displayLink"),
                        "formattedUrl": item.get("formattedUrl")
                    }
                ))

            search_time = time.time() - start_time
            total = data.get("searchInformation", {}).get("totalResults")

            return SearchResponse(
                query=query,
                results=results,
                provider=self.name,
                total_results=int(total) if total else len(results),
                search_time=search_time
            )

        except aiohttp.ClientError as e:
            raise SearchError(f"Network error: {e}")
```

### Brave Search Provider

```python
# src/forge/web/search/brave.py
"""Brave Search provider."""

import logging
import time

import aiohttp

from .base import SearchError, SearchProvider
from ..types import SearchResponse, SearchResult

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
        return "brave"

    @property
    def requires_api_key(self) -> bool:
        return True

    async def search(
        self,
        query: str,
        num_results: int = 10,
        country: str = "us",
        search_lang: str = "en",
        **kwargs
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
        start_time = time.time()

        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key
        }

        params = {
            "q": query,
            "count": num_results,
            "country": country,
            "search_lang": search_lang
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.API_URL,
                    headers=headers,
                    params=params
                ) as resp:
                    if resp.status != 200:
                        error = await resp.text()
                        raise SearchError(f"Brave API error: {error}")

                    data = await resp.json()

            results = []
            for item in data.get("web", {}).get("results", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    date=item.get("page_age"),
                    metadata={
                        "language": item.get("language"),
                        "family_friendly": item.get("family_friendly")
                    }
                ))

            search_time = time.time() - start_time

            return SearchResponse(
                query=query,
                results=results,
                provider=self.name,
                total_results=len(results),
                search_time=search_time
            )

        except aiohttp.ClientError as e:
            raise SearchError(f"Network error: {e}")
```

---

## Step 4: URL Fetcher (fetch/fetcher.py)

```python
# src/forge/web/fetch/fetcher.py
"""URL fetcher implementation."""

import asyncio
import logging
import time
from urllib.parse import urljoin

import aiohttp

from ..types import FetchOptions, FetchResponse

logger = logging.getLogger(__name__)


class FetchError(Exception):
    """URL fetch error."""
    pass


class URLFetcher:
    """Fetches content from URLs."""

    def __init__(self, options: FetchOptions | None = None):
        """Initialize fetcher.

        Args:
            options: Default fetch options
        """
        self.default_options = options or FetchOptions()

    async def fetch(
        self,
        url: str,
        options: FetchOptions | None = None
    ) -> FetchResponse:
        """Fetch URL content.

        Args:
            url: URL to fetch
            options: Override options for this request

        Returns:
            FetchResponse with content
        """
        opts = options or self.default_options
        start_time = time.time()

        # Upgrade HTTP to HTTPS
        if url.startswith("http://"):
            url = "https://" + url[7:]

        headers = {
            "User-Agent": opts.user_agent,
            **opts.headers
        }

        timeout = aiohttp.ClientTimeout(total=opts.timeout)

        try:
            async with aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            ) as session:
                async with session.get(
                    url,
                    allow_redirects=opts.follow_redirects,
                    max_redirects=opts.max_redirects,
                    ssl=opts.verify_ssl
                ) as resp:
                    # Check content size
                    content_length = resp.headers.get("Content-Length")
                    if content_length and int(content_length) > opts.max_size:
                        raise FetchError(
                            f"Content too large: {content_length} bytes"
                        )

                    # Read content with size limit
                    content = await self._read_content(resp, opts.max_size)

                    # Determine encoding
                    encoding = resp.charset or "utf-8"

                    # Decode if text
                    content_type = resp.content_type or ""
                    if "text" in content_type or "json" in content_type:
                        try:
                            content = content.decode(encoding)
                        except UnicodeDecodeError:
                            content = content.decode("utf-8", errors="replace")

                    fetch_time = time.time() - start_time

                    return FetchResponse(
                        url=url,
                        final_url=str(resp.url),
                        status_code=resp.status,
                        content_type=content_type,
                        content=content,
                        headers=dict(resp.headers),
                        encoding=encoding,
                        fetch_time=fetch_time
                    )

        except aiohttp.ClientError as e:
            raise FetchError(f"Network error: {e}")
        except asyncio.TimeoutError:
            raise FetchError(f"Timeout fetching {url}")

    async def _read_content(
        self,
        response: aiohttp.ClientResponse,
        max_size: int
    ) -> bytes:
        """Read response content with size limit."""
        chunks = []
        total_size = 0

        async for chunk in response.content.iter_chunked(8192):
            total_size += len(chunk)
            if total_size > max_size:
                raise FetchError(
                    f"Content exceeds max size: {max_size} bytes"
                )
            chunks.append(chunk)

        return b"".join(chunks)

    async def fetch_multiple(
        self,
        urls: list[str],
        options: FetchOptions | None = None,
        concurrency: int = 5
    ) -> list[FetchResponse | FetchError]:
        """Fetch multiple URLs concurrently.

        Args:
            urls: URLs to fetch
            options: Fetch options
            concurrency: Max concurrent requests

        Returns:
            List of responses or errors
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def fetch_one(url: str):
            async with semaphore:
                try:
                    return await self.fetch(url, options)
                except FetchError as e:
                    return e

        tasks = [fetch_one(url) for url in urls]
        return await asyncio.gather(*tasks)
```

---

## Step 5: HTML Parser (fetch/parser.py)

```python
# src/forge/web/fetch/parser.py
"""HTML parser and converter."""

import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import html2text

from ..types import ParsedContent

logger = logging.getLogger(__name__)


class HTMLParser:
    """Parses and converts HTML content."""

    def __init__(self):
        """Initialize parser."""
        self._h2t = html2text.HTML2Text()
        self._h2t.ignore_links = False
        self._h2t.ignore_images = False
        self._h2t.body_width = 0  # Don't wrap lines

    def parse(
        self,
        html: str,
        base_url: str | None = None
    ) -> ParsedContent:
        """Parse HTML to structured content.

        Args:
            html: HTML content
            base_url: Base URL for relative links

        Returns:
            ParsedContent with extracted data
        """
        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title = None
        if soup.title:
            title = soup.title.string

        # Extract metadata
        metadata = {}
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")
            if name and content:
                metadata[name] = content

        # Extract links
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if base_url:
                href = urljoin(base_url, href)
            links.append({
                "text": a.get_text(strip=True),
                "url": href
            })

        # Extract images
        images = []
        for img in soup.find_all("img", src=True):
            src = img["src"]
            if base_url:
                src = urljoin(base_url, src)
            images.append({
                "alt": img.get("alt", ""),
                "src": src
            })

        # Convert to text and markdown
        text = self.to_text(html)
        markdown = self.to_markdown(html)

        return ParsedContent(
            title=title,
            text=text,
            markdown=markdown,
            links=links,
            images=images,
            metadata=metadata
        )

    def to_text(self, html: str) -> str:
        """Convert HTML to plain text.

        Args:
            html: HTML content

        Returns:
            Plain text content
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style
        for element in soup(["script", "style", "nav", "footer", "aside"]):
            element.decompose()

        text = soup.get_text(separator="\n")

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines()]
        text = "\n".join(line for line in lines if line)

        # Collapse multiple newlines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def to_markdown(self, html: str) -> str:
        """Convert HTML to Markdown.

        Args:
            html: HTML content

        Returns:
            Markdown content
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "footer", "aside"]):
            element.decompose()

        # Convert using html2text
        markdown = self._h2t.handle(str(soup))

        # Clean up
        markdown = re.sub(r"\n{3,}", "\n\n", markdown)

        return markdown.strip()

    def extract_main_content(self, html: str) -> str:
        """Extract main content, removing boilerplate.

        Args:
            html: HTML content

        Returns:
            Main content HTML
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove unwanted elements
        for element in soup([
            "script", "style", "nav", "header", "footer",
            "aside", "form", "iframe", "noscript"
        ]):
            element.decompose()

        # Try to find main content area
        main = (
            soup.find("main") or
            soup.find("article") or
            soup.find("div", {"class": re.compile(r"content|main|article")}) or
            soup.find("div", {"id": re.compile(r"content|main|article")}) or
            soup.body or
            soup
        )

        return str(main)
```

---

## Step 6: Cache (cache.py)

```python
# src/forge/web/cache.py
"""Web response caching."""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

from .types import FetchOptions, FetchResponse

logger = logging.getLogger(__name__)


class WebCache:
    """Cache for web responses.

    Thread-safe: uses RLock for all cache operations.
    """

    def __init__(
        self,
        max_size: int = 100 * 1024 * 1024,
        ttl: int = 900,
        cache_dir: Path | None = None
    ):
        """Initialize cache.

        Args:
            max_size: Maximum cache size in bytes
            ttl: Time-to-live in seconds
            cache_dir: Directory for cache files (memory if None)
        """
        import threading

        self.max_size = max_size
        self.ttl = ttl
        self.cache_dir = cache_dir
        self._memory_cache: dict[str, tuple[float, int, Any]] = {}  # key -> (timestamp, size, data)
        self._current_size = 0
        self._lock = threading.RLock()  # Thread-safe cache operations

        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    def generate_key(
        self,
        url: str,
        options: FetchOptions | None = None
    ) -> str:
        """Generate cache key for URL.

        The cache key is based on the URL only. User-agent and other options
        are NOT included because:
        1. Most websites return the same content regardless of user-agent
        2. Including user-agent would fragment the cache unnecessarily
        3. The same URL should return cached content even if options change

        If you need to cache different responses based on headers (e.g., Accept),
        add a separate `vary_headers` parameter to explicitly opt-in.

        Args:
            url: URL to cache
            options: Fetch options (not used in key generation)

        Returns:
            Cache key string (32-char hex digest)
        """
        # Only URL affects cache key - options like user-agent don't change content
        return hashlib.sha256(url.encode()).hexdigest()[:32]

    def get(self, key: str) -> FetchResponse | None:
        """Get cached response.

        Thread-safe: uses lock.

        Args:
            key: Cache key

        Returns:
            Cached response or None
        """
        with self._lock:
            # Check memory cache
            if key in self._memory_cache:
                timestamp, size, data = self._memory_cache[key]
                if time.time() - timestamp < self.ttl:
                    logger.debug(f"Cache hit (memory): {key}")
                    response = self._deserialize_response(data)
                    response.from_cache = True
                    return response
                else:
                    # Expired - update size tracking
                    self._current_size -= size
                    del self._memory_cache[key]

        # Check file cache (outside lock for I/O)
        if self.cache_dir:
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                stat = cache_file.stat()
                if time.time() - stat.st_mtime < self.ttl:
                    logger.debug(f"Cache hit (file): {key}")
                    data = json.loads(cache_file.read_text())
                    response = self._deserialize_response(data)
                    response.from_cache = True
                    return response
                else:
                    # Expired
                    cache_file.unlink()

        return None

    def set(self, key: str, response: FetchResponse) -> None:
        """Cache a response.

        Thread-safe: uses lock.

        Args:
            key: Cache key
            response: Response to cache
        """
        data = self._serialize_response(response)

        # Estimate size (do serialization outside lock)
        serialized = json.dumps(data)
        size = len(serialized)

        with self._lock:
            # Remove old entry if exists (update size tracking)
            if key in self._memory_cache:
                _, old_size, _ = self._memory_cache[key]
                self._current_size -= old_size
                del self._memory_cache[key]

            # Check if we need to evict
            while self._current_size + size > self.max_size:
                if not self._evict_oldest():
                    break

            # Store in memory with size tracking
            self._memory_cache[key] = (time.time(), size, data)
            self._current_size += size

        # Store to file (outside lock for I/O)
        if self.cache_dir:
            cache_file = self.cache_dir / f"{key}.json"
            cache_file.write_text(serialized)

        logger.debug(f"Cached: {key}")

    def delete(self, key: str) -> bool:
        """Delete cached entry.

        Thread-safe: uses lock.

        Args:
            key: Cache key

        Returns:
            True if deleted
        """
        deleted = False

        with self._lock:
            if key in self._memory_cache:
                _, size, _ = self._memory_cache[key]
                self._current_size -= size
                del self._memory_cache[key]
                deleted = True

        if self.cache_dir:
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                cache_file.unlink()
                deleted = True

        return deleted

    def clear(self) -> int:
        """Clear all cache entries.

        Thread-safe: uses lock.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._memory_cache)
            self._memory_cache.clear()
            self._current_size = 0

        if self.cache_dir:
            for f in self.cache_dir.glob("*.json"):
                f.unlink()
                count += 1

        logger.info(f"Cleared {count} cache entries")
        return count

    def _evict_oldest(self) -> bool:
        """Evict oldest cache entry.

        Note: Caller must hold lock.
        """
        if not self._memory_cache:
            return False

        # Find oldest
        oldest_key = min(
            self._memory_cache.keys(),
            key=lambda k: self._memory_cache[k][0]
        )

        _, size, _ = self._memory_cache[oldest_key]
        self._current_size -= size
        del self._memory_cache[oldest_key]
        return True

    def _serialize_response(self, response: FetchResponse) -> dict:
        """Serialize response for caching."""
        content = response.content
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        return {
            "url": response.url,
            "final_url": response.final_url,
            "status_code": response.status_code,
            "content_type": response.content_type,
            "content": content,
            "headers": response.headers,
            "encoding": response.encoding,
            "fetch_time": response.fetch_time
        }

    def _deserialize_response(self, data: dict) -> FetchResponse:
        """Deserialize cached response."""
        return FetchResponse(
            url=data["url"],
            final_url=data["final_url"],
            status_code=data["status_code"],
            content_type=data["content_type"],
            content=data["content"],
            headers=data["headers"],
            encoding=data["encoding"],
            fetch_time=data["fetch_time"],
            from_cache=True
        )
```

---

## Step 7: Tool Implementations (tools.py)

```python
# src/forge/web/tools.py
"""Web tool implementations."""

import logging
from typing import Any

from .cache import WebCache
from .config import WebConfig
from .fetch.fetcher import FetchError, URLFetcher
from .fetch.parser import HTMLParser
from .search.base import SearchError, SearchProvider
from .types import FetchOptions, SearchResponse

logger = logging.getLogger(__name__)


class WebSearchTool:
    """Web search tool implementation."""

    name = "web_search"
    description = "Search the web for information"

    def __init__(
        self,
        providers: dict[str, SearchProvider],
        default_provider: str = "duckduckgo"
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
        **kwargs
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
        cache: WebCache | None = None
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
        **kwargs
    ) -> str:
        """Fetch URL content.

        Args:
            url: URL to fetch
            prompt: Optional prompt for processing
            format: Output format (markdown, text, raw)
            use_cache: Whether to use cache
            timeout: Override timeout

        Returns:
            Fetched and processed content
        """
        # Check cache
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
            if use_cache and self.cache:
                self.cache.set(cache_key, response)

            return self._format_response(response, format, prompt)

        except FetchError as e:
            return f"Fetch error: {e}"

    def _format_response(
        self,
        response: Any,
        format: str,
        prompt: str | None
    ) -> str:
        """Format response based on format option."""
        from .types import FetchResponse

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
```

---

## Step 8: Package Exports (__init__.py)

```python
# src/forge/web/__init__.py
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
from .search.duckduckgo import DuckDuckGoProvider
from .search.google import GoogleSearchProvider
from .search.brave import BraveSearchProvider
from .tools import WebFetchTool, WebSearchTool
from .types import (
    FetchOptions,
    FetchResponse,
    ParsedContent,
    SearchResponse,
    SearchResult,
)

__all__ = [
    # Types
    "SearchResult",
    "SearchResponse",
    "FetchResponse",
    "FetchOptions",
    "ParsedContent",
    # Search
    "SearchProvider",
    "SearchError",
    "DuckDuckGoProvider",
    "GoogleSearchProvider",
    "BraveSearchProvider",
    # Fetch
    "URLFetcher",
    "FetchError",
    "HTMLParser",
    # Cache
    "WebCache",
    # Config
    "WebConfig",
    "SearchConfig",
    "FetchConfig",
    "CacheConfig",
    "SearchProviderConfig",
    # Tools
    "WebSearchTool",
    "WebFetchTool",
]
```

---

## Testing Strategy

1. **Search provider tests**: Mock HTTP, test result parsing
2. **Fetcher tests**: Mock HTTP, test redirects, errors
3. **Parser tests**: Test HTML conversion, edge cases
4. **Cache tests**: Test get/set/eviction
5. **Tool tests**: Integration with mocks
6. **Integration tests**: Real HTTP (limited)

---

## Notes

- DuckDuckGo provider doesn't require API key
- HTML parsing uses BeautifulSoup and html2text
- Cache supports both memory and file storage
- Content is truncated for LLM context limits
- Domain filtering happens after search results
