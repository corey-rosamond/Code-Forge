# Phase 2.1: Tool System Foundation - Completion Criteria

**Phase:** 2.1
**Name:** Tool System Foundation
**Dependencies:** Phase 1.1 (Project Foundation), Phase 1.2 (Configuration), Phase 1.3 (REPL)

---

## Definition of Done

All of the following criteria must be met before Phase 2.1 is considered complete.

---

## Checklist

### ToolParameter Model (src/forge/tools/base.py)
- [ ] `ToolParameter` Pydantic model implemented
- [ ] Fields: name, type, description, required, default, enum
- [ ] Fields: min_length, max_length (for strings)
- [ ] Fields: minimum, maximum (for numbers)
- [ ] `to_json_schema()` method returns valid JSON Schema dict
- [ ] Type field accepts: "string", "integer", "number", "boolean", "array", "object"
- [ ] Enum constraints included in JSON Schema when present
- [ ] Numeric constraints (min/max) included in JSON Schema
- [ ] String length constraints included in JSON Schema
- [ ] Default values included in JSON Schema when present

### ToolResult Model (src/forge/tools/base.py)
- [ ] `ToolResult` Pydantic model implemented
- [ ] Fields: success, output, error, duration_ms, metadata
- [ ] `ok(output, **metadata)` class method creates success result
- [ ] `fail(error, **metadata)` class method creates failure result
- [ ] `to_display()` method returns human-readable string
- [ ] Success result: to_display() returns output
- [ ] Failure result: to_display() returns "Error: {error}"

### ExecutionContext Model (src/forge/tools/base.py)
- [ ] `ExecutionContext` Pydantic model implemented
- [ ] Fields: working_dir, session_id, agent_id, dry_run, timeout
- [ ] Fields: max_output_size, metadata
- [ ] Default values: dry_run=False, timeout=120, max_output_size=100000
- [ ] metadata defaults to empty dict

### ToolCategory Enum (src/forge/tools/base.py)
- [ ] `ToolCategory` string enum implemented
- [ ] Values: FILE, EXECUTION, WEB, TASK, NOTEBOOK, MCP, OTHER
- [ ] String values: "file", "execution", "web", "task", "notebook", "mcp", "other"

### BaseTool Abstract Class (src/forge/tools/base.py)
- [ ] `BaseTool` ABC class implemented
- [ ] Abstract property: `name` -> str
- [ ] Abstract property: `description` -> str
- [ ] Abstract property: `category` -> ToolCategory
- [ ] Abstract property: `parameters` -> List[ToolParameter]
- [ ] Abstract method: `_execute(context, **kwargs)` -> ToolResult (async)
- [ ] Public method: `execute(context, **kwargs)` -> ToolResult (async)
- [ ] Method: `validate_params(**kwargs)` -> tuple[bool, str | None]
- [ ] Method: `_check_type(value, expected)` -> bool
- [ ] Method: `to_openai_schema()` -> Dict
- [ ] Method: `to_anthropic_schema()` -> Dict
- [ ] Method: `to_langchain_tool()` -> Tool

### Parameter Validation (BaseTool.validate_params)
- [ ] Returns (True, None) for valid parameters
- [ ] Returns (False, error_msg) for invalid parameters
- [ ] Detects missing required parameters
- [ ] Validates type: string
- [ ] Validates type: integer (not float, not string)
- [ ] Validates type: number (int or float)
- [ ] Validates type: boolean
- [ ] Validates type: array (list)
- [ ] Validates type: object (dict)
- [ ] Validates enum constraints
- [ ] Validates minimum/maximum for numbers
- [ ] Validates min_length/max_length for strings
- [ ] Allows unknown types (returns True)
- [ ] Optional parameters can be omitted

### Tool Execution (BaseTool.execute)
- [ ] Calls validate_params before execution
- [ ] Returns failure result on validation error
- [ ] Calls _execute with context and kwargs
- [ ] Wraps execution in asyncio.wait_for with timeout
- [ ] Returns timeout failure result on TimeoutError
- [ ] Catches and wraps all exceptions
- [ ] Never raises exceptions to caller
- [ ] Supports dry_run mode in context
- [ ] Returns dry run result when dry_run=True

### OpenAI Schema Generation (BaseTool.to_openai_schema)
- [ ] Returns dict with "type": "function"
- [ ] Contains nested "function" object
- [ ] Function has "name" matching tool name
- [ ] Function has "description" matching tool description
- [ ] Function has "parameters" object
- [ ] Parameters has "type": "object"
- [ ] Parameters has "properties" dict
- [ ] Parameters has "required" array
- [ ] Property schemas generated from ToolParameter.to_json_schema()
- [ ] Only required parameters in "required" array

