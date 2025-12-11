# Phase 2.1: Tool System Foundation - Requirements

**Phase:** 2.1
**Name:** Tool System Foundation
**Status:** Not Started
**Dependencies:** Phase 1.1 (Project Foundation), Phase 1.2 (Configuration), Phase 1.3 (REPL)

---

## Overview

This phase implements the core tool system architecture - the registry, executor, and factory that manage all tools. Individual tools are implemented in Phase 2.2 and 2.3.

---

## Functional Requirements

### FR-2.1.1: Tool Interface Implementation
- Concrete implementation patterns for ITool interface
- Tool parameter validation before execution
- Tool result standardization
- Async execution support
- Timeout handling for all tools
- Cancellation support

### FR-2.1.2: Tool Registry
- Register tools by name
- List all registered tools
- Get tool by name
- Check if tool exists
- Deregister tools (for plugins)
- Prevent duplicate registrations

### FR-2.1.3: Tool Factory
- Create tool instances with configuration
- Singleton or per-request instantiation
- Dependency injection for tools
- Tool lifecycle management

### FR-2.1.4: Tool Executor
- Execute tools with parameters
- Validate parameters before execution
- Handle tool errors gracefully
- Return standardized results
- Support dry-run mode
- Collect execution metrics

### FR-2.1.5: Tool Schema Generation
- Generate JSON Schema for tool parameters
- OpenAI-compatible tool format
- Anthropic-compatible tool format
- LangChain-compatible tool format

### FR-2.1.6: Tool Categories
- Define tool categories (file, execution, web, task, notebook)
- Filter tools by category
- Group tools for display

### FR-2.1.7: Tool Context
- Execution context passed to tools
- Working directory context
- Session context
- Permission context (prepared for Phase 4.1)

---

## Non-Functional Requirements

### NFR-2.1.1: Performance
- Tool lookup O(1) by name
- Minimal overhead for execution wrapper
- Lazy tool instantiation

### NFR-2.1.2: Extensibility
- Easy to add new tools
- Plugin tools use same interface
- MCP tools integrate seamlessly

### NFR-2.1.3: Safety
- All tools must validate input
- Errors don't crash the system
- Timeouts prevent hanging

---

## Technical Specifications

### Tool Base Class

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, TypeVar, Generic
from pydantic import BaseModel, Field
from enum import Enum
import asyncio

class ToolCategory(str, Enum):
    """Categories for grouping tools."""
    FILE = "file"
    EXECUTION = "execution"
    WEB = "web"
    TASK = "task"
    NOTEBOOK = "notebook"
    MCP = "mcp"
    OTHER = "other"

class ToolParameter(BaseModel):
    """Definition of a tool parameter."""
    name: str
    type: str  # "string", "integer", "boolean", "array", "object"
    description: str
    required: bool = True
    default: Any = None
    enum: List[Any] | None = None

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
        return schema

class ToolResult(BaseModel):
    """Result from tool execution."""
    success: bool
    output: Any = None
    error: str | None = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def ok(cls, output: Any, **metadata: Any) -> "ToolResult":
        """Create successful result."""
        return cls(success=True, output=output, metadata=metadata)

    @classmethod
    def fail(cls, error: str, **metadata: Any) -> "ToolResult":
        """Create failed result."""
        return cls(success=False, error=error, metadata=metadata)

