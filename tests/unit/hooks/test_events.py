"""Tests for hook events."""

from __future__ import annotations

import json
import time

import pytest

from opencode.hooks.events import EventType, HookEvent


class TestEventType:
    """Tests for EventType enum."""

    def test_tool_events_defined(self) -> None:
        """Tool event types are defined."""
        assert EventType.TOOL_PRE_EXECUTE.value == "tool:pre_execute"
        assert EventType.TOOL_POST_EXECUTE.value == "tool:post_execute"
        assert EventType.TOOL_ERROR.value == "tool:error"

    def test_llm_events_defined(self) -> None:
        """LLM event types are defined."""
        assert EventType.LLM_PRE_REQUEST.value == "llm:pre_request"
        assert EventType.LLM_POST_RESPONSE.value == "llm:post_response"
        assert EventType.LLM_STREAM_START.value == "llm:stream_start"
        assert EventType.LLM_STREAM_END.value == "llm:stream_end"

    def test_session_events_defined(self) -> None:
        """Session event types are defined."""
        assert EventType.SESSION_START.value == "session:start"
        assert EventType.SESSION_END.value == "session:end"
        assert EventType.SESSION_MESSAGE.value == "session:message"

    def test_permission_events_defined(self) -> None:
        """Permission event types are defined."""
        assert EventType.PERMISSION_CHECK.value == "permission:check"
        assert EventType.PERMISSION_PROMPT.value == "permission:prompt"
        assert EventType.PERMISSION_GRANTED.value == "permission:granted"
        assert EventType.PERMISSION_DENIED.value == "permission:denied"

    def test_user_events_defined(self) -> None:
        """User event types are defined."""
        assert EventType.USER_PROMPT_SUBMIT.value == "user:prompt_submit"
        assert EventType.USER_INTERRUPT.value == "user:interrupt"

    def test_event_type_is_string_enum(self) -> None:
        """EventType inherits from str."""
        assert isinstance(EventType.TOOL_PRE_EXECUTE, str)
        assert EventType.TOOL_PRE_EXECUTE == "tool:pre_execute"


class TestHookEvent:
    """Tests for HookEvent dataclass."""

    def test_creation_with_type(self) -> None:
        """Create event with type only."""
        event = HookEvent(type=EventType.TOOL_PRE_EXECUTE)
        assert event.type == EventType.TOOL_PRE_EXECUTE
        assert event.timestamp > 0
        assert event.data == {}
        assert event.tool_name is None
        assert event.session_id is None

    def test_creation_with_all_fields(self) -> None:
        """Create event with all fields."""
        ts = time.time()
        event = HookEvent(
            type=EventType.TOOL_PRE_EXECUTE,
            timestamp=ts,
            data={"key": "value"},
            tool_name="bash",
            session_id="sess_123",
        )
        assert event.type == EventType.TOOL_PRE_EXECUTE
        assert event.timestamp == ts
        assert event.data == {"key": "value"}
        assert event.tool_name == "bash"
        assert event.session_id == "sess_123"

    def test_timestamp_auto_generated(self) -> None:
        """Timestamp is auto-generated if not provided."""
        before = time.time()
        event = HookEvent(type=EventType.SESSION_START)
        after = time.time()
        assert before <= event.timestamp <= after


