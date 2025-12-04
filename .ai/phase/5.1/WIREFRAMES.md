# Phase 5.1: Session Management - Wireframes & Usage Examples

**Phase:** 5.1
**Name:** Session Management
**Dependencies:** Phase 3.2 (LangChain Integration), Phase 4.2 (Hooks System)

---

## 1. Basic Session Usage

### Creating a Session

```python
from opencode.sessions import SessionManager

# Get singleton manager
manager = SessionManager.get_instance()

# Create a new session
session = manager.create(
    title="Refactoring API client",
    working_dir="/home/user/project",
    model="anthropic/claude-3-opus",
    tags=["refactoring", "api"],
)

print(f"Session ID: {session.id}")
# Session ID: 550e8400-e29b-41d4-a716-446655440000
```

### Adding Messages

```python
# Add user message
manager.add_message("user", "Help me refactor the API client")

# Add assistant message
manager.add_message(
    "assistant",
    "I'll help you refactor the API client. Let me start by reading the current code.",
)

# Add assistant message with tool calls
manager.add_message(
    "assistant",
    "I'll read the file first.",
    tool_calls=[{
        "id": "call_abc123",
        "type": "function",
        "function": {
            "name": "read",
            "arguments": '{"file_path": "/home/user/project/api.py"}'
        }
    }],
)

# Add tool result
manager.add_message(
    "tool",
    "class APIClient:\n    def __init__(self):\n        ...",
    tool_call_id="call_abc123",
    name="read",
)
```

### Recording Tool Calls

```python
# Record a tool invocation
import time

start = time.perf_counter()
# ... tool execution ...
duration = time.perf_counter() - start

manager.record_tool_call(
    tool_name="bash",
    arguments={"command": "git status"},
    result={"output": "On branch main\nnothing to commit"},
    duration=duration,
    success=True,
)

# Record a failed tool call
manager.record_tool_call(
    tool_name="read",
    arguments={"file_path": "/nonexistent.py"},
    result=None,
    success=False,
    error="FileNotFoundError: /nonexistent.py",
)
```

### Tracking Token Usage

```python
# Update token counts after LLM call
manager.update_usage(
    prompt_tokens=1500,
    completion_tokens=800,
)

# Check totals
print(f"Total tokens: {session.total_tokens}")
# Total tokens: 2300
```

---

## 2. Session Lifecycle

### Resume Session

```python
from opencode.sessions import SessionManager

manager = SessionManager.get_instance()

# Resume specific session
session = manager.resume("550e8400-e29b-41d4-a716-446655440000")

# Resume most recent session
session = manager.resume_latest()

# Resume latest or create new
session = manager.resume_or_create(
    working_dir="/home/user/project",
    model="anthropic/claude-3-opus",
)
```

### Save and Close

```python
# Manual save (also happens automatically)
manager.save()

# Close session (saves and cleans up)
manager.close()

# Check if session is active
if manager.has_current:
    print(f"Active session: {manager.current_session.title}")
```

---

## 3. Session Listing and Search

### List Sessions

```python
from opencode.sessions import SessionManager

manager = SessionManager.get_instance()

# List recent sessions
sessions = manager.list_sessions(limit=10)

for s in sessions:
    print(f"{s.title} - {s.message_count} messages - {s.updated_at}")

# Output:
# Refactoring API client - 15 messages - 2024-01-15 11:45:00
# Implementing auth - 32 messages - 2024-01-14 16:30:00
# Bug fix in parser - 8 messages - 2024-01-13 09:15:00
```

### Filter and Sort

```python
# Filter by tags
python_sessions = manager.list_sessions(tags=["python"])

# Search by title
results = manager.list_sessions(search="refactor")

# Sort by different fields
by_title = manager.list_sessions(sort_by="title", descending=False)
by_tokens = manager.list_sessions(sort_by="total_tokens", descending=True)

# Pagination
page_2 = manager.list_sessions(limit=10, offset=10)
```

---

## 4. Session Management

### Title and Tags

```python
# Set session title
manager.set_title("Refactoring the API client for v2")

# Auto-generate title from first message
title = manager.generate_title(session)
manager.set_title(title)

# Add tags
manager.add_tag("python")
manager.add_tag("refactoring")

# Remove tag
manager.remove_tag("draft")

# Session metadata
session.metadata["git_branch"] = "feature/api-v2"
session.metadata["priority"] = "high"
```

### Delete Session

```python
# Delete by ID
deleted = manager.delete("550e8400-e29b-41d4-a716-446655440000")
if deleted:
    print("Session deleted")
```

---

## 5. Direct Session Model Usage

### Create Session Directly

```python
from opencode.sessions import Session, SessionMessage, ToolInvocation
from datetime import datetime, timezone

# Create session
session = Session(
    title="My session",
    working_dir="/home/user/project",
    model="anthropic/claude-3-opus",
)

# Add message directly
message = SessionMessage(
    role="user",
    content="Hello, world!",
)
session.add_message(message)

# Or using helper method
session.add_message_from_dict("assistant", "Hello! How can I help?")

# Record tool call directly
invocation = ToolInvocation(
    tool_name="bash",
    arguments={"command": "ls"},
    result={"output": "file1.py\nfile2.py"},
    duration=0.05,
)
session.add_tool_invocation(invocation)

# Or using helper method
session.record_tool_call(
    tool_name="read",
    arguments={"file_path": "file1.py"},
    result={"content": "..."},
)
```