class ExecutionContext(BaseModel):
    """Context passed to tool execution."""
    working_dir: str
    session_id: str | None = None
    dry_run: bool = False
    timeout: int = 120  # seconds
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseTool(ABC):
    """
    Base class for all tools.

    Provides common functionality for parameter validation,
    schema generation, and execution wrapping.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for LLM."""
        pass

    @property
    @abstractmethod
    def category(self) -> ToolCategory:
        """Tool category."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> List[ToolParameter]:
        """Tool parameters."""
        pass

    @abstractmethod
    async def _execute(self, context: ExecutionContext, **kwargs: Any) -> ToolResult:
        """
        Internal execution method to override.

        Args:
            context: Execution context
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with execution outcome
        """
        pass

    async def execute(self, context: ExecutionContext, **kwargs: Any) -> ToolResult:
        """
        Execute the tool with validation and timeout.

        This is the public method called by the executor.
        """
        # Validate parameters
        valid, error = self.validate_params(**kwargs)
        if not valid:
            return ToolResult.fail(error or "Validation failed")

        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                self._execute(context, **kwargs),
                timeout=context.timeout
            )
            return result
        except asyncio.TimeoutError:
            return ToolResult.fail(f"Tool timed out after {context.timeout}s")
        except Exception as e:
            return ToolResult.fail(f"Execution error: {str(e)}")

    def validate_params(self, **kwargs: Any) -> tuple[bool, str | None]:
        """Validate parameters against schema."""
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                return False, f"Missing required parameter: {param.name}"

            if param.name in kwargs:
                value = kwargs[param.name]
                # Type checking
                if not self._check_type(value, param.type):
                    return False, f"Invalid type for {param.name}: expected {param.type}"
                # Enum checking
                if param.enum and value not in param.enum:
                    return False, f"Invalid value for {param.name}: must be one of {param.enum}"

        return True, None

    def _check_type(self, value: Any, expected: str) -> bool:
        """Check if value matches expected type."""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        expected_type = type_map.get(expected)
        if expected_type is None:
            return True  # Unknown type, allow
        return isinstance(value, expected_type)

    def to_openai_schema(self) -> Dict[str, Any]:
        """Generate OpenAI-compatible function schema."""
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
```

### Tool Registry

```python
from typing import Dict, List, Type
from forge.core.errors import ToolError

class ToolRegistry:
    """
    Registry for all available tools.

    Singleton pattern - one registry for the application.
    """
    _instance: "ToolRegistry | None" = None
    _tools: Dict[str, BaseTool]

    def __new__(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
        return cls._instance

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        if tool.name in self._tools:
            raise ToolError(tool.name, "Tool already registered")
        self._tools[tool.name] = tool

    def deregister(self, name: str) -> bool:
        """Deregister a tool. Returns True if found and removed."""
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get(self, name: str) -> BaseTool | None:
        """Get tool by name."""
        return self._tools.get(name)

    def get_or_raise(self, name: str) -> BaseTool:
        """Get tool by name, raise if not found."""
        tool = self._tools.get(name)
        if tool is None:
            raise ToolError(name, "Tool not found")
        return tool

    def list_all(self) -> List[BaseTool]:
        """List all registered tools."""
        return list(self._tools.values())

    def list_by_category(self, category: ToolCategory) -> List[BaseTool]:
        """List tools by category."""
        return [t for t in self._tools.values() if t.category == category]

    def exists(self, name: str) -> bool:
        """Check if tool exists."""
        return name in self._tools

    def clear(self) -> None:
        """Clear all tools. For testing only."""
        self._tools.clear()
```

### Tool Executor

```python
from typing import Dict, Any
from forge.core.logging import get_logger

logger = get_logger("tools")

class ToolExecutor:
    """
    Executes tools with context and error handling.
    """

    def __init__(self, registry: ToolRegistry):
        self._registry = registry

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
        # Get tool
        tool = self._registry.get(tool_name)
        if tool is None:
            return ToolResult.fail(f"Unknown tool: {tool_name}")

        # Log execution
        logger.info(f"Executing tool: {tool_name}")
        logger.debug(f"Parameters: {kwargs}")

        # Execute
        result = await tool.execute(context, **kwargs)

        # Log result
        if result.success:
            logger.info(f"Tool {tool_name} succeeded")
        else:
            logger.warning(f"Tool {tool_name} failed: {result.error}")

        return result

    def get_all_schemas(self, format: str = "openai") -> List[Dict[str, Any]]:
        """Get schemas for all tools in specified format."""
        tools = self._registry.list_all()

        if format == "openai":
            return [t.to_openai_schema() for t in tools]
        elif format == "anthropic":
            return [t.to_anthropic_schema() for t in tools]
        else:
            raise ValueError(f"Unknown schema format: {format}")
```

---

## Acceptance Criteria

### Definition of Done

- [ ] `BaseTool` abstract class implemented
- [ ] `ToolParameter` model with JSON Schema generation
- [ ] `ToolResult` model with factory methods
- [ ] `ExecutionContext` model
- [ ] `ToolCategory` enum
- [ ] `ToolRegistry` singleton implemented
- [ ] `ToolExecutor` implemented
- [ ] Parameter validation works correctly
- [ ] Timeout handling works correctly
- [ ] OpenAI schema generation works
- [ ] Anthropic schema generation works
- [ ] Tests achieve ≥90% coverage

### Verification Commands

```bash
# Create a test tool
python -c "
from forge.tools.base import BaseTool, ToolParameter, ToolResult, ExecutionContext, ToolCategory

class TestTool(BaseTool):
    @property
    def name(self): return 'test'

    @property
    def description(self): return 'A test tool'

    @property
    def category(self): return ToolCategory.OTHER

    @property
    def parameters(self):
        return [ToolParameter(name='message', type='string', description='Test message')]

    async def _execute(self, ctx, **kwargs):
        return ToolResult.ok(f'Got: {kwargs[\"message\"]}')

# Test schema generation
print(TestTool().to_openai_schema())
"

# Test registry
python -c "
from forge.tools.registry import ToolRegistry
from forge.tools.base import ToolCategory

registry = ToolRegistry()
print(f'Tools: {len(registry.list_all())}')
print(f'File tools: {len(registry.list_by_category(ToolCategory.FILE))}')
"

# Run tests
pytest tests/unit/tools/ -v --cov=forge.tools
```

---

## Out of Scope

The following are NOT part of Phase 2.1:
- Individual tool implementations (Phase 2.2, 2.3)
- Permission checking (Phase 4.1)
- Hook integration (Phase 4.2)
- MCP tool loading (Phase 8.1)

---

## Notes

This phase creates the infrastructure for tools. Without this foundation:
- Phase 2.2 (File Tools) cannot be implemented
- Phase 2.3 (Execution Tools) cannot be implemented
- Phase 3.2 (LangChain) cannot register tools
- Phase 4.1 (Permissions) has nothing to check
