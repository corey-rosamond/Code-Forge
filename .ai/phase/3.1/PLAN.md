# Phase 3.1: OpenRouter Client - Implementation Plan

**Phase:** 3.1
**Name:** OpenRouter Client
**Dependencies:** Phase 1.1 (Project Foundation), Phase 1.2 (Configuration)

---

## Overview

Phase 3.1 implements the OpenRouter API client that provides unified access to 400+ AI models. The client handles authentication, streaming, tool calling, and error handling.

---

## Architecture

```
src/forge/llm/
├── __init__.py           # Package exports
├── client.py             # OpenRouterClient
├── models.py             # Data models (Message, Response, etc.)
├── streaming.py          # Streaming response handling
├── errors.py             # LLM-specific errors
└── routing.py            # Model routing and variants
```

---

## Implementation Steps

### Step 1: Create LLM Package and Models

```python
# src/forge/llm/__init__.py
"""LLM client package for Code-Forge."""

from forge.llm.client import OpenRouterClient
from forge.llm.models import (
    Message,
    MessageRole,
    ToolDefinition,
    CompletionRequest,
    CompletionResponse,
    CompletionChoice,
    TokenUsage,
    StreamChunk,
)
from forge.llm.errors import (
    LLMError,
    AuthenticationError,
    RateLimitError,
    ModelNotFoundError,
    ContextLengthError,
    ContentPolicyError,
)
from forge.llm.routing import RouteVariant, apply_variant

__all__ = [
    "OpenRouterClient",
    "Message",
    "MessageRole",
    "ToolDefinition",
    "CompletionRequest",
    "CompletionResponse",
    "CompletionChoice",
    "TokenUsage",
    "StreamChunk",
    "LLMError",
    "AuthenticationError",
    "RateLimitError",
    "ModelNotFoundError",
    "ContextLengthError",
    "ContentPolicyError",
    "RouteVariant",
    "apply_variant",
]
```

### Step 2: Implement Data Models

