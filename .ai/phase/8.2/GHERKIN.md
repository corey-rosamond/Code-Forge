# Phase 8.2: Web Tools - Gherkin Specifications

**Phase:** 8.2
**Name:** Web Tools (WebSearch, WebFetch)
**Dependencies:** Phase 2.1 (Tool System), Phase 3.2 (LangChain Integration)

---

## Feature: Web Search

### Scenario: Basic search query
```gherkin
Given a WebSearchTool with DuckDuckGo provider
When I execute search with query "python async tutorial"
Then result should contain SearchResponse
And response should have results
And each result should have title, url, snippet
```

### Scenario: Search with result limit
```gherkin
Given a WebSearchTool
When I execute search with query "test" and num_results=5
Then response should have at most 5 results
```

### Scenario: Search with allowed domains
```gherkin
Given a WebSearchTool
When I execute search with allowed_domains=["stackoverflow.com"]
Then all results should be from stackoverflow.com
```

### Scenario: Search with blocked domains
```gherkin
Given a WebSearchTool
When I execute search with blocked_domains=["pinterest.com"]
Then no results should be from pinterest.com
```

### Scenario: Search with specific provider
```gherkin
Given a WebSearchTool with multiple providers
When I execute search with provider="google"
Then Google Search API should be used
And response.provider should be "google"
```

### Scenario: Search provider fallback
```gherkin
Given a WebSearchTool with default provider unavailable
When I execute search
Then next available provider should be used
And search should complete successfully
```

### Scenario: Search returns markdown format
```gherkin
Given a WebSearchTool
When I execute search
Then result should be formatted as Markdown
And should include numbered results
And should include clickable links
```

### Scenario: Empty search results
```gherkin
Given a WebSearchTool
When I execute search with very obscure query
Then result should indicate no results found
And should not raise error
```

---

## Feature: Search Providers

### Scenario: DuckDuckGo provider works without API key
```gherkin
Given a DuckDuckGoProvider
And no API key configured
When I call search("test query")
Then search should succeed
And results should be returned
```

### Scenario: Google provider requires API key
```gherkin
Given a GoogleSearchProvider without api_key
When I try to search
Then SearchError should be raised
And error should mention API key
```

### Scenario: Brave provider requires API key
```gherkin
Given a BraveSearchProvider without api_key
When I try to search
Then SearchError should be raised
And error should mention API key
```

### Scenario: Provider handles API error
```gherkin
Given a search provider
And API returns error response
When I call search()
Then SearchError should be raised
And error should contain API error message
```

### Scenario: Provider handles timeout
```gherkin
Given a search provider
And API request times out
When I call search()
Then SearchError should be raised
And error should mention timeout
```

---

## Feature: Web Fetch

### Scenario: Fetch HTML page
```gherkin
Given a WebFetchTool
When I execute fetch with url="https://example.com"
Then result should contain page content
And content should be readable text
```

### Scenario: Fetch with Markdown conversion
```gherkin
Given a WebFetchTool
When I execute fetch with format="markdown"
Then HTML should be converted to Markdown
And headings should use # syntax
And links should use [text](url) syntax
```

### Scenario: Fetch with text conversion
```gherkin
Given a WebFetchTool
When I execute fetch with format="text"
Then HTML should be converted to plain text
And all tags should be removed
And structure should be preserved with newlines
```

### Scenario: Fetch with raw HTML
```gherkin
Given a WebFetchTool
When I execute fetch with format="raw"
Then original HTML should be returned
And no conversion should be applied
```

### Scenario: Fetch follows redirects
```gherkin
Given a WebFetchTool with follow_redirects=True
When I fetch a URL that redirects
Then final content should be returned
And response.final_url should be the redirected URL
```

### Scenario: Fetch handles redirect loop
```gherkin
Given a WebFetchTool with max_redirects=5
When I fetch a URL with redirect loop
Then FetchError should be raised
And error should mention redirect limit
```

### Scenario: Fetch respects timeout
```gherkin
Given a WebFetchTool with timeout=5
When I fetch a slow URL
And response takes more than 5 seconds
Then FetchError should be raised
And error should mention timeout
```

### Scenario: Fetch respects size limit
```gherkin
Given a WebFetchTool with max_size=1MB
When I fetch a URL with 5MB content
Then FetchError should be raised
And error should mention size limit
```

### Scenario: Fetch upgrades HTTP to HTTPS
```gherkin
Given a WebFetchTool
When I fetch "http://example.com"
Then request should use "https://example.com"
```

---

## Feature: HTML Parser

### Scenario: Parse HTML to structured content
```gherkin
Given an HTMLParser
When I parse valid HTML
Then result should be ParsedContent
And should contain title
And should contain text
And should contain markdown
```

### Scenario: Extract title from HTML
```gherkin
Given HTML with <title>Page Title</title>
When I parse the HTML
Then content.title should be "Page Title"
```

### Scenario: Extract links from HTML
```gherkin
Given HTML with multiple <a> tags
When I parse the HTML
Then content.links should contain all links
And each link should have text and url
```

### Scenario: Extract images from HTML
```gherkin
Given HTML with <img> tags
When I parse the HTML
Then content.images should contain all images
And each image should have src and alt
```

### Scenario: Extract metadata from HTML
```gherkin
Given HTML with <meta> tags
When I parse the HTML
Then content.metadata should contain meta values
And should include description and keywords
```

### Scenario: Remove script and style tags
```gherkin
Given HTML with <script> and <style> tags
When I convert to text
Then scripts should be removed
And styles should be removed
And visible text should remain
```

### Scenario: Handle malformed HTML
```gherkin
Given malformed HTML with unclosed tags
When I parse the HTML
Then parsing should not raise error
And best-effort content should be extracted
```

