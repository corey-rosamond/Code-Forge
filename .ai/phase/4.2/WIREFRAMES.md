# Phase 4.2: Hooks System - Wireframes

**Phase:** 4.2
**Name:** Hooks System
**Dependencies:** Phase 2.1 (Tool System Foundation), Phase 4.1 (Permission System)

---

## 1. Hook Event Creation

### Creating Events
```python
from opencode.hooks import HookEvent, EventType

# Using factory methods (recommended)
event = HookEvent.tool_pre_execute(
    tool_name="bash",
    arguments={"command": "ls -la"},
    session_id="sess_abc123",
)

event = HookEvent.tool_post_execute(
    tool_name="bash",
    arguments={"command": "ls -la"},
    result={"success": True, "output": "file1.txt\nfile2.txt"},
    session_id="sess_abc123",
)

event = HookEvent.tool_error(
    tool_name="bash",
    arguments={"command": "invalid"},
    error="Command not found",
)

event = HookEvent.llm_pre_request(
    model="anthropic/claude-3-opus",
    message_count=5,
)

event = HookEvent.session_start(session_id="sess_abc123")

event = HookEvent.user_prompt_submit(
    content="Please read /tmp/test.txt",
    session_id="sess_abc123",
)

# Direct creation
event = HookEvent(
    type=EventType.PERMISSION_CHECK,
    data={"perm_level": "ask", "perm_rule": "tool:bash"},
    tool_name="bash",
)
```

### Event Data Access
```python
# Get environment variables for hook
env = event.to_env()
print(env)
# {
#     "OPENCODE_EVENT": "tool:pre_execute",
#     "OPENCODE_TIMESTAMP": "1699999999.123",
#     "OPENCODE_SESSION_ID": "sess_abc123",
#     "OPENCODE_TOOL_NAME": "bash",
#     "OPENCODE_TOOL_ARGS": '{"command": "ls -la"}',
# }

# Serialize to JSON
json_str = event.to_json()
print(json_str)
# {
#     "type": "tool:pre_execute",
#     "timestamp": 1699999999.123,
#     "data": {"tool_args": {"command": "ls -la"}},
#     "tool_name": "bash",
#     "session_id": "sess_abc123"
# }
```

---

## 2. Hook Definition

### Creating Hooks
```python
from opencode.hooks import Hook

# Simple hook
hook = Hook(
    event_pattern="tool:pre_execute",
    command="echo 'Tool starting: $OPENCODE_TOOL_NAME'",
)

# Hook with all options
hook = Hook(
    event_pattern="tool:post_execute:write",
    command="git add -A && git commit -m 'Auto-save'",
    timeout=30.0,
    working_dir="/path/to/project",
    env={"GIT_AUTHOR_NAME": "OpenCode"},
    enabled=True,
    description="Auto-commit on file writes",
)

# Blocking hook
hook = Hook(
    event_pattern="tool:pre_execute:bash",
    command="""
        if echo "$OPENCODE_TOOL_ARGS" | grep -q "sudo"; then
            echo "Blocked: sudo not allowed"
            exit 1
        fi
        exit 0
    """,
    description="Block sudo commands",
)
```

### Pattern Matching Examples
```python
# These patterns match "tool:pre_execute" event with tool_name="bash":

"tool:pre_execute"       # Exact event type match
"tool:*"                 # All tool events
"tool:pre_execute:bash"  # Specific tool match
"*"                      # Everything

# These do NOT match:
"tool:post_execute"      # Wrong event type
"tool:pre_execute:read"  # Wrong tool name
"llm:*"                  # Wrong category
```

---

## 3. Hook Registry

### Registration and Lookup
```python
from opencode.hooks import HookRegistry, Hook, HookEvent

# Get singleton registry
registry = HookRegistry.get_instance()

# Register hooks
registry.register(Hook(
    event_pattern="tool:pre_execute",
    command="echo 'Pre-execute'",
))

registry.register(Hook(
    event_pattern="tool:*",
    command="echo 'Any tool event'",
))

registry.register(Hook(
    event_pattern="session:start",
    command="notify-send 'OpenCode' 'Session started'",
))

# Get matching hooks for an event
event = HookEvent.tool_pre_execute("bash", {})
matching = registry.get_hooks(event)
print(f"Found {len(matching)} matching hooks")
# Found 2 matching hooks (tool:pre_execute and tool:*)

# Unregister
registry.unregister("tool:pre_execute")

# Clear all
registry.clear()
```

