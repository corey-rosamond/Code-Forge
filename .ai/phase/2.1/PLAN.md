# Phase 2.1: Tool System Foundation - Architectural Plan

**Phase:** 2.1
**Name:** Tool System Foundation
**Dependencies:** Phase 1.1, Phase 1.2, Phase 1.3

---

## Architectural Overview

The tool system follows the Command pattern with a Factory and Registry. Tools are the primary way the AI agent interacts with the environment.

---

## Design Patterns Applied

### Command Pattern
Each tool encapsulates a request as an object:
- `BaseTool` is the command interface
- Concrete tools are command implementations
- `ToolExecutor` is the invoker
- Context provides receiver information

### Factory Pattern
`ToolFactory` creates tool instances:
- Centralized tool creation
- Configuration injection
- Dependency management

### Registry Pattern
`ToolRegistry` manages tool registration:
- Singleton for global access
- Name-based lookup
- Category-based filtering

### Template Method Pattern
`BaseTool.execute()` defines the algorithm skeleton:
- Validation step (template)
- Execution step (abstract - subclass implements)
- Error handling (template)

---

## Class Design

### Complete Tool System

```python
from abc import ABC, abstractmethod
import threading
from typing import Any, Dict, List, TypeVar, Generic, Callable, Awaitable
from pydantic import BaseModel, Field
from enum import Enum
import asyncio
from datetime import datetime

from opencode.core.errors import ToolError, OpenCodeError
from opencode.core.logging import get_logger

logger = get_logger("tools")


# ============ Enums ============

class ToolCategory(str, Enum):
    """Categories for grouping tools."""
    FILE = "file"           # Read, Write, Edit, Glob, Grep
    EXECUTION = "execution" # Bash, BashOutput, KillShell
    WEB = "web"             # WebSearch, WebFetch
    TASK = "task"           # TodoRead, TodoWrite, Memory
    NOTEBOOK = "notebook"   # NotebookRead, NotebookEdit
    MCP = "mcp"             # Dynamic MCP tools
    OTHER = "other"         # Miscellaneous


# ============ Models ============

class ToolParameter(BaseModel):
    """Definition of a tool parameter."""
    name: str
    type: str  # JSON Schema types
    description: str
    required: bool = True
    default: Any = None
    enum: List[Any] | None = None
    min_length: int | None = None
    max_length: int | None = None
    minimum: float | None = None
    maximum: float | None = None

    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema: Dict[str, Any] = {
            "type": self.type,
            "description": self.description,
        }
        if self.enum:
            schema["enum"] = self.enum
        if self.default is not None:
            schema["default"] = self.default
        if self.min_length is not None:
            schema["minLength"] = self.min_length
        if self.max_length is not None:
            schema["maxLength"] = self.max_length
        if self.minimum is not None:
            schema["minimum"] = self.minimum
        if self.maximum is not None:
            schema["maximum"] = self.maximum
        return schema


class ToolResult(BaseModel):
    """Result from tool execution."""
    success: bool
    output: Any = None
    error: str | None = None
    duration_ms: float | None = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def ok(cls, output: Any, **metadata: Any) -> "ToolResult":
        """Create successful result."""
        return cls(success=True, output=output, metadata=metadata)

    @classmethod
    def fail(cls, error: str, **metadata: Any) -> "ToolResult":
        """Create failed result."""
        return cls(success=False, error=error, metadata=metadata)

    def to_display(self) -> str:
        """Convert result to display string."""
        if self.success:
            return str(self.output)
        else:
            return f"Error: {self.error}"


class ExecutionContext(BaseModel):
    """Context passed to tool execution.

    Note on timeout units:
    - ExecutionContext.timeout is in SECONDS (default 120s = 2 min)
    - BashTool accepts milliseconds from the LLM but converts internally
    - This allows asyncio.wait_for() to work directly with context.timeout
    """
    working_dir: str
    session_id: str | None = None
    agent_id: str | None = None
    dry_run: bool = False
    timeout: float = 120.0  # seconds (float to match asyncio.wait_for)
    max_output_size: int = 100000  # characters
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Allow arbitrary types for metadata."""
        arbitrary_types_allowed = True


class ToolExecution(BaseModel):
    """Record of a tool execution."""
    tool_name: str
    parameters: Dict[str, Any]
    context: ExecutionContext
    result: ToolResult
    started_at: datetime
    completed_at: datetime

    @property
    def duration_ms(self) -> float:
        """Execution duration in milliseconds."""
        delta = self.completed_at - self.started_at
        return delta.total_seconds() * 1000


# ============ Base Tool ============

class BaseTool(ABC):
    """
    Abstract base class for all tools.

    Implements the Template Method pattern where execute() defines
    the algorithm skeleton and _execute() is the customization point.

    McCabe Complexity Target: ≤ 6 for all methods
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description for LLM."""
        pass

    @property
    @abstractmethod
    def category(self) -> ToolCategory:
        """Tool category for grouping."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> List[ToolParameter]:
        """List of accepted parameters."""
        pass

    @abstractmethod
    async def _execute(
        self,
        context: ExecutionContext,
        **kwargs: Any
    ) -> ToolResult:
        """
        Internal execution method - override in subclasses.

        This method should:
        1. Perform the actual tool operation
        2. Return ToolResult.ok() on success
        3. Return ToolResult.fail() on expected errors
        4. Let unexpected exceptions propagate (caught by execute())
        """
        pass

    async def execute(
        self,
        context: ExecutionContext,
        **kwargs: Any
    ) -> ToolResult:
        """
        Execute the tool with validation, timeout, and error handling.

        This is the Template Method that defines the execution algorithm.
        Subclasses should override _execute(), not this method.
        """
        start_time = datetime.now()

        # Step 1: Validate parameters
        valid, error = self.validate_params(**kwargs)
        if not valid:
            return ToolResult.fail(error or "Validation failed")

        # Step 2: Check for dry run
        if context.dry_run:
            return ToolResult.ok(
                f"[Dry Run] Would execute {self.name} with {kwargs}",
                dry_run=True
            )

        # Step 3: Execute with timeout
        try:
            result = await asyncio.wait_for(
                self._execute(context, **kwargs),
                timeout=context.timeout
            )
        except asyncio.TimeoutError:
            result = ToolResult.fail(
                f"Tool timed out after {context.timeout}s"
            )
        except asyncio.CancelledError:
            result = ToolResult.fail("Tool execution cancelled")
        except OpenCodeError as e:
            result = ToolResult.fail(str(e))
        except Exception as e:
            logger.exception(f"Unexpected error in {self.name}")
            result = ToolResult.fail(f"Unexpected error: {str(e)}")

        # Step 4: Add timing metadata
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() * 1000
        result.duration_ms = duration

        return result

    def validate_params(self, **kwargs: Any) -> tuple[bool, str | None]:
        """
        Validate parameters against schema.

        Returns (True, None) if valid, (False, error_message) if invalid.
        """
        for param in self.parameters:
            # Check required parameters
            if param.required and param.name not in kwargs:
                return False, f"Missing required parameter: {param.name}"

            # Skip validation if parameter not provided
            if param.name not in kwargs:
                continue

            value = kwargs[param.name]

            # Type checking
            if not self._check_type(value, param.type):
                return False, f"Invalid type for '{param.name}': expected {param.type}"

            # Enum checking
            if param.enum and value not in param.enum:
                return False, f"Invalid value for '{param.name}': must be one of {param.enum}"

            # String length checking
            if param.type == "string" and isinstance(value, str):
                if param.min_length and len(value) < param.min_length:
                    return False, f"'{param.name}' too short: minimum {param.min_length} chars"
                if param.max_length and len(value) > param.max_length:
                    return False, f"'{param.name}' too long: maximum {param.max_length} chars"

            # Numeric range checking
            if param.type in ("integer", "number") and isinstance(value, (int, float)):
                if param.minimum is not None and value < param.minimum:
                    return False, f"'{param.name}' below minimum: {param.minimum}"
                if param.maximum is not None and value > param.maximum:
                    return False, f"'{param.name}' above maximum: {param.maximum}"

        return True, None

    def _check_type(self, value: Any, expected: str) -> bool:
        """Check if value matches expected JSON Schema type."""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }
        expected_type = type_map.get(expected)
        if expected_type is None:
            return True  # Unknown type, allow
        return isinstance(value, expected_type)

    def to_openai_schema(self) -> Dict[str, Any]:
        """Generate OpenAI-compatible function/tool schema."""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def to_anthropic_schema(self) -> Dict[str, Any]:
        """Generate Anthropic-compatible tool schema."""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    def to_langchain_tool(self) -> Any:
        """Create a LangChain Tool wrapper."""
        from langchain_core.tools import StructuredTool
        from pydantic import create_model

        # Create Pydantic model for parameters
        fields = {}
        for param in self.parameters:
            python_type = {
                "string": str,
                "integer": int,
                "number": float,
                "boolean": bool,
                "array": list,
                "object": dict,
            }.get(param.type, Any)

            if param.required:
                fields[param.name] = (python_type, ...)
            else:
                fields[param.name] = (python_type, param.default)

        ArgsModel = create_model(f"{self.name}Args", **fields)

        # Create async wrapper
        async def run_tool(**kwargs: Any) -> str:
            ctx = ExecutionContext(working_dir=".")
            result = await self.execute(ctx, **kwargs)
            return result.to_display()

        return StructuredTool.from_function(
            func=lambda **kw: asyncio.run(run_tool(**kw)),
            coroutine=run_tool,
            name=self.name,
            description=self.description,
            args_schema=ArgsModel,
        )


# ============ Registry ============

class ToolRegistry:
    """
    Singleton registry for all available tools.

    Thread-safe tool registration and lookup.
    """
    _instance: "ToolRegistry | None" = None
    _tools: Dict[str, BaseTool]
    _lock: threading.RLock | None  # Use threading lock for synchronous operations

    def __new__(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
            cls._instance._lock = threading.RLock()  # RLock allows reentrant locking
        return cls._instance

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool.

        Thread-safe: uses lock to prevent race conditions.
        Raises ToolError if tool with same name already registered.
        """
        with self._lock:
            if tool.name in self._tools:
                raise ToolError(tool.name, "Tool already registered")
            self._tools[tool.name] = tool
            logger.debug(f"Registered tool: {tool.name}")

    def register_many(self, tools: List[BaseTool]) -> None:
        """Register multiple tools at once."""
        for tool in tools:
            self.register(tool)

    def deregister(self, name: str) -> bool:
        """Deregister a tool. Returns True if found and removed."""
        with self._lock:
            if name in self._tools:
                del self._tools[name]
                logger.debug(f"Deregistered tool: {name}")
                return True
            return False

    def get(self, name: str) -> BaseTool | None:
        """Get tool by name, returns None if not found."""
        return self._tools.get(name)

    def get_or_raise(self, name: str) -> BaseTool:
        """Get tool by name, raises ToolError if not found."""
        tool = self._tools.get(name)
        if tool is None:
            raise ToolError(name, "Tool not found")
        return tool

    def exists(self, name: str) -> bool:
        """Check if tool is registered."""
        return name in self._tools

    def list_all(self) -> List[BaseTool]:
        """Get list of all registered tools."""
        return list(self._tools.values())

    def list_names(self) -> List[str]:
        """Get list of all tool names."""
        return list(self._tools.keys())

    def list_by_category(self, category: ToolCategory) -> List[BaseTool]:
        """Get tools filtered by category."""
        return [t for t in self._tools.values() if t.category == category]

    def count(self) -> int:
        """Get count of registered tools."""
        return len(self._tools)

    def clear(self) -> None:
        """Clear all tools. For testing only."""
        with self._lock:
            self._tools.clear()

    @classmethod
    def reset(cls) -> None:
        """Reset singleton. For testing only."""
        cls._instance = None


# ============ Executor ============

class ToolExecutor:
    """
    Executes tools with context and tracking.

    Provides a clean interface for tool execution with:
    - Context management
    - Execution tracking
    - Schema generation for LLM
    """

    def __init__(self, registry: ToolRegistry | None = None):
        self._registry = registry or ToolRegistry()
        self._executions: List[ToolExecution] = []

    async def execute(
        self,
        tool_name: str,
        context: ExecutionContext,
        **kwargs: Any
    ) -> ToolResult:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of tool to execute
            context: Execution context
            **kwargs: Tool parameters

        Returns:
            ToolResult with execution outcome
        """
        started_at = datetime.now()

        # Get tool
        tool = self._registry.get(tool_name)
        if tool is None:
            return ToolResult.fail(f"Unknown tool: {tool_name}")

        # Log execution
        logger.info(f"Executing tool: {tool_name}")
        if logger.isEnabledFor(10):  # DEBUG
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

    def get_all_schemas(self, format: str = "openai") -> List[Dict[str, Any]]:
        """
        Get schemas for all tools.

        Args:
            format: "openai" or "anthropic"

        Returns:
            List of tool schemas in specified format
        """
        tools = self._registry.list_all()

        if format == "openai":
            return [t.to_openai_schema() for t in tools]
        elif format == "anthropic":
            return [t.to_anthropic_schema() for t in tools]
        else:
            raise ValueError(f"Unknown schema format: {format}")

    def get_schemas_by_category(
        self,
        category: ToolCategory,
        format: str = "openai"
    ) -> List[Dict[str, Any]]:
        """Get schemas for tools in a category."""
        tools = self._registry.list_by_category(category)

        if format == "openai":
            return [t.to_openai_schema() for t in tools]
        elif format == "anthropic":
            return [t.to_anthropic_schema() for t in tools]
        else:
            raise ValueError(f"Unknown schema format: {format}")

    def get_executions(self) -> List[ToolExecution]:
        """Get list of all tracked executions."""
        return self._executions.copy()

    def clear_executions(self) -> None:
        """Clear execution history."""
        self._executions.clear()
```

