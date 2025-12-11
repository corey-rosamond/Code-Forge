"""Tool executor for running tools with tracking.

This module provides the ToolExecutor class which:
- Executes tools by name
- Tracks execution history
- Generates schemas for LLM integration
- Provides logging of tool execution
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from code_forge.core.logging import get_logger
from code_forge.tools.base import (
    ExecutionContext,
    ToolCategory,
    ToolExecution,
    ToolResult,
)
from code_forge.tools.registry import ToolRegistry

logger = get_logger("tools.executor")


class ToolExecutor:
    """Executes tools with context and tracking.

    Provides a clean interface for tool execution with:
    - Context management
    - Execution tracking
    - Schema generation for LLM

    Usage:
        executor = ToolExecutor()  # Uses default registry
        result = await executor.execute("Read", context, file_path="/foo")
        schemas = executor.get_all_schemas("openai")
    """

    def __init__(self, registry: ToolRegistry | None = None) -> None:
        """Initialize the executor.

        Args:
            registry: Tool registry to use. Defaults to the singleton.
        """
        self._registry = registry or ToolRegistry()
        self._executions: list[ToolExecution] = []

    async def execute(
        self, tool_name: str, context: ExecutionContext, **kwargs: Any
    ) -> ToolResult:
        """Execute a tool by name.

        Args:
            tool_name: Name of the tool to execute.
            context: Execution context.
            **kwargs: Tool parameters.

        Returns:
            ToolResult with execution outcome.
        """
        started_at = datetime.now()

        # Get tool
        tool = self._registry.get(tool_name)
        if tool is None:
            return ToolResult.fail(f"Unknown tool: {tool_name}")

        # Log execution
        logger.info(f"Executing tool: {tool_name}")
        if logger.isEnabledFor(10):  # DEBUG level
            logger.debug(f"Parameters: {kwargs}")

        # Execute
        result = await tool.execute(context, **kwargs)

        # Track execution
        completed_at = datetime.now()
        execution = ToolExecution(
            tool_name=tool_name,
            parameters=kwargs,
            context=context,
            result=result,
            started_at=started_at,
            completed_at=completed_at,
        )
        self._executions.append(execution)

        # Log result
        if result.success:
            logger.info(f"Tool {tool_name} succeeded ({result.duration_ms:.1f}ms)")
        else:
            logger.warning(f"Tool {tool_name} failed: {result.error}")

        return result

    def get_all_schemas(self, format: str = "openai") -> list[dict[str, Any]]:
        """Get schemas for all tools.

        Args:
            format: Schema format - "openai" or "anthropic".

        Returns:
            List of tool schemas in the specified format.

        Raises:
            ValueError: If the format is not recognized.
        """
        tools = self._registry.list_all()

        if format == "openai":
            return [t.to_openai_schema() for t in tools]
        elif format == "anthropic":
            return [t.to_anthropic_schema() for t in tools]
        else:
            raise ValueError(f"Unknown schema format: {format}")

    def get_schemas_by_category(
        self, category: ToolCategory, format: str = "openai"
    ) -> list[dict[str, Any]]:
        """Get schemas for tools in a specific category.

        Args:
            category: The category to filter by.
            format: Schema format - "openai" or "anthropic".

        Returns:
            List of tool schemas in the specified format.

        Raises:
            ValueError: If the format is not recognized.
        """
        tools = self._registry.list_by_category(category)

        if format == "openai":
            return [t.to_openai_schema() for t in tools]
        elif format == "anthropic":
            return [t.to_anthropic_schema() for t in tools]
        else:
            raise ValueError(f"Unknown schema format: {format}")

    def get_executions(self) -> list[ToolExecution]:
        """Get a copy of the execution history.

        Returns:
            List of ToolExecution records.
        """
        return self._executions.copy()

    def clear_executions(self) -> None:
        """Clear the execution history."""
        self._executions.clear()
        logger.debug("Cleared execution history")