### Loading from Configuration
```python
from opencode.hooks import HookConfig, HookRegistry

# Load hooks from files
global_hooks = HookConfig.load_global()
project_hooks = HookConfig.load_project(project_root)

# Or load all at once
all_hooks = HookConfig.load_all(project_root)

# Register all
registry = HookRegistry.get_instance()
registry.load_hooks(all_hooks)
```

---

## 4. Hook Execution

### Basic Execution
```python
from opencode.hooks import HookExecutor, HookEvent, fire_event

# Create executor
executor = HookExecutor()

# Fire an event
event = HookEvent.tool_pre_execute("bash", {"command": "ls"})
results = await executor.execute_hooks(event)

# Check results
for result in results:
    print(f"Hook: {result.hook.event_pattern}")
    print(f"  Success: {result.success}")
    print(f"  Exit code: {result.exit_code}")
    print(f"  Duration: {result.duration:.2f}s")
    print(f"  Stdout: {result.stdout}")
    print(f"  Stderr: {result.stderr}")
```

### Convenience Function
```python
from opencode.hooks import fire_event, HookEvent

# Simple way to fire events
event = HookEvent.tool_pre_execute("bash", {"command": "ls"})
results = await fire_event(event)

# With stop_on_failure=False to run all hooks
results = await fire_event(event, stop_on_failure=False)
```

### Handling Blocking Hooks
```python
from opencode.hooks import fire_event, HookBlockedError, HookEvent

event = HookEvent.tool_pre_execute("bash", {"command": "sudo rm -rf /"})

results = await fire_event(event, stop_on_failure=True)

# Check if any hook blocked
for result in results:
    if not result.should_continue:
        print(f"Blocked by: {result.hook.event_pattern}")
        print(f"Reason: {result.stdout}")
        raise HookBlockedError(result)

# Or catch the error directly in tool executor
try:
    await tool_executor.execute(tool, params, context)
except HookBlockedError as e:
    print(f"Operation blocked: {e.result.hook.description}")
```

---

## 5. Hook Result Structure

```python
from opencode.hooks import HookResult

result = HookResult(
    hook=hook,
    exit_code=0,
    stdout="Success!",
    stderr="",
    duration=0.15,
    timed_out=False,
    error=None,
)

# Properties
result.success          # True (exit_code == 0 and no timeout/error)
result.should_continue  # True (exit_code == 0)

# Failed hook
result = HookResult(
    hook=hook,
    exit_code=1,
    stdout="Blocked: dangerous command",
    stderr="",
    duration=0.02,
)

result.success          # False
result.should_continue  # False (blocks operation)

# Timed out hook
result = HookResult(
    hook=hook,
    exit_code=-1,
    stdout="",
    stderr="",
    duration=10.0,
    timed_out=True,
    error="Hook timed out after 10s",
)

result.success          # False
result.should_continue  # False
```

---

## 6. Configuration Files

### Global Configuration (~/.config/src/opencode/hooks.json)
```json
{
  "hooks": [
    {
      "event": "session:start",
      "command": "notify-send 'OpenCode' 'Session started'",
      "description": "Desktop notification on session start"
    },
    {
      "event": "session:end",
      "command": "notify-send 'OpenCode' 'Session ended'",
      "description": "Desktop notification on session end"
    },
    {
      "event": "*",
      "command": "echo \"[$(date)] $OPENCODE_EVENT\" >> ~/.src/opencode/events.log",
      "description": "Log all events"
    }
  ]
}
```

### Project Configuration (.src/opencode/hooks.json)
```json
{
  "hooks": [
    {
      "event": "tool:pre_execute:bash",
      "command": "source .env.local 2>/dev/null || true",
      "description": "Load local environment before bash"
    },
    {
      "event": "tool:post_execute:write",
      "command": "git add -A && git diff --cached --quiet || git commit -m 'Auto-save: $OPENCODE_TOOL_NAME'",
      "timeout": 30.0,
      "description": "Auto-commit on file writes"
    },
    {
      "event": "tool:post_execute",
      "command": "./scripts/validate.sh",
      "timeout": 60.0,
      "enabled": true,
      "description": "Run validation after tool execution"
    }
  ]
}
```

### Configuration Management
```python
from opencode.hooks import HookConfig, Hook

# Load
global_hooks = HookConfig.load_global()
project_hooks = HookConfig.load_project(Path("/my/project"))

# Modify
global_hooks.append(Hook(
    event_pattern="tool:error",
    command="notify-send 'OpenCode Error' '$OPENCODE_ERROR'",
    description="Notify on errors",
))

# Save
HookConfig.save_global(global_hooks)
HookConfig.save_project(Path("/my/project"), project_hooks)
```

---

## 7. Hook Templates

