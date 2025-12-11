# Phase 4.2: Hooks System - Implementation Plan

**Phase:** 4.2
**Name:** Hooks System
**Dependencies:** Phase 2.1 (Tool System Foundation), Phase 4.1 (Permission System)

---

## Implementation Order

1. Event types and data structures
2. Hook definition and pattern matching
3. Hook registry
4. Hook executor
5. Configuration loading
6. Integration with existing systems
7. Package exports and tests

---

## Step 1: Event Types and Data

Create `src/forge/hooks/events.py`:

```python
"""Hook event types and data structures."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """
    Hook event types.

    Events are organized by category:
    - tool: Tool execution lifecycle
    - llm: LLM API interaction lifecycle
    - session: Session management lifecycle
    - permission: Permission system events
    - user: User interaction events
    """

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
    """
    Event data passed to hooks.

    Contains all information about an event that hooks can use
    to decide whether to act and what action to take.

    Attributes:
        type: The event type
        timestamp: Unix timestamp when event occurred
        data: Additional event-specific data
        tool_name: Tool name for tool events
        session_id: Current session ID
    """

    type: EventType
    timestamp: float = field(default_factory=time.time)
    data: dict[str, Any] = field(default_factory=dict)
    tool_name: str | None = None
    session_id: str | None = None

    @staticmethod
    def _sanitize_env_value(value: str) -> str:
        """Sanitize a value for safe use in environment variables.

        Removes or escapes characters that could cause shell injection
        when environment variables are used in shell commands.

        Args:
            value: The raw value to sanitize.

        Returns:
            Sanitized string safe for environment variable use.
        """
        # Remove null bytes (can truncate env vars)
        value = value.replace('\x00', '')
        # Remove newlines (can break env var parsing)
        value = value.replace('\n', ' ').replace('\r', '')
        # Limit length to prevent DoS via huge env vars
        max_len = 8192
        if len(value) > max_len:
            value = value[:max_len] + '...[truncated]'
        return value

    def to_env(self) -> dict[str, str]:
        """
        Convert event to environment variables for hook execution.

        All values are sanitized to prevent shell injection attacks
        when hooks use these variables in shell commands.

        Returns:
            Dictionary of environment variable name -> value
        """
        env = {
            "FORGE_EVENT": self._sanitize_env_value(self.type.value),
            "FORGE_TIMESTAMP": str(self.timestamp),
        }

        if self.session_id:
            env["FORGE_SESSION_ID"] = self._sanitize_env_value(self.session_id)

        if self.tool_name:
            env["FORGE_TOOL_NAME"] = self._sanitize_env_value(self.tool_name)

        # Add specific data fields as environment variables
        for key, value in self.data.items():
            # Sanitize key to valid env var name (alphanumeric + underscore)
            safe_key = ''.join(c if c.isalnum() or c == '_' else '_' for c in key.upper())
            env_key = f"FORGE_{safe_key}"

            if isinstance(value, (dict, list)):
                env[env_key] = self._sanitize_env_value(json.dumps(value))
            else:
                env[env_key] = self._sanitize_env_value(str(value))

        return env

    def to_json(self) -> str:
        """
        Serialize event to JSON string.

        Returns:
            JSON representation of the event
        """
        return json.dumps({
            "type": self.type.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "tool_name": self.tool_name,
            "session_id": self.session_id,
        })

    @classmethod
    def tool_pre_execute(
        cls,
        tool_name: str,
        arguments: dict[str, Any],
        session_id: str | None = None,
    ) -> "HookEvent":
        """Create a tool pre-execute event."""
        return cls(
            type=EventType.TOOL_PRE_EXECUTE,
            tool_name=tool_name,
            session_id=session_id,
            data={
                "tool_args": arguments,
            },
        )

    @classmethod
    def tool_post_execute(
        cls,
        tool_name: str,
        arguments: dict[str, Any],
        result: dict[str, Any],
        session_id: str | None = None,
    ) -> "HookEvent":
        """Create a tool post-execute event."""
        return cls(
            type=EventType.TOOL_POST_EXECUTE,
            tool_name=tool_name,
            session_id=session_id,
            data={
                "tool_args": arguments,
                "tool_result": result,
            },
        )

    @classmethod
    def tool_error(
        cls,
        tool_name: str,
        arguments: dict[str, Any],
        error: str,
        session_id: str | None = None,
    ) -> "HookEvent":
        """Create a tool error event."""
        return cls(
            type=EventType.TOOL_ERROR,
            tool_name=tool_name,
            session_id=session_id,
            data={
                "tool_args": arguments,
                "error": error,
            },
        )

    @classmethod
    def llm_pre_request(
        cls,
        model: str,
        message_count: int,
        session_id: str | None = None,
    ) -> "HookEvent":
        """Create an LLM pre-request event."""
        return cls(
            type=EventType.LLM_PRE_REQUEST,
            session_id=session_id,
            data={
                "llm_model": model,
                "message_count": message_count,
            },
        )

    @classmethod
    def llm_post_response(
        cls,
        model: str,
        tokens: int,
        session_id: str | None = None,
    ) -> "HookEvent":
        """Create an LLM post-response event."""
        return cls(
            type=EventType.LLM_POST_RESPONSE,
            session_id=session_id,
            data={
                "llm_model": model,
                "llm_tokens": tokens,
            },
        )

    @classmethod
    def session_start(cls, session_id: str) -> "HookEvent":
        """Create a session start event."""
        return cls(
            type=EventType.SESSION_START,
            session_id=session_id,
        )

    @classmethod
    def session_end(cls, session_id: str) -> "HookEvent":
        """Create a session end event."""
        return cls(
            type=EventType.SESSION_END,
            session_id=session_id,
        )

    @classmethod
    def permission_check(
        cls,
        tool_name: str,
        level: str,
        rule: str | None = None,
        session_id: str | None = None,
    ) -> "HookEvent":
        """Create a permission check event."""
        return cls(
            type=EventType.PERMISSION_CHECK,
            tool_name=tool_name,
            session_id=session_id,
            data={
                "perm_level": level,
                "perm_rule": rule or "",
            },
        )

    @classmethod
    def user_prompt_submit(
        cls,
        content: str,
        session_id: str | None = None,
    ) -> "HookEvent":
        """Create a user prompt submit event."""
        return cls(
            type=EventType.USER_PROMPT_SUBMIT,
            session_id=session_id,
            data={
                "user_input": content,
            },
        )
```

