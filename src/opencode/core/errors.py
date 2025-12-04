"""Exception hierarchy for OpenCode."""

from __future__ import annotations


class OpenCodeError(Exception):
    """Base exception for all OpenCode errors.

    Provides cause chaining for better error context.
    """

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        """Initialize the error.

        Args:
            message: Human-readable error message.
            cause: Optional underlying exception that caused this error.
        """
        super().__init__(message)
        self.cause = cause

    def __str__(self) -> str:
        """Return string representation with cause if present."""
        if self.cause:
            return f"{self.args[0]} (caused by: {self.cause})"
        return str(self.args[0])


class ConfigError(OpenCodeError):
    """Configuration-related errors."""

    pass


class ToolError(OpenCodeError):
    """Tool execution errors.

    Includes the tool name for better error identification.
    """

    def __init__(
        self, tool_name: str, message: str, cause: Exception | None = None
    ) -> None:
        """Initialize the tool error.

        Args:
            tool_name: Name of the tool that encountered the error.
            message: Human-readable error message.
            cause: Optional underlying exception.
        """
        super().__init__(f"Tool '{tool_name}': {message}", cause)
        self.tool_name = tool_name


class ProviderError(OpenCodeError):
    """Model provider errors.

    Includes the provider name for better error identification.
    """

    def __init__(
        self, provider: str, message: str, cause: Exception | None = None
    ) -> None:
        """Initialize the provider error.

        Args:
            provider: Name of the provider that encountered the error.
            message: Human-readable error message.
            cause: Optional underlying exception.
        """
        super().__init__(f"Provider '{provider}': {message}", cause)
        self.provider = provider


class PermissionDeniedError(OpenCodeError):
    """Permission denied errors.

    Note: Named PermissionDeniedError to avoid shadowing the builtin
    PermissionError exception, which could cause subtle bugs if code
    accidentally catches the wrong exception type.
    """

    def __init__(self, action: str, reason: str) -> None:
        """Initialize the permission denied error.

        Args:
            action: The action that was denied.
            reason: The reason for denial.
        """
        super().__init__(f"Permission denied for '{action}': {reason}")
        self.action = action
        self.reason = reason


class SessionError(OpenCodeError):
    """Session management errors."""

    pass
