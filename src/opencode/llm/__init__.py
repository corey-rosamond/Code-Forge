"""LLM client package for OpenCode."""

from opencode.llm.client import OpenRouterClient
from opencode.llm.errors import (
    AuthenticationError,
    ContentPolicyError,
    ContextLengthError,
    LLMError,
    ModelNotFoundError,
    ProviderError,
    RateLimitError,
)
from opencode.llm.models import (
    CompletionChoice,
    CompletionRequest,
    CompletionResponse,
    ContentPart,
    Message,
    MessageRole,
    StreamChunk,
    StreamDelta,
    TokenUsage,
    ToolCall,
    ToolDefinition,
)
from opencode.llm.routing import MODEL_ALIASES, RouteVariant, apply_variant
from opencode.llm.streaming import StreamCollector

__all__ = [
    "MODEL_ALIASES",
    "AuthenticationError",
    "CompletionChoice",
    "CompletionRequest",
    "CompletionResponse",
    "ContentPart",
    "ContentPolicyError",
    "ContextLengthError",
    "LLMError",
    "Message",
    "MessageRole",
    "ModelNotFoundError",
    "OpenRouterClient",
    "ProviderError",
    "RateLimitError",
    "RouteVariant",
    "StreamChunk",
    "StreamCollector",
    "StreamDelta",
    "TokenUsage",
    "ToolCall",
    "ToolDefinition",
    "apply_variant",
]