---

## Step 2: Hook Definition and Pattern Matching

Create `src/forge/hooks/registry.py`:

```python
"""Hook registration and pattern matching."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import Any, ClassVar

from forge.hooks.events import HookEvent, EventType


@dataclass
class Hook:
    """
    A registered hook.

    Hooks are shell commands that execute in response to events.
    They can observe events, modify behavior, or block operations.

    Attributes:
        event_pattern: Pattern to match events (glob or exact)
        command: Shell command to execute
        timeout: Maximum execution time in seconds (min 0.1, max 300)
        working_dir: Working directory for command
        env: Additional environment variables
        enabled: Whether hook is active
        description: Human-readable description
    """

    # Timeout bounds to prevent runaway or effectively-disabled hooks
    MIN_TIMEOUT: ClassVar[float] = 0.1   # 100ms minimum
    MAX_TIMEOUT: ClassVar[float] = 300.0  # 5 minutes maximum

    event_pattern: str
    command: str
    timeout: float = 10.0
    working_dir: str | None = None
    env: dict[str, str] | None = None
    enabled: bool = True
    description: str = ""

    def __post_init__(self):
        """Validate and clamp timeout to safe bounds."""
        if self.timeout <= 0:
            self.timeout = self.MIN_TIMEOUT
        elif self.timeout < self.MIN_TIMEOUT:
            self.timeout = self.MIN_TIMEOUT
        elif self.timeout > self.MAX_TIMEOUT:
            self.timeout = self.MAX_TIMEOUT

    def matches(self, event: HookEvent) -> bool:
        """
        Check if this hook should fire for the given event.

        Supports patterns:
        - Exact match: "tool:pre_execute"
        - Glob: "tool:*"
        - Tool-specific: "tool:pre_execute:bash"
        - Multiple (comma): "session:start,session:end"

        Args:
            event: The event to check

        Returns:
            True if hook should fire
        """
        event_str = event.type.value
        tool_suffix = f":{event.tool_name}" if event.tool_name else ""
        full_event = f"{event_str}{tool_suffix}"

        # Handle comma-separated patterns
        patterns = [p.strip() for p in self.event_pattern.split(",")]

        for pattern in patterns:
            # Exact match
            if pattern == event_str or pattern == full_event:
                return True

            # Match all events
            if pattern == "*":
                return True

            # Glob match against event type
            if fnmatch.fnmatch(event_str, pattern):
                return True

            # Glob match against full event (with tool name)
            if fnmatch.fnmatch(full_event, pattern):
                return True

            # Tool-specific pattern (e.g., "tool:pre_execute:bash")
            if ":" in pattern:
                parts = pattern.split(":")
                if len(parts) == 3:
                    # Format: category:event:tool
                    cat, evt, tool = parts
                    event_parts = event_str.split(":")
                    if len(event_parts) >= 2:
                        if (fnmatch.fnmatch(event_parts[0], cat) and
                            fnmatch.fnmatch(event_parts[1], evt) and
                            event.tool_name and
                            fnmatch.fnmatch(event.tool_name, tool)):
                            return True

        return False

    def to_dict(self) -> dict[str, Any]:
        """Serialize hook to dictionary."""
        data = {
            "event": self.event_pattern,
            "command": self.command,
        }
        if self.timeout != 10.0:
            data["timeout"] = self.timeout
        if self.working_dir:
            data["working_dir"] = self.working_dir
        if self.env:
            data["env"] = self.env
        if not self.enabled:
            data["enabled"] = False
        if self.description:
            data["description"] = self.description
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Hook":
        """Deserialize hook from dictionary."""
        return cls(
            event_pattern=data["event"],
            command=data["command"],
            timeout=data.get("timeout", 10.0),
            working_dir=data.get("working_dir"),
            env=data.get("env"),
            enabled=data.get("enabled", True),
            description=data.get("description", ""),
        )


class HookRegistry:
    """
    Registry of hooks.

    Maintains a list of hooks and provides lookup by event.
    Singleton pattern ensures consistent state.
    Thread-safe: uses RLock for all mutations.

    Example:
        ```python
        registry = HookRegistry.get_instance()
        registry.register(Hook(
            event_pattern="tool:pre_execute",
            command="echo 'Tool starting'",
        ))

        event = HookEvent.tool_pre_execute("bash", {})
        matching_hooks = registry.get_hooks(event)
        ```
    """

    _instance: ClassVar["HookRegistry | None"] = None

    def __init__(self):
        """Initialize empty registry."""
        import threading
        self.hooks: list[Hook] = []
        self._lock = threading.RLock()  # Thread-safe operations

    @classmethod
    def get_instance(cls) -> "HookRegistry":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None

    def register(self, hook: Hook) -> None:
        """
        Register a hook.

        Thread-safe: uses lock.

        Args:
            hook: Hook to register
        """
        with self._lock:
            self.hooks.append(hook)

    def unregister(self, event_pattern: str) -> bool:
        """
        Unregister hooks matching a pattern.

        Thread-safe: uses lock.

        Args:
            event_pattern: Pattern to match

        Returns:
            True if any hooks were removed
        """
        with self._lock:
            original_count = len(self.hooks)
            self.hooks = [h for h in self.hooks if h.event_pattern != event_pattern]
            return len(self.hooks) < original_count

    def get_hooks(self, event: HookEvent) -> list[Hook]:
        """
        Get all hooks that match an event.

        Thread-safe: returns a copy of matching hooks.

        Args:
            event: Event to match

        Returns:
            List of matching, enabled hooks
        """
        with self._lock:
            return [
                hook for hook in self.hooks
                if hook.enabled and hook.matches(event)
            ]

    def clear(self) -> None:
        """Clear all registered hooks."""
        with self._lock:
            self.hooks = []

    def load_hooks(self, hooks: list[Hook]) -> None:
        """
        Load multiple hooks.

        Thread-safe: uses lock.

        Args:
            hooks: Hooks to add
        """
        with self._lock:
            self.hooks.extend(hooks)

    def __len__(self) -> int:
        with self._lock:
            return len(self.hooks)

    def __iter__(self):
        # Return copy to avoid issues during iteration
        with self._lock:
            return iter(list(self.hooks))
```