### Anthropic Schema Generation (BaseTool.to_anthropic_schema)
- [ ] Returns dict with "name" at top level
- [ ] Returns dict with "description" at top level
- [ ] Contains "input_schema" object
- [ ] input_schema has "type": "object"
- [ ] input_schema has "properties" dict
- [ ] input_schema has "required" array
- [ ] Property schemas generated from ToolParameter.to_json_schema()

### LangChain Integration (BaseTool.to_langchain_tool)
- [ ] Returns LangChain Tool instance
- [ ] Tool has correct name
- [ ] Tool has correct description
- [ ] Tool is callable
- [ ] Tool executes the underlying _execute method

### ToolExecution Record (src/forge/tools/base.py)
- [ ] `ToolExecution` Pydantic model implemented
- [ ] Fields: tool_name, parameters, context, result
- [ ] Fields: started_at, completed_at, duration_ms
- [ ] All fields correctly typed

### ToolRegistry Singleton (src/forge/tools/registry.py)
- [ ] `ToolRegistry` class implemented
- [ ] Singleton pattern: only one instance exists
- [ ] `_instance` class variable holds singleton
- [ ] `_tools` dict stores registered tools
- [ ] `register(tool)` adds tool to registry
- [ ] `register_many(tools)` adds multiple tools
- [ ] `deregister(name)` removes tool, returns bool
- [ ] `get(name)` returns tool or None
- [ ] `get_or_raise(name)` returns tool or raises ToolError
- [ ] `exists(name)` returns bool
- [ ] `list_all()` returns List[BaseTool]
- [ ] `list_names()` returns List[str] (sorted)
- [ ] `list_by_category(category)` returns filtered list
- [ ] `count()` returns int
- [ ] `clear()` removes all tools
- [ ] `reset()` class method recreates singleton (for testing)
- [ ] Duplicate registration raises ToolError

### ToolExecutor (src/forge/tools/executor.py)
- [ ] `ToolExecutor` class implemented
- [ ] Constructor takes ToolRegistry
- [ ] `execute(tool_name, context, **kwargs)` async method
- [ ] Returns failure for unknown tool
- [ ] Logs execution start (info level)
- [ ] Logs parameters (debug level)
- [ ] Calls tool.execute() with context and kwargs
- [ ] Logs success (info level)
- [ ] Logs failure (warning level)
- [ ] Tracks executions in internal list
- [ ] `get_executions()` returns List[ToolExecution]
- [ ] `clear_executions()` clears history
- [ ] `get_all_schemas(format)` returns list of schemas
- [ ] Supports format="openai"
- [ ] Supports format="anthropic"
- [ ] Raises ValueError for unknown format
- [ ] `get_schemas_by_category(category, format)` filters by category

### Error Handling
- [ ] `ToolError` exception class exists (from Phase 1.1)
- [ ] ToolError has tool_name attribute
- [ ] ToolError has descriptive message
- [ ] All tool operations catch and handle exceptions
- [ ] No unhandled exceptions escape the tool system

### Thread Safety
- [ ] ToolRegistry uses thread-safe dict operations
- [ ] Concurrent registration doesn't corrupt state
- [ ] Concurrent execution doesn't corrupt state

### Testing
- [ ] Unit tests for ToolParameter
- [ ] Unit tests for ToolParameter.to_json_schema()
- [ ] Unit tests for ToolResult
- [ ] Unit tests for ToolResult.ok() and .fail()
- [ ] Unit tests for ExecutionContext
- [ ] Unit tests for ToolCategory
- [ ] Unit tests for BaseTool validation
- [ ] Unit tests for BaseTool schema generation
- [ ] Unit tests for BaseTool execution
- [ ] Unit tests for BaseTool timeout handling
- [ ] Unit tests for ToolRegistry singleton
- [ ] Unit tests for ToolRegistry registration
- [ ] Unit tests for ToolRegistry deregistration
- [ ] Unit tests for ToolRegistry lookup
- [ ] Unit tests for ToolRegistry listing
- [ ] Unit tests for ToolExecutor execution
- [ ] Unit tests for ToolExecutor schema generation
- [ ] Unit tests for ToolExecutor execution tracking
- [ ] Integration test: full tool lifecycle
- [ ] Test coverage ≥ 90%

---

## Verification Commands

