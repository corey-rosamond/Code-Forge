# Phase 8.2: Web Tools - Completion Criteria

**Phase:** 8.2
**Name:** Web Tools (WebSearch, WebFetch)
**Dependencies:** Phase 2.1 (Tool System), Phase 3.2 (LangChain Integration)

---

## Completion Checklist

### 1. Data Types (types.py)

- [ ] `SearchResult` dataclass implemented
  - [ ] `title: str`
  - [ ] `url: str`
  - [ ] `snippet: str`
  - [ ] `date: str | None`
  - [ ] `source: str | None`
  - [ ] `metadata: dict`
  - [ ] `to_dict()` method
  - [ ] `to_markdown()` method

- [ ] `SearchResponse` dataclass implemented
  - [ ] `query: str`
  - [ ] `results: list[SearchResult]`
  - [ ] `provider: str`
  - [ ] `total_results: int | None`
  - [ ] `search_time: float | None`
  - [ ] `to_dict()` method
  - [ ] `to_markdown()` method

- [ ] `FetchResponse` dataclass implemented
  - [ ] `url: str`
  - [ ] `final_url: str`
  - [ ] `status_code: int`
  - [ ] `content_type: str`
  - [ ] `content: str | bytes`
  - [ ] `headers: dict`
  - [ ] `encoding: str`
  - [ ] `fetch_time: float`
  - [ ] `from_cache: bool`
  - [ ] `is_html` property
  - [ ] `is_text` property

- [ ] `FetchOptions` dataclass implemented
  - [ ] `timeout: int`
  - [ ] `max_size: int`
  - [ ] `user_agent: str`
  - [ ] `follow_redirects: bool`
  - [ ] `max_redirects: int`
  - [ ] `headers: dict`
  - [ ] `verify_ssl: bool`

- [ ] `ParsedContent` dataclass implemented
  - [ ] `title: str | None`
  - [ ] `text: str`
  - [ ] `markdown: str`
  - [ ] `links: list[dict]`
  - [ ] `images: list[dict]`
  - [ ] `metadata: dict`

### 2. Search Providers (search/)

- [ ] `SearchProvider` abstract base class
  - [ ] `name` property
  - [ ] `requires_api_key` property
  - [ ] `search()` async method
  - [ ] `filter_results()` method

- [ ] `DuckDuckGoProvider` implemented
  - [ ] `name = "duckduckgo"`
  - [ ] `requires_api_key = False`
  - [ ] `search()` uses duckduckgo-search library
  - [ ] Handles region and safe search options

- [ ] `GoogleSearchProvider` implemented
  - [ ] `name = "google"`
  - [ ] `requires_api_key = True`
  - [ ] `api_key` and `cx` parameters
  - [ ] `search()` uses Google Custom Search API

- [ ] `BraveSearchProvider` implemented
  - [ ] `name = "brave"`
  - [ ] `requires_api_key = True`
  - [ ] `api_key` parameter
  - [ ] `search()` uses Brave Search API

- [ ] `SearchError` exception defined

### 3. URL Fetcher (fetch/fetcher.py)

- [ ] `URLFetcher` class implemented
  - [ ] `default_options: FetchOptions`
  - [ ] `fetch()` async method
  - [ ] `fetch_multiple()` async method
  - [ ] `_read_content()` helper method

- [ ] Fetch features
  - [ ] HTTP to HTTPS upgrade
  - [ ] Redirect following
  - [ ] Size limit enforcement
  - [ ] Timeout handling
  - [ ] Custom headers support
  - [ ] SSL verification option

- [ ] `FetchError` exception defined

### 4. HTML Parser (fetch/parser.py)

- [ ] `HTMLParser` class implemented
  - [ ] `parse()` method returns ParsedContent
  - [ ] `to_text()` method
  - [ ] `to_markdown()` method
  - [ ] `extract_main_content()` method

- [ ] Parser features
  - [ ] Title extraction
  - [ ] Link extraction with base URL
  - [ ] Image extraction
  - [ ] Metadata extraction
  - [ ] Script/style removal
  - [ ] Boilerplate removal
  - [ ] Malformed HTML handling

### 5. Web Cache (cache.py)

- [ ] `WebCache` class implemented
  - [ ] `max_size: int`
  - [ ] `ttl: int`
  - [ ] `cache_dir: Path | None`
  - [ ] `_memory_cache: dict`
  - [ ] `_current_size: int`

