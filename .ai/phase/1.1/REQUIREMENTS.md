# Phase 1.1: Project Foundation - Requirements

**Phase:** 1.1
**Name:** Project Foundation
**Status:** Not Started
**Dependencies:** None (First Phase)

---

## Overview

This phase establishes the foundational project structure, dependencies, and core abstractions that all subsequent phases will build upon. No functional features are implemented - only the scaffolding.

---

## Functional Requirements

### FR-1.1.1: Project Structure
- Create Python package `Code-Forge` with proper module structure
- Establish clear separation: `cli/`, `core/`, `tools/`, `providers/`, `utils/`
- Create `__init__.py` files with appropriate exports
- Set up `__main__.py` for `python -m Code-Forge` execution

### FR-1.1.2: Dependency Management
- Use `pyproject.toml` with setuptools for dependency management
- Use virtual environment (`.venv/`) for isolation
- Define core dependencies:
  - Python >=3.10,<4.0 (3.11+ recommended)
  - pydantic >=2.0 for data validation
  - rich >=13.0 for terminal formatting
  - textual >=0.40 for TUI framework
  - prompt_toolkit >=3.0 for input handling
  - httpx >=0.25 for HTTP client (HTTP/2)
  - aiohttp >=3.9 for WebSocket/high-concurrency
  - langchain >=0.1.0 for agent framework
  - pytest >=7.0 for testing
  - mypy for type checking
  - ruff for linting

### FR-1.1.3: Core Abstractions (Interfaces Only)
- Define `ITool` abstract base class
- Define `IModelProvider` abstract base class
- Define `IConfigLoader` abstract base class
- Define `ISessionRepository` abstract base class
- Define common result types (`Result`, `Error`)
- Define core value objects (`AgentId`, `SessionId`, `ToolName`)

### FR-1.1.4: Logging Infrastructure
- Set up structured logging with `logging` module
- Create log formatters for console and file output
- Define log levels and filtering
- Create `get_logger()` for consistent logger creation

### FR-1.1.5: Exception Hierarchy
- Define base `Code-ForgeError` exception
- Create specific exceptions: `ConfigError`, `ToolError`, `ProviderError`, `PermissionDeniedError`
- Implement exception context and chaining

### FR-1.1.6: Entry Point
- Create CLI entry point `forge` command
- Implement `--version` flag
- Implement `--help` flag (basic)
- Return proper exit codes (0 success, 1 error)

---

## Non-Functional Requirements

### NFR-1.1.1: Code Quality
- 100% type hints on all public APIs
- McCabe complexity ≤ 8 for all functions
- Docstrings on all public classes and methods
- Pass mypy strict mode
- Pass ruff linting

### NFR-1.1.2: Project Standards
- Follow PEP 8 style guide
- Use absolute imports only
- No circular imports
- Clear module boundaries

### NFR-1.1.3: Testing Foundation
- Set up pytest configuration
- Create test directory structure mirroring source
- Achieve 90% coverage on Phase 1.1 code
- Create fixtures for common test patterns

---

## Technical Specifications

### Directory Structure
```
src/forge/                    # Project root (also the package)
├── __init__.py              # Package init, version
├── __main__.py              # Entry point for python -m
├── pyproject.toml           # Project configuration
├── README.md                # Project readme
├── .venv/                   # Virtual environment
├── cli/
│   ├── __init__.py
│   └── main.py              # CLI entry point
├── core/
│   ├── __init__.py
│   ├── interfaces.py        # All abstract base classes
│   ├── types.py             # Value objects, type aliases
│   ├── errors.py            # Exception hierarchy
│   └── logging.py           # Logging setup
├── tools/
│   └── __init__.py          # Empty, placeholder
├── providers/
│   └── __init__.py          # Empty, placeholder
├── config/
│   └── __init__.py          # Empty, placeholder
├── session/
│   └── __init__.py          # Empty, placeholder
├── utils/
│   ├── __init__.py
│   └── result.py            # Result/Error types
└── tests/
    ├── __init__.py
    ├── conftest.py          # Shared fixtures
    ├── unit/
    │   ├── __init__.py
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── test_types.py
    │   │   ├── test_errors.py
    │   │   ├── test_interfaces.py
    │   │   └── test_logging.py
    │   ├── utils/
    │   │   ├── __init__.py
    │   │   └── test_result.py
    │   └── cli/
    │       ├── __init__.py
    │       └── test_main.py
    └── integration/
        └── __init__.py
```

### pyproject.toml Structure
```toml
[project]
name = "forge"
version = "0.1.0"
description = "AI-powered CLI development assistant"
requires-python = ">=3.10,<4.0"

dependencies = [
    "pydantic>=2.5,<3.0",
    "rich>=13.7,<14.0",
    "textual>=0.47,<1.0",
    "prompt-toolkit>=3.0,<4.0",
    "httpx[http2]>=0.26,<1.0",
    "aiohttp>=3.9,<4.0",
    "langchain>=0.1,<1.0",
    "langchain-core>=0.1,<1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4,<9.0",
    "pytest-cov>=4.1,<6.0",
    "pytest-asyncio>=0.23,<1.0",
    "mypy>=1.8,<2.0",
    "ruff>=0.1,<1.0",
]

[project.scripts]
forge = "Code-Forge.cli.main:main"

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.mypy]
strict = true
python_version = "3.11"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

## Acceptance Criteria

### Definition of Done

- [ ] `pyproject.toml` exists with all dependencies defined
- [ ] `python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"` completes without errors
- [ ] `forge --version` outputs version number
- [ ] `forge --help` displays help text
- [ ] All abstract base classes defined in `core/interfaces.py`
- [ ] All value objects defined in `core/types.py`
- [ ] Exception hierarchy in `core/errors.py`
- [ ] Logging infrastructure in `core/logging.py`
- [ ] Result type in `utils/result.py`
- [ ] `pytest` runs and passes
- [ ] `mypy .` passes with no errors
- [ ] `ruff check .` passes with no errors
- [ ] Test coverage ≥ 90% for Phase 1.1 code

### Verification Commands
```bash
# Create and activate virtual environment
python -m venv .venv
. .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run application
forge --version
forge --help

# Or run as module (works without installing)
PYTHONPATH=. python -m Code-Forge --version

# Run tests
pytest --cov=. --cov-report=term-missing

# Type checking
mypy .

# Linting
ruff check .
```

---

## Out of Scope

The following are explicitly NOT part of Phase 1.1:
- Any functional REPL behavior
- Configuration file loading
- Tool implementations
- Model provider connections
- Session persistence
- Any user-facing features beyond --version and --help

---

## Notes

This phase is purely foundational. Success is measured by:
1. Clean project structure that supports future phases
2. Type-safe abstractions that enforce contracts
3. Development tooling (tests, linting, type checking) working
4. No functionality - just scaffolding

All subsequent phases depend on this foundation being solid.
