# Phase 8.2: Web Tools - Wireframes & Usage Examples

**Phase:** 8.2
**Name:** Web Tools (WebSearch, WebFetch)
**Dependencies:** Phase 2.1 (Tool System), Phase 3.2 (LangChain Integration)

---

## 1. Web Search Usage

### Basic Search

```
You: Search for recent Python async/await tutorials

I'll search the web for Python async/await tutorials.

[Calling web_search: query="Python async await tutorial 2024"]

## Search Results for: Python async await tutorial 2024

### 1. [Real Python - Async IO in Python: A Complete Walkthrough](https://realpython.com/async-io-python/)
Async IO is a concurrent programming design that has received dedicated support
in Python, evolving rapidly from Python 3.4 through 3.7. This tutorial covers
async/await syntax and shows you how to use it effectively.

### 2. [Python asyncio: The Complete Guide](https://superfastpython.com/python-asyncio/)
A comprehensive guide to Python's asyncio module. Learn how to write concurrent
code using coroutines, tasks, and the event loop with practical examples.

### 3. [AsyncIO Tutorial - Python Documentation](https://docs.python.org/3/library/asyncio.html)
Official Python documentation for the asyncio library. Covers event loops,
coroutines, streams, and synchronization primitives.

### 4. [Understanding Python Async/Await](https://testdriven.io/blog/python-async-await/)
A beginner-friendly guide to understanding Python's async/await syntax with
clear examples and explanations of when to use asynchronous programming.

Would you like me to fetch the full content of any of these articles?
```

### Search with Domain Filter

```
You: Search for React hooks examples, only from official docs and MDN

[Calling web_search: query="React hooks examples",
 allowed_domains=["react.dev", "developer.mozilla.org"]]

## Search Results for: React hooks examples

### 1. [Built-in React Hooks – React](https://react.dev/reference/react/hooks)
Hooks let you use different React features from your components. You can either
use the built-in Hooks or combine them to build your own.

### 2. [Introducing Hooks – React](https://react.dev/learn#using-hooks)
Hooks are functions that let you "hook into" React state and lifecycle features
from function components. Learn the basics of useState and useEffect.

### 3. [React: Getting Started - MDN Web Docs](https://developer.mozilla.org/en-US/docs/Learn/Tools_and_testing/Client-side_JavaScript_frameworks/React_getting_started)
Introduction to React with examples of components, props, state, and hooks for
beginners.
```

### No Results Found

```
You: Search for "xyzzy123 foobar quantum cryptography implementation"

[Calling web_search: query="xyzzy123 foobar quantum cryptography implementation"]

## Search Results

No results found for "xyzzy123 foobar quantum cryptography implementation".

Try:
- Using more common search terms
- Checking for typos
- Using fewer or broader keywords
```

---

## 2. Web Fetch Usage

### Fetch Documentation Page

```
You: Fetch the Python requests library quickstart guide

[Calling web_fetch: url="https://requests.readthedocs.io/en/latest/user/quickstart/"]

**Source:** https://requests.readthedocs.io/en/latest/user/quickstart/

# Quickstart

Eager to get started? This page gives a good introduction in how to get started
with Requests.

## Make a Request

Making a request with Requests is very simple. Begin by importing the Requests
module:

```python
import requests
```

Now, let's try to get a webpage. For this example, let's get GitHub's public
timeline:

```python
r = requests.get('https://api.github.com/events')
```

Now, we have a Response object called `r`. We can get all the information we
need from this object.

## Response Content

We can read the content of the server's response:

```python
r.text
# '{"type":"...'
```

Requests will automatically decode content from the server...

[Content truncated for display]
```

### Fetch with Text Format

```
You: Fetch the Hacker News front page as plain text

[Calling web_fetch: url="https://news.ycombinator.com", format="text"]

**Source:** https://news.ycombinator.com/

Hacker News

1. Show HN: I built an open-source AI code assistant
   (github.com)
   342 points by developer 3 hours ago | 156 comments

2. The hidden cost of software complexity
   (blog.example.com)
   289 points by techwriter 5 hours ago | 203 comments

3. PostgreSQL 17 Released with Major Performance Improvements
   (postgresql.org)
   567 points by dbadmin 7 hours ago | 234 comments

...
```

### Fetch from Cache

```
You: Fetch that Python requests page again

[Calling web_fetch: url="https://requests.readthedocs.io/en/latest/user/quickstart/"]

[From cache]

**Source:** https://requests.readthedocs.io/en/latest/user/quickstart/

# Quickstart

Eager to get started? This page gives a good introduction...

[Same content as before, served from cache]
```

### Fetch with Redirect

```
You: Fetch http://github.com

[Calling web_fetch: url="http://github.com"]

**Source:** https://github.com/ (redirected from http://github.com)

# GitHub: Let's build from here

GitHub is where over 100 million developers shape the future of software,
together. Contribute to the open source community, manage your Git repositories,
review code like a pro, track bugs and features...
```

