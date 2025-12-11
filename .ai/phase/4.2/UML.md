# Phase 4.2: Hooks System - UML Diagrams

**Phase:** 4.2
**Name:** Hooks System
**Dependencies:** Phase 2.1 (Tool System Foundation), Phase 4.1 (Permission System)

---

## 1. Class Diagram - Event Types

```mermaid
classDiagram
    class EventType {
        <<enumeration>>
        TOOL_PRE_EXECUTE = "tool:pre_execute"
        TOOL_POST_EXECUTE = "tool:post_execute"
        TOOL_ERROR = "tool:error"
        LLM_PRE_REQUEST = "llm:pre_request"
        LLM_POST_RESPONSE = "llm:post_response"
        LLM_STREAM_START = "llm:stream_start"
        LLM_STREAM_END = "llm:stream_end"
        SESSION_START = "session:start"
        SESSION_END = "session:end"
        SESSION_MESSAGE = "session:message"
        PERMISSION_CHECK = "permission:check"
        PERMISSION_PROMPT = "permission:prompt"
        PERMISSION_GRANTED = "permission:granted"
        PERMISSION_DENIED = "permission:denied"
        USER_PROMPT_SUBMIT = "user:prompt_submit"
        USER_INTERRUPT = "user:interrupt"
    }

    class HookEvent {
        +type: EventType
        +timestamp: float
        +data: dict
        +tool_name: str?
        +session_id: str?
        +to_env() dict
        +to_json() str
        +tool_pre_execute(...)$ HookEvent
        +tool_post_execute(...)$ HookEvent
        +tool_error(...)$ HookEvent
        +llm_pre_request(...)$ HookEvent
        +llm_post_response(...)$ HookEvent
        +session_start(...)$ HookEvent
        +session_end(...)$ HookEvent
        +permission_check(...)$ HookEvent
        +user_prompt_submit(...)$ HookEvent
    }

    HookEvent --> EventType : has
```

---

## 2. Class Diagram - Hook Registry

```mermaid
classDiagram
    class Hook {
        +event_pattern: str
        +command: str
        +timeout: float
        +working_dir: str?
        +env: dict?
        +enabled: bool
        +description: str
        +matches(event) bool
        +to_dict() dict
        +from_dict(data)$ Hook
    }

    class HookRegistry {
        -_instance: HookRegistry$
        +hooks: list~Hook~
        +get_instance()$ HookRegistry
        +reset_instance()$ void
        +register(hook) void
        +unregister(event_pattern) bool
        +get_hooks(event) list~Hook~
        +clear() void
        +load_hooks(hooks) void
    }

    HookRegistry o-- Hook : contains
    HookRegistry --> HookEvent : filters by
```

---

## 3. Class Diagram - Hook Executor

```mermaid
classDiagram
    class HookResult {
        +hook: Hook
        +exit_code: int
        +stdout: str
        +stderr: str
        +duration: float
        +timed_out: bool
        +error: str?
        +success: bool
        +should_continue: bool
    }

    class HookExecutor {
        +registry: HookRegistry
        +default_timeout: float
        +working_dir: Path
        +execute_hooks(event, stop_on_failure) list~HookResult~
        -_execute_hook(hook, event) HookResult
    }

    class HookBlockedError {
        +result: HookResult
    }

    HookExecutor --> HookRegistry : uses
    HookExecutor --> HookResult : produces
    HookExecutor ..> HookBlockedError : raises
    HookResult --> Hook : references
```

---

## 4. Class Diagram - Configuration

```mermaid
classDiagram
    class HookConfig {
        +GLOBAL_FILE: str$
        +PROJECT_FILE: str$
        +get_global_path()$ Path
        +get_project_path(project_root)$ Path?
        +load_global()$ list~Hook~
        +load_project(project_root)$ list~Hook~
        +save_global(hooks) void
        +save_project(project_root, hooks) void
        +load_all(project_root)$ list~Hook~
    }

    class HOOK_TEMPLATES {
        <<dict>>
        log_all: Hook
        notify_session_start: Hook
        git_auto_commit: Hook
        block_sudo: Hook
    }

    HookConfig --> Hook : creates
    HookConfig --> HOOK_TEMPLATES : references
```

---

## 5. Sequence Diagram - Tool Pre-Execute Hook

