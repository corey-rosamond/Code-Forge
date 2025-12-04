# Phase 5.1: Session Management - UML Diagrams

**Phase:** 5.1
**Name:** Session Management
**Dependencies:** Phase 3.2 (LangChain Integration), Phase 4.2 (Hooks System)

---

## 1. Class Diagram - Session Models

```mermaid
classDiagram
    class ToolInvocation {
        +id: str
        +tool_name: str
        +arguments: dict
        +result: dict?
        +timestamp: datetime
        +duration: float
        +success: bool
        +error: str?
        +to_dict() dict
        +from_dict(data)$ ToolInvocation
    }

    class SessionMessage {
        +id: str
        +role: str
        +content: str
        +tool_calls: list?
        +tool_call_id: str?
        +name: str?
        +timestamp: datetime
        +to_dict() dict
        +from_dict(data)$ SessionMessage
    }

    class Session {
        +id: str
        +title: str
        +created_at: datetime
        +updated_at: datetime
        +working_dir: str
        +model: str
        +messages: list~SessionMessage~
        +tool_history: list~ToolInvocation~
        +total_prompt_tokens: int
        +total_completion_tokens: int
        +tags: list~str~
        +metadata: dict
        +add_message(message) void
        +add_message_from_dict(role, content, **kwargs) SessionMessage
        +add_tool_invocation(invocation) void
        +record_tool_call(...) ToolInvocation
        +update_usage(prompt, completion) void
        +total_tokens: int
        +message_count: int
        +to_dict() dict
        +to_json(indent) str
        +from_dict(data)$ Session
        +from_json(json_str)$ Session
    }

    Session o-- SessionMessage : contains
    Session o-- ToolInvocation : contains
```

---

## 2. Class Diagram - Storage Layer

```mermaid
classDiagram
    class SessionStorageError {
        <<exception>>
    }

    class SessionNotFoundError {
        <<exception>>
    }

    class SessionCorruptedError {
        <<exception>>
    }

    class SessionStorage {
        +storage_dir: Path
        +DEFAULT_DIR_NAME: str$
        +SESSION_EXTENSION: str$
        +BACKUP_EXTENSION: str$
        +__init__(storage_dir)
        +get_default_dir()$ Path
        +get_project_dir(project_root)$ Path
        +get_path(session_id) Path
        +get_backup_path(session_id) Path
        +exists(session_id) bool
        +save(session) void
        +load(session_id) Session
        +load_or_none(session_id) Session?
        +delete(session_id) bool
        +list_session_ids() list~str~
        +recover_from_backup(session_id) bool
        +get_storage_size() int
        +cleanup_old_sessions(max_age, keep_min) list~str~
    }

    SessionStorageError <|-- SessionNotFoundError
    SessionStorageError <|-- SessionCorruptedError
    SessionStorage ..> SessionStorageError : raises
    SessionStorage --> Session : manages
```

---

## 3. Class Diagram - Index Layer

```mermaid
classDiagram
    class SessionSummary {
        +id: str
        +title: str
        +created_at: datetime
        +updated_at: datetime
        +message_count: int
        +total_tokens: int
        +tags: list~str~
        +working_dir: str
        +model: str
        +to_dict() dict
        +from_dict(data)$ SessionSummary
        +from_session(session)$ SessionSummary
    }

    class SessionIndex {
        +storage: SessionStorage
        -_index: dict~str, SessionSummary~
        -_dirty: bool
        +INDEX_FILE: str$
        +INDEX_VERSION: int$
        +index_path: Path
        +__init__(storage)
        +rebuild() void
        +add(session) void
        +update(session) void
        +remove(session_id) bool
        +get(session_id) SessionSummary?
        +count() int
        +list(...) list~SessionSummary~
        +get_recent(count) list~SessionSummary~
        +get_by_working_dir(dir) list~SessionSummary~
        +save_if_dirty() void
    }

    SessionIndex --> SessionStorage : uses
    SessionIndex o-- SessionSummary : contains
    SessionSummary ..> Session : summarizes
```

---

## 4. Class Diagram - Session Manager

