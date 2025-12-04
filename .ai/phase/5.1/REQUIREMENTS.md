# Phase 5.1: Session Management - Requirements

**Phase:** 5.1
**Name:** Session Management
**Dependencies:** Phase 3.2 (LangChain Integration), Phase 4.2 (Hooks System)

---

## Overview

Phase 5.1 implements session management for OpenCode, enabling conversation persistence, session resume, and conversation history tracking. Sessions are the fundamental unit of interaction, containing messages, tool calls, and metadata that can be saved and restored.

---

## Goals

1. Define session model with messages and metadata
2. Implement session persistence to disk
3. Enable session resume from previous state
4. Provide session listing and management
5. Track tool usage and token consumption per session

---

## Non-Goals (This Phase)

- Cloud-based session storage
- Session sharing between users
- Real-time session synchronization
- Session branching/forking
- Session templates

---

## Functional Requirements

### FR-1: Session Model

**FR-1.1:** Session data structure
- Unique session ID (UUID-based)
- Creation timestamp
- Last updated timestamp
- Session title (auto-generated or user-provided)
- Working directory
- Model used
- Total token usage

**FR-1.2:** Session contains messages
- List of conversation messages
- Messages are OpenCode Message objects
- Preserve message ordering
- Track message timestamps

**FR-1.3:** Session contains tool history
- List of tool invocations
- Tool name, arguments, results
- Execution timestamps
- Success/failure status

**FR-1.4:** Session metadata
- Tags for organization
- User notes
- Custom key-value data

### FR-2: Session Storage

**FR-2.1:** File-based storage
- Sessions stored as JSON files
- One file per session
- Stored in user's data directory
- Human-readable format

**FR-2.2:** Storage location
- Default: `~/.local/share/src/opencode/sessions/`
- Configurable via settings
- Project-local option: `.src/opencode/sessions/`

**FR-2.3:** File naming
- `{session_id}.json` format
- Session ID is UUID
- Index file for fast listing

### FR-3: Session Operations

**FR-3.1:** Create session
- Generate unique ID
- Set initial metadata
- Save to storage immediately

**FR-3.2:** Resume session
- Load session from storage
- Restore all messages
- Restore tool history
- Update "last accessed" timestamp

**FR-3.3:** Update session
- Add messages
- Update metadata
- Auto-save on changes

**FR-3.4:** Delete session
- Remove from storage
- Remove from index
- No recovery (permanent)

**FR-3.5:** List sessions
- List all available sessions
- Filter by date, tags, title
- Sort by various criteria
- Pagination support

### FR-4: Session Manager

**FR-4.1:** Singleton manager
- Central access point for sessions
- Manages current active session
- Handles persistence

**FR-4.2:** Auto-save
- Configurable auto-save interval
- Save on significant events
- Save on graceful exit

**FR-4.3:** Session lifecycle hooks
- Fire `session:start` on create/resume
- Fire `session:end` on close
- Fire `session:message` on message add

### FR-5: Session Resume

**FR-5.1:** Continue previous session
- CLI flag: `--resume` or `--continue`
- Show session picker if multiple
- Resume most recent by default

**FR-5.2:** Session selection UI
- List recent sessions
- Show title, date, message count
- Allow search/filter

**FR-5.3:** Partial resume
- Option to resume with limited history
- Token-budget-based truncation
- Preserve important context

### FR-6: Title Generation

**FR-6.1:** Auto-generate title
- Generate from first user message
- Use LLM to summarize if long
- Fallback to timestamp-based

**FR-6.2:** Manual title
- User can set/update title
- Title persisted with session

---

## Non-Functional Requirements

### NFR-1: Performance
- Session load < 100ms for typical session
- Session save < 50ms
- List sessions < 500ms for 1000 sessions
- Index-based lookups O(1)

### NFR-2: Storage
- Efficient JSON serialization
- Optional compression for large sessions
- Cleanup of old sessions (configurable)

### NFR-3: Reliability
- Atomic saves (write-then-rename)
- Backup before overwrite
- Recovery from corrupted sessions

### NFR-4: Privacy
- Sessions stored locally only
- No external transmission
- Secure file permissions

---

## Technical Specifications

### Package Structure

```
src/opencode/sessions/
├── __init__.py           # Package exports
├── models.py             # Session data models
├── storage.py            # Persistence layer
├── manager.py            # Session manager
└── index.py              # Session index
```

### Class Signatures