---

## 3. Error Handling

### Network Error

```
You: Fetch https://definitely-not-a-real-website-12345.com

[Calling web_fetch: url="https://definitely-not-a-real-website-12345.com"]

Fetch error: Unable to connect to host. The domain could not be resolved.

Please check:
- The URL is spelled correctly
- The website is online
- Your network connection is working
```

### Timeout Error

```
You: Fetch content from this slow API endpoint

[Calling web_fetch: url="https://slow-api.example.com/data", timeout=5]

Fetch error: Request timed out after 5 seconds.

The server took too long to respond. You can:
- Try again later
- Increase the timeout value
- Check if the server is experiencing issues
```

### Size Limit

```
You: Download that large dataset file

[Calling web_fetch: url="https://example.com/large-dataset.csv"]

Fetch error: Content exceeds maximum size (5MB).

The requested file is too large to fetch directly. Consider:
- Downloading it manually
- Using a streaming approach
- Finding a smaller sample
```

### Search Provider Error

```
You: Search for "test" using google

[Calling web_search: query="test", provider="google"]

Search error: Google API returned an error: Invalid API key.

Please check your Google Custom Search API configuration:
1. Verify GOOGLE_API_KEY is set correctly
2. Ensure GOOGLE_CX (Custom Search Engine ID) is configured
3. Check API quota hasn't been exceeded

Falling back to DuckDuckGo...

## Search Results for: test

### 1. [Speedtest by Ookla](https://www.speedtest.net/)
...
```

---

## 4. Combined Search and Fetch

### Research Workflow

```
You: Find information about Rust error handling best practices

First, let me search for relevant resources.

[Calling web_search: query="Rust error handling best practices 2024"]

## Search Results

### 1. [Error Handling - The Rust Programming Language](https://doc.rust-lang.org/book/ch09-00-error-handling.html)
Rust groups errors into two major categories: recoverable and unrecoverable
errors...

### 2. [Rust Error Handling Best Practices](https://blog.burntsushi.net/rust-error-handling/)
A comprehensive guide to error handling patterns in Rust...

I found some good resources. Let me fetch the official documentation for more details.

[Calling web_fetch: url="https://doc.rust-lang.org/book/ch09-00-error-handling.html"]

**Source:** https://doc.rust-lang.org/book/ch09-00-error-handling.html

# Error Handling

Rust groups errors into two major categories: recoverable and unrecoverable
errors. For a recoverable error, such as a file not found error, it's
reasonable to report the problem to the user and retry the operation.
Unrecoverable errors are always symptoms of bugs, like trying to access a
location beyond the end of an array.

## Unrecoverable Errors with `panic!`

Sometimes, bad things happen in your code, and there's nothing you can do about
it. In these cases, Rust has the `panic!` macro...

## Recoverable Errors with `Result`

Most errors aren't serious enough to require the program to stop entirely.
Sometimes, when a function fails, it's for a reason that you can easily
interpret and respond to...

Would you like me to fetch more details from any of the other search results?
```

---

## 5. Configuration Examples

### Configuration File

```yaml
# ~/.src/opencode/config.yaml

web:
  search:
    default_provider: duckduckgo
    default_results: 10
    timeout: 15

    providers:
      google:
        api_key: "${GOOGLE_API_KEY}"
        cx: "${GOOGLE_CX}"

      brave:
        api_key: "${BRAVE_API_KEY}"

  fetch:
    timeout: 30
    max_size: 5242880  # 5MB
    user_agent: "src/opencode/1.0 (AI Assistant)"
    follow_redirects: true
    max_redirects: 5

  cache:
    enabled: true
    ttl: 900  # 15 minutes
    max_size: 104857600  # 100MB
    directory: ~/.src/opencode/cache/web
```

### Environment Variables

```bash
# Search provider API keys
export GOOGLE_API_KEY="your-google-api-key"
export GOOGLE_CX="your-custom-search-engine-id"
export BRAVE_API_KEY="your-brave-api-key"
```

---

## 6. Tool Schemas

### WebSearch Tool Schema

```
You: /tools web_search

Tool: web_search
══════════════════════════════════════════════════

Description: Search the web for information

Parameters:
  query (string, required)
    The search query

  num_results (integer, optional, default: 10)
    Number of results to return

  provider (string, optional)
    Search provider to use: duckduckgo, google, brave

  allowed_domains (array of strings, optional)
    Only include results from these domains

  blocked_domains (array of strings, optional)
    Exclude results from these domains

Returns:
  Formatted markdown with search results

Example:
  web_search(
    query="Python async programming",
    num_results=5,
    allowed_domains=["python.org", "realpython.com"]
  )
```

### WebFetch Tool Schema