```python
# src/forge/llm/models.py
"""Data models for LLM interactions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MessageRole(str, Enum):
    """Role of a message in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ContentPart:
    """Part of a multimodal message."""
    type: str  # "text" or "image_url"
    text: Optional[str] = None
    image_url: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API format."""
        if self.type == "text":
            return {"type": "text", "text": self.text}
        else:
            return {"type": "image_url", "image_url": self.image_url}


@dataclass
class ToolCall:
    """A tool call from the assistant."""
    id: str
    type: str  # "function"
    function: Dict[str, Any]  # {"name": str, "arguments": str}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "function": self.function,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        return cls(
            id=data["id"],
            type=data["type"],
            function=data["function"],
        )


@dataclass
class Message:
    """A message in the conversation."""
    role: MessageRole
    content: str | List[ContentPart] | None = None
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API format."""
        msg: Dict[str, Any] = {"role": self.role.value}

        if isinstance(self.content, str):
            msg["content"] = self.content
        elif isinstance(self.content, list):
            msg["content"] = [p.to_dict() for p in self.content]
        elif self.content is None and self.tool_calls:
            msg["content"] = None
        else:
            msg["content"] = self.content

        if self.name:
            msg["name"] = self.name
        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id
        if self.tool_calls:
            msg["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]

        return msg

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create from API response."""
        tool_calls = None
        if "tool_calls" in data and data["tool_calls"]:
            tool_calls = [ToolCall.from_dict(tc) for tc in data["tool_calls"]]

        return cls(
            role=MessageRole(data["role"]),
            content=data.get("content"),
            name=data.get("name"),
            tool_call_id=data.get("tool_call_id"),
            tool_calls=tool_calls,
        )

    @classmethod
    def system(cls, content: str) -> "Message":
        """Create a system message."""
        return cls(role=MessageRole.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str | List[ContentPart]) -> "Message":
        """Create a user message."""
        return cls(role=MessageRole.USER, content=content)

    @classmethod
    def assistant(
        cls,
        content: Optional[str] = None,
        tool_calls: Optional[List[ToolCall]] = None,
    ) -> "Message":
        """Create an assistant message."""
        return cls(role=MessageRole.ASSISTANT, content=content, tool_calls=tool_calls)

    @classmethod
    def tool_result(cls, tool_call_id: str, content: str) -> "Message":
        """Create a tool result message."""
        return cls(
            role=MessageRole.TOOL,
            content=content,
            tool_call_id=tool_call_id,
        )


@dataclass
class ToolDefinition:
    """Definition of a tool for function calling."""
    name: str
    description: str
    parameters: Dict[str, Any]
    type: str = "function"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API format."""
        return {
            "type": self.type,
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class CompletionRequest:
    """Request for chat completion."""
    model: str
    messages: List[Message]
    tools: Optional[List[ToolDefinition]] = None
    tool_choice: Optional[str | Dict[str, Any]] = None
    temperature: float = 1.0
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[List[str]] = None
    stream: bool = False
    # OpenRouter-specific
    transforms: Optional[List[str]] = None
    route: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API payload."""
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [m.to_dict() for m in self.messages],
            "temperature": self.temperature,
            "stream": self.stream,
        }

        if self.tools:
            payload["tools"] = [t.to_dict() for t in self.tools]
        if self.tool_choice:
            payload["tool_choice"] = self.tool_choice
        if self.max_tokens:
            payload["max_tokens"] = self.max_tokens
        if self.top_p != 1.0:
            payload["top_p"] = self.top_p
        if self.frequency_penalty != 0.0:
            payload["frequency_penalty"] = self.frequency_penalty
        if self.presence_penalty != 0.0:
            payload["presence_penalty"] = self.presence_penalty
        if self.stop:
            payload["stop"] = self.stop
        if self.transforms:
            payload["transforms"] = self.transforms
        if self.route:
            payload["route"] = self.route

        return payload


@dataclass
class TokenUsage:
    """Token usage statistics."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenUsage":
        return cls(
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
        )


@dataclass
class CompletionChoice:
    """A completion choice from the response."""
    index: int
    message: Message
    finish_reason: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompletionChoice":
        return cls(
            index=data["index"],
            message=Message.from_dict(data["message"]),
            finish_reason=data.get("finish_reason"),
        )


@dataclass
class CompletionResponse:
    """Response from chat completion."""
    id: str
    model: str
    choices: List[CompletionChoice]
    usage: TokenUsage
    created: int
    provider: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompletionResponse":
        return cls(
            id=data["id"],
            model=data["model"],
            choices=[CompletionChoice.from_dict(c) for c in data["choices"]],
            usage=TokenUsage.from_dict(data.get("usage", {})),
            created=data["created"],
            provider=data.get("provider"),
        )


@dataclass
class StreamDelta:
    """Delta in a streaming chunk."""
    role: Optional[str] = None
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamDelta":
        return cls(
            role=data.get("role"),
            content=data.get("content"),
            tool_calls=data.get("tool_calls"),
        )


@dataclass
class StreamChunk:
    """A chunk from streaming response."""
    id: str
    model: str
    delta: StreamDelta
    index: int
    finish_reason: Optional[str]
    usage: Optional[TokenUsage] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamChunk":
        choice = data["choices"][0] if data.get("choices") else {}
        usage = None
        if "usage" in data and data["usage"]:
            usage = TokenUsage.from_dict(data["usage"])

        return cls(
            id=data["id"],
            model=data["model"],
            delta=StreamDelta.from_dict(choice.get("delta", {})),
            index=choice.get("index", 0),
            finish_reason=choice.get("finish_reason"),
            usage=usage,
        )
```

### Step 3: Implement Error Classes

```python
# src/forge/llm/errors.py
"""LLM-specific error classes."""

from forge.core.errors import forgeError


class LLMError(Code-ForgeError):
    """Base class for LLM errors."""
    pass


class AuthenticationError(LLMError):
    """API key is invalid or missing."""
    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message)


class RateLimitError(LLMError):
    """Rate limit exceeded."""
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: float | None = None,
    ):
        super().__init__(message)
        self.retry_after = retry_after


class ModelNotFoundError(LLMError):
    """Requested model not found."""
    def __init__(self, model_id: str):
        super().__init__(f"Model not found: {model_id}")
        self.model_id = model_id


class ContextLengthError(LLMError):
    """Context length exceeded."""
    def __init__(
        self,
        message: str = "Context length exceeded",
        max_tokens: int | None = None,
        requested_tokens: int | None = None,
    ):
        super().__init__(message)
        self.max_tokens = max_tokens
        self.requested_tokens = requested_tokens


class ContentPolicyError(LLMError):
    """Content violates policy."""
    def __init__(self, message: str = "Content violates policy"):
        super().__init__(message)


class ProviderError(LLMError):
    """Error from upstream provider."""
    def __init__(self, message: str, provider: str | None = None):
        super().__init__(message)
        self.provider = provider
```

