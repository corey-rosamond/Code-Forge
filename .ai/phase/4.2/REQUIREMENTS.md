# Phase 4.2: Hooks System - Requirements

**Phase:** 4.2
**Name:** Hooks System
**Dependencies:** Phase 2.1 (Tool System Foundation), Phase 4.1 (Permission System)

---

## Overview

Phase 4.2 implements a hooks system that allows users to execute custom shell commands in response to various events in the Code-Forge lifecycle. This enables automation, integration with external tools, and customization of behavior through shell scripts rather than code.

---

## Goals

1. Define hook event types for all significant actions
2. Execute shell commands as hooks with proper context
3. Support hook configuration in settings files
4. Provide mechanism for hooks to modify or block operations
5. Enable safe execution with proper error handling

---

## Non-Goals (This Phase)

- Plugin-based hooks written in Python (Phase 10.1)
- Remote webhook support
- Hook marketplace or sharing
- Complex hook dependency management
- Hook debugging/profiling tools

---

## Functional Requirements

### FR-1: Hook Events

**FR-1.1:** Define event types for tool lifecycle
- `tool:pre_execute` - Before tool execution
- `tool:post_execute` - After tool execution
- `tool:error` - When tool execution fails

**FR-1.2:** Define event types for LLM lifecycle
- `llm:pre_request` - Before LLM API call
- `llm:post_response` - After LLM response
- `llm:stream_start` - When streaming begins
- `llm:stream_end` - When streaming completes

**FR-1.3:** Define event types for session lifecycle
- `session:start` - When session begins
- `session:end` - When session ends
- `session:message` - When a message is added

**FR-1.4:** Define event types for permission events
- `permission:check` - When permission is checked
- `permission:prompt` - When user is prompted
- `permission:granted` - When permission is granted
- `permission:denied` - When permission is denied

**FR-1.5:** Define event types for user interaction
- `user:prompt_submit` - When user submits input
- `user:interrupt` - When user interrupts (Ctrl+C)

### FR-2: Hook Definition

**FR-2.1:** Hook structure
- Event pattern to match
- Shell command to execute
- Optional working directory
- Optional timeout
- Optional environment variables

**FR-2.2:** Event pattern matching
- Exact match: `tool:pre_execute`
- Glob pattern: `tool:*`
- Tool-specific: `tool:pre_execute:bash`
- Multiple events: `tool:pre_execute,tool:post_execute`

**FR-2.3:** Command templating
- Access to event data in command
- Environment variable expansion
- Shell variable syntax: `$EVENT_TYPE`, `$TOOL_NAME`

### FR-3: Hook Execution

**FR-3.1:** Execute hooks as shell commands
- Run in a subshell
- Capture stdout and stderr
- Return exit code

**FR-3.2:** Provide event context to hooks
- Set environment variables with event data
- Pass JSON event data via stdin (optional)
- Working directory is project root

**FR-3.3:** Handle hook output
- stdout captured and optionally logged
- stderr captured and logged as warnings
- Non-zero exit code treated as failure

**FR-3.4:** Timeout handling
- Default timeout per hook (configurable)
- Kill hook process on timeout
- Log timeout as error

### FR-4: Hook Control Flow

**FR-4.1:** Pre-execution hooks can block operations
- Exit code 0 = continue
- Exit code non-zero = block/abort
- stdout may contain modification data

**FR-4.2:** Hook ordering
- Hooks execute in registration order
- First blocking hook stops chain
- All hooks see original event (not modified)

**FR-4.3:** Error handling
- Hook errors don't crash main application
- Hook failures logged with context
- Option to continue or abort on hook failure

### FR-5: Hook Configuration

**FR-5.1:** Configuration in settings files
- Global hooks in user config
- Project hooks in .src/forge/hooks.json
- Session-only hooks (programmatic)

**FR-5.2:** Configuration format
```json
{
  "hooks": [
    {
      "event": "tool:pre_execute:bash",
      "command": "echo 'Running bash: $TOOL_ARGS'",
      "timeout": 5.0,
      "enabled": true
    }
  ]
}
```

**FR-5.3:** Built-in hook templates
- Logging hooks for audit trails
- Notification hooks (desktop notifications)
- Git hooks (auto-commit on write)

### FR-6: Event Context

**FR-6.1:** Standard environment variables for all events
- `FORGE_EVENT` - Event type
- `FORGE_SESSION_ID` - Current session ID
- `FORGE_WORKING_DIR` - Working directory

