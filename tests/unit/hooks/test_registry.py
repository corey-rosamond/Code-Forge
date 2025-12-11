"""Tests for hook registry."""

from __future__ import annotations

import pytest

from code_forge.hooks.events import EventType, HookEvent
from code_forge.hooks.registry import Hook, HookRegistry


class TestHook:
    """Tests for Hook dataclass."""

    def test_creation_minimal(self) -> None:
        """Create hook with minimal arguments."""
        hook = Hook(
            event_pattern="tool:pre_execute",
            command="echo hello",
        )
        assert hook.event_pattern == "tool:pre_execute"
        assert hook.command == "echo hello"
        assert hook.timeout == 10.0
        assert hook.working_dir is None
        assert hook.env == {}
        assert hook.enabled is True
        assert hook.description == ""

    def test_creation_full(self) -> None:
        """Create hook with all arguments."""
        hook = Hook(
            event_pattern="tool:*",
            command="echo test",
            timeout=5.0,
            working_dir="/tmp",
            env={"KEY": "value"},
            enabled=False,
            description="Test hook",
        )
        assert hook.timeout == 5.0
        assert hook.working_dir == "/tmp"
        assert hook.env == {"KEY": "value"}
        assert hook.enabled is False
        assert hook.description == "Test hook"

    def test_timeout_clamped_to_minimum(self) -> None:
        """Timeout below minimum is clamped."""
        hook = Hook(event_pattern="*", command="test", timeout=0.01)
        assert hook.timeout == Hook.MIN_TIMEOUT

    def test_timeout_clamped_to_maximum(self) -> None:
        """Timeout above maximum is clamped."""
        hook = Hook(event_pattern="*", command="test", timeout=1000.0)
        assert hook.timeout == Hook.MAX_TIMEOUT

    def test_timeout_zero_clamped(self) -> None:
        """Zero timeout is clamped to minimum."""
        hook = Hook(event_pattern="*", command="test", timeout=0)
        assert hook.timeout == Hook.MIN_TIMEOUT

    def test_timeout_negative_clamped(self) -> None:
        """Negative timeout is clamped to minimum."""
        hook = Hook(event_pattern="*", command="test", timeout=-5.0)
        assert hook.timeout == Hook.MIN_TIMEOUT

    def test_env_none_becomes_empty_dict(self) -> None:
        """None env is converted to empty dict."""
        hook = Hook(event_pattern="*", command="test", env=None)  # type: ignore[arg-type]
        assert hook.env == {}


class TestHookMatches:
    """Tests for Hook.matches() method."""

    def test_exact_match(self) -> None:
        """Exact event type match."""
        hook = Hook(event_pattern="tool:pre_execute", command="test")
        event = HookEvent.tool_pre_execute("bash", {})
        assert hook.matches(event) is True

    def test_exact_match_fails_different_event(self) -> None:
        """Exact match fails for different event."""
        hook = Hook(event_pattern="tool:pre_execute", command="test")
        event = HookEvent.tool_post_execute("bash", {}, {})
        assert hook.matches(event) is False

    def test_wildcard_matches_category(self) -> None:
        """Wildcard matches all in category."""
        hook = Hook(event_pattern="tool:*", command="test")

        pre = HookEvent.tool_pre_execute("bash", {})
        post = HookEvent.tool_post_execute("bash", {}, {})
        error = HookEvent.tool_error("bash", {}, "error")

        assert hook.matches(pre) is True
        assert hook.matches(post) is True
        assert hook.matches(error) is True

    def test_wildcard_does_not_match_other_category(self) -> None:
        """Wildcard does not match other categories."""
        hook = Hook(event_pattern="tool:*", command="test")
        event = HookEvent.llm_pre_request("model", 1)
        assert hook.matches(event) is False

    def test_catch_all_pattern(self) -> None:
        """Star pattern matches everything."""
        hook = Hook(event_pattern="*", command="test")

        assert hook.matches(HookEvent.tool_pre_execute("bash", {})) is True
        assert hook.matches(HookEvent.llm_pre_request("model", 1)) is True
        assert hook.matches(HookEvent.session_start("sess")) is True
        assert hook.matches(HookEvent.user_interrupt()) is True

    def test_tool_specific_pattern(self) -> None:
        """Tool-specific pattern matches correct tool."""
        hook = Hook(event_pattern="tool:pre_execute:bash", command="test")

        bash_event = HookEvent.tool_pre_execute("bash", {})
        read_event = HookEvent.tool_pre_execute("read", {})

        assert hook.matches(bash_event) is True
        assert hook.matches(read_event) is False

    def test_tool_specific_wildcard_event(self) -> None:
        """Tool-specific with wildcard event."""
        hook = Hook(event_pattern="tool:*:bash", command="test")

        pre = HookEvent.tool_pre_execute("bash", {})
        post = HookEvent.tool_post_execute("bash", {}, {})
        other = HookEvent.tool_pre_execute("read", {})

        assert hook.matches(pre) is True
        assert hook.matches(post) is True
        assert hook.matches(other) is False

    def test_comma_separated_patterns(self) -> None:
        """Comma-separated patterns match any."""
        hook = Hook(event_pattern="session:start,session:end", command="test")

        start = HookEvent.session_start("sess")
        end = HookEvent.session_end("sess")
        message = HookEvent.session_message("sess", "user", "hello")

        assert hook.matches(start) is True
        assert hook.matches(end) is True
        assert hook.matches(message) is False

    def test_comma_separated_with_spaces(self) -> None:
        """Comma-separated patterns handle spaces."""
        hook = Hook(event_pattern="session:start, session:end", command="test")
        assert hook.matches(HookEvent.session_start("sess")) is True
        assert hook.matches(HookEvent.session_end("sess")) is True

    def test_full_event_match_with_tool(self) -> None:
        """Full event string with tool name matches."""
        hook = Hook(event_pattern="tool:pre_execute:bash", command="test")
        event = HookEvent.tool_pre_execute("bash", {})
        assert hook.matches(event) is True

    def test_glob_pattern_in_tool_name(self) -> None:
        """Glob pattern works in tool name."""
        hook = Hook(event_pattern="tool:pre_execute:bash*", command="test")

        bash = HookEvent.tool_pre_execute("bash", {})
        bash_output = HookEvent.tool_pre_execute("bash_output", {})
        read = HookEvent.tool_pre_execute("read", {})

        assert hook.matches(bash) is True
        assert hook.matches(bash_output) is True
        assert hook.matches(read) is False


