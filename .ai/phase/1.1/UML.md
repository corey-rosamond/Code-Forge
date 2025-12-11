# Phase 1.1: Project Foundation - UML Diagrams

**Phase:** 1.1
**Name:** Project Foundation
**Scope:** Core interfaces, types, and project structure

---

## 1. Package Diagram

```mermaid
flowchart TB
    subgraph forge["forge (Main Package)"]
        direction TB

        subgraph cli["cli"]
            MAIN[main.py]
        end

        subgraph core["core"]
            INTERFACES[interfaces.py]
            TYPES[types.py]
            ERRORS[errors.py]
            LOGGING[logging.py]
        end

        subgraph utils["utils"]
            RESULT[result.py]
        end

        subgraph placeholders["Placeholder Packages"]
            TOOLS[tools/]
            PROVIDERS[providers/]
            CONFIG[config/]
            SESSION[session/]
        end
    end

    cli --> core
    core --> utils
```

---

## 2. Class Diagram - Core Interfaces

```mermaid
classDiagram
    class ITool {
        <<interface>>
        +name: str
        +description: str
        +parameters: list~ToolParameter~
        +execute(**kwargs) ToolResult
        +validate_params(**kwargs) tuple
    }

    class IModelProvider {
        <<interface>>
        +name: str
        +supports_tools: bool
        +complete(request) CompletionResponse
        +stream(request) AsyncIterator~str~
        +list_models() list~str~
    }

    class IConfigLoader {
        <<interface>>
        +load(path) dict
        +merge(base, override) dict
        +validate(config) tuple
    }

    class ISessionRepository {
        <<interface>>
        +save(session) None
        +load(session_id) Session
        +list_recent(limit) list~SessionSummary~
        +delete(session_id) bool
    }

    class ToolParameter {
        <<Value Object>>
        +name: str
        +type: str
        +description: str
        +required: bool
        +default: Any
    }

    class ToolResult {
        <<Value Object>>
        +success: bool
        +output: Any
        +error: str?
        +metadata: dict
    }

    ITool --> ToolParameter
    ITool --> ToolResult
```

---

## 3. Class Diagram - Value Objects

```mermaid
classDiagram
    class AgentId {
        <<Value Object>>
        +value: str
        +__str__() str
        +__hash__() int
    }

    class SessionId {
        <<Value Object>>
        +value: str
        +__str__() str
    }

    class ProjectId {
        <<Value Object>>
        +value: str
        +path: str
        +from_path(path)$ ProjectId
    }

    class Message {
        <<Value Object>>
        +role: str
        +content: str
        +name: str?
        +tool_calls: list?
    }

    class CompletionRequest {
        <<Value Object>>
        +messages: list~Message~
        +model: str
        +max_tokens: int?
        +temperature: float
        +stream: bool
        +tools: list?
    }

    class CompletionResponse {
        <<Value Object>>
        +content: str
        +model: str
        +finish_reason: str
        +usage: dict
        +tool_calls: list?
    }

    CompletionRequest --> Message
```

---

## 4. Class Diagram - Exception Hierarchy

```mermaid
classDiagram
    class Exception {
        <<builtin>>
    }

    class Code-ForgeError {
        +message: str
        +cause: Exception?
        +__str__() str
    }

    class ConfigError {
    }

    class ToolError {
        +tool_name: str
    }

    class ProviderError {
        +provider: str
    }

    class PermissionError {
        +action: str
        +reason: str
    }

    class SessionError {
    }

    Exception <|-- Code-ForgeError
    Code-ForgeError <|-- ConfigError
    Code-ForgeError <|-- ToolError
    Code-ForgeError <|-- ProviderError
    Code-ForgeError <|-- PermissionError
    Code-ForgeError <|-- SessionError
```

---

## 5. Class Diagram - Result Type

```mermaid
classDiagram
    class Result~T~ {
        <<Generic>>
        +success: bool
        +value: T?
        +error: str?
        +ok(value)$ Result~T~
        +fail(error)$ Result~T~
        +unwrap() T
        +unwrap_or(default) T
    }
```

---

## 6. Class Diagram - Session Entities

