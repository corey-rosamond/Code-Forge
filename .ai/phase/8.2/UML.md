# Phase 8.2: Web Tools - UML Diagrams

**Phase:** 8.2
**Name:** Web Tools (WebSearch, WebFetch)
**Dependencies:** Phase 2.1 (Tool System), Phase 3.2 (LangChain Integration)

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA TYPES                                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐     ┌─────────────────────────┐
│     SearchResult        │     │    SearchResponse       │
├─────────────────────────┤     ├─────────────────────────┤
│ + title: str            │     │ + query: str            │
│ + url: str              │     │ + results: list[Result] │
│ + snippet: str          │     │ + provider: str         │
│ + date: str | None      │     │ + total_results: int    │
│ + source: str | None    │     │ + search_time: float    │
│ + metadata: dict        │     ├─────────────────────────┤
├─────────────────────────┤     │ + to_dict(): dict       │
│ + to_dict(): dict       │     │ + to_markdown(): str    │
│ + to_markdown(): str    │     └─────────────────────────┘
└─────────────────────────┘

┌─────────────────────────┐     ┌─────────────────────────┐
│     FetchResponse       │     │     FetchOptions        │
├─────────────────────────┤     ├─────────────────────────┤
│ + url: str              │     │ + timeout: int          │
│ + final_url: str        │     │ + max_size: int         │
│ + status_code: int      │     │ + user_agent: str       │
│ + content_type: str     │     │ + follow_redirects: bool│
│ + content: str | bytes  │     │ + max_redirects: int    │
│ + headers: dict         │     │ + headers: dict         │
│ + encoding: str         │     │ + verify_ssl: bool      │
│ + fetch_time: float     │     └─────────────────────────┘
│ + from_cache: bool      │
├─────────────────────────┤     ┌─────────────────────────┐
│ + is_html: bool         │     │    ParsedContent        │
│ + is_text: bool         │     ├─────────────────────────┤
└─────────────────────────┘     │ + title: str | None     │
                                │ + text: str             │
                                │ + markdown: str         │
                                │ + links: list[dict]     │
                                │ + images: list[dict]    │
                                │ + metadata: dict        │
                                └─────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                           SEARCH PROVIDERS                                   │
└─────────────────────────────────────────────────────────────────────────────┘

              ┌─────────────────────────────────────┐
              │   SearchProvider <<abstract>>       │
              ├─────────────────────────────────────┤
              │                                     │
              ├─────────────────────────────────────┤
              │ + name: str <<property>>            │
              │ + requires_api_key: bool <<prop>>   │
              │ + search(query, num): Response      │
              │ + filter_results(response): Resp    │
              └─────────────────┬───────────────────┘
                                │
                                │ implements
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│DuckDuckGoProvider │   │GoogleSearchProvider│   │BraveSearchProvider│
├───────────────────┤   ├───────────────────┤   ├───────────────────┤
│                   │   │ + api_key: str    │   │ + api_key: str    │
│                   │   │ + cx: str         │   │                   │
├───────────────────┤   ├───────────────────┤   ├───────────────────┤
│ + name = "ddg"    │   │ + name = "google" │   │ + name = "brave"  │
│ + search()        │   │ + search()        │   │ + search()        │
└───────────────────┘   └───────────────────┘   └───────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                             FETCH SYSTEM                                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│              URLFetcher                 │
├─────────────────────────────────────────┤
│ + default_options: FetchOptions         │
├─────────────────────────────────────────┤
│ + fetch(url, options): FetchResponse    │
│ + fetch_multiple(urls): list[Response]  │
│ - _read_content(resp, max): bytes       │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│              HTMLParser                 │
├─────────────────────────────────────────┤
│ - _h2t: HTML2Text                       │
├─────────────────────────────────────────┤
│ + parse(html, base_url): ParsedContent  │
│ + to_text(html): str                    │
│ + to_markdown(html): str                │
│ + extract_main_content(html): str       │
└─────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                               CACHING                                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        WebCache                                 │
├─────────────────────────────────────────────────────────────────┤
│ + max_size: int                                                 │
│ + ttl: int                                                      │
│ + cache_dir: Path | None                                        │
│ - _memory_cache: dict[str, tuple[float, Any]]                  │
│ - _current_size: int                                            │
├─────────────────────────────────────────────────────────────────┤
│ + generate_key(url, options): str                               │
│ + get(key): FetchResponse | None                                │
│ + set(key, response): None                                      │
│ + delete(key): bool                                             │
│ + clear(): int                                                  │
│ - _evict_oldest(): bool                                         │
│ - _serialize_response(response): dict                           │
│ - _deserialize_response(data): FetchResponse                    │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                            TOOL CLASSES                                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│           WebSearchTool                 │
├─────────────────────────────────────────┤
│ + name = "web_search"                   │
│ + description: str                      │
│ + providers: dict[str, SearchProvider]  │
│ + default_provider: str                 │
├─────────────────────────────────────────┤
│ + execute(query, num_results,           │
│           provider, allowed_domains,    │
│           blocked_domains): str         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│           WebFetchTool                  │
├─────────────────────────────────────────┤
│ + name = "web_fetch"                    │
│ + description: str                      │
│ + fetcher: URLFetcher                   │
│ + parser: HTMLParser                    │
│ + cache: WebCache | None                │
├─────────────────────────────────────────┤
│ + execute(url, prompt, format,          │
│           use_cache, timeout): str      │
│ - _format_response(response, format,    │
│                    prompt): str         │
└─────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONFIGURATION                                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────┐     ┌───────────────────────┐
│ SearchProviderConfig  │     │    SearchConfig       │
├───────────────────────┤     ├───────────────────────┤
│ + name: str           │     │ + default_provider: str│
│ + api_key: str | None │     │ + default_results: int │
│ + endpoint: str | None│     │ + timeout: int         │
│ + extra: dict         │     │ + providers: dict      │
└───────────────────────┘     └───────────────────────┘