---

## Step 3: Hook Executor

Create `src/forge/hooks/executor.py`:

```python
"""Hook execution engine."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from forge.hooks.events import HookEvent
from forge.hooks.registry import Hook, HookRegistry

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class HookResult:
    """
    Result of hook execution.

    Attributes:
        hook: The hook that was executed
        exit_code: Process exit code (0 = success)
        stdout: Captured standard output
        stderr: Captured standard error
        duration: Execution time in seconds
        timed_out: Whether the hook timed out
        error: Error message if execution failed
    """

    hook: Hook
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    timed_out: bool = False
    error: str | None = None

    @property
    def success(self) -> bool:
        """Check if hook executed successfully."""
        return self.exit_code == 0 and not self.timed_out and not self.error

    @property
    def should_continue(self) -> bool:
        """
        Check if operation should continue.

        For pre-execution hooks, non-zero exit means block.
        """
        return self.exit_code == 0


class HookExecutor:
    """
    Executes hooks in response to events.

    Handles shell command execution with proper environment,
    timeout management, and result collection.

    Example:
        ```python
        executor = HookExecutor()
        event = HookEvent.tool_pre_execute("bash", {"command": "ls"})

        results = await executor.execute_hooks(event)
        for result in results:
            if not result.should_continue:
                raise HookBlockedError(result)
        ```
    """

    def __init__(
        self,
        registry: HookRegistry | None = None,
        default_timeout: float = 10.0,
        working_dir: Path | None = None,
    ):
        """
        Initialize executor.

        Args:
            registry: Hook registry (uses singleton if not provided)
            default_timeout: Default timeout for hooks
            working_dir: Default working directory
        """
        self.registry = registry or HookRegistry.get_instance()
        self.default_timeout = default_timeout
        self.working_dir = working_dir or Path.cwd()

    # Maximum number of results to keep per execute_hooks call
    MAX_RESULTS = 100

    async def execute_hooks(
        self,
        event: HookEvent,
        *,
        stop_on_failure: bool = True,
        max_results: int | None = None,
    ) -> list[HookResult]:
        """
        Execute all matching hooks for an event.

        Args:
            event: The event to handle
            stop_on_failure: Stop after first failing hook
            max_results: Maximum results to return (default: MAX_RESULTS)

        Returns:
            List of hook execution results (bounded to max_results)
        """
        hooks = self.registry.get_hooks(event)

        if not hooks:
            return []

        max_results = max_results or self.MAX_RESULTS
        results: list[HookResult] = []

        for hook in hooks:
            try:
                result = await self._execute_hook(hook, event)
                results.append(result)

                # Log result
                if result.success:
                    logger.debug(
                        f"Hook '{hook.event_pattern}' succeeded "
                        f"(exit={result.exit_code}, {result.duration:.2f}s)"
                    )
                else:
                    logger.warning(
                        f"Hook '{hook.event_pattern}' failed: "
                        f"exit={result.exit_code}, timed_out={result.timed_out}"
                    )

                # Check if we should stop
                if stop_on_failure and not result.should_continue:
                    logger.info(f"Hook blocked operation: {hook.event_pattern}")
                    break

                # Check if we've hit the results limit
                if len(results) >= max_results:
                    logger.warning(
                        f"Hook results limit reached ({max_results}), "
                        f"skipping remaining hooks"
                    )
                    break

            except Exception as e:
                logger.error(f"Hook '{hook.event_pattern}' error: {e}")
                results.append(HookResult(
                    hook=hook,
                    exit_code=-1,
                    stdout="",
                    stderr="",
                    duration=0.0,
                    error=str(e),
                ))
                if stop_on_failure:
                    break

                # Also check limit after errors
                if len(results) >= max_results:
                    break

        return results

    async def _execute_hook(
        self,
        hook: Hook,
        event: HookEvent,
    ) -> HookResult:
        """
        Execute a single hook.

        Args:
            hook: The hook to execute
            event: The triggering event

        Returns:
            HookResult with execution details
        """
        start_time = time.time()

        # Build environment
        env = os.environ.copy()
        env.update(event.to_env())

        # Add working directory
        work_dir = hook.working_dir or str(self.working_dir)
        env["FORGE_WORKING_DIR"] = work_dir

        # Add hook-specific env vars
        if hook.env:
            env.update(hook.env)

        # Determine timeout
        timeout = hook.timeout or self.default_timeout

        try:
            # Create subprocess - may raise OSError for invalid commands/paths
            process = await asyncio.create_subprocess_shell(
                hook.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir,
                env=env,
            )

            try:
                # Wait with timeout
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )

                duration = time.time() - start_time

                return HookResult(
                    hook=hook,
                    exit_code=process.returncode or 0,
                    stdout=stdout_bytes.decode("utf-8", errors="replace"),
                    stderr=stderr_bytes.decode("utf-8", errors="replace"),
                    duration=duration,
                )

            except asyncio.TimeoutError:
                # Kill process on timeout
                process.kill()
                await process.wait()

                duration = time.time() - start_time

                return HookResult(
                    hook=hook,
                    exit_code=-1,
                    stdout="",
                    stderr="",
                    duration=duration,
                    timed_out=True,
                    error=f"Hook timed out after {timeout}s",
                )

        except OSError as e:
            # Handle subprocess creation failures (invalid command, bad path, etc.)
            duration = time.time() - start_time
            return HookResult(
                hook=hook,
                exit_code=-1,
                stdout="",
                stderr="",
                duration=duration,
                error=f"Failed to execute hook: {e}",
            )

        except Exception as e:
            # Catch-all for unexpected errors
            duration = time.time() - start_time
            logger.exception(f"Unexpected error executing hook: {hook.event_pattern}")
            return HookResult(
                hook=hook,
                exit_code=-1,
                stdout="",
                stderr="",
                duration=duration,
                error=f"Unexpected error: {e}",
            )


class HookBlockedError(Exception):
    """Raised when a hook blocks an operation."""

    def __init__(self, result: HookResult):
        self.result = result
        super().__init__(
            f"Operation blocked by hook '{result.hook.event_pattern}': "
            f"exit code {result.exit_code}"
        )


async def fire_event(
    event: HookEvent,
    *,
    executor: HookExecutor | None = None,
    stop_on_failure: bool = True,
) -> list[HookResult]:
    """
    Convenience function to fire an event.

    Args:
        event: Event to fire
        executor: Executor to use (creates default if not provided)
        stop_on_failure: Stop after first failing hook

    Returns:
        List of hook results
    """
    exec_instance = executor or HookExecutor()
    return await exec_instance.execute_hooks(event, stop_on_failure=stop_on_failure)
```

