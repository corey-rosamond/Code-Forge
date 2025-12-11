"""Tool registry for managing available tools.

This module provides a thread-safe singleton registry for tool management:
- Register/deregister tools
- Look up tools by name
- List tools by category
- Prevent duplicate registrations
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from code_forge.core.errors import ToolError
from code_forge.core.logging import get_logger

if TYPE_CHECKING:
    from code_forge.tools.base import BaseTool, ToolCategory

logger = get_logger("tools.registry")


class ToolRegistry:
    """Singleton registry for all available tools.

    Thread-safe tool registration and lookup using RLock.

    Usage:
        registry = ToolRegistry()  # Always returns same instance
        registry.register(my_tool)
        tool = registry.get("my_tool")

    Thread Safety:
        All mutations are protected by RLock, allowing reentrant calls.
        Read operations (get, exists, list_all) are also protected to
        ensure consistency.
    """

    _instance: ToolRegistry | None = None
    _instance_lock: threading.Lock = threading.Lock()
    _initialized: bool = False

    # Instance attributes declared at class level for mypy
    _tools: dict[str, BaseTool]
    _lock: threading.RLock

    def __new__(cls) -> ToolRegistry:
        """Create or return the singleton instance.

        Thread-safe singleton creation using double-checked locking.
        """
        if cls._instance is None:
            with cls._instance_lock:
                # Double-check after acquiring lock
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the registry on first creation only."""
        # Guard against re-initialization
        if ToolRegistry._initialized and hasattr(self, "_tools"):
            return
        self._tools = {}
        self._lock = threading.RLock()
        ToolRegistry._initialized = True

    def register(self, tool: BaseTool) -> None:
        """Register a tool.

        Thread-safe: uses lock to prevent race conditions.

        Args:
            tool: The tool to register.

        Raises:
            ToolError: If a tool with the same name is already registered.
        """
        with self._lock:
            if tool.name in self._tools:
                raise ToolError(tool.name, "Tool already registered")
            self._tools[tool.name] = tool
            logger.debug(f"Registered tool: {tool.name}")

    def register_many(self, tools: list[BaseTool]) -> None:
        """Register multiple tools at once.

        Args:
            tools: List of tools to register.

        Raises:
            ToolError: If any tool name is already registered.
        """
        for tool in tools:
            self.register(tool)

    def deregister(self, name: str) -> bool:
        """Deregister a tool.

        Args:
            name: Name of the tool to deregister.

        Returns:
            True if the tool was found and removed, False otherwise.
        """
        with self._lock:
            if name in self._tools:
                del self._tools[name]
                logger.debug(f"Deregistered tool: {name}")
                return True
            return False

    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name.

        Args:
            name: Name of the tool to retrieve.

        Returns:
            The tool if found, None otherwise.
        """
        with self._lock:
            return self._tools.get(name)

    def get_or_raise(self, name: str) -> BaseTool:
        """Get a tool by name, raising if not found.

        Args:
            name: Name of the tool to retrieve.

        Returns:
            The tool instance.

        Raises:
            ToolError: If the tool is not found.
        """
        with self._lock:
            tool = self._tools.get(name)
            if tool is None:
                raise ToolError(name, "Tool not found")
            return tool

    def exists(self, name: str) -> bool:
        """Check if a tool is registered.

        Args:
            name: Name of the tool to check.

        Returns:
            True if the tool is registered, False otherwise.
        """
        with self._lock:
            return name in self._tools

    def list_all(self) -> list[BaseTool]:
        """Get a list of all registered tools.

        Returns:
            List of all registered tool instances.
        """
        with self._lock:
            return list(self._tools.values())

    def list_names(self) -> list[str]:
        """Get a sorted list of all tool names.

        Returns:
            Sorted list of all registered tool names.
        """
        with self._lock:
            return sorted(self._tools.keys())

    def list_by_category(self, category: ToolCategory) -> list[BaseTool]:
        """Get tools filtered by category.

        Args:
            category: The category to filter by.

        Returns:
            List of tools in the specified category.
        """
        with self._lock:
            return [t for t in self._tools.values() if t.category == category]

    def count(self) -> int:
        """Get the count of registered tools.

        Returns:
            Number of registered tools.
        """
        with self._lock:
            return len(self._tools)

    def clear(self) -> None:
        """Clear all tools.

        Warning: For testing only. Do not use in production code.
        """
        with self._lock:
            self._tools.clear()
            logger.debug("Cleared all tools from registry")

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance.

        Warning: For testing only. Do not use in production code.
        This allows tests to start with a fresh registry.
        """
        with cls._instance_lock:
            cls._instance = None
            cls._initialized = False
            logger.debug("Reset ToolRegistry singleton")