┌───────────────────────┐     ┌───────────────────────┐
│     FetchConfig       │     │     CacheConfig       │
├───────────────────────┤     ├───────────────────────┤
│ + timeout: int        │     │ + enabled: bool       │
│ + max_size: int       │     │ + ttl: int            │
│ + user_agent: str     │     │ + max_size: int       │
│ + follow_redirects    │     │ + directory: str|None │
│ + max_redirects: int  │     └───────────────────────┘
└───────────────────────┘

┌─────────────────────────────────────────┐
│             WebConfig                   │
├─────────────────────────────────────────┤
│ + search: SearchConfig                  │
│ + fetch: FetchConfig                    │
│ + cache: CacheConfig                    │
├─────────────────────────────────────────┤
│ + from_dict(data): cls                  │
└─────────────────────────────────────────┘
```

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            WEB TOOLS SYSTEM                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                          Tool Layer                                   │  │
│  │                                                                       │  │
│  │   ┌───────────────────┐         ┌───────────────────┐               │  │
│  │   │   WebSearchTool   │         │   WebFetchTool    │               │  │
│  │   │                   │         │                   │               │  │
│  │   │  - Query web      │         │  - Fetch URLs     │               │  │
│  │   │  - Filter results │         │  - Parse HTML     │               │  │
│  │   │  - Format output  │         │  - Cache results  │               │  │
│  │   └─────────┬─────────┘         └─────────┬─────────┘               │  │
│  │             │                             │                          │  │
│  └─────────────┼─────────────────────────────┼──────────────────────────┘  │
│                │                             │                              │
│                ▼                             ▼                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        Service Layer                                  │  │
│  │                                                                       │  │
│  │   ┌───────────────┐    ┌───────────────┐    ┌───────────────┐       │  │
│  │   │   Search      │    │   URLFetcher  │    │   HTMLParser  │       │  │
│  │   │   Providers   │    │               │    │               │       │  │
│  │   │               │    │  - HTTP req   │    │  - BS4 parse  │       │  │
│  │   │  - DuckDuckGo │    │  - Redirects  │    │  - html2text  │       │  │
│  │   │  - Google     │    │  - Size limit │    │  - Extract    │       │  │
│  │   │  - Brave      │    │               │    │               │       │  │
│  │   └───────────────┘    └───────────────┘    └───────────────┘       │  │
│  │                                                                       │  │
│  │   ┌─────────────────────────────────────────────────────────────┐   │  │
│  │   │                      WebCache                                │   │  │
│  │   │                                                              │   │  │
│  │   │  - Memory cache      - File cache      - LRU eviction       │   │  │
│  │   └─────────────────────────────────────────────────────────────┘   │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                       External Services                                │  │
│  │                                                                        │  │
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │  │
│  │   │  DuckDuckGo  │  │  Google CSE  │  │ Brave Search │               │  │
│  │   │     API      │  │     API      │  │     API      │               │  │
│  │   └──────────────┘  └──────────────┘  └──────────────┘               │  │
│  │                                                                        │  │
│  │   ┌─────────────────────────────────────────────────────────────┐    │  │
│  │   │                  World Wide Web                              │    │  │
│  │   │                                                              │    │  │
│  │   │  HTTP/HTTPS endpoints for content fetching                   │    │  │
│  │   └─────────────────────────────────────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Sequence Diagram: Web Search

```
┌──────┐    ┌─────────────┐    ┌────────────────┐    ┌─────────────┐
│ LLM  │    │WebSearchTool│    │ SearchProvider │    │ Search API  │
└──┬───┘    └──────┬──────┘    └───────┬────────┘    └──────┬──────┘
   │               │                   │                    │
   │ web_search    │                   │                    │
   │ query="..."   │                   │                    │
   │──────────────>│                   │                    │
   │               │                   │                    │
   │               │ get provider      │                    │
   │               │───────────┐       │                    │
   │               │           │       │                    │
   │               │<──────────┘       │                    │
   │               │                   │                    │
   │               │ search(query, n)  │                    │
   │               │──────────────────>│                    │
   │               │                   │                    │
   │               │                   │ HTTP GET/POST      │
   │               │                   │───────────────────>│
   │               │                   │                    │
   │               │                   │    results JSON    │
   │               │                   │<───────────────────│
   │               │                   │                    │
   │               │                   │ parse results      │
   │               │                   │─────────┐          │
   │               │                   │         │          │
   │               │                   │<────────┘          │
   │               │                   │                    │
   │               │ SearchResponse    │                    │
   │               │<──────────────────│                    │
   │               │                   │                    │
   │               │ filter_results    │                    │
   │               │ (domains)         │                    │
   │               │───────────┐       │                    │
   │               │           │       │                    │
   │               │<──────────┘       │                    │
   │               │                   │                    │
   │               │ to_markdown()     │                    │
   │               │───────────┐       │                    │
   │               │           │       │                    │
   │               │<──────────┘       │                    │
   │               │                   │                    │
   │  markdown     │                   │                    │
   │  results      │                   │                    │
   │<──────────────│                   │                    │
   │               │                   │                    │