**FR-6.2:** Tool event variables
- `FORGE_TOOL_NAME` - Tool being executed
- `FORGE_TOOL_ARGS` - JSON of tool arguments
- `FORGE_TOOL_RESULT` - JSON of result (post only)

**FR-6.3:** LLM event variables
- `FORGE_LLM_MODEL` - Model being used
- `FORGE_LLM_TOKENS` - Token count (post only)

**FR-6.4:** Permission event variables
- `FORGE_PERM_LEVEL` - Permission level
- `FORGE_PERM_RULE` - Matching rule (if any)

---

## Non-Functional Requirements

### NFR-1: Performance
- Hook registration O(1)
- Hook lookup O(n) where n = matching hooks
- Hook execution overhead < 100ms per hook
- No blocking of main thread during hook execution

### NFR-2: Security
- Hooks run with user's permissions
- No automatic privilege escalation
- Sensitive data redacted in logs
- Hooks cannot access internal state directly

### NFR-3: Reliability
- Hook failures isolated from main application
- Timeout prevents hung hooks
- Clear error messages for debugging

### NFR-4: Usability
- Simple configuration format
- Helpful error messages
- Hook execution can be traced

---

## Technical Specifications

### Package Structure

```
src/forge/hooks/
├── __init__.py           # Package exports
├── events.py             # Event types and data
├── registry.py           # Hook registration
├── executor.py           # Hook execution
└── config.py             # Hook configuration
```

### Class Signatures

```python
# events.py
from enum import Enum
from dataclasses import dataclass, field
from typing import Any

class EventType(str, Enum):
    """Hook event types."""
    # Tool events
    TOOL_PRE_EXECUTE = "tool:pre_execute"
    TOOL_POST_EXECUTE = "tool:post_execute"
    TOOL_ERROR = "tool:error"

    # LLM events
    LLM_PRE_REQUEST = "llm:pre_request"
    LLM_POST_RESPONSE = "llm:post_response"
    LLM_STREAM_START = "llm:stream_start"
    LLM_STREAM_END = "llm:stream_end"

    # Session events
    SESSION_START = "session:start"
    SESSION_END = "session:end"
    SESSION_MESSAGE = "session:message"

    # Permission events
    PERMISSION_CHECK = "permission:check"
    PERMISSION_PROMPT = "permission:prompt"
    PERMISSION_GRANTED = "permission:granted"
    PERMISSION_DENIED = "permission:denied"

    # User events
    USER_PROMPT_SUBMIT = "user:prompt_submit"
    USER_INTERRUPT = "user:interrupt"


@dataclass
class HookEvent:
    """Event data passed to hooks."""
    type: EventType
    timestamp: float
    data: dict[str, Any] = field(default_factory=dict)
    tool_name: str | None = None
    session_id: str | None = None

    def to_env(self) -> dict[str, str]: ...
    def to_json(self) -> str: ...


# registry.py
@dataclass
class Hook:
    """A registered hook."""
    event_pattern: str
    command: str
    timeout: float = 10.0
    working_dir: str | None = None
    env: dict[str, str] | None = None
    enabled: bool = True
    description: str = ""

    def matches(self, event: HookEvent) -> bool: ...
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "Hook": ...


class HookRegistry:
    """Registry of hooks."""

    hooks: list[Hook]

    def __init__(self): ...
    def register(self, hook: Hook) -> None: ...
    def unregister(self, event_pattern: str) -> bool: ...
    def get_hooks(self, event: HookEvent) -> list[Hook]: ...
    def clear(self) -> None: ...

    @classmethod
    def get_instance(cls) -> "HookRegistry": ...


# executor.py
@dataclass
class HookResult:
    """Result of hook execution."""
    hook: Hook
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    timed_out: bool = False
    error: str | None = None

    @property
    def success(self) -> bool: ...
    @property
    def should_continue(self) -> bool: ...


class HookExecutor:
    """Executes hooks."""

    registry: HookRegistry
    default_timeout: float = 10.0
    working_dir: Path | None = None

    async def execute_hooks(
        self,
        event: HookEvent,
        *,
        stop_on_failure: bool = True,
    ) -> list[HookResult]: ...

    async def _execute_hook(
        self,
        hook: Hook,
        event: HookEvent,
    ) -> HookResult: ...


# config.py
class HookConfig:
    """Hook configuration management."""

    @classmethod
    def load_global(cls) -> list[Hook]: ...

    @classmethod
    def load_project(cls, project_root: Path) -> list[Hook]: ...

    @classmethod
    def save_global(cls, hooks: list[Hook]) -> None: ...

    @classmethod
    def save_project(cls, project_root: Path, hooks: list[Hook]) -> None: ...

    @classmethod
    def get_default_hooks(cls) -> list[Hook]: ...
```