class TestHookEventToEnv:
    """Tests for HookEvent.to_env() method."""

    def test_basic_env_vars(self) -> None:
        """Basic environment variables are set."""
        event = HookEvent(
            type=EventType.TOOL_PRE_EXECUTE,
            timestamp=1234567890.123,
        )
        env = event.to_env()
        assert env["OPENCODE_EVENT"] == "tool:pre_execute"
        assert env["OPENCODE_TIMESTAMP"] == "1234567890.123"

    def test_session_id_env_var(self) -> None:
        """Session ID is included when present."""
        event = HookEvent(
            type=EventType.SESSION_START,
            session_id="sess_abc123",
        )
        env = event.to_env()
        assert env["OPENCODE_SESSION_ID"] == "sess_abc123"

    def test_tool_name_env_var(self) -> None:
        """Tool name is included when present."""
        event = HookEvent(
            type=EventType.TOOL_PRE_EXECUTE,
            tool_name="bash",
        )
        env = event.to_env()
        assert env["OPENCODE_TOOL_NAME"] == "bash"

    def test_data_as_env_vars(self) -> None:
        """Data fields are converted to env vars."""
        event = HookEvent(
            type=EventType.TOOL_PRE_EXECUTE,
            data={
                "tool_args": {"command": "ls"},
                "simple_value": "hello",
            },
        )
        env = event.to_env()
        assert "OPENCODE_TOOL_ARGS" in env
        assert json.loads(env["OPENCODE_TOOL_ARGS"]) == {"command": "ls"}
        assert env["OPENCODE_SIMPLE_VALUE"] == "hello"

    def test_sanitizes_null_bytes(self) -> None:
        """Null bytes are removed from values."""
        event = HookEvent(
            type=EventType.USER_PROMPT_SUBMIT,
            data={"user_input": "hello\x00world"},
        )
        env = event.to_env()
        assert "\x00" not in env["OPENCODE_USER_INPUT"]
        assert env["OPENCODE_USER_INPUT"] == "helloworld"

    def test_sanitizes_newlines(self) -> None:
        """Newlines are replaced with spaces."""
        event = HookEvent(
            type=EventType.USER_PROMPT_SUBMIT,
            data={"user_input": "hello\nworld"},
        )
        env = event.to_env()
        assert "\n" not in env["OPENCODE_USER_INPUT"]
        assert env["OPENCODE_USER_INPUT"] == "hello world"

    def test_truncates_long_values(self) -> None:
        """Long values are truncated."""
        long_value = "x" * 10000
        event = HookEvent(
            type=EventType.USER_PROMPT_SUBMIT,
            data={"user_input": long_value},
        )
        env = event.to_env()
        assert len(env["OPENCODE_USER_INPUT"]) <= 8192 + 20  # truncation marker

    def test_sanitizes_key_names(self) -> None:
        """Key names are sanitized for env var use."""
        event = HookEvent(
            type=EventType.TOOL_PRE_EXECUTE,
            data={"tool-args": "value", "with spaces": "other"},
        )
        env = event.to_env()
        assert "OPENCODE_TOOL_ARGS" in env
        assert "OPENCODE_WITH_SPACES" in env


class TestHookEventToJson:
    """Tests for HookEvent.to_json() method."""

    def test_basic_json(self) -> None:
        """Event serializes to valid JSON."""
        event = HookEvent(
            type=EventType.TOOL_PRE_EXECUTE,
            timestamp=1234567890.123,
        )
        json_str = event.to_json()
        data = json.loads(json_str)
        assert data["type"] == "tool:pre_execute"
        assert data["timestamp"] == 1234567890.123
        assert data["data"] == {}
        assert data["tool_name"] is None
        assert data["session_id"] is None

    def test_full_json(self) -> None:
        """All fields are included in JSON."""
        event = HookEvent(
            type=EventType.TOOL_PRE_EXECUTE,
            timestamp=1234567890.123,
            data={"key": "value"},
            tool_name="bash",
            session_id="sess_123",
        )
        json_str = event.to_json()
        data = json.loads(json_str)
        assert data["type"] == "tool:pre_execute"
        assert data["data"] == {"key": "value"}
        assert data["tool_name"] == "bash"
        assert data["session_id"] == "sess_123"