```mermaid
sequenceDiagram
    participant TE as ToolExecutor
    participant HE as HookExecutor
    participant HR as HookRegistry
    participant Shell as Shell Process

    TE->>TE: Create HookEvent.tool_pre_execute()

    TE->>HE: execute_hooks(event, stop_on_failure=True)

    HE->>HR: get_hooks(event)
    HR-->>HE: [Hook1, Hook2]

    loop For each matching hook
        HE->>Shell: Create subprocess with env
        Shell->>Shell: Execute command

        alt Success (exit 0)
            Shell-->>HE: stdout, stderr, exit=0
            HE->>HE: Create HookResult(success=True)
        else Failure (exit != 0)
            Shell-->>HE: stdout, stderr, exit=1
            HE->>HE: Create HookResult(success=False)
            HE-->>TE: [HookResult(blocked)]
            Note over TE: Operation blocked
        else Timeout
            HE->>Shell: Kill process
            HE->>HE: Create HookResult(timed_out=True)
        end
    end

    HE-->>TE: [HookResult, ...]

    alt All hooks passed
        TE->>TE: Continue with tool execution
    else Hook blocked
        TE->>TE: Raise HookBlockedError
    end
```

---

## 6. Sequence Diagram - Tool Lifecycle with Hooks

```mermaid
sequenceDiagram
    participant User
    participant TE as ToolExecutor
    participant Hooks as HookExecutor
    participant Tool as BaseTool

    User->>TE: execute(tool, params, context)

    TE->>Hooks: fire_event(tool:pre_execute)
    Hooks-->>TE: [results]

    alt Pre-hooks blocked
        TE-->>User: HookBlockedError
    else Pre-hooks passed
        TE->>TE: Check permissions

        TE->>Tool: execute(params, context)
        Tool-->>TE: ToolResult

        alt Success
            TE->>Hooks: fire_event(tool:post_execute)
            Hooks-->>TE: [results]
            TE-->>User: ToolResult
        else Error
            TE->>Hooks: fire_event(tool:error)
            Hooks-->>TE: [results]
            TE-->>User: Exception
        end
    end
```

---

## 7. Sequence Diagram - Hook Pattern Matching

```mermaid
sequenceDiagram
    participant Event as HookEvent
    participant Hook
    participant Matcher as Pattern Matcher

    Event->>Hook: matches(event)

    Hook->>Hook: Parse pattern into parts

    loop For each pattern part
        Hook->>Matcher: Check pattern type

        alt Exact match
            Matcher->>Matcher: pattern == event.type
        else Wildcard (*)
            Matcher-->>Hook: True (matches all)
        else Glob pattern
            Matcher->>Matcher: fnmatch(event.type, pattern)
        else Tool-specific (tool:event:name)
            Matcher->>Matcher: Match all three parts
        end

        alt Match found
            Hook-->>Event: True
        end
    end

    Hook-->>Event: False (no match)
```

---

## 8. State Diagram - Hook Execution

```mermaid
stateDiagram-v2
    [*] --> Pending: Hook created

    Pending --> Executing: Start subprocess

    Executing --> Capturing: Process running

    Capturing --> Success: Exit code 0
    Capturing --> Failed: Exit code != 0
    Capturing --> TimedOut: Timeout exceeded
    Capturing --> Error: Exception

    TimedOut --> Killed: Kill process
    Killed --> Failed

    Success --> [*]: HookResult(success=True)
    Failed --> [*]: HookResult(success=False)
    Error --> [*]: HookResult(error=...)
```

---

## 9. State Diagram - Hook Chain Execution

```mermaid
stateDiagram-v2
    [*] --> GetHooks: Event fired

    GetHooks --> NoHooks: No matching hooks
    GetHooks --> ExecuteNext: Has hooks

    NoHooks --> [*]: Return empty list

    ExecuteNext --> Running: Execute hook

    Running --> CheckResult: Hook completed

    CheckResult --> CollectResult: success or stop_on_failure=False
    CheckResult --> StopChain: failure and stop_on_failure=True

    CollectResult --> ExecuteNext: More hooks
    CollectResult --> Done: No more hooks

    StopChain --> Done

    Done --> [*]: Return results
```

---

## 10. Activity Diagram - Fire Event Flow

```mermaid
flowchart TD
    START([fire_event called]) --> GET[Get matching hooks from registry]

    GET --> CHECK_EMPTY{Any hooks?}

    CHECK_EMPTY -->|No| RETURN_EMPTY[Return empty list]
    CHECK_EMPTY -->|Yes| LOOP[For each hook]

    LOOP --> BUILD_ENV[Build environment variables]
    BUILD_ENV --> BUILD_CMD[Build command]
    BUILD_CMD --> EXEC[Execute subprocess]

    EXEC --> WAIT{Wait for completion}

    WAIT -->|Complete| CHECK_EXIT{Exit code 0?}
    WAIT -->|Timeout| TIMEOUT[Kill process]

    TIMEOUT --> ADD_TIMEOUT[Add timeout result]
    ADD_TIMEOUT --> CHECK_STOP{stop_on_failure?}

    CHECK_EXIT -->|Yes| ADD_SUCCESS[Add success result]
    CHECK_EXIT -->|No| ADD_FAIL[Add failure result]

    ADD_SUCCESS --> MORE{More hooks?}
    ADD_FAIL --> CHECK_STOP

    CHECK_STOP -->|Yes| RETURN[Return results]
    CHECK_STOP -->|No| MORE

    MORE -->|Yes| LOOP
    MORE -->|No| RETURN

    RETURN_EMPTY --> END([Return])
    RETURN --> END
```