### Available Templates
```python
from opencode.hooks import HOOK_TEMPLATES

# Log all events
log_hook = HOOK_TEMPLATES["log_all"]
# Hook(
#     event_pattern="*",
#     command='echo "[$(date)] $OPENCODE_EVENT" >> ~/.src/opencode/events.log',
#     description="Log all events to file",
# )

# Desktop notifications
notify_hook = HOOK_TEMPLATES["notify_session_start"]
# Hook(
#     event_pattern="session:start",
#     command="notify-send 'OpenCode' 'Session started'",
#     description="Desktop notification on session start",
# )

# Git auto-commit
git_hook = HOOK_TEMPLATES["git_auto_commit"]
# Hook(
#     event_pattern="tool:post_execute:write",
#     command="git add -A && git diff --cached --quiet || git commit -m 'Auto-save'",
#     timeout=30.0,
#     description="Auto-commit on file writes",
# )

# Block sudo
block_hook = HOOK_TEMPLATES["block_sudo"]
# Hook(
#     event_pattern="tool:pre_execute:bash",
#     command='if echo "$OPENCODE_TOOL_ARGS" | grep -q "sudo"; then exit 1; fi',
#     description="Block sudo commands in bash",
# )

# Use a template
from opencode.hooks import HookRegistry
registry = HookRegistry.get_instance()
registry.register(HOOK_TEMPLATES["log_all"])
```

---

## 8. Integration Example

### Tool Executor with Hooks
```python
from opencode.tools import BaseTool, ToolResult, ExecutionContext
from opencode.hooks import HookEvent, fire_event, HookBlockedError

class ToolExecutor:
    async def execute(
        self,
        tool: BaseTool,
        params: dict,
        context: ExecutionContext,
    ) -> ToolResult:
        # Fire pre-execute hooks
        pre_event = HookEvent.tool_pre_execute(
            tool_name=tool.name,
            arguments=params,
            session_id=context.session_id,
        )

        pre_results = await fire_event(pre_event, stop_on_failure=True)

        # Check for blocking
        for result in pre_results:
            if not result.should_continue:
                raise HookBlockedError(result)

        try:
            # Execute the tool
            result = await tool.execute(params, context)

            # Fire post-execute hooks
            post_event = HookEvent.tool_post_execute(
                tool_name=tool.name,
                arguments=params,
                result=result.to_dict(),
                session_id=context.session_id,
            )
            await fire_event(post_event, stop_on_failure=False)

            return result

        except Exception as e:
            # Fire error hooks
            error_event = HookEvent.tool_error(
                tool_name=tool.name,
                arguments=params,
                error=str(e),
                session_id=context.session_id,
            )
            await fire_event(error_event, stop_on_failure=False)

            raise
```

---

## 9. Shell Command Examples

### Logging Hook
```bash
#!/bin/bash
# Hook: *
# Log all events to file

LOG_FILE="$HOME/.src/opencode/events.log"
echo "[$(date -Iseconds)] $OPENCODE_EVENT tool=$OPENCODE_TOOL_NAME" >> "$LOG_FILE"
```

### Validation Hook
```bash
#!/bin/bash
# Hook: tool:post_execute:write
# Validate files after writing

FILE=$(echo "$OPENCODE_TOOL_RESULT" | jq -r '.file_path // empty')

if [[ "$FILE" == *.py ]]; then
    # Run Python linter
    python -m py_compile "$FILE" 2>&1
    exit $?
elif [[ "$FILE" == *.json ]]; then
    # Validate JSON
    jq empty "$FILE" 2>&1
    exit $?
fi

exit 0
```

### Security Hook
```bash
#!/bin/bash
# Hook: tool:pre_execute:bash
# Block dangerous commands

COMMAND=$(echo "$OPENCODE_TOOL_ARGS" | jq -r '.command // empty')

# Check for dangerous patterns
BLOCKED_PATTERNS=(
    "rm -rf /"
    "rm -fr /"
    "> /dev/"
    "mkfs"
    "dd if="
    ":(){:|:&};:"
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -q "$pattern"; then
        echo "BLOCKED: Dangerous command pattern detected: $pattern"
        exit 1
    fi
done

exit 0
```

### Git Hook
```bash
#!/bin/bash
# Hook: tool:post_execute:write
# Auto-commit file changes

# Only if in a git repo
if [ ! -d .git ]; then
    exit 0
fi

# Get the file that was written
FILE=$(echo "$OPENCODE_TOOL_RESULT" | jq -r '.file_path // empty')

if [ -n "$FILE" ]; then
    git add "$FILE"

    if ! git diff --cached --quiet; then
        git commit -m "Auto-save: $(basename "$FILE")"
    fi
fi

exit 0
```