---

## Step 4: Configuration

Create `src/forge/hooks/config.py`:

```python
"""Hook configuration management."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from forge.hooks.registry import Hook

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# Default hooks (mostly logging/examples)
DEFAULT_HOOKS: list[Hook] = []  # No default hooks - user must configure


class HookConfig:
    """Manages hook configuration files."""

    GLOBAL_FILE = "hooks.json"
    PROJECT_FILE = ".src/forge/hooks.json"

    @classmethod
    def get_global_path(cls) -> Path:
        """Get path to global hooks file."""
        from forge.config import Config

        config_dir = Config.get_config_dir()
        return config_dir / cls.GLOBAL_FILE

    @classmethod
    def get_project_path(cls, project_root: Path | None = None) -> Path | None:
        """Get path to project hooks file."""
        if project_root is None:
            return None
        return project_root / cls.PROJECT_FILE

    @classmethod
    def load_global(cls) -> list[Hook]:
        """
        Load global hooks.

        Returns:
            List of hooks from global config
        """
        path = cls.get_global_path()

        if not path.exists():
            return list(DEFAULT_HOOKS)

        try:
            with open(path) as f:
                data = json.load(f)

            hooks = [Hook.from_dict(h) for h in data.get("hooks", [])]
            logger.debug(f"Loaded {len(hooks)} global hooks")
            return hooks

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Error loading global hooks: {e}")
            return list(DEFAULT_HOOKS)

    @classmethod
    def load_project(cls, project_root: Path | None) -> list[Hook]:
        """
        Load project-specific hooks.

        Args:
            project_root: Path to project root

        Returns:
            List of project hooks
        """
        path = cls.get_project_path(project_root)

        if path is None or not path.exists():
            return []

        try:
            with open(path) as f:
                data = json.load(f)

            hooks = [Hook.from_dict(h) for h in data.get("hooks", [])]
            logger.debug(f"Loaded {len(hooks)} project hooks")
            return hooks

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Error loading project hooks: {e}")
            return []

    @classmethod
    def save_global(cls, hooks: list[Hook]) -> None:
        """Save global hooks."""
        path = cls.get_global_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "hooks": [h.to_dict() for h in hooks],
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved {len(hooks)} global hooks")

    @classmethod
    def save_project(cls, project_root: Path, hooks: list[Hook]) -> None:
        """Save project hooks."""
        path = project_root / cls.PROJECT_FILE
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "hooks": [h.to_dict() for h in hooks],
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved {len(hooks)} project hooks")

    @classmethod
    def load_all(cls, project_root: Path | None = None) -> list[Hook]:
        """
        Load all hooks (global + project).

        Args:
            project_root: Optional project root path

        Returns:
            Combined list of hooks
        """
        hooks = cls.load_global()
        hooks.extend(cls.load_project(project_root))
        return hooks


# Example hook templates
HOOK_TEMPLATES = {
    "log_all": Hook(
        event_pattern="*",
        command='echo "[$(date)] $FORGE_EVENT" >> ~/.src/forge/events.log',
        description="Log all events to file",
    ),
    "notify_session_start": Hook(
        event_pattern="session:start",
        command="notify-send 'Code-Forge' 'Session started'",
        description="Desktop notification on session start",
    ),
    "git_auto_commit": Hook(
        event_pattern="tool:post_execute:write",
        command=(
            "git add -A && "
            "git diff --cached --quiet || "
            "git commit -m 'Auto-save: file written'"
        ),
        timeout=30.0,
        description="Auto-commit on file writes",
    ),
    "block_sudo": Hook(
        event_pattern="tool:pre_execute:bash",
        command=(
            'if echo "$FORGE_TOOL_ARGS" | grep -q "sudo"; then '
            'echo "sudo blocked by hook"; exit 1; fi'
        ),
        description="Block sudo commands in bash",
    ),
}
```