### Serialize Session

```python
# To dictionary
data = session.to_dict()

# To JSON string
json_str = session.to_json(indent=2)

# From dictionary
session = Session.from_dict(data)

# From JSON string
session = Session.from_json(json_str)
```

---

## 6. Storage Operations

### Using SessionStorage Directly

```python
from opencode.sessions import SessionStorage, Session
from pathlib import Path

# Default storage
storage = SessionStorage()

# Custom storage directory
storage = SessionStorage(Path("/custom/path/sessions"))

# Project-local storage
storage = SessionStorage(
    SessionStorage.get_project_dir("/home/user/project")
)

# Save session
session = Session(title="Test")
storage.save(session)

# Load session
session = storage.load(session.id)

# Check if exists
if storage.exists(session.id):
    print("Session exists")

# Delete
storage.delete(session.id)

# List all session IDs
for sid in storage.list_session_ids():
    print(sid)
```

### Error Handling

```python
from opencode.sessions import (
    SessionStorage,
    SessionNotFoundError,
    SessionCorruptedError,
    SessionStorageError,
)

storage = SessionStorage()

try:
    session = storage.load("nonexistent-id")
except SessionNotFoundError:
    print("Session not found")

try:
    session = storage.load("corrupted-id")
except SessionCorruptedError:
    # Try to recover from backup
    if storage.recover_from_backup("corrupted-id"):
        session = storage.load("corrupted-id")
    else:
        print("Cannot recover session")
except SessionStorageError as e:
    print(f"Storage error: {e}")
```

### Cleanup Old Sessions

```python
# Clean up sessions older than 30 days, keeping at least 10
deleted_ids = storage.cleanup_old_sessions(
    max_age_days=30,
    keep_minimum=10,
)

print(f"Deleted {len(deleted_ids)} old sessions")

# Get storage size
size_bytes = storage.get_storage_size()
print(f"Storage size: {size_bytes / 1024:.1f} KB")
```

---

## 7. Session Index

### Using SessionIndex Directly

```python
from opencode.sessions import SessionStorage, SessionIndex

storage = SessionStorage()
index = SessionIndex(storage)

# Get session count
print(f"Total sessions: {index.count()}")

# Check if session is indexed
if "session-id" in index:
    summary = index.get("session-id")
    print(f"Session: {summary.title}")

# Get recent sessions
recent = index.get_recent(count=5)

# Get sessions by working directory
project_sessions = index.get_by_working_dir("/home/user/project")

# Rebuild index from session files
index.rebuild()

# Save index changes
index.save_if_dirty()
```

---

## 8. Session Hooks

### Register Custom Hooks

```python
from opencode.sessions import SessionManager, Session

def on_session_start(session: Session):
    print(f"Session started: {session.id}")
    # Log to file, send notification, etc.

def on_session_end(session: Session):
    print(f"Session ended: {session.id}")
    print(f"Total tokens used: {session.total_tokens}")

def on_message_added(session: Session, message):
    print(f"Message added: {message.role}")

manager = SessionManager.get_instance()

# Register hooks
manager.register_hook("session:start", on_session_start)
manager.register_hook("session:end", on_session_end)
manager.register_hook("session:message", on_message_added)

# Create session - triggers session:start
session = manager.create()

# Add message - triggers session:message
manager.add_message("user", "Hello")

# Close - triggers session:end
manager.close()

# Unregister hooks
manager.unregister_hook("session:start", on_session_start)
```

---

## 9. Integration with Hooks System

### Fire Session Events via Hooks System

```python
from opencode.sessions import SessionManager
from opencode.hooks import fire_event, HookEvent, HookRegistry, Hook

# Register a shell hook for session events
registry = HookRegistry.get_instance()
registry.register(Hook(
    event_pattern="session:start",
    command='echo "Session $OPENCODE_SESSION_ID started" >> /tmp/sessions.log',
))

# Session manager integration
async def on_session_start(session):
    event = HookEvent.session_start(session.id)
    await fire_event(event)

manager = SessionManager.get_instance()
manager.register_hook("session:start", lambda s: asyncio.run(on_session_start(s)))
```

---

## 10. CLI Integration Example

### Session Command Flow

```
$ opencode
OpenCode v1.0.0
Starting new session...
Session: 550e8400-e29b-41d4-a716-446655440000

You: Help me refactor the API client
Assistant: I'll help you refactor the API client. Let me read the current code...

[Session auto-saved]

You: /quit
Session saved. Goodbye!

$ opencode --resume
OpenCode v1.0.0
Resuming session: 550e8400-e29b-41d4-a716-446655440000
(Refactoring API client - 3 messages)

You: Continue where we left off
```

### Session Listing