- [ ] Cache methods
  - [ ] `generate_key()` returns consistent hash
  - [ ] `get()` returns cached or None
  - [ ] `set()` stores response
  - [ ] `delete()` removes entry
  - [ ] `clear()` removes all entries

- [ ] Cache features
  - [ ] TTL expiration
  - [ ] LRU eviction
  - [ ] File-based persistence (optional)
  - [ ] Size tracking
  - [ ] Binary content handling

### 6. Configuration (config.py)

- [ ] `SearchProviderConfig` dataclass
  - [ ] `name: str`
  - [ ] `api_key: str | None`
  - [ ] `endpoint: str | None`
  - [ ] `extra: dict`

- [ ] `SearchConfig` dataclass
  - [ ] `default_provider: str`
  - [ ] `default_results: int`
  - [ ] `timeout: int`
  - [ ] `providers: dict`

- [ ] `FetchConfig` dataclass
  - [ ] `timeout: int`
  - [ ] `max_size: int`
  - [ ] `user_agent: str`
  - [ ] `follow_redirects: bool`
  - [ ] `max_redirects: int`

- [ ] `CacheConfig` dataclass
  - [ ] `enabled: bool`
  - [ ] `ttl: int`
  - [ ] `max_size: int`
  - [ ] `directory: str | None`

- [ ] `WebConfig` dataclass
  - [ ] `search: SearchConfig`
  - [ ] `fetch: FetchConfig`
  - [ ] `cache: CacheConfig`
  - [ ] `from_dict()` class method
  - [ ] Environment variable expansion

### 7. Tool Implementations (tools.py)

- [ ] `WebSearchTool` class implemented
  - [ ] `name = "web_search"`
  - [ ] `description` provided
  - [ ] `providers: dict[str, SearchProvider]`
  - [ ] `default_provider: str`
  - [ ] `execute()` async method

- [ ] WebSearchTool features
  - [ ] Query execution
  - [ ] Result count limiting
  - [ ] Provider selection
  - [ ] Domain filtering (allowed/blocked)
  - [ ] Markdown output formatting
  - [ ] Error handling

- [ ] `WebFetchTool` class implemented
  - [ ] `name = "web_fetch"`
  - [ ] `description` provided
  - [ ] `fetcher: URLFetcher`
  - [ ] `parser: HTMLParser`
  - [ ] `cache: WebCache | None`
  - [ ] `execute()` async method

- [ ] WebFetchTool features
  - [ ] URL fetching
  - [ ] Format options (markdown, text, raw)
  - [ ] Cache integration
  - [ ] Content truncation
  - [ ] Source URL in output
  - [ ] Cache indicator
  - [ ] Error handling

### 8. Package Exports (__init__.py)

- [ ] All data types exported
- [ ] All search providers exported
- [ ] URLFetcher and HTMLParser exported
- [ ] WebCache exported
- [ ] Configuration classes exported
- [ ] Tool classes exported
- [ ] `__all__` list complete

### 9. Integration

- [ ] Tools registered in ToolRegistry
- [ ] Tool schemas provided for LLM
- [ ] Configuration loaded from settings
- [ ] API keys from environment
- [ ] Cache directory created

### 10. Testing

- [ ] Unit tests for SearchResult/SearchResponse
- [ ] Unit tests for DuckDuckGoProvider (mock)
- [ ] Unit tests for GoogleSearchProvider (mock)
- [ ] Unit tests for BraveSearchProvider (mock)
- [ ] Unit tests for URLFetcher (mock HTTP)
- [ ] Unit tests for HTMLParser
- [ ] Unit tests for WebCache
- [ ] Unit tests for WebSearchTool
- [ ] Unit tests for WebFetchTool
- [ ] Integration tests with real HTTP (limited)
- [ ] Test coverage ≥ 90%

### 11. Code Quality

- [ ] McCabe complexity ≤ 10 for all functions
- [ ] Type hints on all public methods
- [ ] Docstrings on all public classes/methods
- [ ] No circular imports
- [ ] Follows project code style

---

## Verification Commands

```bash
# Run unit tests
pytest tests/web/ -v

# Run with coverage
pytest tests/web/ --cov=src/forge/web --cov-report=term-missing

# Check coverage threshold
pytest tests/web/ --cov=src/forge/web --cov-fail-under=90

# Type checking
mypy src/forge/web/

# Complexity check
flake8 src/forge/web/ --max-complexity=10
```

---

## Test Scenarios

### Search Provider Tests