```python
# models.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid

@dataclass
class ToolInvocation:
    """Record of a tool invocation."""
    id: str
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any] | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    duration: float = 0.0
    success: bool = True
    error: str | None = None

    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "ToolInvocation": ...


@dataclass
class Session:
    """A conversation session."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    working_dir: str = ""
    model: str = ""

    messages: list["Message"] = field(default_factory=list)
    tool_history: list[ToolInvocation] = field(default_factory=list)

    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0

    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: "Message") -> None: ...
    def add_tool_invocation(self, invocation: ToolInvocation) -> None: ...
    def update_usage(self, prompt_tokens: int, completion_tokens: int) -> None: ...
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "Session": ...


# storage.py
from pathlib import Path

class SessionStorage:
    """Handles session persistence."""

    storage_dir: Path

    def __init__(self, storage_dir: Path | None = None): ...
    def save(self, session: Session) -> None: ...
    def load(self, session_id: str) -> Session | None: ...
    def delete(self, session_id: str) -> bool: ...
    def exists(self, session_id: str) -> bool: ...
    def get_path(self, session_id: str) -> Path: ...

    @classmethod
    def get_default_dir(cls) -> Path: ...


# index.py
@dataclass
class SessionSummary:
    """Summary of a session for listing."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    total_tokens: int
    tags: list[str]


class SessionIndex:
    """Index of sessions for fast lookup."""

    def __init__(self, storage: SessionStorage): ...
    def rebuild(self) -> None: ...
    def add(self, session: Session) -> None: ...
    def remove(self, session_id: str) -> None: ...
    def update(self, session: Session) -> None: ...
    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "updated_at",
        descending: bool = True,
        tags: list[str] | None = None,
        search: str | None = None,
    ) -> list[SessionSummary]: ...
    def get(self, session_id: str) -> SessionSummary | None: ...
    def count(self) -> int: ...


# manager.py
class SessionManager:
    """Manages session lifecycle."""

    storage: SessionStorage
    index: SessionIndex
    current_session: Session | None

    def __init__(
        self,
        storage: SessionStorage | None = None,
        auto_save_interval: float = 60.0,
    ): ...

    def create(
        self,
        *,
        title: str = "",
        working_dir: str | None = None,
        model: str = "",
    ) -> Session: ...

    def resume(self, session_id: str) -> Session: ...
    def resume_latest(self) -> Session | None: ...

    def save(self, session: Session | None = None) -> None: ...
    def close(self, session: Session | None = None) -> None: ...

    def delete(self, session_id: str) -> bool: ...

    def list_sessions(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "updated_at",
        descending: bool = True,
    ) -> list[SessionSummary]: ...

    def generate_title(self, session: Session) -> str: ...

    @property
    def has_current(self) -> bool: ...

    @classmethod
    def get_instance(cls) -> "SessionManager": ...
```

---

## Session File Format

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Refactoring the API client",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:45:00Z",
  "working_dir": "/home/user/project",
  "model": "anthropic/claude-3-opus",

  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Help me refactor the API client"
    },
    {
      "role": "assistant",
      "content": "I'll help you refactor...",
      "tool_calls": null
    }
  ],

  "tool_history": [
    {
      "id": "tool_abc123",
      "tool_name": "read",
      "arguments": {"file_path": "/home/user/project/api.py"},
      "result": {"success": true, "content": "..."},
      "timestamp": "2024-01-15T10:35:00Z",
      "duration": 0.05,
      "success": true
    }
  ],

  "total_prompt_tokens": 1500,
  "total_completion_tokens": 800,

  "tags": ["refactoring", "api"],
  "metadata": {
    "git_branch": "feature/api-refactor"
  }
}
```

---

## Session Index Format

```json
{
  "version": 1,
  "sessions": {
    "550e8400-e29b-41d4-a716-446655440000": {
      "title": "Refactoring the API client",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T11:45:00Z",
      "message_count": 15,
      "total_tokens": 2300,
      "tags": ["refactoring", "api"]
    }
  }
}
```

---

## Integration Points

### With LangChain Integration (Phase 3.2)
- ConversationMemory backed by session
- Messages synchronized with session
- Token usage tracked in session

### With Hooks System (Phase 4.2)
- Fire session lifecycle events
- Hooks can access session context
- Session ID in hook environment

### With REPL (Phase 1.3)
- `--resume` command line flag
- `/session` slash command
- Session status in prompt

### With Context Management (Phase 5.2)
- Session provides messages
- Context manager truncates as needed
- Token counts synchronized

---

## Error Scenarios

| Scenario | Handling |
|----------|----------|
| Session file corrupted | Log error, return None |
| Session not found | Return None or raise error |
| Storage directory missing | Create on first access |
| Disk full | Raise storage error |
| Permission denied | Raise permission error |
| Concurrent access | File locking or last-write-wins |

---

## Testing Requirements

1. Unit tests for Session model
2. Unit tests for ToolInvocation model
3. Unit tests for SessionStorage
4. Unit tests for SessionIndex
5. Unit tests for SessionManager
6. Test session serialization/deserialization
7. Test session listing with filters
8. Test auto-save functionality
9. Integration tests with memory
10. Test coverage ≥ 90%

---

## Acceptance Criteria

1. Sessions persist to disk correctly
2. Sessions resume with full history
3. Session listing works with pagination
4. Token usage tracked accurately
5. Tool history preserved
6. Auto-save works reliably
7. Session lifecycle hooks fire
8. Title generation works
9. Index updates correctly
10. Corrupted sessions handled gracefully
