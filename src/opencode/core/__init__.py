"""Core package containing interfaces, types, and errors."""

from opencode.core.errors import (
    ConfigError,
    OpenCodeError,
    PermissionDeniedError,
    ProviderError,
    SessionError,
    ToolError,
)
from opencode.core.interfaces import (
    IConfigLoader,
    IModelProvider,
    ISessionRepository,
    ITool,
)
from opencode.core.logging import get_logger, setup_logging
from opencode.core.types import (
    AgentId,
    CompletionRequest,
    CompletionResponse,
    Message,
    ModelId,
    ProjectId,
    Session,
    SessionId,
    SessionSummary,
    ToolName,
    ToolParameter,
    ToolResult,
)

__all__ = [
    "AgentId",
    "CompletionRequest",
    "CompletionResponse",
    "ConfigError",
    "IConfigLoader",
    "IModelProvider",
    "ISessionRepository",
    "ITool",
    "Message",
    "ModelId",
    "OpenCodeError",
    "PermissionDeniedError",
    "ProjectId",
    "ProviderError",
    "Session",
    "SessionError",
    "SessionId",
    "SessionSummary",
    "ToolError",
    "ToolName",
    "ToolParameter",
    "ToolResult",
    "get_logger",
    "setup_logging",
]