```mermaid
classDiagram
    class SessionManager {
        -_instance: SessionManager$
        +storage: SessionStorage
        +index: SessionIndex
        +current_session: Session?
        -_auto_save_interval: float
        -_auto_save_task: Task?
        -_hooks: dict
        +__init__(storage, auto_save_interval)
        +get_instance()$ SessionManager
        +reset_instance()$ void
        +create(...) Session
        +resume(session_id) Session
        +resume_latest() Session?
        +resume_or_create(...) Session
        +save(session?) void
        +close(session?) void
        +delete(session_id) bool
        +list_sessions(...) list~SessionSummary~
        +get_session(session_id) Session?
        +add_message(role, content, ...) SessionMessage
        +record_tool_call(...) ToolInvocation
        +update_usage(prompt, completion) void
        +generate_title(session) str
        +set_title(title, session?) void
        +add_tag(tag, session?) void
        +remove_tag(tag, session?) bool
        +has_current: bool
        +register_hook(event, callback) void
        +unregister_hook(event, callback) bool
    }

    SessionManager --> SessionStorage : uses
    SessionManager --> SessionIndex : uses
    SessionManager --> Session : manages
    SessionManager ..> SessionSummary : returns
```

---

## 5. Package Diagram

```mermaid
flowchart TB
    subgraph SessionsPkg["src/opencode/sessions/"]
        INIT["__init__.py"]
        MODELS["models.py<br/>Session, SessionMessage, ToolInvocation"]
        STORAGE["storage.py<br/>SessionStorage"]
        INDEX["index.py<br/>SessionIndex, SessionSummary"]
        MANAGER["manager.py<br/>SessionManager"]
    end

    subgraph LangChainPkg["src/opencode/langchain/"]
        MEMORY["memory.py<br/>ConversationMemory"]
    end

    subgraph HooksPkg["src/opencode/hooks/"]
        EVENTS["events.py<br/>HookEvent"]
        EXECUTOR["executor.py<br/>fire_event"]
    end

    subgraph REPLPkg["src/opencode/repl/"]
        REPL["repl.py"]
    end

    MANAGER --> STORAGE
    MANAGER --> INDEX
    INDEX --> STORAGE

    MEMORY --> MANAGER
    REPL --> MANAGER

    MANAGER --> EVENTS
    MANAGER --> EXECUTOR

    INIT --> MODELS
    INIT --> STORAGE
    INIT --> INDEX
    INIT --> MANAGER
```

---

## 6. Sequence Diagram - Create Session

```mermaid
sequenceDiagram
    participant Client
    participant Manager as SessionManager
    participant Storage as SessionStorage
    participant Index as SessionIndex
    participant Hooks

    Client->>Manager: create(title, working_dir, model)

    Manager->>Manager: Create Session object

    Manager->>Storage: save(session)
    Storage->>Storage: Write to temp file
    Storage->>Storage: Atomic rename
    Storage-->>Manager: Success

    Manager->>Index: add(session)
    Index->>Index: Update _index dict
    Index-->>Manager: Done

    Manager->>Index: save_if_dirty()
    Index->>Index: Write index.json

    Manager->>Manager: current_session = session
    Manager->>Manager: _start_auto_save()

    Manager->>Hooks: _fire_hook("session:start", session)
    Hooks-->>Manager: Done

    Manager-->>Client: Session
```

---

## 7. Sequence Diagram - Resume Session

```mermaid
sequenceDiagram
    participant Client
    participant Manager as SessionManager
    participant Storage as SessionStorage
    participant Index as SessionIndex
    participant Hooks

    Client->>Manager: resume(session_id)

    Manager->>Storage: load(session_id)

    alt Session exists
        Storage->>Storage: Read JSON file
        Storage->>Storage: Deserialize Session
        Storage-->>Manager: Session

        Manager->>Manager: session._mark_updated()

        Manager->>Storage: save(session)
        Storage-->>Manager: Success

        Manager->>Index: update(session)
        Index->>Index: Update _index dict

        Manager->>Manager: current_session = session
        Manager->>Manager: _start_auto_save()

        Manager->>Hooks: _fire_hook("session:start", session)

        Manager-->>Client: Session

    else Session not found
        Storage-->>Manager: SessionNotFoundError
        Manager-->>Client: SessionNotFoundError
    end
```

---