---

## Step 5: Package Exports

Create `src/forge/hooks/__init__.py`:

```python
"""
Hooks system for Code-Forge.

This package provides a hooks mechanism that allows users to
execute custom shell commands in response to various events
in the Code-Forge lifecycle.

Example:
    ```python
    from forge.hooks import (
        HookRegistry,
        HookExecutor,
        HookEvent,
        Hook,
        fire_event,
    )

    # Register a hook
    registry = HookRegistry.get_instance()
    registry.register(Hook(
        event_pattern="tool:pre_execute",
        command="echo 'Executing tool: $FORGE_TOOL_NAME'",
    ))

    # Fire an event
    event = HookEvent.tool_pre_execute("bash", {"command": "ls"})
    results = await fire_event(event)

    # Check results
    for result in results:
        if not result.should_continue:
            print(f"Blocked by hook: {result.hook.event_pattern}")
    ```
"""

from forge.hooks.events import (
    EventType,
    HookEvent,
)
from forge.hooks.registry import (
    Hook,
    HookRegistry,
)
from forge.hooks.executor import (
    HookResult,
    HookExecutor,
    HookBlockedError,
    fire_event,
)
from forge.hooks.config import (
    HookConfig,
    HOOK_TEMPLATES,
)

__all__ = [
    # Events
    "EventType",
    "HookEvent",
    # Registry
    "Hook",
    "HookRegistry",
    # Executor
    "HookResult",
    "HookExecutor",
    "HookBlockedError",
    "fire_event",
    # Config
    "HookConfig",
    "HOOK_TEMPLATES",
]
```

