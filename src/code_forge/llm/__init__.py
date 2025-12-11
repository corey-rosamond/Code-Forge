"""LLM client package for Code-Forge."""

from code_forge.llm.client import OpenRouterClient
from code_forge.llm.errors import (
    AuthenticationError,
    ContentPolicyError,
    ContextLengthError,
    LLMError,
    ModelNotFoundError,
    ProviderError,
    RateLimitError,
)
from code_forge.llm.models import (
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
from code_forge.llm.routing import MODEL_ALIASES, RouteVariant, apply_variant
from code_forge.llm.streaming import StreamCollector

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