```bash
# 1. Verify module structure
ls -la src/forge/tools/
# Expected: __init__.py, base.py, registry.py, executor.py

# 2. Test imports
python -c "
from forge.tools.base import (
    ToolParameter, ToolResult, ExecutionContext,
    ToolCategory, BaseTool, ToolExecution
)
from forge.tools.registry import ToolRegistry
from forge.tools.executor import ToolExecutor
print('All imports successful')
"

# 3. Test ToolParameter JSON Schema
python -c "
from forge.tools.base import ToolParameter

param = ToolParameter(
    name='file_path',
    type='string',
    description='Path to file',
    required=True,
    min_length=1
)
schema = param.to_json_schema()
assert schema['type'] == 'string'
assert schema['description'] == 'Path to file'
assert schema.get('minLength') == 1
print('ToolParameter: OK')
"

# 4. Test ToolResult factory methods
python -c "
from forge.tools.base import ToolResult

success = ToolResult.ok('output', lines=10)
assert success.success == True
assert success.output == 'output'
assert success.metadata['lines'] == 10

failure = ToolResult.fail('error message')
assert failure.success == False
assert failure.error == 'error message'

print('ToolResult: OK')
"

# 5. Test concrete tool implementation
python -c "
import asyncio
from forge.tools.base import (
    BaseTool, ToolParameter, ToolResult,
    ExecutionContext, ToolCategory
)

class EchoTool(BaseTool):
    @property
    def name(self): return 'Echo'

    @property
    def description(self): return 'Echo a message'

    @property
    def category(self): return ToolCategory.OTHER

    @property
    def parameters(self):
        return [ToolParameter(
            name='message',
            type='string',
            description='Message to echo',
            required=True
        )]

    async def _execute(self, context, **kwargs):
        return ToolResult.ok(kwargs['message'])

tool = EchoTool()

# Test schema generation
openai_schema = tool.to_openai_schema()
assert openai_schema['type'] == 'function'
assert openai_schema['function']['name'] == 'Echo'

anthropic_schema = tool.to_anthropic_schema()
assert anthropic_schema['name'] == 'Echo'
assert 'input_schema' in anthropic_schema

# Test validation
valid, error = tool.validate_params(message='Hello')
assert valid == True

valid, error = tool.validate_params()
assert valid == False
assert 'message' in error

# Test execution
ctx = ExecutionContext(working_dir='/tmp')
result = asyncio.run(tool.execute(ctx, message='Hello World'))
assert result.success == True
assert result.output == 'Hello World'

print('BaseTool implementation: OK')
"

# 6. Test ToolRegistry singleton
python -c "
from forge.tools.registry import ToolRegistry

# Reset for clean test
ToolRegistry.reset()

reg1 = ToolRegistry()
reg2 = ToolRegistry()
assert reg1 is reg2, 'Not a singleton!'

print('ToolRegistry singleton: OK')
"

# 7. Test ToolRegistry operations
python -c "
from forge.tools.registry import ToolRegistry
from forge.tools.base import BaseTool, ToolParameter, ToolResult, ExecutionContext, ToolCategory

class TestTool(BaseTool):
    @property
    def name(self): return 'Test'
    @property
    def description(self): return 'Test tool'
    @property
    def category(self): return ToolCategory.OTHER
    @property
    def parameters(self): return []
    async def _execute(self, context, **kwargs):
        return ToolResult.ok('test')

ToolRegistry.reset()
registry = ToolRegistry()

# Test registration
tool = TestTool()
registry.register(tool)
assert registry.exists('Test')
assert registry.count() == 1

# Test get
retrieved = registry.get('Test')
assert retrieved is tool

# Test list
tools = registry.list_all()
assert len(tools) == 1

names = registry.list_names()
assert names == ['Test']

# Test deregister
result = registry.deregister('Test')
assert result == True
assert not registry.exists('Test')

print('ToolRegistry operations: OK')
"

# 8. Test ToolExecutor
python -c "
import asyncio
from forge.tools.registry import ToolRegistry
from forge.tools.executor import ToolExecutor
from forge.tools.base import BaseTool, ToolParameter, ToolResult, ExecutionContext, ToolCategory

class EchoTool(BaseTool):
    @property
    def name(self): return 'Echo'
    @property
    def description(self): return 'Echo'
    @property
    def category(self): return ToolCategory.OTHER
    @property
    def parameters(self):
        return [ToolParameter(name='msg', type='string', description='Message', required=True)]
    async def _execute(self, context, **kwargs):
        return ToolResult.ok(kwargs['msg'])

ToolRegistry.reset()
registry = ToolRegistry()
registry.register(EchoTool())

executor = ToolExecutor(registry)
ctx = ExecutionContext(working_dir='/tmp')

# Test successful execution
result = asyncio.run(executor.execute('Echo', ctx, msg='Hello'))
assert result.success == True
assert result.output == 'Hello'

# Test unknown tool
result = asyncio.run(executor.execute('Unknown', ctx))
assert result.success == False
assert 'Unknown' in result.error

# Test schema generation
schemas = executor.get_all_schemas('openai')
assert len(schemas) == 1
assert schemas[0]['function']['name'] == 'Echo'

print('ToolExecutor: OK')
"

# 9. Test timeout handling
python -c "
import asyncio
from forge.tools.base import BaseTool, ToolParameter, ToolResult, ExecutionContext, ToolCategory

class SlowTool(BaseTool):
    @property
    def name(self): return 'Slow'
    @property
    def description(self): return 'Slow tool'
    @property
    def category(self): return ToolCategory.OTHER
    @property
    def parameters(self): return []
    async def _execute(self, context, **kwargs):
        await asyncio.sleep(10)
        return ToolResult.ok('done')

tool = SlowTool()
ctx = ExecutionContext(working_dir='/tmp', timeout=1)
result = asyncio.run(tool.execute(ctx))

assert result.success == False
assert 'timed out' in result.error.lower()

print('Timeout handling: OK')
"

# 10. Run all unit tests
pytest tests/unit/tools/ -v --cov=forge.tools --cov-report=term-missing

# Expected: All tests pass, coverage ≥ 90%

# 11. Type checking
mypy src/forge/tools/ --strict
# Expected: No errors

# 12. Linting
ruff check src/forge/tools/
# Expected: No errors

# 13. Test LangChain integration
python -c "
from forge.tools.base import BaseTool, ToolParameter, ToolResult, ExecutionContext, ToolCategory
from langchain_core.tools import Tool

class TestTool(BaseTool):
    @property
    def name(self): return 'Test'
    @property
    def description(self): return 'Test tool'
    @property
    def category(self): return ToolCategory.OTHER
    @property
    def parameters(self): return []
    async def _execute(self, context, **kwargs):
        return ToolResult.ok('result')

tool = TestTool()
lc_tool = tool.to_langchain_tool()

assert isinstance(lc_tool, Tool)
assert lc_tool.name == 'Test'
assert lc_tool.description == 'Test tool'

print('LangChain integration: OK')
"
```