## 8. Sequence Diagram - Auto-Save

```mermaid
sequenceDiagram
    participant Timer as Auto-Save Timer
    participant Manager as SessionManager
    participant Storage as SessionStorage
    participant Index as SessionIndex

    loop Every auto_save_interval seconds
        Timer->>Timer: await sleep(interval)

        alt current_session exists
            Timer->>Manager: Check current_session

            Manager->>Storage: save(current_session)
            Storage->>Storage: Create backup
            Storage->>Storage: Write temp file
            Storage->>Storage: Atomic rename
            Storage-->>Manager: Success

            Manager->>Index: update(session)
            Manager->>Index: save_if_dirty()
            Index->>Index: Write index.json

            Manager->>Manager: _fire_hook("session:save")

        else No current session
            Note over Timer,Manager: Skip save
        end
    end
```

---

## 9. Sequence Diagram - Session Close

```mermaid
sequenceDiagram
    participant Client
    participant Manager as SessionManager
    participant Storage as SessionStorage
    participant Index as SessionIndex
    participant Hooks
    participant AutoSave as Auto-Save Task

    Client->>Manager: close(session)

    Manager->>Storage: save(session)
    Storage->>Storage: Create backup
    Storage->>Storage: Atomic write
    Storage-->>Manager: Success

    Manager->>Index: update(session)
    Manager->>Index: save_if_dirty()

    Manager->>Hooks: _fire_hook("session:end", session)
    Hooks-->>Manager: Done

    alt session is current_session
        Manager->>AutoSave: cancel()
        AutoSave-->>Manager: Cancelled

        Manager->>Manager: current_session = None
        Manager->>Manager: _auto_save_task = None
    end

    Manager-->>Client: Done
```

---

## 10. Sequence Diagram - List Sessions

```mermaid
sequenceDiagram
    participant Client
    participant Manager as SessionManager
    participant Index as SessionIndex

    Client->>Manager: list_sessions(limit, offset, sort_by, tags, search)

    Manager->>Index: list(limit, offset, sort_by, tags, search)

    Index->>Index: Filter by tags

    alt tags provided
        Index->>Index: Filter sessions with all tags
    end

    alt search provided
        Index->>Index: Filter by title match
    end

    Index->>Index: Sort by sort_by field

    Index->>Index: Apply offset and limit

    Index-->>Manager: list[SessionSummary]

    Manager-->>Client: list[SessionSummary]
```

---

## 11. State Diagram - Session Lifecycle

```mermaid
stateDiagram-v2
    [*] --> New: create()

    New --> Active: Session created
    Active --> Active: add_message()
    Active --> Active: record_tool_call()
    Active --> Active: update_usage()
    Active --> Saving: Auto-save / save()

    Saving --> Active: Save complete

    Active --> Closed: close()
    Closed --> [*]

    state Persisted {
        [*] --> OnDisk: save()
        OnDisk --> Loaded: load()
        Loaded --> [*]
    }

    Active --> Persisted: Storage sync
    Persisted --> Active: Resume
```

---

## 12. State Diagram - Storage Operations

```mermaid
stateDiagram-v2
    [*] --> Ready: SessionStorage()

    Ready --> Saving: save(session)

    Saving --> BackingUp: Backup existing
    BackingUp --> Writing: Write temp file
    Writing --> Renaming: Atomic rename
    Renaming --> Ready: Success

    BackingUp --> Ready: No existing file
    Writing --> Error: Write failed
    Renaming --> Error: Rename failed

    Ready --> Loading: load(session_id)

    Loading --> Reading: Read file
    Reading --> Parsing: Parse JSON
    Parsing --> Ready: Return Session

    Reading --> NotFound: File not found
    Parsing --> Corrupted: Invalid JSON

    NotFound --> Ready: Raise SessionNotFoundError
    Corrupted --> Ready: Raise SessionCorruptedError
    Error --> Ready: Raise SessionStorageError
```

---

## 13. Activity Diagram - Session Create Flow