---

## Step 6: Integration with Tool Executor

Update `src/forge/tools/executor.py` to fire hook events:

```python
# Add to ToolExecutor.execute()

from forge.hooks import HookEvent, fire_event, HookBlockedError

async def execute(
    self,
    tool: BaseTool,
    params: dict,
    context: ExecutionContext,
) -> ToolResult:
    """Execute a tool with hooks and permissions."""

    # Fire pre-execute hook
    pre_event = HookEvent.tool_pre_execute(
        tool_name=tool.name,
        arguments=params,
        session_id=context.session_id,
    )

    hook_results = await fire_event(pre_event, stop_on_failure=True)

    # Check if any hook blocked execution
    for result in hook_results:
        if not result.should_continue:
            raise HookBlockedError(result)

    # ... existing permission check ...

    try:
        # Execute tool
        result = await tool.execute(params, context)

        # Fire post-execute hook
        post_event = HookEvent.tool_post_execute(
            tool_name=tool.name,
            arguments=params,
            result=result.to_dict(),
            session_id=context.session_id,
        )
        await fire_event(post_event, stop_on_failure=False)

        return result

    except Exception as e:
        # Fire error hook
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

## Testing Strategy

### Test Files Structure

```
tests/unit/hooks/
├── __init__.py
├── test_events.py
├── test_registry.py
├── test_executor.py
└── test_config.py
```

### Key Test Cases

1. **test_events.py**
   - Test EventType enum values
   - Test HookEvent factory methods
   - Test to_env() conversion
   - Test to_json() serialization

2. **test_registry.py**
   - Test Hook pattern matching
   - Test exact match
   - Test glob patterns
   - Test tool-specific patterns
   - Test HookRegistry registration
   - Test get_hooks filtering

3. **test_executor.py**
   - Test successful hook execution
   - Test hook timeout
   - Test hook failure
   - Test blocking hooks
   - Test multiple hooks

4. **test_config.py**
   - Test config loading
   - Test config saving
   - Test hook templates
