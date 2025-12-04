"""Tests for opencode.tools.registry module."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest

from opencode.core.errors import ToolError
from opencode.tools.base import (
    BaseTool,
    ExecutionContext,
    ToolCategory,
    ToolParameter,
    ToolResult,
)
from opencode.tools.registry import ToolRegistry


# =============================================================================
# Test Fixtures
# =============================================================================


class MockTool(BaseTool):
    """A mock tool for testing."""

    def __init__(self, tool_name: str = "MockTool", category: ToolCategory = ToolCategory.OTHER):
        self._name = tool_name
        self._category = category

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"Mock tool: {self._name}"

    @property
    def category(self) -> ToolCategory:
        return self._category

    @property
    def parameters(self) -> list[ToolParameter]:
        return []

    async def _execute(self, context: ExecutionContext, **kwargs: Any) -> ToolResult:
        return ToolResult.ok(f"Executed {self._name}")


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset the registry singleton before and after each test."""
    ToolRegistry.reset()
    yield
    ToolRegistry.reset()


# =============================================================================
# Singleton Tests
# =============================================================================


class TestToolRegistrySingleton:
    """Tests for ToolRegistry singleton behavior."""

    def test_singleton_returns_same_instance(self) -> None:
        """Test that ToolRegistry always returns the same instance."""
        reg1 = ToolRegistry()
        reg2 = ToolRegistry()
        assert reg1 is reg2

    def test_reset_creates_new_instance(self) -> None:
        """Test that reset() creates a new singleton instance."""
        reg1 = ToolRegistry()
        reg1.register(MockTool())
        assert reg1.count() == 1

        ToolRegistry.reset()
        reg2 = ToolRegistry()

        assert reg1 is not reg2
        assert reg2.count() == 0

    def test_singleton_thread_safety(self) -> None:
        """Test that singleton creation is thread-safe."""
        results: list[ToolRegistry] = []

        def get_registry():
            results.append(ToolRegistry())

        threads = [threading.Thread(target=get_registry) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should have gotten the same instance
        assert all(r is results[0] for r in results)


# =============================================================================
# Registration Tests
# =============================================================================


class TestToolRegistryRegistration:
    """Tests for tool registration."""

    def test_register_tool(self) -> None:
        """Test registering a tool."""
        registry = ToolRegistry()
        tool = MockTool("TestTool")
        registry.register(tool)

        assert registry.exists("TestTool")
        assert registry.count() == 1

    def test_register_duplicate_raises(self) -> None:
        """Test that registering a duplicate raises ToolError."""
        registry = ToolRegistry()
        tool1 = MockTool("Duplicate")
        tool2 = MockTool("Duplicate")

        registry.register(tool1)
        with pytest.raises(ToolError) as exc_info:
            registry.register(tool2)

        assert "already registered" in str(exc_info.value)
        assert exc_info.value.tool_name == "Duplicate"

    def test_register_many(self) -> None:
        """Test registering multiple tools at once."""
        registry = ToolRegistry()
        tools = [MockTool("Tool1"), MockTool("Tool2"), MockTool("Tool3")]
        registry.register_many(tools)

        assert registry.count() == 3
        assert registry.exists("Tool1")
        assert registry.exists("Tool2")
        assert registry.exists("Tool3")

    def test_register_many_fails_on_duplicate(self) -> None:
        """Test register_many fails if any tool is duplicate."""
        registry = ToolRegistry()
        registry.register(MockTool("Existing"))

        tools = [MockTool("New1"), MockTool("Existing"), MockTool("New2")]
        with pytest.raises(ToolError):
            registry.register_many(tools)

        # Only New1 should be registered
        assert registry.count() == 2
        assert registry.exists("New1")


# =============================================================================
# Deregistration Tests
# =============================================================================


class TestToolRegistryDeregistration:
    """Tests for tool deregistration."""

    def test_deregister_existing(self) -> None:
        """Test deregistering an existing tool."""
        registry = ToolRegistry()
        registry.register(MockTool("ToRemove"))
        assert registry.exists("ToRemove")

        result = registry.deregister("ToRemove")
        assert result is True
        assert not registry.exists("ToRemove")

    def test_deregister_nonexistent(self) -> None:
        """Test deregistering a nonexistent tool returns False."""
        registry = ToolRegistry()
        result = registry.deregister("DoesNotExist")
        assert result is False


# =============================================================================
# Lookup Tests
# =============================================================================


class TestToolRegistryLookup:
    """Tests for tool lookup."""

    def test_get_existing(self) -> None:
        """Test getting an existing tool."""
        registry = ToolRegistry()
        tool = MockTool("MyTool")
        registry.register(tool)

        retrieved = registry.get("MyTool")
        assert retrieved is tool

    def test_get_nonexistent(self) -> None:
        """Test getting a nonexistent tool returns None."""
        registry = ToolRegistry()
        result = registry.get("DoesNotExist")
        assert result is None

    def test_get_or_raise_existing(self) -> None:
        """Test get_or_raise returns tool for existing."""
        registry = ToolRegistry()
        tool = MockTool("MyTool")
        registry.register(tool)

        retrieved = registry.get_or_raise("MyTool")
        assert retrieved is tool

    def test_get_or_raise_nonexistent(self) -> None:
        """Test get_or_raise raises for nonexistent tool."""
        registry = ToolRegistry()
        with pytest.raises(ToolError) as exc_info:
            registry.get_or_raise("DoesNotExist")

        assert "not found" in str(exc_info.value)
        assert exc_info.value.tool_name == "DoesNotExist"

    def test_exists_true(self) -> None:
        """Test exists returns True for registered tool."""
        registry = ToolRegistry()
        registry.register(MockTool("Exists"))
        assert registry.exists("Exists") is True

    def test_exists_false(self) -> None:
        """Test exists returns False for unregistered tool."""
        registry = ToolRegistry()
        assert registry.exists("DoesNotExist") is False


# =============================================================================
# Listing Tests
# =============================================================================


class TestToolRegistryListing:
    """Tests for tool listing."""

    def test_list_all_empty(self) -> None:
        """Test list_all on empty registry."""
        registry = ToolRegistry()
        tools = registry.list_all()
        assert tools == []

    def test_list_all_with_tools(self) -> None:
        """Test list_all returns all tools."""
        registry = ToolRegistry()
        tool1 = MockTool("Tool1")
        tool2 = MockTool("Tool2")
        registry.register(tool1)
        registry.register(tool2)

        tools = registry.list_all()
        assert len(tools) == 2
        assert tool1 in tools
        assert tool2 in tools

    def test_list_names_empty(self) -> None:
        """Test list_names on empty registry."""
        registry = ToolRegistry()
        names = registry.list_names()
        assert names == []

    def test_list_names_sorted(self) -> None:
        """Test list_names returns sorted names."""
        registry = ToolRegistry()
        registry.register(MockTool("Zebra"))
        registry.register(MockTool("Apple"))
        registry.register(MockTool("Mango"))

        names = registry.list_names()
        assert names == ["Apple", "Mango", "Zebra"]

    def test_list_by_category(self) -> None:
        """Test list_by_category filters correctly."""
        registry = ToolRegistry()
        registry.register(MockTool("FileTool1", ToolCategory.FILE))
        registry.register(MockTool("FileTool2", ToolCategory.FILE))
        registry.register(MockTool("ExecTool", ToolCategory.EXECUTION))
        registry.register(MockTool("OtherTool", ToolCategory.OTHER))

        file_tools = registry.list_by_category(ToolCategory.FILE)
        assert len(file_tools) == 2
        assert all(t.category == ToolCategory.FILE for t in file_tools)

        exec_tools = registry.list_by_category(ToolCategory.EXECUTION)
        assert len(exec_tools) == 1
        assert exec_tools[0].name == "ExecTool"

        web_tools = registry.list_by_category(ToolCategory.WEB)
        assert len(web_tools) == 0

    def test_count(self) -> None:
        """Test count returns correct number."""
        registry = ToolRegistry()
        assert registry.count() == 0

        registry.register(MockTool("Tool1"))
        assert registry.count() == 1

        registry.register(MockTool("Tool2"))
        assert registry.count() == 2

        registry.deregister("Tool1")
        assert registry.count() == 1


# =============================================================================
# Clear Tests
# =============================================================================


class TestToolRegistryClear:
    """Tests for registry clearing."""

    def test_clear(self) -> None:
        """Test clear removes all tools."""
        registry = ToolRegistry()
        registry.register(MockTool("Tool1"))
        registry.register(MockTool("Tool2"))
        registry.register(MockTool("Tool3"))
        assert registry.count() == 3

        registry.clear()
        assert registry.count() == 0
        assert registry.list_all() == []


# =============================================================================
# Thread Safety Tests
# =============================================================================


class TestToolRegistryThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_registration(self) -> None:
        """Test concurrent registration doesn't corrupt state."""
        registry = ToolRegistry()
        num_tools = 100
        errors: list[Exception] = []

        def register_tool(i: int):
            try:
                registry.register(MockTool(f"Tool_{i}"))
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as executor:
            list(executor.map(register_tool, range(num_tools)))

        # All tools should be registered
        assert len(errors) == 0
        assert registry.count() == num_tools

    def test_concurrent_read_write(self) -> None:
        """Test concurrent reads and writes don't corrupt state."""
        registry = ToolRegistry()
        # Pre-register some tools
        for i in range(10):
            registry.register(MockTool(f"Initial_{i}"))

        results: list[bool] = []
        errors: list[Exception] = []

        def worker(i: int):
            try:
                # Mix of reads and writes
                if i % 3 == 0:
                    registry.register(MockTool(f"Dynamic_{i}"))
                elif i % 3 == 1:
                    registry.list_all()
                else:
                    registry.get(f"Initial_{i % 10}")
                results.append(True)
            except Exception as e:
                errors.append(e)
                results.append(False)

        with ThreadPoolExecutor(max_workers=20) as executor:
            list(executor.map(worker, range(100)))

        # No errors should have occurred
        assert len(errors) == 0, f"Errors: {errors}"


# =============================================================================
# Edge Cases
# =============================================================================


class TestToolRegistryEdgeCases:
    """Tests for edge cases."""

    def test_empty_tool_name(self) -> None:
        """Test tool with empty name can be registered."""
        registry = ToolRegistry()
        tool = MockTool("")
        registry.register(tool)
        assert registry.exists("")
        assert registry.get("") is tool

    def test_special_characters_in_name(self) -> None:
        """Test tool with special characters in name."""
        registry = ToolRegistry()
        tool = MockTool("Tool-With_Special.Chars!")
        registry.register(tool)
        assert registry.exists("Tool-With_Special.Chars!")

    def test_list_all_returns_copy(self) -> None:
        """Test that list_all returns a copy, not the internal list."""
        registry = ToolRegistry()
        registry.register(MockTool("Tool1"))

        tools = registry.list_all()
        tools.clear()  # Modify the returned list

        # Internal list should be unaffected
        assert registry.count() == 1
