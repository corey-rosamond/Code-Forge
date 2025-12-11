# Code-Forge: Conventions

Quick reference for coding standards and patterns.

---

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `ToolRegistry`, `SessionManager` |
| Functions | snake_case | `get_logger`, `fire_event` |
| Constants | UPPER_SNAKE | `MAX_FILE_SIZE`, `DEFAULT_TIMEOUT` |
| Private | Leading underscore | `_execute`, `_lock` |
| Files | snake_case | `tool_registry.py`, `session_manager.py` |
| Test files | `test_` prefix | `test_registry.py` |

---

## Type Hints

**Always use type hints.** The project uses `mypy --strict`.

```python
# Good
def process(items: list[str], limit: int | None = None) -> dict[str, int]:
    ...

# Bad
def process(items, limit=None):
    ...
```

Use `from __future__ import annotations` for forward references.

---

## Import Order

```python
# 1. Future imports
from __future__ import annotations

# 2. Standard library
import asyncio
import threading
from typing import TYPE_CHECKING, Any

# 3. Third-party
from pydantic import BaseModel
from langchain_core.tools import StructuredTool

# 4. Local imports
from code_forge.core.errors import CodeForgeError
from code_forge.core.logging import get_logger

# 5. Type checking only imports
if TYPE_CHECKING:
    from code_forge.tools.base import BaseTool
```

---

## Error Handling

```python
# Use Result pattern for expected failures
def read_file(path: Path) -> ToolResult:
    if not path.exists():
        return ToolResult.fail(f"File not found: {path}")
    try:
        content = path.read_text()
        return ToolResult.ok(content)
    except OSError as e:
        return ToolResult.fail(f"Cannot read file: {e}")

# Let unexpected errors propagate (caught by execute() wrapper)
async def _execute(self, context: ExecutionContext, **kwargs) -> ToolResult:
    # Don't catch Exception here - let BaseTool.execute() handle it
    result = do_risky_operation()
    return ToolResult.ok(result)
```

---

## Async Patterns

```python
# Lazy initialization for asyncio primitives
class Manager:
    def __init__(self):
        self._lock: asyncio.Lock | None = None

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def do_work(self) -> None:
        async with self._get_lock():
            # protected work
            pass
```

---

## Singleton Pattern

```python
class MyRegistry:
    _instance: MyRegistry | None = None
    _lock = threading.Lock()

    def __new__(cls) -> MyRegistry:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._items = {}
                cls._instance._rlock = threading.RLock()
            return cls._instance

    @classmethod
    def get_instance(cls) -> MyRegistry:
        return cls()

    @classmethod
    def reset(cls) -> None:
        """For testing only."""
        with cls._lock:
            cls._instance = None
```

---

## Testing Patterns

```python
# Use pytest fixtures
@pytest.fixture
def tool():
    return MyTool()

@pytest.fixture
def context():
    return ExecutionContext(working_dir="/tmp")

# Reset singletons in fixtures
@pytest.fixture(autouse=True)
def reset_registry():
    ToolRegistry.reset()
    yield
    ToolRegistry.reset()

# Test both success and failure
async def test_success(tool, context):
    result = await tool.execute(context, input="valid")
    assert result.success

async def test_failure(tool, context):
    result = await tool.execute(context, input="")
    assert not result.success
    assert "error message" in result.error

# Use parametrize for variations
@pytest.mark.parametrize("input,expected", [
    ("a", "result_a"),
    ("b", "result_b"),
])
async def test_variations(tool, context, input, expected):
    result = await tool.execute(context, input=input)
    assert result.output == expected
```

---

## Docstrings

```python
def calculate_tokens(text: str, model: str | None = None) -> int:
    """Count tokens in text for a specific model.

    Args:
        text: The text to count tokens for.
        model: Model name for tokenizer selection. Defaults to approximate counting.

    Returns:
        Number of tokens in the text.

    Raises:
        ValueError: If text is empty.

    Example:
        >>> count = calculate_tokens("Hello world", model="gpt-4")
        >>> print(count)
        2
    """
```

---

## Logging

```python
from code_forge.core.logging import get_logger

logger = get_logger(__name__)

# Use appropriate levels
logger.debug("Detailed info for debugging")
logger.info("Normal operation info")
logger.warning("Something unexpected but handled")
logger.error("Error that affects functionality")
logger.exception("Error with stack trace")  # In except blocks
```

---

## Configuration

```python
# Use Pydantic models
class MyConfig(BaseModel):
    enabled: bool = True
    max_items: int = 100
    timeout: float = 30.0

    model_config = {"extra": "forbid"}  # Reject unknown fields

# Load from multiple sources
config = ConfigLoader().load_all()
my_config = MyConfig(**config.get("my_section", {}))
```

---

## Security

```python
# Never use shell=True with user input
subprocess.run(["ls", "-la", path], capture_output=True)  # Good
subprocess.run(f"ls -la {path}", shell=True)  # Bad

# Validate paths
def safe_path(path: str, base_dir: str) -> Path:
    resolved = Path(path).resolve()
    base = Path(base_dir).resolve()
    if not str(resolved).startswith(str(base)):
        raise SecurityError("Path traversal detected")
    return resolved

# Sanitize output
def truncate_output(output: str, max_size: int = 100000) -> str:
    if len(output) > max_size:
        return output[:max_size] + f"\n... (truncated {len(output) - max_size} chars)"
    return output
```

---

## Quick Checklist

Before committing:
- [ ] Type hints on all functions
- [ ] Docstrings on public APIs
- [ ] Tests for new code
- [ ] `pytest tests/` passes
- [ ] `mypy src/code_forge/` passes
- [ ] `ruff check src/code_forge/` passes