---

## Quality Gates

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Test Coverage | ≥ 90% | `pytest --cov` |
| Type Hints | 100% public APIs | `mypy --strict` |
| Lint Errors | 0 | `ruff check` |
| McCabe Complexity | ≤ 10 | `ruff check --select=C901` |
| Schema Validation | 100% | Manual test with LLM |

---

## Files to Create

| File | Purpose |
|------|---------|
| `src/forge/tools/__init__.py` | Package exports |
| `src/forge/tools/base.py` | BaseTool, ToolParameter, ToolResult, ExecutionContext, ToolCategory, ToolExecution |
| `src/forge/tools/registry.py` | ToolRegistry singleton |
| `src/forge/tools/executor.py` | ToolExecutor class |
| `tests/unit/tools/__init__.py` | Test package |
| `tests/unit/tools/test_base.py` | Base classes tests |
| `tests/unit/tools/test_registry.py` | Registry tests |
| `tests/unit/tools/test_executor.py` | Executor tests |

---

## Dependencies to Verify

Ensure these are in `pyproject.toml`:
```toml
[tool.poetry.dependencies]
pydantic = "^2.5"
langchain-core = "^0.3"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-asyncio = "^0.23"
pytest-cov = "^4.1"
mypy = "^1.8"
ruff = "^0.1"
```

---

## Integration Points

Phase 2.1 provides foundations for:

| Consumer | What It Uses |
|----------|--------------|
| Phase 2.2 (File Tools) | BaseTool, ToolParameter, ToolResult |
| Phase 2.3 (Execution Tools) | BaseTool, ToolParameter, ToolResult |
| Phase 3.2 (LangChain) | ToolRegistry, to_langchain_tool() |
| Phase 4.1 (Permissions) | ToolRegistry, ExecutionContext |
| Phase 4.2 (Hooks) | ToolExecutor, ToolExecution |
| Phase 8.1 (MCP) | BaseTool interface |

---

## Manual Testing Checklist

- [ ] Can create custom tool by extending BaseTool
- [ ] Tool validates parameters correctly
- [ ] Tool executes and returns results
- [ ] Tool respects timeout setting
- [ ] Dry run mode works correctly
- [ ] OpenAI schema validates with OpenAI API
- [ ] Anthropic schema validates with Anthropic API
- [ ] LangChain tool works in LangChain agent
- [ ] Registry maintains singleton across imports
- [ ] Executor tracks execution history
- [ ] Error messages are clear and actionable

---

## Sign-Off

Phase 2.1 is complete when:

1. [ ] All checklist items above are checked
2. [ ] All verification commands pass
3. [ ] All quality gates are met
4. [ ] Manual testing checklist completed
5. [ ] Code has been reviewed (if applicable)
6. [ ] No TODO comments remain in Phase 2.1 code

---

## Next Phase

After completing Phase 2.1, proceed to:
- **Phase 2.2: File Tools**

Phase 2.2 will implement:
- ReadTool
- WriteTool
- EditTool
- GlobTool
- GrepTool

These all extend BaseTool from Phase 2.1.