### Step 4: Implement Routing

```python
# src/forge/llm/routing.py
"""Model routing and variants for OpenRouter."""

from enum import Enum
from typing import Optional


class RouteVariant(str, Enum):
    """OpenRouter routing variants."""
    DEFAULT = ""
    NITRO = ":nitro"       # Fastest providers
    FLOOR = ":floor"       # Cheapest providers
    ONLINE = ":online"     # Web search enabled
    THINKING = ":thinking"  # Extended reasoning (Claude)


def apply_variant(model_id: str, variant: RouteVariant) -> str:
    """
    Apply routing variant to model ID.

    Args:
        model_id: Base model ID (e.g., "anthropic/claude-3-opus")
        variant: Routing variant to apply

    Returns:
        Model ID with variant suffix

    Example:
        apply_variant("anthropic/claude-3-opus", RouteVariant.NITRO)
        # Returns: "anthropic/claude-3-opus:nitro"
    """
    if variant == RouteVariant.DEFAULT or not variant.value:
        return model_id
    return f"{model_id}{variant.value}"


def parse_model_id(model_id: str) -> tuple[str, Optional[RouteVariant]]:
    """
    Parse model ID to extract base model and variant.

    Args:
        model_id: Model ID potentially with variant

    Returns:
        Tuple of (base_model_id, variant or None)

    Example:
        parse_model_id("anthropic/claude-3-opus:nitro")
        # Returns: ("anthropic/claude-3-opus", RouteVariant.NITRO)
    """
    for variant in RouteVariant:
        if variant.value and model_id.endswith(variant.value):
            base = model_id[: -len(variant.value)]
            return base, variant
    return model_id, None


# Common model aliases
MODEL_ALIASES = {
    "claude-3-opus": "anthropic/claude-3-opus",
    "claude-3-sonnet": "anthropic/claude-3-sonnet",
    "claude-3-haiku": "anthropic/claude-3-haiku",
    "gpt-4": "openai/gpt-4",
    "gpt-4-turbo": "openai/gpt-4-turbo",
    "gpt-4o": "openai/gpt-4o",
    "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
    "gemini-pro": "google/gemini-pro",
    "gemini-ultra": "google/gemini-ultra",
    "llama-3-70b": "meta-llama/llama-3-70b-instruct",
    "mixtral-8x7b": "mistralai/mixtral-8x7b-instruct",
}


def resolve_model_alias(model_id: str) -> str:
    """Resolve model alias to full model ID.

    Args:
        model_id: Model ID or alias to resolve.

    Returns:
        Full model ID.

    Raises:
        ValueError: If model_id is empty or None.
    """
    if not model_id or not model_id.strip():
        raise ValueError("model_id cannot be empty or None")
    return MODEL_ALIASES.get(model_id, model_id)
```

### Step 5: Implement OpenRouter Client