---

## 10. Complete Usage Example

```python
"""Complete example of hooks system usage."""

import asyncio
from pathlib import Path

from opencode.hooks import (
    HookRegistry,
    HookExecutor,
    HookEvent,
    Hook,
    HookConfig,
    HookBlockedError,
    fire_event,
    HOOK_TEMPLATES,
)

async def main():
    # Get registry and clear any existing hooks
    registry = HookRegistry.get_instance()
    registry.clear()

    # Load hooks from config
    all_hooks = HookConfig.load_all(Path.cwd())
    registry.load_hooks(all_hooks)

    # Add some hooks programmatically
    registry.register(Hook(
        event_pattern="tool:pre_execute",
        command="echo '>>> Executing: $OPENCODE_TOOL_NAME'",
        description="Announce tool execution",
    ))

    registry.register(Hook(
        event_pattern="tool:pre_execute:bash",
        command="""
            if echo "$OPENCODE_TOOL_ARGS" | grep -q "sudo"; then
                echo "BLOCKED: sudo not allowed"
                exit 1
            fi
        """,
        description="Block sudo commands",
    ))

    registry.register(Hook(
        event_pattern="tool:post_execute",
        command="echo '<<< Completed: $OPENCODE_TOOL_NAME'",
        description="Announce tool completion",
    ))

    # Create executor
    executor = HookExecutor(registry=registry)

    # Simulate tool execution
    print("=" * 60)
    print("Test 1: Normal bash command")

    event = HookEvent.tool_pre_execute(
        tool_name="bash",
        arguments={"command": "ls -la"},
        session_id="test_session",
    )

    results = await executor.execute_hooks(event, stop_on_failure=True)
    print(f"Pre-execute results: {len(results)} hooks")
    for r in results:
        print(f"  {r.hook.event_pattern}: exit={r.exit_code}")
        if r.stdout.strip():
            print(f"    stdout: {r.stdout.strip()}")

    # Simulate successful completion
    post_event = HookEvent.tool_post_execute(
        tool_name="bash",
        arguments={"command": "ls -la"},
        result={"success": True, "output": "files..."},
    )
    await fire_event(post_event, stop_on_failure=False)

    print("\n" + "=" * 60)
    print("Test 2: Blocked sudo command")

    event = HookEvent.tool_pre_execute(
        tool_name="bash",
        arguments={"command": "sudo rm -rf /"},
        session_id="test_session",
    )

    results = await executor.execute_hooks(event, stop_on_failure=True)
    print(f"Pre-execute results: {len(results)} hooks")
    for r in results:
        print(f"  {r.hook.event_pattern}: exit={r.exit_code}, continue={r.should_continue}")
        if r.stdout.strip():
            print(f"    stdout: {r.stdout.strip()}")

    # Check for blocking
    blocked = [r for r in results if not r.should_continue]
    if blocked:
        print(f"\nOperation blocked by {len(blocked)} hook(s)!")

    print("\n" + "=" * 60)
    print("Test 3: Read operation (no blocking hooks)")

    event = HookEvent.tool_pre_execute(
        tool_name="read",
        arguments={"file_path": "/tmp/test.txt"},
    )

    results = await executor.execute_hooks(event)
    print(f"Pre-execute results: {len(results)} hooks")
    for r in results:
        print(f"  {r.hook.event_pattern}: exit={r.exit_code}")

    print("\n" + "=" * 60)
    print("Registered hooks:")
    for hook in registry:
        status = "enabled" if hook.enabled else "disabled"
        print(f"  [{status}] {hook.event_pattern}: {hook.description or hook.command[:40]}")


if __name__ == "__main__":
    asyncio.run(main())
```

Output:
```
============================================================
Test 1: Normal bash command
Pre-execute results: 2 hooks
  tool:pre_execute: exit=0
    stdout: >>> Executing: bash
  tool:pre_execute:bash: exit=0
<<< Completed: bash

============================================================
Test 2: Blocked sudo command
Pre-execute results: 2 hooks
  tool:pre_execute: exit=0
    stdout: >>> Executing: bash
  tool:pre_execute:bash: exit=1, continue=False
    stdout: BLOCKED: sudo not allowed

Operation blocked by 1 hook(s)!

============================================================
Test 3: Read operation (no blocking hooks)
Pre-execute results: 1 hooks
  tool:pre_execute: exit=0
    stdout: >>> Executing: read

============================================================
Registered hooks:
  [enabled] tool:pre_execute: Announce tool execution
  [enabled] tool:pre_execute:bash: Block sudo commands
  [enabled] tool:post_execute: Announce tool completion
```
