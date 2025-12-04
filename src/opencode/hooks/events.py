"""Hook event types and data structures."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """
    Hook event types.

    Events are organized by category:
    - tool: Tool execution lifecycle
    - llm: LLM API interaction lifecycle
    - session: Session management lifecycle
    - permission: Permission system events
    - user: User interaction events
    """

    # Tool events
    TOOL_PRE_EXECUTE = "tool:pre_execute"
    TOOL_POST_EXECUTE = "tool:post_execute"
    TOOL_ERROR = "tool:error"

    # LLM events
    LLM_PRE_REQUEST = "llm:pre_request"
    LLM_POST_RESPONSE = "llm:post_response"
    LLM_STREAM_START = "llm:stream_start"
    LLM_STREAM_END = "llm:stream_end"

    # Session events
    SESSION_START = "session:start"
    SESSION_END = "session:end"
    SESSION_MESSAGE = "session:message"

    # Permission events
    PERMISSION_CHECK = "permission:check"
    PERMISSION_PROMPT = "permission:prompt"
    PERMISSION_GRANTED = "permission:granted"
    PERMISSION_DENIED = "permission:denied"

    # User events
    USER_PROMPT_SUBMIT = "user:prompt_submit"
    USER_INTERRUPT = "user:interrupt"


@dataclass
class HookEvent:
    """
    Event data passed to hooks.

    Contains all information about an event that hooks can use
    to decide whether to act and what action to take.

    Attributes:
        type: The event type
        timestamp: Unix timestamp when event occurred
        data: Additional event-specific data
        tool_name: Tool name for tool events
        session_id: Current session ID
    """

    type: EventType
    timestamp: float = field(default_factory=time.time)
    data: dict[str, Any] = field(default_factory=dict)
    tool_name: str | None = None
    session_id: str | None = None

    @staticmethod
    def _sanitize_env_value(value: str) -> str:
        """Sanitize a value for safe use in environment variables.

        Removes or escapes characters that could cause shell injection
        when environment variables are used in shell commands.

        Args:
            value: The raw value to sanitize.

        Returns:
            Sanitized string safe for environment variable use.
        """
        # Remove null bytes (can truncate env vars)
        value = value.replace("\x00", "")
        # Remove newlines (can break env var parsing)
        value = value.replace("\n", " ").replace("\r", "")
        # Limit length to prevent DoS via huge env vars
        max_len = 8192
        if len(value) > max_len:
            value = value[:max_len] + "...[truncated]"
        return value

    def to_env(self) -> dict[str, str]:
        """
        Convert event to environment variables for hook execution.

        All values are sanitized to prevent shell injection attacks
        when hooks use these variables in shell commands.

        Returns:
            Dictionary of environment variable name -> value
        """
        env: dict[str, str] = {
            "OPENCODE_EVENT": self._sanitize_env_value(self.type.value),
            "OPENCODE_TIMESTAMP": str(self.timestamp),
        }

        if self.session_id:
            env["OPENCODE_SESSION_ID"] = self._sanitize_env_value(self.session_id)

        if self.tool_name:
            env["OPENCODE_TOOL_NAME"] = self._sanitize_env_value(self.tool_name)

        # Add specific data fields as environment variables
        for key, value in self.data.items():
            # Sanitize key to valid env var name (alphanumeric + underscore)
            safe_key = "".join(
                c if c.isalnum() or c == "_" else "_" for c in key.upper()
            )
            env_key = f"OPENCODE_{safe_key}"

            if isinstance(value, (dict, list)):
                env[env_key] = self._sanitize_env_value(json.dumps(value))
            else:
                env[env_key] = self._sanitize_env_value(str(value))

        return env

    def to_json(self) -> str:
        """
        Serialize event to JSON string.

        Returns:
            JSON representation of the event
        """
        return json.dumps(
            {
                "type": self.type.value,
                "timestamp": self.timestamp,
                "data": self.data,
                "tool_name": self.tool_name,
                "session_id": self.session_id,
            }
        )

    @classmethod
    def tool_pre_execute(
        cls,
        tool_name: str,
        arguments: dict[str, Any],
        session_id: str | None = None,
    ) -> HookEvent:
        """Create a tool pre-execute event."""
        return cls(
            type=EventType.TOOL_PRE_EXECUTE,
            tool_name=tool_name,
            session_id=session_id,
            data={
                "tool_args": arguments,
            },
        )

    @classmethod
    def tool_post_execute(
        cls,
        tool_name: str,
        arguments: dict[str, Any],
        result: dict[str, Any],
        session_id: str | None = None,
    ) -> HookEvent:
        """Create a tool post-execute event."""
        return cls(
            type=EventType.TOOL_POST_EXECUTE,
            tool_name=tool_name,
            session_id=session_id,
            data={
                "tool_args": arguments,
                "tool_result": result,
            },
        )

    @classmethod
    def tool_error(
        cls,
        tool_name: str,
        arguments: dict[str, Any],
        error: str,
        session_id: str | None = None,
    ) -> HookEvent:
        """Create a tool error event."""
        return cls(
            type=EventType.TOOL_ERROR,
            tool_name=tool_name,
            session_id=session_id,
            data={
                "tool_args": arguments,
                "error": error,
            },
        )

    @classmethod
    def llm_pre_request(
        cls,
        model: str,
        message_count: int,
        session_id: str | None = None,
    ) -> HookEvent:
        """Create an LLM pre-request event."""
        return cls(
            type=EventType.LLM_PRE_REQUEST,
            session_id=session_id,
            data={
                "llm_model": model,
                "message_count": message_count,
            },
        )

    @classmethod
    def llm_post_response(
        cls,
        model: str,
        tokens: int,
        session_id: str | None = None,
    ) -> HookEvent:
        """Create an LLM post-response event."""
        return cls(
            type=EventType.LLM_POST_RESPONSE,
            session_id=session_id,
            data={
                "llm_model": model,
                "llm_tokens": tokens,
            },
        )

    @classmethod
    def llm_stream_start(
        cls,
        model: str,
        session_id: str | None = None,
    ) -> HookEvent:
        """Create an LLM stream start event."""
        return cls(
            type=EventType.LLM_STREAM_START,
            session_id=session_id,
            data={
                "llm_model": model,
            },
        )

    @classmethod
    def llm_stream_end(
        cls,
        model: str,
        tokens: int,
        session_id: str | None = None,
    ) -> HookEvent:
        """Create an LLM stream end event."""
        return cls(
            type=EventType.LLM_STREAM_END,
            session_id=session_id,
            data={
                "llm_model": model,
                "llm_tokens": tokens,
            },
        )

    @classmethod
    def session_start(cls, session_id: str) -> HookEvent:
        """Create a session start event."""
        return cls(
            type=EventType.SESSION_START,
            session_id=session_id,
        )

    @classmethod
    def session_end(cls, session_id: str) -> HookEvent:
        """Create a session end event."""
        return cls(
            type=EventType.SESSION_END,
            session_id=session_id,
        )

    @classmethod
    def session_message(
        cls,
        session_id: str,
        role: str,
        content: str,
    ) -> HookEvent:
        """Create a session message event."""
        return cls(
            type=EventType.SESSION_MESSAGE,
            session_id=session_id,
            data={
                "message_role": role,
                "message_content": content,
            },
        )

    @classmethod
    def permission_check(
        cls,
        tool_name: str,
        level: str,
        rule: str | None = None,
        session_id: str | None = None,
    ) -> HookEvent:
        """Create a permission check event."""
        return cls(
            type=EventType.PERMISSION_CHECK,
            tool_name=tool_name,
            session_id=session_id,
            data={
                "perm_level": level,
                "perm_rule": rule or "",
            },
        )

    @classmethod
    def permission_prompt(
        cls,
        tool_name: str,
        level: str,
        session_id: str | None = None,
    ) -> HookEvent:
        """Create a permission prompt event."""
        return cls(
            type=EventType.PERMISSION_PROMPT,
            tool_name=tool_name,
            session_id=session_id,
            data={
                "perm_level": level,
            },
        )

    @classmethod
    def permission_granted(
        cls,
        tool_name: str,
        session_id: str | None = None,
    ) -> HookEvent:
        """Create a permission granted event."""
        return cls(
            type=EventType.PERMISSION_GRANTED,
            tool_name=tool_name,
            session_id=session_id,
        )

    @classmethod
    def permission_denied(
        cls,
        tool_name: str,
        session_id: str | None = None,
    ) -> HookEvent:
        """Create a permission denied event."""
        return cls(
            type=EventType.PERMISSION_DENIED,
            tool_name=tool_name,
            session_id=session_id,
        )

    @classmethod
    def user_prompt_submit(
        cls,
        content: str,
        session_id: str | None = None,
    ) -> HookEvent:
        """Create a user prompt submit event."""
        return cls(
            type=EventType.USER_PROMPT_SUBMIT,
            session_id=session_id,
            data={
                "user_input": content,
            },
        )

    @classmethod
    def user_interrupt(
        cls,
        session_id: str | None = None,
    ) -> HookEvent:
        """Create a user interrupt event."""
        return cls(
            type=EventType.USER_INTERRUPT,
            session_id=session_id,
        )