```

---

## Sequence Diagram: Web Fetch with Cache

```
┌──────┐    ┌────────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐
│ LLM  │    │WebFetchTool│    │ WebCache │    │URLFetcher │    │HTMLParser│
└──┬───┘    └─────┬──────┘    └────┬─────┘    └─────┬─────┘    └────┬─────┘
   │              │                │                │               │
   │ web_fetch    │                │                │               │
   │ url="..."    │                │                │               │
   │─────────────>│                │                │               │
   │              │                │                │               │
   │              │ generate_key() │                │               │
   │              │───────────────>│                │               │
   │              │                │                │               │
   │              │     key        │                │               │
   │              │<───────────────│                │               │
   │              │                │                │               │
   │              │ get(key)       │                │               │
   │              │───────────────>│                │               │
   │              │                │                │               │
   │              │    None        │                │               │
   │              │<───────────────│                │               │
   │              │                │                │               │
   │              │ fetch(url)     │                │               │
   │              │───────────────────────────────>│               │
   │              │                │                │               │
   │              │                │                │ HTTP GET      │
   │              │                │                │──────────>    │
   │              │                │                │               │
   │              │                │                │   response    │
   │              │                │                │<──────────    │
   │              │                │                │               │
   │              │   FetchResponse│                │               │
   │              │<───────────────────────────────│               │
   │              │                │                │               │
   │              │ set(key, resp) │                │               │
   │              │───────────────>│                │               │
   │              │                │                │               │
   │              │ to_markdown()  │                │               │
   │              │────────────────────────────────────────────────>│
   │              │                │                │               │
   │              │    markdown    │                │               │
   │              │<────────────────────────────────────────────────│
   │              │                │                │               │
   │  formatted   │                │                │               │
   │  content     │                │                │               │
   │<─────────────│                │                │               │
   │              │                │                │               │