### Scenario: Extract main content
```gherkin
Given HTML with navigation, footer, and main content
When I call extract_main_content()
Then only main content should be returned
And navigation should be removed
And footer should be removed
```

---

## Feature: Web Cache

### Scenario: Cache stores response
```gherkin
Given an empty WebCache
And a FetchResponse
When I call cache.set(key, response)
Then cache should store the response
And cache.get(key) should return the response
```

### Scenario: Cache hit returns stored response
```gherkin
Given a WebCache with stored response
When I call cache.get(key) within TTL
Then stored response should be returned
And response.from_cache should be True
```

### Scenario: Cache miss returns None
```gherkin
Given a WebCache without the key
When I call cache.get(unknown_key)
Then None should be returned
```

### Scenario: Cache entry expires after TTL
```gherkin
Given a WebCache with TTL=60 seconds
And a cached response
When 61 seconds pass
And I call cache.get(key)
Then None should be returned
And entry should be deleted
```

### Scenario: Cache evicts old entries when full
```gherkin
Given a WebCache with max_size=1MB
And cache is 90% full
When I store a 200KB response
Then oldest entries should be evicted
And new entry should be stored
```

### Scenario: Cache clear removes all entries
```gherkin
Given a WebCache with 10 entries
When I call cache.clear()
Then all entries should be removed
And return value should be 10
```

### Scenario: Cache key generation
```gherkin
Given a URL and FetchOptions
When I call cache.generate_key(url, options)
Then key should be consistent for same inputs
And key should be different for different URLs
```

### Scenario: Cache handles binary content
```gherkin
Given a FetchResponse with binary content
When I cache and retrieve it
Then binary content should be preserved
```

---

## Feature: Web Fetch Tool with Cache

### Scenario: Tool uses cache by default
```gherkin
Given a WebFetchTool with cache
When I fetch the same URL twice
Then second fetch should use cache
And result should indicate from cache
```

### Scenario: Tool bypasses cache when requested
```gherkin
Given a WebFetchTool with cache
And URL is already cached
When I fetch with use_cache=False
Then fresh fetch should be performed
And cache should not be used
```

### Scenario: Tool caches new responses
```gherkin
Given a WebFetchTool with empty cache
When I fetch a URL
Then response should be cached
And subsequent fetch should hit cache
```

---

## Feature: Tool Integration

### Scenario: WebSearchTool registered in ToolRegistry
```gherkin
Given tool system is initialized
When I check registered tools
Then "web_search" should be available
And should have correct schema
```

### Scenario: WebFetchTool registered in ToolRegistry
```gherkin
Given tool system is initialized
When I check registered tools
Then "web_fetch" should be available
And should have correct schema
```

### Scenario: LLM can call WebSearch
```gherkin
Given LLM with web tools bound
When LLM decides to search web
Then web_search tool should be called
And results should be returned to LLM
```

### Scenario: LLM can call WebFetch
```gherkin
Given LLM with web tools bound
When LLM decides to fetch URL
Then web_fetch tool should be called
And content should be returned to LLM
```

---

## Feature: Error Handling

### Scenario: Handle network error
```gherkin
Given a WebFetchTool
When network is unavailable
And I try to fetch
Then FetchError should be raised
And error should mention network
```

### Scenario: Handle DNS error
```gherkin
Given a WebFetchTool
When I fetch "https://nonexistent.domain.invalid"
Then FetchError should be raised
And error should indicate DNS failure
```

### Scenario: Handle SSL error
```gherkin
Given a WebFetchTool with verify_ssl=True
When I fetch URL with invalid certificate
Then FetchError should be raised
And error should mention SSL
```

### Scenario: Handle 404 response
```gherkin
Given a WebFetchTool
When I fetch URL that returns 404
Then response should indicate error
Or content should show 404 message
```

### Scenario: Handle 500 response
```gherkin
Given a WebFetchTool
When I fetch URL that returns 500
Then response should indicate server error
```

### Scenario: Tool returns error message, not exception
```gherkin
Given a WebSearchTool
When search fails
Then error message should be returned
And LLM should receive usable response
```

---

## Feature: Configuration

### Scenario: Load search configuration
```gherkin
Given config with search settings
When WebConfig.from_dict() is called
Then search.default_provider should be set
And search.timeout should be set
And search.providers should be populated
```

### Scenario: Load fetch configuration
```gherkin
Given config with fetch settings
When WebConfig.from_dict() is called
Then fetch.timeout should be set
And fetch.max_size should be set
And fetch.user_agent should be set
```

### Scenario: Expand environment variables in config
```gherkin
Given config with api_key="${GOOGLE_API_KEY}"
And environment variable GOOGLE_API_KEY="secret"
When config is loaded
Then api_key should be "secret"
```

### Scenario: Default configuration values
```gherkin
Given empty web config
When WebConfig is created
Then default_provider should be "duckduckgo"
And timeout should have default value
And cache.enabled should be True
```

---

## Feature: Content Processing

### Scenario: Truncate large content
```gherkin
Given a WebFetchTool
When I fetch page with 100KB of text
Then content should be truncated
And truncation message should be added
```

### Scenario: Add source URL to output
```gherkin
Given a WebFetchTool
When I fetch a URL
Then output should include source URL
And should show final URL after redirects
```

### Scenario: Indicate cached content
```gherkin
Given a WebFetchTool
When I get cached response
Then output should indicate "[From cache]"
```

### Scenario: Handle non-HTML content
```gherkin
Given a WebFetchTool
When I fetch JSON endpoint
Then JSON should be returned as-is
And no HTML conversion should be attempted
```

### Scenario: Handle binary content
```gherkin
Given a WebFetchTool
When I fetch image URL
Then result should indicate binary content
And content type should be shown
```
