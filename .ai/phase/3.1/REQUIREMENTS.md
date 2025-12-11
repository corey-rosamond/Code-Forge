# Phase 3.1: OpenRouter Client - Requirements

**Phase:** 3.1
**Name:** OpenRouter Client
**Status:** Not Started
**Dependencies:** Phase 1.1 (Project Foundation), Phase 1.2 (Configuration)

---

## Overview

This phase implements the OpenRouter API client that provides access to 400+ AI models through a unified interface. OpenRouter acts as a gateway to multiple LLM providers (OpenAI, Anthropic, Google, Meta, etc.) with standardized API format.

---

## Functional Requirements

### FR-3.1.1: OpenRouter API Client
- Connect to OpenRouter API (https://openrouter.ai/api/v1)
- Support OpenAI-compatible chat completions endpoint
- Handle API key authentication via Authorization header
- Include HTTP-Referer and X-Title headers for rankings
- Support all OpenRouter-specific parameters
- Handle rate limiting with exponential backoff
- Implement request retry logic

### FR-3.1.2: Model Selection
- List available models from OpenRouter
- Filter models by capability (chat, completion, code)
- Select models by ID (e.g., "anthropic/claude-3-opus")
- Support model routing variants:
  - `:nitro` - fastest providers
  - `:floor` - cheapest providers
  - `:online` - models with web search
  - `:thinking` - extended reasoning
- Validate model availability before requests

### FR-3.1.3: Streaming Responses
- Support Server-Sent Events (SSE) streaming
- Parse streaming chunks incrementally
- Handle stream interruption gracefully
- Provide async iterator interface for chunks
- Collect full response from stream
- Report token usage from final chunk

### FR-3.1.4: Message Formatting
- Support system, user, assistant message roles
- Support multimodal messages (text + images)
- Support tool/function call messages
- Support tool results in messages
- Format messages per OpenAI chat format
- Validate message structure before sending

### FR-3.1.5: Tool/Function Calling
- Send tool definitions with requests
- Parse tool call responses
- Support parallel tool calls
- Handle tool call IDs
- Format tool results for continuation

### FR-3.1.6: Error Handling
- Parse OpenRouter error responses
- Handle authentication errors (401)
- Handle rate limit errors (429)
- Handle model unavailable errors
- Handle context length errors
- Handle content policy errors
- Provide clear error messages

### FR-3.1.7: Token Management
- Track input tokens per request
- Track output tokens per request
- Track total tokens across session
- Estimate tokens before sending (approximate)
- Respect model context limits

### FR-3.1.8: Cost Tracking
- Track cost per request
- Track cumulative session cost
- Retrieve model pricing from API
- Report cost in metadata

---

## Non-Functional Requirements

### NFR-3.1.1: Performance
- API response latency tracking
- Streaming first-token time tracking
- Connection pooling for HTTP client
- Async/concurrent request support

### NFR-3.1.2: Reliability
- Automatic retry with exponential backoff
- Circuit breaker for failing endpoints
- Graceful degradation on errors
- Request timeout handling

### NFR-3.1.3: Security
- API key stored securely (not logged)
- HTTPS-only communication
- Sanitize error messages
- No credential leakage in errors

---

## Technical Specifications

### OpenRouter Client

```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, AsyncIterator
from enum import Enum
import httpx


class MessageRole(str, Enum):
    """Message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """A message in the conversation."""
    role: MessageRole
    content: str | List[Dict[str, Any]]  # Text or multimodal content
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


@dataclass
class ToolDefinition:
    """Definition of a tool for function calling."""
    type: str = "function"
    function: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompletionRequest:
    """Request for chat completion."""
    model: str
    messages: List[Message]
    tools: Optional[List[ToolDefinition]] = None
    tool_choice: Optional[str | Dict] = None
    temperature: float = 1.0
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[List[str]] = None
    stream: bool = False
    # OpenRouter-specific
    transforms: Optional[List[str]] = None
    route: Optional[str] = None  # "fallback" for auto-routing


@dataclass
class TokenUsage:
    """Token usage statistics."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class CompletionChoice:
    """A completion choice from the response."""
    index: int
    message: Message
    finish_reason: str


@dataclass
class CompletionResponse:
    """Response from chat completion."""
    id: str
    model: str
    choices: List[CompletionChoice]
    usage: TokenUsage
    created: int
    # OpenRouter-specific
    provider: Optional[str] = None


@dataclass
class StreamChunk:
    """A chunk from streaming response."""
    id: str
    model: str
    delta: Dict[str, Any]
    finish_reason: Optional[str]
    usage: Optional[TokenUsage] = None


class OpenRouterClient:
    """
    Client for the OpenRouter API.

    Provides access to 400+ AI models through a unified interface.
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        app_name: str = "Code-Forge",
        app_url: str = "https://github.com/forge",
        timeout: float = 120.0,
        max_retries: int = 3,
    ):
        """
        Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key
            base_url: Override API base URL
            app_name: Application name for rankings
            app_url: Application URL for rankings
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL
        self.app_name = app_name
        self.app_url = app_url
        self.timeout = timeout
        self.max_retries = max_retries

        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
        return self._client

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.app_url,
            "X-Title": self.app_name,
            "Content-Type": "application/json",
        }

    async def complete(
        self, request: CompletionRequest
    ) -> CompletionResponse:
        """
        Send a chat completion request.

        Args:
            request: The completion request

        Returns:
            CompletionResponse with the model's response
        """
        client = await self._get_client()
        payload = self._build_payload(request)

        response = await self._make_request(
            client, "POST", "/chat/completions", payload
        )

        return self._parse_response(response)

    async def stream(
        self, request: CompletionRequest
    ) -> AsyncIterator[StreamChunk]:
        """
        Send a streaming chat completion request.

        Args:
            request: The completion request (stream=True is set automatically)

        Yields:
            StreamChunk for each piece of the response
        """
        request.stream = True
        client = await self._get_client()
        payload = self._build_payload(request)

        async with client.stream(
            "POST", "/chat/completions", json=payload
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    chunk = self._parse_chunk(data)
                    if chunk:
                        yield chunk

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        client = await self._get_client()
        response = await client.get("/models")
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
```

### Model Information

```python
@dataclass
class ModelInfo:
    """Information about an OpenRouter model."""
    id: str
    name: str
    description: str
    context_length: int
    pricing: Dict[str, float]  # prompt, completion prices per token
    top_provider: Dict[str, Any]
    architecture: Dict[str, Any]
    capabilities: List[str]  # e.g., ["chat", "tool_use", "vision"]


class ModelRegistry:
    """
    Registry of available models with caching.
    """

    def __init__(self, client: OpenRouterClient):
        self._client = client
        self._models: Dict[str, ModelInfo] = {}
        self._last_refresh: Optional[float] = None
        self._cache_ttl: float = 3600  # 1 hour

    async def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Get model info by ID."""
        await self._ensure_loaded()
        return self._models.get(model_id)

    async def list_models(
        self,
        capability: Optional[str] = None,
        max_price: Optional[float] = None,
    ) -> List[ModelInfo]:
        """List models with optional filtering."""
        await self._ensure_loaded()
        models = list(self._models.values())

        if capability:
            models = [m for m in models if capability in m.capabilities]

        if max_price:
            models = [
                m for m in models
                if m.pricing.get("prompt", 0) <= max_price
            ]

        return models

    async def _ensure_loaded(self) -> None:
        """Ensure models are loaded and fresh."""
        import time
        now = time.time()

        if self._last_refresh and (now - self._last_refresh) < self._cache_ttl:
            return

        models_data = await self._client.list_models()
        self._models = {
            m["id"]: self._parse_model(m) for m in models_data
        }
        self._last_refresh = now
```

### Routing Variants

```python
class RouteVariant(str, Enum):
    """OpenRouter routing variants."""
    DEFAULT = ""
    NITRO = ":nitro"      # Fastest providers
    FLOOR = ":floor"      # Cheapest providers
    ONLINE = ":online"    # Web search enabled
    THINKING = ":thinking"  # Extended reasoning


def apply_variant(model_id: str, variant: RouteVariant) -> str:
    """Apply routing variant to model ID."""
    if variant == RouteVariant.DEFAULT:
        return model_id
    return f"{model_id}{variant.value}"
```

---

## API Endpoints

### Chat Completions
```
POST /api/v1/chat/completions

Request:
{
  "model": "anthropic/claude-3-opus",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false,
  "tools": [...],  // Optional
  "tool_choice": "auto"  // Optional
}

Response:
{
  "id": "gen-xxx",
  "model": "anthropic/claude-3-opus",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 10,
    "total_tokens": 35
  }
}
```

### List Models
```
GET /api/v1/models

Response:
{
  "data": [
    {
      "id": "anthropic/claude-3-opus",
      "name": "Claude 3 Opus",
      "context_length": 200000,
      "pricing": {
        "prompt": "0.000015",
        "completion": "0.000075"
      },
      ...
    }
  ]
}
```

---

## Acceptance Criteria

### Definition of Done

- [ ] OpenRouterClient class implemented
- [ ] Chat completions endpoint working
- [ ] Streaming responses working
- [ ] Tool/function calling working
- [ ] Model listing working
- [ ] Error handling comprehensive
- [ ] Retry logic implemented
- [ ] Token tracking working
- [ ] Cost tracking working
- [ ] All routing variants supported
- [ ] Tests achieve ≥90% coverage

---

## Configuration

```yaml
# .src/forge/settings.yaml
llm:
  provider: openrouter
  api_key: ${OPENROUTER_API_KEY}
  default_model: anthropic/claude-3-opus
  temperature: 0.7
  max_tokens: 4096
  timeout: 120
  max_retries: 3
```

---

## Out of Scope

The following are NOT part of Phase 3.1:
- LangChain integration (Phase 3.2)
- Agent orchestration (Phase 3.2)
- Conversation history management (Phase 5.1)
- Context window management (Phase 5.2)

---

## Notes

OpenRouter provides:
- Access to 400+ models from various providers
- Unified API format (OpenAI-compatible)
- Automatic failover between providers
- Cost optimization through routing variants
- Web search integration (:online variant)