---

## 11. Component Diagram - Hooks Package

```mermaid
flowchart TB
    subgraph HooksPkg["src/forge/hooks/"]
        INIT["__init__.py"]
        EVENTS["events.py<br/>EventType, HookEvent"]
        REGISTRY["registry.py<br/>Hook, HookRegistry"]
        EXECUTOR["executor.py<br/>HookExecutor, HookResult"]
        CONFIG["config.py<br/>HookConfig"]
    end

    subgraph ToolsPkg["src/forge/tools/"]
        TOOL_EXEC["executor.py"]
    end

    subgraph LLMPkg["src/forge/llm/"]
        CLIENT["client.py"]
    end

    subgraph SessionPkg["src/forge/sessions/"]
        MANAGER["manager.py"]
    end

    TOOL_EXEC --> EVENTS
    TOOL_EXEC --> EXECUTOR

    CLIENT --> EVENTS
    CLIENT --> EXECUTOR

    MANAGER --> EVENTS
    MANAGER --> EXECUTOR

    EXECUTOR --> REGISTRY
    EXECUTOR --> EVENTS

    CONFIG --> REGISTRY

    INIT --> EVENTS
    INIT --> REGISTRY
    INIT --> EXECUTOR
    INIT --> CONFIG
```

---

## 12. Data Flow Diagram - Hook Event Processing

```mermaid
flowchart LR
    subgraph Input
        ACTION[User Action]
        TOOL[Tool Execution]
        LLM[LLM Request]
    end

    subgraph EventCreation["Event Creation"]
        FACTORY[HookEvent Factory]
    end

    subgraph Execution
        REGISTRY[HookRegistry]
        EXECUTOR[HookExecutor]
        SHELL[Shell Process]
    end

    subgraph Output
        RESULTS[HookResults]
        BLOCKED[HookBlockedError]
    end

    ACTION --> FACTORY
    TOOL --> FACTORY
    LLM --> FACTORY

    FACTORY --> EXECUTOR

    EXECUTOR --> REGISTRY
    REGISTRY --> EXECUTOR

    EXECUTOR --> SHELL
    SHELL --> EXECUTOR

    EXECUTOR --> RESULTS
    EXECUTOR --> BLOCKED
```

---

## 13. Environment Variables Diagram

```mermaid
flowchart TB
    subgraph Event["HookEvent Data"]
        TYPE[type: EventType]
        TIMESTAMP[timestamp: float]
        DATA[data: dict]
        TOOL[tool_name: str?]
        SESSION[session_id: str?]
    end

    subgraph EnvVars["Environment Variables"]
        E_EVENT[FORGE_EVENT]
        E_TS[FORGE_TIMESTAMP]
        E_SESS[FORGE_SESSION_ID]
        E_TOOL[FORGE_TOOL_NAME]
        E_ARGS[FORGE_TOOL_ARGS]
        E_RESULT[FORGE_TOOL_RESULT]
        E_MODEL[FORGE_LLM_MODEL]
        E_TOKENS[FORGE_LLM_TOKENS]
        E_PERM[FORGE_PERM_LEVEL]
    end

    TYPE --> E_EVENT
    TIMESTAMP --> E_TS
    SESSION --> E_SESS
    TOOL --> E_TOOL
    DATA --> E_ARGS
    DATA --> E_RESULT
    DATA --> E_MODEL
    DATA --> E_TOKENS
    DATA --> E_PERM
```

---

## 14. Hook Pattern Matching Examples

```
Pattern: "tool:pre_execute"
├── Matches: tool:pre_execute
└── Does not match: tool:post_execute, llm:pre_request

Pattern: "tool:*"
├── Matches: tool:pre_execute, tool:post_execute, tool:error
└── Does not match: llm:pre_request, session:start

Pattern: "tool:pre_execute:bash"
├── Matches: tool:pre_execute (when tool_name=bash)
└── Does not match: tool:pre_execute (when tool_name=read)

Pattern: "tool:*:write"
├── Matches: tool:pre_execute:write, tool:post_execute:write
└── Does not match: tool:pre_execute:bash

Pattern: "*"
└── Matches: Everything

Pattern: "session:start,session:end"
├── Matches: session:start, session:end
└── Does not match: session:message
```

---

## Notes

- Hooks execute shell commands in subprocesses
- Environment variables provide event context to hooks
- Pre-execute hooks can block operations (exit != 0)
- Hooks are configured in JSON files (global and project)
- Timeout prevents hung hooks from blocking the system
- HookRegistry is a singleton for consistent state
