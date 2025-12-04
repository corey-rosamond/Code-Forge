"""Tests for exception hierarchy."""

from __future__ import annotations

import pytest

from opencode.core.errors import (
    ConfigError,
    OpenCodeError,
    PermissionDeniedError,
    ProviderError,
    SessionError,
    ToolError,
)


class TestOpenCodeError:
    """Tests for OpenCodeError base exception."""

    def test_create_error_with_message(self) -> None:
        """OpenCodeError should store message."""
        error = OpenCodeError("test error")
        assert str(error) == "test error"

    def test_error_is_catchable_as_exception(self) -> None:
        """OpenCodeError should be catchable as Exception."""
        with pytest.raises(Exception):
            raise OpenCodeError("test")

    def test_error_with_cause(self) -> None:
        """OpenCodeError should chain cause correctly."""
        original = ValueError("original error")
        error = OpenCodeError("wrapper error", cause=original)
        assert error.cause is original
        assert "caused by" in str(error)
        assert "original error" in str(error)

    def test_error_without_cause(self) -> None:
        """OpenCodeError without cause should not show 'caused by'."""
        error = OpenCodeError("simple error")
        assert error.cause is None
        assert "caused by" not in str(error)


class TestConfigError:
    """Tests for ConfigError exception."""

    def test_config_error_inherits_from_opencode_error(self) -> None:
        """ConfigError should be catchable as OpenCodeError."""
        with pytest.raises(OpenCodeError):
            raise ConfigError("config problem")

    def test_config_error_is_catchable_as_exception(self) -> None:
        """ConfigError should be catchable as Exception."""
        with pytest.raises(Exception):
            raise ConfigError("config problem")

    def test_config_error_message(self) -> None:
        """ConfigError should store message correctly."""
        error = ConfigError("missing key")
        assert str(error) == "missing key"


class TestToolError:
    """Tests for ToolError exception."""

    def test_tool_error_includes_tool_name(self) -> None:
        """ToolError should include tool name in message."""
        error = ToolError("Read", "file not found")
        assert error.tool_name == "Read"
        assert "Tool 'Read'" in str(error)
        assert "file not found" in str(error)

    def test_tool_error_is_catchable_as_opencode_error(self) -> None:
        """ToolError should be catchable as OpenCodeError."""
        with pytest.raises(OpenCodeError):
            raise ToolError("Write", "permission denied")

    def test_tool_error_with_cause(self) -> None:
        """ToolError should support cause chaining."""
        original = IOError("disk full")
        error = ToolError("Write", "write failed", cause=original)
        assert error.cause is original
        assert "caused by" in str(error)


class TestProviderError:
    """Tests for ProviderError exception."""

    def test_provider_error_includes_provider_name(self) -> None:
        """ProviderError should include provider name in message."""
        error = ProviderError("openrouter", "rate limited")
        assert error.provider == "openrouter"
        assert "Provider 'openrouter'" in str(error)
        assert "rate limited" in str(error)

    def test_provider_error_is_catchable_as_opencode_error(self) -> None:
        """ProviderError should be catchable as OpenCodeError."""
        with pytest.raises(OpenCodeError):
            raise ProviderError("anthropic", "api error")

    def test_provider_error_with_cause(self) -> None:
        """ProviderError should support cause chaining."""
        original = ConnectionError("timeout")
        error = ProviderError("openai", "connection failed", cause=original)
        assert error.cause is original


class TestPermissionDeniedError:
    """Tests for PermissionDeniedError exception."""

    def test_permission_error_includes_action_and_reason(self) -> None:
        """PermissionDeniedError should include action and reason."""
        error = PermissionDeniedError("file_write", "denied by policy")
        assert error.action == "file_write"
        assert error.reason == "denied by policy"
        assert "file_write" in str(error)
        assert "denied by policy" in str(error)

    def test_permission_error_is_catchable_as_opencode_error(self) -> None:
        """PermissionDeniedError should be catchable as OpenCodeError."""
        with pytest.raises(OpenCodeError):
            raise PermissionDeniedError("execute", "not allowed")

    def test_permission_error_message_format(self) -> None:
        """PermissionDeniedError should have correct message format."""
        error = PermissionDeniedError("delete", "user denied")
        assert str(error) == "Permission denied for 'delete': user denied"


class TestSessionError:
    """Tests for SessionError exception."""

    def test_session_error_inherits_from_opencode_error(self) -> None:
        """SessionError should be catchable as OpenCodeError."""
        with pytest.raises(OpenCodeError):
            raise SessionError("session not found")

    def test_session_error_message(self) -> None:
        """SessionError should store message correctly."""
        error = SessionError("corrupted session data")
        assert str(error) == "corrupted session data"

    def test_session_error_with_cause(self) -> None:
        """SessionError should support cause chaining."""
        original = IOError("file corrupted")
        error = SessionError("failed to load session", cause=original)
        assert error.cause is original
