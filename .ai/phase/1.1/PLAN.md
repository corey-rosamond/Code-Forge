# Phase 1.1: Project Foundation - Architectural Plan

**Phase:** 1.1
**Name:** Project Foundation
**Methodology:** SOLID Principles, Clean Architecture Foundation

---

## Architectural Overview

Phase 1.1 establishes the foundational architecture using Hexagonal Architecture principles. We define ports (interfaces) without adapters (implementations), creating contracts that all future code must honor.

---

## Design Principles Applied

### Single Responsibility Principle (SRP)
Each module has one clear purpose:
- `interfaces.py` - Define contracts
- `types.py` - Define value objects
- `errors.py` - Define exceptions
- `logging.py` - Configure logging
- `result.py` - Define result types

### Open-Closed Principle (OCP)
Abstract base classes allow extension without modification:
- `ITool` can have unlimited implementations
- `IModelProvider` supports any AI provider
- `IConfigLoader` supports any config source

### Dependency Inversion Principle (DIP)
High-level modules depend on abstractions:
- All interfaces defined in `core/`
- No concrete implementations in Phase 1.1
- Future phases implement against these interfaces

---

## Core Abstractions

### ITool Interface

```python
from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel

class ToolParameter(BaseModel):
    """Schema for a tool parameter."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None

class ToolResult(BaseModel):
    """Result from tool execution."""
    success: bool
    output: Any
    error: str | None = None
    metadata: Dict[str, Any] = {}

class ITool(ABC):
    """
    Abstract base class for all tools.

    Tools are the primary way the agent interacts with the environment.
    Each tool has a name, description, parameters, and execute method.

    McCabe Complexity Target: All methods ≤ 5
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description for the LLM."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> list[ToolParameter]:
        """List of parameters this tool accepts."""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with success status and output
        """
        pass

    def validate_params(self, **kwargs: Any) -> tuple[bool, str | None]:
        """
        Validate parameters before execution.

        Returns:
            Tuple of (is_valid, error_message)
        """
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                return False, f"Missing required parameter: {param.name}"
        return True, None
```

### IModelProvider Interface

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator
from pydantic import BaseModel

class Message(BaseModel):
    """A conversation message."""
    role: str  # "user", "assistant", "system", "tool"
    content: str
    name: str | None = None
    tool_calls: list[dict] | None = None

class CompletionRequest(BaseModel):
    """Request for model completion."""
    messages: list[Message]
    model: str
    max_tokens: int | None = None
    temperature: float = 1.0
    stream: bool = False
    tools: list[dict] | None = None

class CompletionResponse(BaseModel):
    """Response from model completion."""
    content: str
    model: str
    finish_reason: str
    usage: dict[str, int]
    tool_calls: list[dict] | None = None

class IModelProvider(ABC):
    """
    Abstract base class for AI model providers.

    Supports both OpenRouter and direct API connections.
    All providers must support streaming.

    McCabe Complexity Target: All methods ≤ 6
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier."""
        pass

    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """
        Send completion request and return full response.

        Args:
            request: The completion request

        Returns:
            Complete response from the model
        """
        pass

    @abstractmethod
    async def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        """
        Stream completion response token by token.

        Args:
            request: The completion request

        Yields:
            Individual tokens as they arrive
        """
        pass

    @abstractmethod
    async def list_models(self) -> list[str]:
        """Return list of available model IDs."""
        pass

    @property
    @abstractmethod
    def supports_tools(self) -> bool:
        """Whether this provider supports tool/function calling."""
        pass
```

### IConfigLoader Interface

```python
from abc import ABC, abstractmethod
from typing import Any
from pathlib import Path

