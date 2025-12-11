"""Abstract base classes defining core interfaces for Code-Forge."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path

    from code_forge.core.types import (
        CompletionRequest,
        CompletionResponse,
        Session,
        SessionId,
        SessionSummary,
        ToolParameter,
        ToolResult,
    )


class ITool(ABC):
    """Abstract base class for all tools.

    Tools are the primary way the agent interacts with the environment.
    Each tool has a name, description, parameters, and execute method.

    McCabe Complexity Target: All methods <= 5
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the tool."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description for the LLM."""
        ...

    @property
    @abstractmethod
    def parameters(self) -> list[ToolParameter]:
        """List of parameters this tool accepts."""
        ...

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters.

        Returns:
            ToolResult with success status and output.
        """
        ...

    def validate_params(self, **kwargs: Any) -> tuple[bool, str | None]:
        """Validate parameters before execution.

        Args:
            **kwargs: Parameters to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                return False, f"Missing required parameter: {param.name}"
        return True, None


class IModelProvider(ABC):
    """Abstract base class for AI model providers.

    Supports both OpenRouter and direct API connections.
    All providers must support streaming.

    McCabe Complexity Target: All methods <= 6
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier."""
        ...

    @property
    @abstractmethod
    def supports_tools(self) -> bool:
        """Whether this provider supports tool/function calling."""
        ...

    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Send completion request and return full response.

        Args:
            request: The completion request.

        Returns:
            Complete response from the model.
        """
        ...

    @abstractmethod
    def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        """Stream completion response token by token.

        Args:
            request: The completion request.

        Yields:
            Individual tokens as they arrive.
        """
        ...

    @abstractmethod
    async def list_models(self) -> list[str]:
        """Return list of available model IDs."""
        ...


class IConfigLoader(ABC):
    """Abstract base class for configuration loaders.

    Supports loading from files, environment, and merging.

    McCabe Complexity Target: All methods <= 5
    """

    @abstractmethod
    def load(self, path: Path) -> dict[str, Any]:
        """Load configuration from a path.

        Args:
            path: Path to configuration file.

        Returns:
            Configuration dictionary.

        Raises:
            ConfigError: If loading fails.
        """
        ...

    @abstractmethod
    def merge(
        self, base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge two configurations with override taking precedence.

        Args:
            base: Base configuration.
            override: Override configuration.

        Returns:
            Merged configuration.
        """
        ...

    @abstractmethod
    def validate(self, config: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate configuration against schema.

        Args:
            config: Configuration to validate.

        Returns:
            Tuple of (is_valid, list_of_errors).
        """
        ...


class ISessionRepository(ABC):
    """Abstract base class for session persistence.

    McCabe Complexity Target: All methods <= 5
    """

    @abstractmethod
    async def save(self, session: Session) -> None:
        """Persist session to storage.

        Args:
            session: The session to save.
        """
        ...

    @abstractmethod
    async def load(self, session_id: SessionId) -> Session | None:
        """Load session by ID.

        Args:
            session_id: The ID of the session to load.

        Returns:
            The session if found, None otherwise.
        """
        ...

    @abstractmethod
    async def list_recent(self, limit: int = 10) -> list[SessionSummary]:
        """List recent sessions with summaries.

        Args:
            limit: Maximum number of sessions to return.

        Returns:
            List of session summaries.
        """
        ...

    @abstractmethod
    async def delete(self, session_id: SessionId) -> bool:
        """Delete session.

        Args:
            session_id: The ID of the session to delete.

        Returns:
            True if deleted, False if not found.
        """
        ...