---

## Implementation Order

1. Create `src/opencode/tools/__init__.py` with exports
2. Create `src/opencode/tools/base.py` with BaseTool and models
3. Create `src/opencode/tools/registry.py` with ToolRegistry
4. Create `src/opencode/tools/executor.py` with ToolExecutor
5. Create example tool for testing
6. Write comprehensive tests
7. Verify schema generation

---

## File Structure

```
src/opencode/tools/
├── __init__.py       # Exports: BaseTool, ToolRegistry, ToolExecutor, etc.
├── base.py           # BaseTool, ToolParameter, ToolResult, ExecutionContext
├── registry.py       # ToolRegistry singleton
├── executor.py       # ToolExecutor
└── _example.py       # Example tool for testing (not exported)

tests/unit/tools/
├── __init__.py
├── test_base.py      # BaseTool tests
├── test_registry.py  # Registry tests
├── test_executor.py  # Executor tests
└── conftest.py       # Test fixtures (mock tools)
```

---

## Quality Gates

Before completing Phase 2.1:
- [ ] BaseTool abstract class works
- [ ] Parameter validation catches all invalid inputs
- [ ] Timeout handling works correctly
- [ ] Registry singleton works
- [ ] Registry prevents duplicates
- [ ] Executor tracks executions
- [ ] OpenAI schema generation is valid JSON Schema
- [ ] Anthropic schema generation is valid
- [ ] Tests pass with ≥90% coverage
- [ ] `mypy --strict` passes
- [ ] `ruff check` passes