class IConfigLoader(ABC):
    """
    Abstract base class for configuration loaders.

    Supports loading from files, environment, and merging.

    McCabe Complexity Target: All methods ≤ 5
    """

    @abstractmethod
    def load(self, path: Path) -> dict[str, Any]:
        """
        Load configuration from a path.

        Args:
            path: Path to configuration file

        Returns:
            Configuration dictionary

        Raises:
            ConfigError: If loading fails
        """
        pass

    @abstractmethod
    def merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """
        Merge two configurations with override taking precedence.

        Args:
            base: Base configuration
            override: Override configuration

        Returns:
            Merged configuration
        """
        pass

    @abstractmethod
    def validate(self, config: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate configuration against schema.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        pass
```

### ISessionRepository Interface

```python
from abc import ABC, abstractmethod
from datetime import datetime
from pydantic import BaseModel

class SessionId(BaseModel):
    """Value object for session identification."""
    value: str

    def __str__(self) -> str:
        return self.value

class SessionSummary(BaseModel):
    """Summary of a session for listing."""
    id: SessionId
    project_path: str
    created_at: datetime
    last_activity: datetime
    message_count: int
    preview: str

class Session(BaseModel):
    """Full session data."""
    id: SessionId
    project_path: str
    created_at: datetime
    last_activity: datetime
    messages: list[dict]
    context: dict
    metadata: dict

class ISessionRepository(ABC):
    """
    Abstract base class for session persistence.

    McCabe Complexity Target: All methods ≤ 5
    """

    @abstractmethod
    async def save(self, session: Session) -> None:
        """Persist session to storage."""
        pass

    @abstractmethod
    async def load(self, session_id: SessionId) -> Session | None:
        """Load session by ID, returns None if not found."""
        pass

    @abstractmethod
    async def list_recent(self, limit: int = 10) -> list[SessionSummary]:
        """List recent sessions with summaries."""
        pass

    @abstractmethod
    async def delete(self, session_id: SessionId) -> bool:
        """Delete session, returns True if deleted."""
        pass
```

---

## Value Objects

```python
from pydantic import BaseModel, Field
from typing import NewType
from uuid import uuid4

# Type aliases for clarity
ToolName = NewType('ToolName', str)
ModelId = NewType('ModelId', str)

class AgentId(BaseModel):
    """Unique identifier for an agent instance."""
    value: str = Field(default_factory=lambda: str(uuid4()))

    def __str__(self) -> str:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)

class ProjectId(BaseModel):
    """Identifier for a project (directory path hash)."""
    value: str
    path: str

    @classmethod
    def from_path(cls, path: str) -> "ProjectId":
        import hashlib
        hash_val = hashlib.sha256(path.encode()).hexdigest()[:12]
        return cls(value=hash_val, path=path)
```

---

## Exception Hierarchy

```python
class Code-ForgeError(Exception):
    """Base exception for all Code-Forge errors."""

    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(message)
        self.cause = cause

    def __str__(self) -> str:
        if self.cause:
            return f"{self.args[0]} (caused by: {self.cause})"
        return self.args[0]

class ConfigError(Code-ForgeError):
    """Configuration-related errors."""
    pass

class ToolError(Code-ForgeError):
    """Tool execution errors."""
    def __init__(self, tool_name: str, message: str, cause: Exception | None = None):
        super().__init__(f"Tool '{tool_name}': {message}", cause)
        self.tool_name = tool_name

class ProviderError(Code-ForgeError):
    """Model provider errors."""
    def __init__(self, provider: str, message: str, cause: Exception | None = None):
        super().__init__(f"Provider '{provider}': {message}", cause)
        self.provider = provider

class PermissionDeniedError(Code-ForgeError):
    """Permission denied errors.

    Note: Named PermissionDeniedError to avoid shadowing the builtin
    PermissionError exception, which could cause subtle bugs if code
    accidentally catches the wrong exception type.
    """
    def __init__(self, action: str, reason: str):
        super().__init__(f"Permission denied for '{action}': {reason}")
        self.action = action
        self.reason = reason

class SessionError(Code-ForgeError):
    """Session management errors."""
    pass
```

---

## Result Type Pattern

```python
from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T')