```mermaid
flowchart TD
    START([create called]) --> GET_CWD{working_dir<br/>provided?}

    GET_CWD -->|No| USE_CWD[Use os.getcwd]
    GET_CWD -->|Yes| HAS_CWD[Use provided]

    USE_CWD --> CREATE[Create Session object]
    HAS_CWD --> CREATE

    CREATE --> SAVE_STORAGE[Save to storage]
    SAVE_STORAGE --> UPDATE_INDEX[Add to index]
    UPDATE_INDEX --> SAVE_INDEX[Save index]

    SAVE_INDEX --> SET_CURRENT[Set as current_session]
    SET_CURRENT --> START_AUTO[Start auto-save task]
    START_AUTO --> FIRE_HOOK[Fire session:start hook]

    FIRE_HOOK --> RETURN([Return Session])
```

---

## 14. Activity Diagram - Resume Flow

```mermaid
flowchart TD
    START([resume called]) --> LOAD[Load from storage]

    LOAD --> FOUND{Session<br/>found?}

    FOUND -->|No| ERROR([Raise SessionNotFoundError])

    FOUND -->|Yes| UPDATE_TS[Update updated_at]
    UPDATE_TS --> SAVE[Save session]
    SAVE --> UPDATE_IDX[Update index]
    UPDATE_IDX --> SAVE_IDX[Save index]

    SAVE_IDX --> SET_CURRENT[Set as current_session]
    SET_CURRENT --> START_AUTO[Start auto-save]
    START_AUTO --> FIRE_HOOK[Fire session:start hook]

    FIRE_HOOK --> RETURN([Return Session])
```

---

## 15. Component Diagram - Session Storage

```mermaid
flowchart TB
    subgraph Storage["Storage Layer"]
        direction TB
        STORAGE_DIR["~/.local/share/src/opencode/sessions/"]

        subgraph Files["Session Files"]
            S1["session-uuid-1.json"]
            S2["session-uuid-2.json"]
            S3["session-uuid-3.json"]
        end

        subgraph Backups["Backup Files"]
            B1["session-uuid-1.backup"]
            B2["session-uuid-2.backup"]
        end

        INDEX["index.json"]
    end

    subgraph Classes["Python Classes"]
        SESSION_STORAGE["SessionStorage"]
        SESSION_INDEX["SessionIndex"]
    end

    SESSION_STORAGE --> Files
    SESSION_STORAGE --> Backups
    SESSION_INDEX --> INDEX
    SESSION_INDEX --> SESSION_STORAGE
```

---

## 16. Data Flow Diagram - Message Flow

```mermaid
flowchart LR
    subgraph Input
        USER[User Message]
        ASSISTANT[Assistant Response]
        TOOL[Tool Result]
    end

    subgraph Processing
        ADD[add_message]
        SESSION[Session.messages]
        MANAGER[SessionManager]
    end

    subgraph Output
        STORAGE[SessionStorage]
        INDEX[SessionIndex]
        HOOKS[Hook Events]
    end

    USER --> ADD
    ASSISTANT --> ADD
    TOOL --> ADD

    ADD --> SESSION
    SESSION --> MANAGER

    MANAGER --> STORAGE
    MANAGER --> INDEX
    MANAGER --> HOOKS
```

---

## 17. Entity Relationship Diagram

```mermaid
erDiagram
    SESSION ||--o{ SESSION_MESSAGE : contains
    SESSION ||--o{ TOOL_INVOCATION : contains
    SESSION }o--o{ TAG : has

    SESSION {
        uuid id PK
        string title
        datetime created_at
        datetime updated_at
        string working_dir
        string model
        int total_prompt_tokens
        int total_completion_tokens
        json metadata
    }

    SESSION_MESSAGE {
        uuid id PK
        uuid session_id FK
        string role
        text content
        json tool_calls
        string tool_call_id
        string name
        datetime timestamp
    }

    TOOL_INVOCATION {
        uuid id PK
        uuid session_id FK
        string tool_name
        json arguments
        json result
        datetime timestamp
        float duration
        boolean success
        text error
    }

    TAG {
        string name PK
    }
```

---

## Notes

- Session uses UUID-based IDs for uniqueness
- Storage uses atomic writes for data safety
- Index provides fast session listing without loading full sessions
- Manager is singleton for consistent state
- Auto-save runs in background asyncio task
- Hooks integrate with Phase 4.2 hooks system
- Sessions are JSON files for human readability