---

## Environment Variables

All hooks receive these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `FORGE_EVENT` | Event type | `tool:pre_execute` |
| `FORGE_SESSION_ID` | Session identifier | `sess_abc123` |
| `FORGE_WORKING_DIR` | Working directory | `/home/user/project` |
| `FORGE_TOOL_NAME` | Tool name (tool events) | `bash` |
| `FORGE_TOOL_ARGS` | Tool arguments as JSON | `{"command": "ls"}` |
| `FORGE_TOOL_RESULT` | Tool result as JSON | `{"success": true}` |
| `FORGE_LLM_MODEL` | LLM model (LLM events) | `anthropic/claude-3` |
| `FORGE_LLM_TOKENS` | Token count | `1500` |
| `FORGE_PERM_LEVEL` | Permission level | `ask` |

---

## Hook Configuration Format

### Global Config (~/.config/src/forge/hooks.json)
```json
{
  "hooks": [
    {
      "event": "session:start",
      "command": "notify-send 'Code-Forge' 'Session started'",
      "description": "Desktop notification on session start"
    },
    {
      "event": "tool:post_execute:write",
      "command": "git add -A && git diff --cached --quiet || git commit -m 'Auto-save: $FORGE_TOOL_ARGS'",
      "timeout": 30.0,
      "description": "Auto-commit on file writes"
    }
  ]
}
```

### Project Config (.src/forge/hooks.json)
```json
{
  "hooks": [
    {
      "event": "tool:pre_execute:bash",
      "command": "[ ! -f .env.local ] || source .env.local",
      "description": "Load local environment before bash"
    },
    {
      "event": "tool:post_execute",
      "command": "./scripts/validate.sh",
      "timeout": 60.0,
      "description": "Run validation after tool execution"
    }
  ]
}
```

---

## Event Pattern Matching

```python
# Exact match
"tool:pre_execute"  # Matches only tool:pre_execute

# Wildcard events
"tool:*"  # Matches all tool events

# Tool-specific
"tool:pre_execute:bash"  # Matches pre_execute for bash only
"tool:*:write"  # Matches all tool events for write

# Multiple patterns (comma-separated)
"session:start,session:end"  # Matches both events

# All events
"*"  # Matches everything (use with caution)
```

---

## Blocking Hooks

Pre-execution hooks can block the operation:

```bash
#!/bin/bash
# Hook: tool:pre_execute:bash
# Exit 0 to allow, non-zero to block

COMMAND="$FORGE_TOOL_ARGS"

# Block certain commands
if echo "$COMMAND" | grep -q "sudo"; then
    echo "Blocked: sudo commands not allowed"
    exit 1
fi

# Allow everything else
exit 0
```

---

## Integration Points

### With Tool Executor
- Fire `tool:pre_execute` before execution
- Fire `tool:post_execute` after success
- Fire `tool:error` on failure
- Block execution if pre-hook fails

### With LLM Client
- Fire `llm:pre_request` before API call
- Fire `llm:post_response` after response
- Fire stream events for streaming

### With Permission System
- Fire `permission:check` on every check
- Fire `permission:prompt` when prompting
- Fire granted/denied based on outcome

### With Session Manager
- Fire `session:start` on new session
- Fire `session:end` on session close
- Fire `session:message` on message add

---

## Error Scenarios

| Scenario | Handling |
|----------|----------|
| Hook command not found | Log error, continue |
| Hook times out | Kill process, log error |
| Hook exits non-zero | Log warning, optionally block |
| Hook crashes | Catch exception, log error |
| Invalid hook config | Log warning, skip hook |
| Circular hook trigger | Detect and prevent |

---

## Testing Requirements

1. Unit tests for EventType enum
2. Unit tests for HookEvent data class
3. Unit tests for Hook pattern matching
4. Unit tests for HookRegistry
5. Unit tests for HookExecutor
6. Unit tests for configuration loading
7. Integration tests with mock commands
8. Test timeout handling
9. Test blocking hooks
10. Test coverage ≥ 90%

---

## Acceptance Criteria

1. All event types defined and documented
2. Hooks execute shell commands correctly
3. Environment variables set properly
4. Pattern matching works for all formats
5. Timeout handling prevents hung hooks
6. Blocking hooks can prevent operations
7. Configuration loads from both global and project
8. Hook failures don't crash application
9. Clear logging of hook execution
10. Integration with tool executor works