class Result(BaseModel, Generic[T]):
    """
    Result type for operations that can fail.

    Provides explicit success/failure handling without exceptions
    for expected failure cases.

    Note: Using frozen=False to allow Pydantic v2 compatibility with generics.
    """
    model_config = {"frozen": False, "arbitrary_types_allowed": True}

    success: bool
    value: T | None = None
    error: str | None = None

    @classmethod
    def ok(cls, value: T) -> "Result[T]":
        """Create successful result."""
        return cls(success=True, value=value)

    @classmethod
    def fail(cls, error: str) -> "Result[T]":
        """Create failed result."""
        return cls(success=False, error=error)

    def unwrap(self) -> T:
        """Get value or raise if failed."""
        if not self.success:
            raise ValueError(f"Result failed: {self.error}")
        if self.value is None:
            raise ValueError("Result succeeded but value is None")
        return self.value

    def unwrap_or(self, default: T) -> T:
        """Get value or return default if failed."""
        if self.success and self.value is not None:
            return self.value
        return default

    def map(self, func: "Callable[[T], U]") -> "Result[U]":
        """Apply function to value if successful."""
        if self.success and self.value is not None:
            try:
                return Result[U].ok(func(self.value))
            except Exception as e:
                return Result[U].fail(str(e))
        return Result[U].fail(self.error or "No value")


# Type variable for map function
from typing import Callable
U = TypeVar('U')
```

---

## Logging Setup

```python
import logging
import sys
from pathlib import Path
from rich.logging import RichHandler

def setup_logging(
    level: int = logging.INFO,
    log_file: Path | None = None,
    rich_console: bool = True
) -> None:
    """
    Configure logging for Code-Forge.

    Args:
        level: Logging level
        log_file: Optional file path for log output
        rich_console: Use Rich for console formatting
    """
    handlers: list[logging.Handler] = []

    if rich_console:
        handlers.append(RichHandler(
            rich_tracebacks=True,
            show_time=True,
            show_path=False
        ))
    else:
        handlers.append(logging.StreamHandler(sys.stderr))

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format="%(message)s" if rich_console else "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers
    )

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(f"forge.{name}")
```

---

## CLI Entry Point

```python
import sys
from forge import __version__

def main() -> int:
    """Main entry point for Code-Forge CLI."""
    args = sys.argv[1:]

    if "--version" in args or "-v" in args:
        print(f"forge {__version__}")
        return 0

    if "--help" in args or "-h" in args:
        print_help()
        return 0

    # Future phases will add actual functionality
    print("Code-Forge - AI Development Assistant")
    print("Run with --help for usage information")
    return 0

def print_help() -> None:
    """Print help message."""
    help_text = """
Code-Forge - AI-powered CLI Development Assistant

Usage: forge [OPTIONS] [PROMPT]

Options:
  -v, --version     Show version and exit
  -h, --help        Show this help message
  --continue        Resume most recent session
  --resume          Select session to resume
  -p, --print       Run in headless mode with prompt

For more information, visit: https://github.com/forge
"""
    print(help_text.strip())

if __name__ == "__main__":
    sys.exit(main())
```

---

## Implementation Order

1. Create `pyproject.toml` with all dependencies
2. Create directory structure with `__init__.py` files
3. Implement `core/types.py` (value objects)
4. Implement `core/errors.py` (exceptions)
5. Implement `core/interfaces.py` (ABCs)
6. Implement `core/logging.py` (logging setup)
7. Implement `utils/result.py` (Result type)
8. Implement `cli/main.py` (entry point)
9. Implement `__main__.py` (module execution)
10. Write tests for all components
11. Run mypy and fix type errors
12. Run ruff and fix lint errors

---

## Quality Gates

Before completing Phase 1.1:
- [ ] `pip install -e ".[dev]"` succeeds
- [ ] `forge --version` works
- [ ] `forge --help` works
- [ ] `pytest` passes with ≥90% coverage
- [ ] `mypy --strict` passes
- [ ] `ruff check` passes
- [ ] All interfaces are fully documented
- [ ] No TODO comments in code