```python
# src/forge/llm/client.py
"""OpenRouter API client."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from forge.core.logging import get_logger
from forge.llm.models import (
    CompletionRequest,
    CompletionResponse,
    StreamChunk,
    TokenUsage,
)
from forge.llm.errors import (
    LLMError,
    AuthenticationError,
    RateLimitError,
    ModelNotFoundError,
    ContextLengthError,
    ContentPolicyError,
    ProviderError,
)
from forge.llm.routing import resolve_model_alias

logger = get_logger("llm")


class OpenRouterClient:
    """
    Client for the OpenRouter API.

    Provides unified access to 400+ AI models through OpenRouter's
    OpenAI-compatible API interface.

    IMPORTANT: This client manages HTTP connections that must be closed.
    Always use as an async context manager or call close() explicitly:

        # Recommended: async context manager
        async with OpenRouterClient(api_key) as client:
            response = await client.complete(request)

        # Alternative: explicit close
        client = OpenRouterClient(api_key)
        try:
            response = await client.complete(request)
        finally:
            await client.close()
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    # Track all active clients for cleanup at exit
    _active_clients: "weakref.WeakSet[OpenRouterClient]" = None

    @classmethod
    def _get_active_clients(cls) -> "weakref.WeakSet[OpenRouterClient]":
        """Get or create the weak set of active clients."""
        if cls._active_clients is None:
            import weakref
            cls._active_clients = weakref.WeakSet()
        return cls._active_clients

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        app_name: str = "Code-Forge",
        app_url: str = "https://github.com/forge",
        timeout: float = 120.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
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
            retry_delay: Initial delay between retries
        """
        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL
        self.app_name = app_name
        self.app_url = app_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self._client: Optional[httpx.AsyncClient] = None
        self._closed = False

        # Usage tracking
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._total_requests = 0

        # Register for tracking
        self._get_active_clients().add(self)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._get_headers(),
                timeout=httpx.Timeout(self.timeout),
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

        Raises:
            LLMError: On API errors
        """
        # Resolve model alias
        request.model = resolve_model_alias(request.model)
        request.stream = False

        client = await self._get_client()
        payload = request.to_dict()

        logger.debug(f"Completion request: model={request.model}")

        response_data = await self._make_request(
            client, "POST", "/chat/completions", payload
        )

        response = CompletionResponse.from_dict(response_data)

        # Track usage
        self._total_prompt_tokens += response.usage.prompt_tokens
        self._total_completion_tokens += response.usage.completion_tokens
        self._total_requests += 1

        logger.debug(
            f"Completion response: tokens={response.usage.total_tokens}"
        )

        return response

    async def stream(
        self, request: CompletionRequest
    ) -> AsyncIterator[StreamChunk]:
        """
        Send a streaming chat completion request.

        Args:
            request: The completion request

        Yields:
            StreamChunk for each piece of the response

        Raises:
            LLMError: On API errors
        """
        # Resolve model alias
        request.model = resolve_model_alias(request.model)
        request.stream = True

        client = await self._get_client()
        payload = request.to_dict()

        logger.debug(f"Streaming request: model={request.model}")

        async with client.stream(
            "POST", "/chat/completions", json=payload
        ) as response:
            await self._check_response(response)

            async for line in response.aiter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk_data = json.loads(data)
                        chunk = StreamChunk.from_dict(chunk_data)

                        # Track final usage
                        if chunk.usage:
                            self._total_prompt_tokens += chunk.usage.prompt_tokens
                            self._total_completion_tokens += chunk.usage.completion_tokens
                            self._total_requests += 1

                        yield chunk
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse chunk: {data}")

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models.

        Returns:
            List of model information dicts
        """
        client = await self._get_client()
        response = await client.get("/models")
        await self._check_response(response)
        data = response.json()
        return data.get("data", [])

    async def _make_request(
        self,
        client: httpx.AsyncClient,
        method: str,
        path: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Make a request with retry logic.

        Args:
            client: HTTP client
            method: HTTP method
            path: API path
            payload: Request payload

        Returns:
            Response JSON data

        Raises:
            LLMError: On unrecoverable errors
        """
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                response = await client.request(method, path, json=payload)
                await self._check_response(response)
                return response.json()

            except RateLimitError as e:
                last_error = e
                wait_time = e.retry_after or (self.retry_delay * (2 ** attempt))
                logger.warning(
                    f"Rate limited, retrying in {wait_time}s "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                await asyncio.sleep(wait_time)

            except httpx.TimeoutException as e:
                last_error = LLMError(f"Request timeout: {str(e)}")
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(
                    f"Timeout, retrying in {wait_time}s "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                await asyncio.sleep(wait_time)

            except httpx.HTTPError as e:
                last_error = LLMError(f"HTTP error: {str(e)}")
                break

        raise last_error or LLMError("Request failed after retries")

    async def _check_response(
        self, response: httpx.Response
    ) -> None:
        """
        Check response for errors.

        Args:
            response: HTTP response

        Raises:
            Appropriate LLMError subclass
        """
        if response.is_success:
            return

        try:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", str(response.text))
            error_code = error_data.get("error", {}).get("code", "")
        except json.JSONDecodeError:
            error_msg = response.text
            error_code = ""

        status = response.status_code

        if status == 401:
            raise AuthenticationError(error_msg)
        elif status == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                error_msg,
                retry_after=float(retry_after) if retry_after else None,
            )
        elif status == 404:
            raise ModelNotFoundError(error_msg)
        elif status == 400 and "context" in error_msg.lower():
            raise ContextLengthError(error_msg)
        elif status == 400 and "content" in error_msg.lower():
            raise ContentPolicyError(error_msg)
        else:
            raise ProviderError(error_msg)

    def get_usage(self) -> TokenUsage:
        """Get cumulative token usage."""
        return TokenUsage(
            prompt_tokens=self._total_prompt_tokens,
            completion_tokens=self._total_completion_tokens,
            total_tokens=self._total_prompt_tokens + self._total_completion_tokens,
        )

    def reset_usage(self) -> None:
        """Reset usage counters."""
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._total_requests = 0

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._closed:
            await self._client.aclose()
            self._client = None
        self._closed = True

    async def __aenter__(self) -> "OpenRouterClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args) -> None:
        """Async context manager exit."""
        await self.close()

    def __del__(self) -> None:
        """Destructor: warn if client wasn't closed properly.

        Note: We can't await close() in __del__, so we just log a warning.
        Users should use the async context manager or call close() explicitly.
        """
        if not self._closed and self._client is not None and not self._client.is_closed:
            import warnings
            warnings.warn(
                f"OpenRouterClient was not closed properly. "
                f"Use 'async with' or call 'await client.close()' explicitly.",
                ResourceWarning,
                stacklevel=2,
            )
```