```python
async def test_duckduckgo_search():
    provider = DuckDuckGoProvider()
    response = await provider.search("test query", num_results=5)
    assert response.query == "test query"
    assert len(response.results) <= 5
    assert response.provider == "duckduckgo"

async def test_domain_filtering():
    provider = DuckDuckGoProvider()
    response = await provider.search("python")
    filtered = provider.filter_results(
        response,
        allowed_domains=["python.org"]
    )
    for result in filtered.results:
        assert "python.org" in result.url
```

### URL Fetcher Tests

```python
async def test_fetch_html_page(mock_http):
    mock_http.get("https://example.com", text="<html>...</html>")

    fetcher = URLFetcher()
    response = await fetcher.fetch("https://example.com")

    assert response.status_code == 200
    assert response.is_html
    assert "<html>" in response.content

async def test_fetch_follows_redirect(mock_http):
    mock_http.get(
        "https://old.example.com",
        status=301,
        headers={"Location": "https://new.example.com"}
    )
    mock_http.get("https://new.example.com", text="content")

    fetcher = URLFetcher()
    response = await fetcher.fetch("https://old.example.com")

    assert response.final_url == "https://new.example.com"
```

### HTML Parser Tests

```python
def test_parse_html():
    parser = HTMLParser()
    html = """
    <html>
    <head><title>Test Page</title></head>
    <body>
        <h1>Hello World</h1>
        <p>This is a test.</p>
    </body>
    </html>
    """
    content = parser.parse(html)

    assert content.title == "Test Page"
    assert "Hello World" in content.text
    assert "# Hello World" in content.markdown

def test_remove_scripts():
    parser = HTMLParser()
    html = "<html><script>alert('xss')</script><p>Text</p></html>"
    text = parser.to_text(html)

    assert "alert" not in text
    assert "Text" in text
```

### Cache Tests

```python
def test_cache_stores_response():
    cache = WebCache(ttl=60)
    response = FetchResponse(url="https://example.com", ...)

    cache.set("key1", response)
    cached = cache.get("key1")

    assert cached is not None
    assert cached.url == response.url
    assert cached.from_cache == True

def test_cache_expires():
    cache = WebCache(ttl=1)  # 1 second TTL
    cache.set("key1", response)

    time.sleep(2)
    cached = cache.get("key1")

    assert cached is None
```

### Tool Tests

```python
async def test_web_search_tool():
    providers = {"duckduckgo": DuckDuckGoProvider()}
    tool = WebSearchTool(providers, "duckduckgo")

    result = await tool.execute(query="test", num_results=3)

    assert "## Search Results" in result
    assert "test" in result.lower()

async def test_web_fetch_tool():
    fetcher = URLFetcher()
    parser = HTMLParser()
    cache = WebCache()
    tool = WebFetchTool(fetcher, parser, cache)

    result = await tool.execute(
        url="https://example.com",
        format="markdown"
    )

    assert "**Source:**" in result
```

---

## Definition of Done

Phase 8.2 is complete when:

1. All checklist items are checked off
2. All unit tests pass
3. Test coverage is ≥ 90%
4. Code complexity is ≤ 10
5. Type checking passes with no errors
6. DuckDuckGo search works without API key
7. Google and Brave search work with API keys
8. URL fetching retrieves content correctly
9. HTML converts to Markdown properly
10. Caching reduces duplicate requests
11. Domain filtering works
12. Error handling is graceful
13. Configuration loads correctly
14. Environment variables expand
15. Documentation is complete
16. Code review approved

---

## Dependencies Verification

Before starting Phase 8.2, verify:

- [ ] Phase 2.1 (Tool System) is complete
  - [ ] Tool interface available
  - [ ] ToolRegistry for registration

- [ ] Phase 3.2 (LangChain Integration) is complete
  - [ ] Tool binding works
  - [ ] LLM can call tools

- [ ] Phase 1.2 (Configuration) is complete
  - [ ] Config loading works
  - [ ] Environment variable expansion

---

## External Dependencies

Required Python packages:
- `aiohttp` - Async HTTP client
- `beautifulsoup4` - HTML parsing
- `html2text` - HTML to Markdown conversion
- `duckduckgo-search` - DuckDuckGo API (optional)

---

## Notes

- DuckDuckGo is the default provider (no API key required)
- Google and Brave require API keys in configuration
- HTML is converted to Markdown for better LLM understanding
- Content is truncated to fit context window limits
- Cache TTL defaults to 15 minutes
- Domain filtering applies after search results received
- HTTP URLs are automatically upgraded to HTTPS