class TestHookEventFactoryMethods:
    """Tests for HookEvent factory methods."""

    def test_tool_pre_execute(self) -> None:
        """tool_pre_execute creates correct event."""
        event = HookEvent.tool_pre_execute(
            tool_name="bash",
            arguments={"command": "ls"},
            session_id="sess_123",
        )
        assert event.type == EventType.TOOL_PRE_EXECUTE
        assert event.tool_name == "bash"
        assert event.session_id == "sess_123"
        assert event.data["tool_args"] == {"command": "ls"}

    def test_tool_post_execute(self) -> None:
        """tool_post_execute creates correct event."""
        event = HookEvent.tool_post_execute(
            tool_name="bash",
            arguments={"command": "ls"},
            result={"success": True},
            session_id="sess_123",
        )
        assert event.type == EventType.TOOL_POST_EXECUTE
        assert event.tool_name == "bash"
        assert event.data["tool_args"] == {"command": "ls"}
        assert event.data["tool_result"] == {"success": True}

    def test_tool_error(self) -> None:
        """tool_error creates correct event."""
        event = HookEvent.tool_error(
            tool_name="bash",
            arguments={"command": "fail"},
            error="Command failed",
            session_id="sess_123",
        )
        assert event.type == EventType.TOOL_ERROR
        assert event.tool_name == "bash"
        assert event.data["error"] == "Command failed"

    def test_llm_pre_request(self) -> None:
        """llm_pre_request creates correct event."""
        event = HookEvent.llm_pre_request(
            model="anthropic/claude-3",
            message_count=5,
            session_id="sess_123",
        )
        assert event.type == EventType.LLM_PRE_REQUEST
        assert event.data["llm_model"] == "anthropic/claude-3"
        assert event.data["message_count"] == 5

    def test_llm_post_response(self) -> None:
        """llm_post_response creates correct event."""
        event = HookEvent.llm_post_response(
            model="anthropic/claude-3",
            tokens=1500,
            session_id="sess_123",
        )
        assert event.type == EventType.LLM_POST_RESPONSE
        assert event.data["llm_model"] == "anthropic/claude-3"
        assert event.data["llm_tokens"] == 1500

    def test_llm_stream_start(self) -> None:
        """llm_stream_start creates correct event."""
        event = HookEvent.llm_stream_start(
            model="anthropic/claude-3",
            session_id="sess_123",
        )
        assert event.type == EventType.LLM_STREAM_START
        assert event.data["llm_model"] == "anthropic/claude-3"

    def test_llm_stream_end(self) -> None:
        """llm_stream_end creates correct event."""
        event = HookEvent.llm_stream_end(
            model="anthropic/claude-3",
            tokens=1500,
            session_id="sess_123",
        )
        assert event.type == EventType.LLM_STREAM_END
        assert event.data["llm_tokens"] == 1500

    def test_session_start(self) -> None:
        """session_start creates correct event."""
        event = HookEvent.session_start(session_id="sess_123")
        assert event.type == EventType.SESSION_START
        assert event.session_id == "sess_123"

    def test_session_end(self) -> None:
        """session_end creates correct event."""
        event = HookEvent.session_end(session_id="sess_123")
        assert event.type == EventType.SESSION_END
        assert event.session_id == "sess_123"

    def test_session_message(self) -> None:
        """session_message creates correct event."""
        event = HookEvent.session_message(
            session_id="sess_123",
            role="user",
            content="Hello",
        )
        assert event.type == EventType.SESSION_MESSAGE
        assert event.data["message_role"] == "user"
        assert event.data["message_content"] == "Hello"

    def test_permission_check(self) -> None:
        """permission_check creates correct event."""
        event = HookEvent.permission_check(
            tool_name="bash",
            level="ask",
            rule="tool:bash",
            session_id="sess_123",
        )
        assert event.type == EventType.PERMISSION_CHECK
        assert event.tool_name == "bash"
        assert event.data["perm_level"] == "ask"
        assert event.data["perm_rule"] == "tool:bash"

    def test_permission_check_no_rule(self) -> None:
        """permission_check handles missing rule."""
        event = HookEvent.permission_check(
            tool_name="bash",
            level="ask",
        )
        assert event.data["perm_rule"] == ""

    def test_permission_prompt(self) -> None:
        """permission_prompt creates correct event."""
        event = HookEvent.permission_prompt(
            tool_name="bash",
            level="ask",
            session_id="sess_123",
        )
        assert event.type == EventType.PERMISSION_PROMPT
        assert event.data["perm_level"] == "ask"

    def test_permission_granted(self) -> None:
        """permission_granted creates correct event."""
        event = HookEvent.permission_granted(
            tool_name="bash",
            session_id="sess_123",
        )
        assert event.type == EventType.PERMISSION_GRANTED
        assert event.tool_name == "bash"

    def test_permission_denied(self) -> None:
        """permission_denied creates correct event."""
        event = HookEvent.permission_denied(
            tool_name="bash",
            session_id="sess_123",
        )
        assert event.type == EventType.PERMISSION_DENIED
        assert event.tool_name == "bash"

    def test_user_prompt_submit(self) -> None:
        """user_prompt_submit creates correct event."""
        event = HookEvent.user_prompt_submit(
            content="Hello, world!",
            session_id="sess_123",
        )
        assert event.type == EventType.USER_PROMPT_SUBMIT
        assert event.data["user_input"] == "Hello, world!"

    def test_user_interrupt(self) -> None:
        """user_interrupt creates correct event."""
        event = HookEvent.user_interrupt(session_id="sess_123")
        assert event.type == EventType.USER_INTERRUPT
        assert event.session_id == "sess_123"

    def test_factory_methods_have_optional_session_id(self) -> None:
        """Factory methods work without session_id."""
        event = HookEvent.tool_pre_execute("bash", {})
        assert event.session_id is None

        event = HookEvent.llm_pre_request("model", 1)
        assert event.session_id is None