```
You: /tools web_fetch

Tool: web_fetch
══════════════════════════════════════════════════

Description: Fetch and process content from a URL

Parameters:
  url (string, required)
    The URL to fetch

  prompt (string, optional)
    Optional prompt for processing the content

  format (string, optional, default: "markdown")
    Output format: markdown, text, raw

  use_cache (boolean, optional, default: true)
    Whether to use cached responses

  timeout (integer, optional)
    Request timeout in seconds

Returns:
  Formatted content from the URL

Example:
  web_fetch(
    url="https://docs.python.org/3/tutorial/index.html",
    format="markdown"
  )
```

---

## 7. Integration with Agent

### Agent Using Web Tools

```
You: I need to understand how to implement JWT authentication in FastAPI.
     Research this and summarize the best approach.

I'll research JWT authentication in FastAPI for you.

[Agent: research-auth]

Step 1: Searching for FastAPI JWT resources...
[web_search: "FastAPI JWT authentication tutorial 2024"]

Found 8 relevant results. Let me examine the top resources.

Step 2: Fetching FastAPI documentation...
[web_fetch: "https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/"]

Step 3: Fetching additional tutorial...
[web_fetch: "https://testdriven.io/blog/fastapi-jwt-auth/"]

Step 4: Synthesizing findings...

---

## JWT Authentication in FastAPI - Summary

### Overview
FastAPI provides built-in support for OAuth2 with JWT tokens through the
`fastapi.security` module.

### Key Components

1. **Password Hashing**
   Use `passlib` with bcrypt for secure password storage:
   ```python
   from passlib.context import CryptContext
   pwd_context = CryptContext(schemes=["bcrypt"])
   ```

2. **JWT Token Creation**
   Use `python-jose` for JWT handling:
   ```python
   from jose import JWTError, jwt

   def create_access_token(data: dict):
       to_encode = data.copy()
       expire = datetime.utcnow() + timedelta(minutes=30)
       to_encode.update({"exp": expire})
       return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
   ```

3. **OAuth2 Password Flow**
   ```python
   oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
   ```

### Best Practices
- Use environment variables for SECRET_KEY
- Set appropriate token expiration times
- Implement refresh tokens for long sessions
- Use HTTPS in production

### Sources
- FastAPI Official Documentation
- TestDriven.io JWT Tutorial

Would you like me to provide a complete implementation example?
```

---

## 8. Cache Management

### Cache Status

```
You: How much web content is cached?

[Checking web cache...]

Web Cache Status
══════════════════════════════════════════════════

Location: ~/.src/opencode/cache/web
Entries:  47
Size:     12.3 MB / 100 MB
TTL:      15 minutes

Recent entries:
  • requests.readthedocs.io (2 min ago)
  • docs.python.org (5 min ago)
  • fastapi.tiangolo.com (8 min ago)
  • realpython.com (12 min ago)
```

### Clear Cache

```
You: Clear the web cache

[Clearing web cache...]

Cleared 47 cache entries (12.3 MB freed).

Web cache is now empty.
```

---

## 9. Advanced Usage

### Fetch API Documentation

```
You: Fetch the OpenAI API reference for chat completions

[Calling web_fetch: url="https://platform.openai.com/docs/api-reference/chat"]

**Source:** https://platform.openai.com/docs/api-reference/chat

# Chat Completions API

Given a list of messages comprising a conversation, the model will return a
response.

## Create chat completion

`POST https://api.openai.com/v1/chat/completions`

### Request body

**model** (string, required)
ID of the model to use. See the model endpoint compatibility table.

**messages** (array, required)
A list of messages comprising the conversation so far.

| Role      | Description                                    |
|-----------|------------------------------------------------|
| system    | Sets the behavior of the assistant             |
| user      | Messages from the user                         |
| assistant | Previous responses from the assistant          |

**temperature** (number, optional)
What sampling temperature to use, between 0 and 2...

[Content continues...]
```

### Compare Multiple Sources

```
You: Search for "best Python web framework 2024" and fetch the top 2 results

[Calling web_search: query="best Python web framework 2024", num_results=5]

## Search Results

### 1. [Top Python Web Frameworks in 2024](https://blog.example.com/python-frameworks)
### 2. [Python Web Frameworks Comparison](https://comparison.example.com/python)
...

Let me fetch the top 2 results for detailed comparison.

[Calling web_fetch: url="https://blog.example.com/python-frameworks"]
[Calling web_fetch: url="https://comparison.example.com/python"]

## Source 1: Top Python Web Frameworks in 2024
...

## Source 2: Python Web Frameworks Comparison
...

## Summary Comparison

| Framework | Pros | Cons | Best For |
|-----------|------|------|----------|
| FastAPI   | Fast, async, auto-docs | Newer | APIs |
| Django    | Batteries included | Monolithic | Full apps |
| Flask     | Simple, flexible | Manual setup | Small apps |
```

---

## Notes

- DuckDuckGo is the default search provider (no API key required)
- Caching reduces repeated fetches for the same URLs
- HTML is converted to Markdown for better LLM understanding
- Content is truncated if too large for context
- Domain filtering allows focusing on trusted sources
- Error messages are user-friendly and actionable