class TestHookSerialization:
    """Tests for Hook serialization."""

    def test_to_dict_minimal(self) -> None:
        """Serialize hook with defaults."""
        hook = Hook(event_pattern="tool:*", command="echo test")
        data = hook.to_dict()
        assert data == {
            "event": "tool:*",
            "command": "echo test",
        }

    def test_to_dict_full(self) -> None:
        """Serialize hook with all fields."""
        hook = Hook(
            event_pattern="tool:*",
            command="echo test",
            timeout=5.0,
            working_dir="/tmp",
            env={"KEY": "value"},
            enabled=False,
            description="Test hook",
        )
        data = hook.to_dict()
        assert data["event"] == "tool:*"
        assert data["command"] == "echo test"
        assert data["timeout"] == 5.0
        assert data["working_dir"] == "/tmp"
        assert data["env"] == {"KEY": "value"}
        assert data["enabled"] is False
        assert data["description"] == "Test hook"

    def test_from_dict_minimal(self) -> None:
        """Deserialize hook with minimal data."""
        data = {"event": "tool:*", "command": "echo test"}
        hook = Hook.from_dict(data)
        assert hook.event_pattern == "tool:*"
        assert hook.command == "echo test"
        assert hook.timeout == 10.0
        assert hook.enabled is True

    def test_from_dict_full(self) -> None:
        """Deserialize hook with all fields."""
        data = {
            "event": "tool:*",
            "command": "echo test",
            "timeout": 5.0,
            "working_dir": "/tmp",
            "env": {"KEY": "value"},
            "enabled": False,
            "description": "Test hook",
        }
        hook = Hook.from_dict(data)
        assert hook.event_pattern == "tool:*"
        assert hook.timeout == 5.0
        assert hook.working_dir == "/tmp"
        assert hook.env == {"KEY": "value"}
        assert hook.enabled is False
        assert hook.description == "Test hook"

    def test_roundtrip(self) -> None:
        """Serialize then deserialize preserves data."""
        original = Hook(
            event_pattern="session:*",
            command="notify-send",
            timeout=15.0,
            working_dir="/home/user",
            env={"DISPLAY": ":0"},
            enabled=True,
            description="Desktop notification",
        )
        data = original.to_dict()
        restored = Hook.from_dict(data)
        assert restored.event_pattern == original.event_pattern
        assert restored.command == original.command
        assert restored.timeout == original.timeout
        assert restored.working_dir == original.working_dir
        assert restored.env == original.env
        assert restored.enabled == original.enabled
        assert restored.description == original.description