```mermaid
classDiagram
    class Session {
        <<Entity>>
        +id: SessionId
        +project_path: str
        +created_at: datetime
        +last_activity: datetime
        +messages: list~dict~
        +context: dict
        +metadata: dict
    }

    class SessionSummary {
        <<Value Object>>
        +id: SessionId
        +project_path: str
        +created_at: datetime
        +last_activity: datetime
        +message_count: int
        +preview: str
    }

    Session --> SessionId
    SessionSummary --> SessionId
```

---

## 7. Component Diagram

```mermaid
flowchart LR
    subgraph External["External (Future Phases)"]
        USER[User]
        API[OpenRouter API]
        FS[File System]
    end

    subgraph Phase1.1["Phase 1.1 Components"]
        CLI[CLI Entry Point]
        IFACES[Interfaces]
        TYPES[Types]
        ERRORS[Errors]
        LOGGING[Logging]
        RESULT[Result Type]
    end

    USER --> CLI
    CLI --> IFACES
    CLI --> TYPES
    CLI --> ERRORS
    CLI --> LOGGING
    IFACES --> TYPES
    IFACES --> RESULT
```

---

## 8. Sequence Diagram - CLI Startup

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as cli/main.py
    participant Log as core/logging.py

    U->>CLI: forge --version
    CLI->>CLI: Parse arguments
    CLI->>CLI: Check for --version flag
    CLI-->>U: Print version
    CLI-->>U: Exit code 0

    U->>CLI: forge --help
    CLI->>CLI: Parse arguments
    CLI->>CLI: Check for --help flag
    CLI->>CLI: print_help()
    CLI-->>U: Print help text
    CLI-->>U: Exit code 0

    U->>CLI: forge
    CLI->>CLI: Parse arguments
    CLI->>Log: setup_logging()
    Log-->>CLI: Logging configured
    CLI-->>U: Print welcome message
    CLI-->>U: Exit code 0
```

---

## 9. Dependency Diagram

```mermaid
flowchart TD
    subgraph External["External Dependencies"]
        PYDANTIC[pydantic]
        RICH[rich]
        TEXTUAL[textual]
        PROMPT[prompt_toolkit]
        HTTPX[httpx]
        AIOHTTP[aiohttp]
        LANGCHAIN[langchain]
    end

    subgraph Internal["Internal Modules"]
        CLI_MAIN[cli.main]
        CORE_IFACES[core.interfaces]
        CORE_TYPES[core.types]
        CORE_ERRORS[core.errors]
        CORE_LOG[core.logging]
        UTILS_RESULT[utils.result]
    end

    CLI_MAIN --> CORE_IFACES
    CLI_MAIN --> CORE_LOG
    CLI_MAIN --> CORE_ERRORS

    CORE_IFACES --> CORE_TYPES
    CORE_IFACES --> UTILS_RESULT
    CORE_IFACES --> PYDANTIC

    CORE_TYPES --> PYDANTIC
    CORE_ERRORS --> CORE_TYPES
    CORE_LOG --> RICH
    UTILS_RESULT --> PYDANTIC
```

---

## 10. File Structure Diagram

```
src/forge/
│
├── __init__.py           # __version__ = "0.1.0"
├── __main__.py           # from cli.main import main; main()
│
├── cli/
│   ├── __init__.py
│   └── main.py           # main(), print_help()
│
├── core/
│   ├── __init__.py       # Export all public symbols
│   ├── interfaces.py     # ITool, IModelProvider, IConfigLoader, ISessionRepository
│   ├── types.py          # AgentId, SessionId, ProjectId, Message, etc.
│   ├── errors.py         # Code-ForgeError hierarchy
│   └── logging.py        # setup_logging(), get_logger()
│
├── utils/
│   ├── __init__.py
│   └── result.py         # Result[T]
│
├── tools/
│   └── __init__.py       # Empty placeholder
│
├── providers/
│   └── __init__.py       # Empty placeholder
│
├── config/
│   └── __init__.py       # Empty placeholder
│
└── session/
    └── __init__.py       # Empty placeholder
```

---

## Notes

This phase creates only interfaces and types - no implementations except:
1. CLI entry point (minimal --version, --help)
2. Logging setup
3. Result type utility

All boxes marked as interfaces (`<<interface>>`) will have concrete implementations in future phases.