```

---

## Sequence Diagram: Cache Hit

```
┌──────┐    ┌────────────┐    ┌──────────┐
│ LLM  │    │WebFetchTool│    │ WebCache │
└──┬───┘    └─────┬──────┘    └────┬─────┘
   │              │                │
   │ web_fetch    │                │
   │ url="..."    │                │
   │─────────────>│                │
   │              │                │
   │              │ generate_key() │
   │              │───────────────>│
   │              │                │
   │              │     key        │
   │              │<───────────────│
   │              │                │
   │              │ get(key)       │
   │              │───────────────>│
   │              │                │
   │              │                │ check TTL
   │              │                │────────┐
   │              │                │        │
   │              │                │<───────┘
   │              │                │
   │              │ FetchResponse  │
   │              │ (from_cache)   │
   │              │<───────────────│
   │              │                │
   │ [From cache] │                │
   │  formatted   │                │
   │  content     │                │
   │<─────────────│                │
   │              │                │
```

---

## State Diagram: Cache Entry Lifecycle

```
                    ┌─────────────────┐
                    │                 │
                    │    EMPTY        │
                    │                 │
                    └────────┬────────┘
                             │
                             │ set(key, response)
                             ▼
                    ┌─────────────────┐
                    │                 │
                    │    CACHED       │
                    │                 │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           │ get() &&        │ TTL expired     │ evict (LRU)
           │ TTL valid       │                 │
           ▼                 ▼                 ▼
  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
  │                 │ │                 │ │                 │
  │   HIT           │ │   EXPIRED       │ │   EVICTED       │
  │  (return data)  │ │  (delete)       │ │  (delete)       │
  │                 │ │                 │ │                 │
  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
           │                   │                   │
           │                   │                   │
           └───────────────────┴───────────────────┘
                               │
                               ▼
                    ┌─────────────────┐
                    │                 │
                    │    EMPTY        │
                    │                 │
                    └─────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          WEB TOOLS DATA FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

                           USER QUERY
                               │
                               ▼
                    ┌──────────────────┐
                    │   LLM/Agent      │
                    │                  │
                    │ Determines:      │
                    │ - web_search     │
                    │ - web_fetch      │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
     ┌────────────────┐            ┌────────────────┐
     │ WebSearchTool  │            │ WebFetchTool   │
     │                │            │                │
     │ query          │            │ url            │
     │ num_results    │            │ format         │
     │ domains        │            │ use_cache      │
     └───────┬────────┘            └───────┬────────┘
             │                             │
             ▼                             │
     ┌────────────────┐                    │
     │SearchProvider  │                    │
     │                │                    │
     │ - DuckDuckGo   │                    │
     │ - Google       │                    │
     │ - Brave        │                    │
     └───────┬────────┘                    │
             │                             │
             ▼                             ▼
     ┌────────────────┐            ┌────────────────┐
     │  Search API    │            │   WebCache     │
     │  (External)    │            │                │
     └───────┬────────┘            │ Check cache    │
             │                     └───────┬────────┘
             │                             │
             │                    ┌────────┴────────┐
             │                    │                 │
             │               Cache Hit         Cache Miss
             │                    │                 │
             │                    │                 ▼
             │                    │        ┌────────────────┐
             │                    │        │  URLFetcher    │
             │                    │        │                │
             │                    │        │  HTTP Request  │
             │                    │        └───────┬────────┘
             │                    │                │
             │                    │                ▼
             │                    │        ┌────────────────┐
             │                    │        │  Web Server    │
             │                    │        │  (External)    │
             │                    │        └───────┬────────┘
             │                    │                │
             │                    │                ▼
             │                    │        ┌────────────────┐
             │                    │        │  HTMLParser    │
             │                    │        │                │
             │                    │        │ - to_text      │
             │                    │        │ - to_markdown  │
             │                    │        └───────┬────────┘
             │                    │                │
             ▼                    ▼                ▼
     ┌────────────────────────────────────────────────────┐
     │                    Response Formatting              │
     │                                                     │
     │  SearchResponse.to_markdown()                       │
     │  FetchResponse + ParsedContent                      │
     └────────────────────────┬────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   LLM Context    │
                    │                  │
                    │ Formatted text   │
                    │ for conversation │
                    └──────────────────┘
