# Architecture Overview

This document describes the high-level architecture of Code-Forge.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                           CLI Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │     REPL        │  │    Commands     │  │     Modes       │ │
│  │   (prompt_     │  │  (/help, /exit) │  │ (plan, headless)│ │
│  │    toolkit)     │  │                 │  │                 │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
└───────────┼────────────────────┼────────────────────┼──────────┘
            │                    │                    │
            └────────────────────┴────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Core Layer                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │    Session      │  │    Context      │  │   Permission    │ │
│  │    Manager      │  │    Manager      │  │    System       │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
│           │                    │                    │           │
│  ┌────────┴────────┐  ┌────────┴────────┐  ┌────────┴────────┐ │
│  │     Hooks       │  │    Config       │  │    Plugins      │ │
│  │    System       │  │    Loader       │  │    Manager      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Tool Layer                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Tool Registry  │  │  Tool Executor  │  │    File Tools   │ │
│  └─────────────────┘  └─────────────────┘  │  (Read, Write,  │ │
│                                             │   Edit, Glob,   │ │
│  ┌─────────────────┐  ┌─────────────────┐  │   Grep)         │ │
│  │  Exec Tools     │  │   Web Tools     │  └─────────────────┘ │
│  │  (Bash, etc.)   │  │  (Fetch, Search)│                      │
│  └─────────────────┘  └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Integration Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │    LangChain    │  │      Git        │  │     GitHub      │ │
│  │   Middleware    │  │  Integration    │  │   Integration   │ │
│  └────────┬────────┘  └─────────────────┘  └─────────────────┘ │
│           │                                                      │
│  ┌────────┴────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   OpenRouter    │  │       MCP       │  │    Subagents    │ │
│  │     Client      │  │     Support     │  │     System      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### CLI Layer

**REPL** (`cli/repl.py`)
- Interactive prompt using prompt_toolkit
- Input handling and display
- Theme support

**Commands** (`commands/`)
- Slash command parsing and execution
- Built-in commands (/help, /session, etc.)
- Command registry for extensibility

**Modes** (`modes/`)
- Operating modes (normal, plan, headless)
- Mode-specific prompts and behaviors

### Core Layer

**Session Manager** (`sessions/`)
- Conversation persistence
- Message and tool history
- Session index for fast listing

**Context Manager** (`context/`)
- Token counting and budgeting
- Truncation strategies
- LLM-based compaction

**Permission System** (`permissions/`)
- Pattern-based permission rules
- Allow/Ask/Deny levels
- User confirmation prompts

**Hooks System** (`hooks/`)
- Pre/post execution hooks
- Shell command execution
- Event-driven architecture

**Config Loader** (`config/`)
- Hierarchical configuration
- YAML/JSON file support
- Environment variable overrides

**Plugin Manager** (`plugins/`)
- Plugin discovery and loading
- Plugin lifecycle management
- Tool/command/hook registration

### Tool Layer

**Tool Registry** (`tools/registry.py`)
- Thread-safe tool registration
- Tool lookup by name

**Tool Executor** (`tools/executor.py`)
- Parameter validation
- Execution tracking
- Error handling

**File Tools** (`tools/file/`)
- Read, Write, Edit
- Glob, Grep
- Security utilities

**Execution Tools** (`tools/execution/`)
- Bash command execution
- Background process management
- Shell lifecycle

**Web Tools** (`web/`)
- URL fetching
- Web search
- Content parsing

### Integration Layer

**LangChain Middleware** (`langchain/`)
- OpenRouterLLM wrapper
- Message conversion
- Agent executor (ReAct pattern)

**OpenRouter Client** (`llm/client.py`)
- API communication
- Streaming support
- Retry logic

**Git Integration** (`git/`)
- Repository operations
- Safety guards
- Status/diff/history

**GitHub Integration** (`github/`)
- Issues and PRs
- Actions workflows
- API client

**MCP Support** (`mcp/`)
- Protocol implementation
- Transport abstraction
- Tool integration

**Subagents** (`agents/`)
- Agent types (explore, plan, etc.)
- Parallel execution
- Resource limits

## Design Principles

1. **Modularity** - Each component has clear boundaries
2. **Extensibility** - Plugin system for customization
3. **Safety** - Permission checks and safety guards
4. **Performance** - Async operations, caching
5. **Testability** - Dependency injection, mocking support