### Step 6: Create Streaming Helper

```python
# src/forge/llm/streaming.py
"""Streaming response utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from forge.llm.models import (
    Message,
    MessageRole,
    StreamChunk,
    StreamDelta,
    ToolCall,
    TokenUsage,
)


@dataclass
class StreamCollector:
    """
    Collects streaming chunks into a complete response.

    Usage:
        collector = StreamCollector()
        async for chunk in client.stream(request):
            collector.add_chunk(chunk)
            print(collector.content, end="", flush=True)
        message = collector.get_message()
    """
    content: str = ""
    tool_calls: List[dict] = field(default_factory=list)
    usage: Optional[TokenUsage] = None
    model: str = ""
    finish_reason: Optional[str] = None
    _tool_call_index: int = -1

    def add_chunk(self, chunk: StreamChunk) -> Optional[str]:
        """
        Add a chunk and return new content if any.

        Args:
            chunk: Streaming chunk

        Returns:
            New content text, or None if no new content
        """
        self.model = chunk.model

        if chunk.finish_reason:
            self.finish_reason = chunk.finish_reason

        if chunk.usage:
            self.usage = chunk.usage

        delta = chunk.delta
        new_content = None

        # Handle content
        if delta.content:
            self.content += delta.content
            new_content = delta.content

        # Handle tool calls
        if delta.tool_calls:
            for tc in delta.tool_calls:
                index = tc.get("index", 0)

                if index > self._tool_call_index:
                    # New tool call
                    self._tool_call_index = index
                    self.tool_calls.append({
                        "id": tc.get("id", ""),
                        "type": tc.get("type", "function"),
                        "function": {
                            "name": tc.get("function", {}).get("name", ""),
                            "arguments": tc.get("function", {}).get("arguments", ""),
                        },
                    })
                else:
                    # Continue existing tool call
                    if self.tool_calls:
                        current = self.tool_calls[-1]
                        func = tc.get("function", {})
                        if "arguments" in func:
                            current["function"]["arguments"] += func["arguments"]

        return new_content

    def get_message(self) -> Message:
        """
        Get the complete message.

        Returns:
            Complete Message object
        """
        tool_calls = None
        if self.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc["id"],
                    type=tc["type"],
                    function=tc["function"],
                )
                for tc in self.tool_calls
            ]

        return Message(
            role=MessageRole.ASSISTANT,
            content=self.content if self.content else None,
            tool_calls=tool_calls,
        )

    @property
    def is_complete(self) -> bool:
        """Check if streaming is complete."""
        return self.finish_reason is not None
```

---

## Testing Strategy

### Unit Tests

1. **Models Tests**
   - Message serialization/deserialization
   - Tool call handling
   - Multimodal content
   - Request building

2. **Client Tests**
   - Successful completion
   - Streaming completion
   - Error handling (401, 429, 404, etc.)
   - Retry logic
   - Timeout handling

3. **Routing Tests**
   - Variant application
   - Model alias resolution
   - Model ID parsing

4. **Streaming Tests**
   - Chunk collection
   - Tool call assembly
   - Content accumulation

### Integration Tests (with mocked API)

1. Full completion flow
2. Streaming with tool calls
3. Error recovery
4. Usage tracking

---

## Dependencies

```toml
[tool.poetry.dependencies]
httpx = "^0.27"
```

---

## Security Considerations

1. **API Key Protection**: Never log API keys
2. **Error Messages**: Sanitize before displaying
3. **HTTPS Only**: Enforce TLS
4. **Timeout Protection**: Prevent hanging requests