```

---

## Package Structure Diagram

```
src/opencode/web/
├── __init__.py
│   ├── SearchResult
│   ├── SearchResponse
│   ├── FetchResponse
│   ├── FetchOptions
│   ├── SearchProvider
│   ├── URLFetcher
│   ├── HTMLParser
│   ├── WebCache
│   ├── WebConfig
│   ├── WebSearchTool
│   └── WebFetchTool
│
├── types.py
│   ├── SearchResult
│   ├── SearchResponse
│   ├── FetchResponse
│   ├── FetchOptions
│   └── ParsedContent
│
├── config.py
│   ├── SearchProviderConfig
│   ├── SearchConfig
│   ├── FetchConfig
│   ├── CacheConfig
│   └── WebConfig
│
├── search/
│   ├── __init__.py
│   ├── base.py
│   │   ├── SearchProvider (abstract)
│   │   └── SearchError
│   ├── duckduckgo.py
│   │   └── DuckDuckGoProvider
│   ├── google.py
│   │   └── GoogleSearchProvider
│   └── brave.py
│       └── BraveSearchProvider
│
├── fetch/
│   ├── __init__.py
│   ├── fetcher.py
│   │   ├── URLFetcher
│   │   └── FetchError
│   └── parser.py
│       └── HTMLParser
│
├── cache.py
│   └── WebCache
│
└── tools.py
    ├── WebSearchTool
    └── WebFetchTool
```

---

## Integration Points Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        WEB TOOLS INTEGRATION                                 │
└─────────────────────────────────────────────────────────────────────────────┘

                         ┌────────────────┐
                         │   Web Tools    │
                         │  (Phase 8.2)   │
                         └───────┬────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐        ┌───────────────┐        ┌───────────────┐
│ Tool System   │        │  LangChain    │        │ Configuration │
│ (Phase 2.1)   │        │ (Phase 3.2)   │        │ (Phase 1.2)   │
├───────────────┤        ├───────────────┤        ├───────────────┤
│               │        │               │        │               │
│ WebSearchTool │        │ Tools bound   │        │ web: section  │
│ WebFetchTool  │        │ to LLM        │        │ in config     │
│ registered    │        │               │        │               │
│               │        │ Tool schemas  │        │ API keys from │
│ Tool schemas  │        │ provided      │        │ environment   │
│ for LLM       │        │               │        │               │
└───────────────┘        └───────────────┘        └───────────────┘

        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐        ┌───────────────┐        ┌───────────────┐
│  Permission   │        │    Session    │        │ Subagents     │
│ (Phase 4.1)   │        │ (Phase 5.1)   │        │ (Phase 7.1)   │
├───────────────┤        ├───────────────┤        ├───────────────┤
│               │        │               │        │               │
│ Web tools may │        │ Cache config  │        │ Agents can    │
│ require       │        │ persists      │        │ use web tools │
│ permission    │        │               │        │               │
│               │        │ Cache shared  │        │ Explore agent │
│ Domain        │        │ across        │        │ searches web  │
│ allowlists    │        │ sessions      │        │               │
└───────────────┘        └───────────────┘        └───────────────┘
```

---

## Notes

- Web search supports multiple providers with consistent interface
- DuckDuckGo is default (no API key required)
- HTML content converted to Markdown for LLM context
- Caching reduces repeated fetches within TTL
- Domain filtering allows/blocks specific sites
- Content truncated to fit context limits