class TestHookRegistry:
    """Tests for HookRegistry class."""

    @pytest.fixture(autouse=True)
    def reset_registry(self) -> None:
        """Reset singleton before each test."""
        HookRegistry.reset_instance()

    def test_singleton_instance(self) -> None:
        """get_instance returns same object."""
        reg1 = HookRegistry.get_instance()
        reg2 = HookRegistry.get_instance()
        assert reg1 is reg2

    def test_reset_instance(self) -> None:
        """reset_instance creates new object."""
        reg1 = HookRegistry.get_instance()
        HookRegistry.reset_instance()
        reg2 = HookRegistry.get_instance()
        assert reg1 is not reg2

    def test_register_hook(self) -> None:
        """Register adds hook to registry."""
        registry = HookRegistry.get_instance()
        hook = Hook(event_pattern="tool:*", command="test")
        registry.register(hook)
        assert len(registry) == 1

    def test_register_multiple(self) -> None:
        """Register multiple hooks."""
        registry = HookRegistry.get_instance()
        registry.register(Hook(event_pattern="tool:*", command="test1"))
        registry.register(Hook(event_pattern="llm:*", command="test2"))
        assert len(registry) == 2

    def test_unregister_hook(self) -> None:
        """Unregister removes hooks by pattern."""
        registry = HookRegistry.get_instance()
        registry.register(Hook(event_pattern="tool:*", command="test"))
        result = registry.unregister("tool:*")
        assert result is True
        assert len(registry) == 0

    def test_unregister_nonexistent(self) -> None:
        """Unregister returns False for missing pattern."""
        registry = HookRegistry.get_instance()
        result = registry.unregister("nonexistent")
        assert result is False

    def test_get_hooks_matching(self) -> None:
        """get_hooks returns matching hooks."""
        registry = HookRegistry.get_instance()
        registry.register(Hook(event_pattern="tool:pre_execute", command="test1"))
        registry.register(Hook(event_pattern="tool:*", command="test2"))
        registry.register(Hook(event_pattern="llm:*", command="test3"))

        event = HookEvent.tool_pre_execute("bash", {})
        matching = registry.get_hooks(event)

        assert len(matching) == 2
        patterns = [h.event_pattern for h in matching]
        assert "tool:pre_execute" in patterns
        assert "tool:*" in patterns

    def test_get_hooks_excludes_disabled(self) -> None:
        """get_hooks excludes disabled hooks."""
        registry = HookRegistry.get_instance()
        registry.register(Hook(event_pattern="tool:*", command="test1", enabled=True))
        registry.register(Hook(event_pattern="tool:*", command="test2", enabled=False))

        event = HookEvent.tool_pre_execute("bash", {})
        matching = registry.get_hooks(event)

        assert len(matching) == 1
        assert matching[0].command == "test1"

    def test_clear_removes_all(self) -> None:
        """clear removes all hooks."""
        registry = HookRegistry.get_instance()
        registry.register(Hook(event_pattern="tool:*", command="test1"))
        registry.register(Hook(event_pattern="llm:*", command="test2"))
        registry.clear()
        assert len(registry) == 0

    def test_load_hooks(self) -> None:
        """load_hooks adds multiple hooks."""
        registry = HookRegistry.get_instance()
        hooks = [
            Hook(event_pattern="tool:*", command="test1"),
            Hook(event_pattern="llm:*", command="test2"),
        ]
        registry.load_hooks(hooks)
        assert len(registry) == 2

    def test_hooks_property(self) -> None:
        """hooks property returns copy."""
        registry = HookRegistry.get_instance()
        hook = Hook(event_pattern="tool:*", command="test")
        registry.register(hook)

        hooks = registry.hooks
        hooks.clear()  # Modify the copy

        assert len(registry) == 1  # Original unchanged

    def test_iteration(self) -> None:
        """Registry is iterable."""
        registry = HookRegistry.get_instance()
        registry.register(Hook(event_pattern="tool:*", command="test1"))
        registry.register(Hook(event_pattern="llm:*", command="test2"))

        patterns = [h.event_pattern for h in registry]
        assert "tool:*" in patterns
        assert "llm:*" in patterns


class TestHookRegistryThreadSafety:
    """Tests for thread safety of HookRegistry."""

    @pytest.fixture(autouse=True)
    def reset_registry(self) -> None:
        """Reset singleton before each test."""
        HookRegistry.reset_instance()

    def test_concurrent_registration(self) -> None:
        """Multiple threads can register hooks safely."""
        import threading

        registry = HookRegistry.get_instance()
        errors: list[Exception] = []

        def register_hook(i: int) -> None:
            try:
                registry.register(Hook(event_pattern=f"test:{i}", command=f"cmd{i}"))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=register_hook, args=(i,)) for i in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(registry) == 100

    def test_concurrent_get_hooks(self) -> None:
        """Multiple threads can get hooks safely."""
        import threading

        registry = HookRegistry.get_instance()
        for i in range(10):
            registry.register(Hook(event_pattern=f"tool:{i}", command=f"cmd{i}"))

        event = HookEvent.tool_pre_execute("bash", {})
        results: list[list[Hook]] = []
        lock = threading.Lock()

        def get_hooks() -> None:
            matching = registry.get_hooks(event)
            with lock:
                results.append(matching)

        threads = [threading.Thread(target=get_hooks) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 50
        # All results should be the same length
        assert all(len(r) == len(results[0]) for r in results)