```
$ opencode --list-sessions

Recent Sessions:
┌──────────────────────────────────────────────────────────────────────┐
│ ID          │ Title                      │ Messages │ Updated       │
├──────────────────────────────────────────────────────────────────────┤
│ 550e8400... │ Refactoring API client     │ 15       │ 2 hours ago   │
│ a1b2c3d4... │ Implementing auth          │ 32       │ 1 day ago     │
│ e5f6g7h8... │ Bug fix in parser          │ 8        │ 3 days ago    │
└──────────────────────────────────────────────────────────────────────┘

$ opencode --resume 550e8400
```

---

## 11. Session File Format

### Example Session JSON

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Refactoring the API client",
  "created_at": "2024-01-15T10:30:00+00:00",
  "updated_at": "2024-01-15T11:45:00+00:00",
  "working_dir": "/home/user/project",
  "model": "anthropic/claude-3-opus",

  "messages": [
    {
      "id": "msg_001",
      "role": "system",
      "content": "You are a helpful coding assistant.",
      "timestamp": "2024-01-15T10:30:00+00:00"
    },
    {
      "id": "msg_002",
      "role": "user",
      "content": "Help me refactor the API client",
      "timestamp": "2024-01-15T10:30:05+00:00"
    },
    {
      "id": "msg_003",
      "role": "assistant",
      "content": "I'll help you refactor...",
      "tool_calls": [
        {
          "id": "call_abc123",
          "type": "function",
          "function": {
            "name": "read",
            "arguments": "{\"file_path\": \"/home/user/project/api.py\"}"
          }
        }
      ],
      "timestamp": "2024-01-15T10:30:10+00:00"
    },
    {
      "id": "msg_004",
      "role": "tool",
      "content": "class APIClient:\n    ...",
      "tool_call_id": "call_abc123",
      "name": "read",
      "timestamp": "2024-01-15T10:30:11+00:00"
    }
  ],

  "tool_history": [
    {
      "id": "tool_001",
      "tool_name": "read",
      "arguments": {"file_path": "/home/user/project/api.py"},
      "result": {"success": true, "content": "..."},
      "timestamp": "2024-01-15T10:30:11+00:00",
      "duration": 0.05,
      "success": true,
      "error": null
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

### Index File Format

```json
{
  "version": 1,
  "sessions": {
    "550e8400-e29b-41d4-a716-446655440000": {
      "title": "Refactoring the API client",
      "created_at": "2024-01-15T10:30:00+00:00",
      "updated_at": "2024-01-15T11:45:00+00:00",
      "message_count": 15,
      "total_tokens": 2300,
      "tags": ["refactoring", "api"],
      "working_dir": "/home/user/project",
      "model": "anthropic/claude-3-opus"
    }
  }
}
```

---

## 12. Integration with REPL

### Session Status in Prompt

```python
from opencode.sessions import SessionManager

def get_prompt() -> str:
    """Build REPL prompt with session info."""
    manager = SessionManager.get_instance()

    if manager.has_current:
        session = manager.current_session
        tokens = session.total_tokens
        msg_count = session.message_count

        return f"[{msg_count} msgs | {tokens} tokens] You: "
    else:
        return "You: "
```

### Session Slash Commands

```python
# /session command implementation
async def handle_session_command(args: str) -> str:
    manager = SessionManager.get_instance()

    if not args:
        # Show current session info
        if manager.has_current:
            s = manager.current_session
            return f"""
Session: {s.id}
Title: {s.title}
Messages: {s.message_count}
Tokens: {s.total_tokens}
Created: {s.created_at}
Updated: {s.updated_at}
"""
        return "No active session"

    parts = args.split()
    subcommand = parts[0]

    if subcommand == "list":
        sessions = manager.list_sessions(limit=10)
        lines = [f"Recent sessions ({len(sessions)}):"]
        for s in sessions:
            lines.append(f"  {s.id[:8]}... {s.title} ({s.message_count} msgs)")
        return "\n".join(lines)

    elif subcommand == "new":
        manager.close()
        session = manager.create()
        return f"New session: {session.id}"

    elif subcommand == "resume":
        session_id = parts[1] if len(parts) > 1 else None
        if session_id:
            # Find matching session
            sessions = manager.list_sessions()
            for s in sessions:
                if s.id.startswith(session_id):
                    manager.resume(s.id)
                    return f"Resumed: {s.title}"
            return f"Session not found: {session_id}"
        else:
            session = manager.resume_latest()
            if session:
                return f"Resumed: {session.title}"
            return "No sessions to resume"

    elif subcommand == "title":
        title = " ".join(parts[1:])
        manager.set_title(title)
        return f"Title set: {title}"

    elif subcommand == "tag":
        tag = parts[1] if len(parts) > 1 else None
        if tag:
            manager.add_tag(tag)
            return f"Tag added: {tag}"
        return "Usage: /session tag <name>"

    return f"Unknown subcommand: {subcommand}"
```

---

## Notes

- Sessions are automatically saved on significant events
- Auto-save runs in background every 60 seconds (configurable)
- Session files are human-readable JSON
- Index file enables fast session listing
- Atomic writes prevent data corruption
- Backups are created before overwrite
- Secure file permissions (600/700) protect data