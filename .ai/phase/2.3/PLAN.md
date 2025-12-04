# Phase 2.3: Execution Tools - Implementation Plan

**Phase:** 2.3
**Name:** Execution Tools
**Dependencies:** Phase 2.1 (Tool System Foundation)

---

## Overview

Phase 2.3 implements the command execution tools:
1. **Bash** - Execute shell commands
2. **BashOutput** - Get output from background shells
3. **KillShell** - Terminate background shells
4. **ShellManager** - Manage shell processes

All tools extend `BaseTool` from Phase 2.1.

---

## Architecture

```
src/opencode/tools/
├── __init__.py          # Updated exports
├── base.py              # From Phase 2.1
├── registry.py          # From Phase 2.1
├── executor.py          # From Phase 2.1
├── file/                # From Phase 2.2
└── execution/
    ├── __init__.py      # Execution tools exports
    ├── bash.py          # BashTool
    ├── bash_output.py   # BashOutputTool
    ├── kill_shell.py    # KillShellTool
    └── shell_manager.py # ShellManager singleton
```

---

## Implementation Steps

### Step 1: Create Execution Tools Package

```python
# src/opencode/tools/execution/__init__.py
"""Execution tools for OpenCode."""

from opencode.tools.execution.bash import BashTool
from opencode.tools.execution.bash_output import BashOutputTool
from opencode.tools.execution.kill_shell import KillShellTool
from opencode.tools.execution.shell_manager import ShellManager, ShellProcess, ShellStatus

__all__ = [
    "BashTool",
    "BashOutputTool",
    "KillShellTool",
    "ShellManager",
    "ShellProcess",
    "ShellStatus",
]


def register_execution_tools(registry: "ToolRegistry") -> None:
    """Register all execution tools with the registry."""
    registry.register(BashTool())
    registry.register(BashOutputTool())
    registry.register(KillShellTool())
```

### Step 2: Implement ShellManager

```python
# src/opencode/tools/execution/shell_manager.py
"""Shell process management for background command execution."""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ShellStatus(str, Enum):
    """Status of a shell process."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED = "killed"
    TIMEOUT = "timeout"


@dataclass
class ShellProcess:
    """
    Represents a background shell process.

    Tracks process state, output buffers, and provides
    methods for reading output and controlling the process.
    """
    id: str
    command: str
    working_dir: str
    process: Optional[asyncio.subprocess.Process] = None
    status: ShellStatus = ShellStatus.PENDING
    exit_code: Optional[int] = None
    stdout_buffer: str = ""
    stderr_buffer: str = ""
    last_read_stdout: int = 0
    last_read_stderr: int = 0
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    def get_new_output(self, include_stderr: bool = True) -> str:
        """
        Get output since last read.

        Args:
            include_stderr: Whether to include stderr in output

        Returns:
            New output since last read
        """
        stdout = self.stdout_buffer[self.last_read_stdout:]
        self.last_read_stdout = len(self.stdout_buffer)

        if include_stderr:
            stderr = self.stderr_buffer[self.last_read_stderr:]
            self.last_read_stderr = len(self.stderr_buffer)
            if stderr:
                stdout += f"\n[stderr]\n{stderr}"

        return stdout

    def get_all_output(self) -> str:
        """Get all output from the process."""
        output = self.stdout_buffer
        if self.stderr_buffer:
            output += f"\n[stderr]\n{self.stderr_buffer}"
        return output

    async def read_output(self) -> bool:
        """
        Read available output from process streams.

        Returns:
            True if any data was read
        """
        if self.process is None:
            return False

        read_any = False

        # Read stdout
        if self.process.stdout:
            try:
                data = await asyncio.wait_for(
                    self.process.stdout.read(4096),
                    timeout=0.05
                )
                if data:
                    self.stdout_buffer += data.decode('utf-8', errors='replace')
                    read_any = True
            except asyncio.TimeoutError:
                pass
            except Exception:
                pass

        # Read stderr
        if self.process.stderr:
            try:
                data = await asyncio.wait_for(
                    self.process.stderr.read(4096),
                    timeout=0.05
                )
                if data:
                    self.stderr_buffer += data.decode('utf-8', errors='replace')
                    read_any = True
            except asyncio.TimeoutError:
                pass
            except Exception:
                pass

        return read_any

    async def wait(self, timeout: Optional[float] = None) -> int:
        """
        Wait for process to complete.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            Exit code

        Raises:
            asyncio.TimeoutError: If timeout exceeded
        """
        if self.process is None:
            raise RuntimeError("Process not started")

        try:
            exit_code = await asyncio.wait_for(
                self.process.wait(),
                timeout=timeout
            )
            self.exit_code = exit_code
            self.completed_at = time.time()
            self.status = ShellStatus.COMPLETED if exit_code == 0 else ShellStatus.FAILED
            return exit_code
        except asyncio.TimeoutError:
            self.status = ShellStatus.TIMEOUT
            raise

    def kill(self) -> None:
        """Kill the process."""
        if self.process and self.process.returncode is None:
            self.process.kill()
        self.status = ShellStatus.KILLED
        self.completed_at = time.time()

    def terminate(self) -> None:
        """Send SIGTERM to the process."""
        if self.process and self.process.returncode is None:
            self.process.terminate()

    @property
    def is_running(self) -> bool:
        """Check if process is still running."""
        if self.process is None:
            return False
        return self.process.returncode is None

    @property
    def duration_ms(self) -> Optional[float]:
        """Get duration in milliseconds."""
        if self.started_at is None:
            return None
        end = self.completed_at or time.time()
        return (end - self.started_at) * 1000


class ShellManager:
    """
    Manages background shell processes.

    Singleton pattern ensures global access to shell state.
    Provides methods for creating, tracking, and cleaning up shells.
    """
    _instance: Optional["ShellManager"] = None
    _shells: Dict[str, ShellProcess]
    _lock: Optional[asyncio.Lock]  # Created lazily in async context

    def __new__(cls) -> "ShellManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._shells = {}
            cls._instance._lock = None  # Lazy init - asyncio.Lock() requires running loop
        return cls._instance

    def _get_lock(self) -> asyncio.Lock:
        """Get or create the async lock (lazy initialization).

        asyncio.Lock() cannot be created outside of an async context,
        so we defer creation until first use within an async context.
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    @classmethod
    def reset(cls) -> None:
        """Reset singleton for testing."""
        if cls._instance:
            # Kill all running shells
            for shell in cls._instance._shells.values():
                if shell.is_running:
                    shell.kill()
            cls._instance._shells.clear()
        cls._instance = None

    @classmethod
    async def create_shell(
        cls,
        command: str,
        working_dir: str,
        env: Optional[Dict[str, str]] = None,
    ) -> ShellProcess:
        """
        Create and start a new background shell.

        Args:
            command: Command to execute
            working_dir: Working directory for command
            env: Optional environment variables

        Returns:
            ShellProcess instance
        """
        manager = cls()
        shell_id = f"shell_{uuid.uuid4().hex[:8]}"

        shell = ShellProcess(
            id=shell_id,
            command=command,
            working_dir=working_dir,
        )

        # Prepare environment
        shell_env = os.environ.copy()
        if env:
            shell_env.update(env)

        # Start process
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir,
            env=shell_env,
        )

        shell.process = process
        shell.status = ShellStatus.RUNNING
        shell.started_at = time.time()

        async with manager._get_lock():
            manager._shells[shell_id] = shell

        return shell

    @classmethod
    def get_shell(cls, shell_id: str) -> Optional[ShellProcess]:
        """Get shell by ID."""
        manager = cls()
        return manager._shells.get(shell_id)

    @classmethod
    def list_shells(cls) -> List[ShellProcess]:
        """List all shells."""
        manager = cls()
        return list(manager._shells.values())

    @classmethod
    def list_running(cls) -> List[ShellProcess]:
        """List running shells."""
        manager = cls()
        return [s for s in manager._shells.values() if s.is_running]

    @classmethod
    async def cleanup_completed(cls, max_age_seconds: float = 3600) -> int:
        """
        Remove completed shells older than max_age.

        Args:
            max_age_seconds: Maximum age for completed shells

        Returns:
            Number of shells removed
        """
        manager = cls()
        now = time.time()
        to_remove = []

        async with manager._get_lock():
            for shell_id, shell in manager._shells.items():
                if not shell.is_running:
                    if shell.completed_at and (now - shell.completed_at) > max_age_seconds:
                        to_remove.append(shell_id)

            for shell_id in to_remove:
                del manager._shells[shell_id]

        return len(to_remove)

    @classmethod
    async def kill_all(cls) -> int:
        """Kill all running shells. Returns count killed."""
        manager = cls()
        count = 0

        async with manager._get_lock():
            for shell in manager._shells.values():
                if shell.is_running:
                    shell.kill()
                    count += 1

        return count
```

### Step 3: Implement BashTool

```python
# src/opencode/tools/execution/bash.py
"""Bash command execution tool."""

from __future__ import annotations

import asyncio
import re
from typing import Any, List

from opencode.tools.base import (
    BaseTool,
    ToolParameter,
    ToolResult,
    ExecutionContext,
    ToolCategory,
)
from opencode.tools.execution.shell_manager import ShellManager, ShellStatus


class BashTool(BaseTool):
    """
    Execute bash commands in a persistent shell session.

    Supports foreground execution with timeout and
    background execution for long-running commands.
    """

    DEFAULT_TIMEOUT_MS = 120000  # 2 minutes
    MAX_TIMEOUT_MS = 600000  # 10 minutes
    MAX_OUTPUT_SIZE = 30000  # characters

    # Patterns for dangerous commands
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf\s+/\s*$",           # rm -rf /
        r"rm\s+-rf\s+/\*",              # rm -rf /*
        r"mkfs\.",                       # Format filesystem
        r"dd\s+if=.+of=/dev/sd",        # Direct disk write
        r">\s*/dev/sd",                  # Write to disk device
        r"chmod\s+-R\s+777\s+/\s*$",    # Recursive 777 on root
        r":()\{\s*:\|:&\s*\};:",        # Fork bomb
        r"mv\s+/\s+",                    # Move root
        r"chown\s+-R\s+.+\s+/\s*$",     # Chown root
    ]

    @property
    def name(self) -> str:
        return "Bash"

    @property
    def description(self) -> str:
        return """Executes a bash command in a persistent shell session with optional timeout.

IMPORTANT: This tool is for terminal operations like git, npm, docker, etc.
DO NOT use it for file operations (reading, writing, editing, searching) - use specialized tools instead.

Usage notes:
- The command argument is required
- Timeout defaults to 120000ms (2 min), max 600000ms (10 min)
- Output exceeding 30000 characters will be truncated
- Use run_in_background=true for long-running commands
- Always quote file paths containing spaces with double quotes
- Use && to chain dependent commands
- Use ; when you don't care if earlier commands fail
- Avoid cd - use absolute paths instead"""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.EXECUTION

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="command",
                type="string",
                description="The command to execute",
                required=True,
                min_length=1,
            ),
            ToolParameter(
                name="description",
                type="string",
                description="Clear, concise description of what this command does (5-10 words)",
                required=False,
            ),
            ToolParameter(
                name="timeout",
                type="integer",
                description="Optional timeout in milliseconds (max 600000)",
                required=False,
                minimum=1000,
                maximum=600000,
            ),
            ToolParameter(
                name="run_in_background",
                type="boolean",
                description="Run command in background. Use BashOutput to read output later.",
                required=False,
                default=False,
            ),
        ]

    async def _execute(
        self, context: ExecutionContext, **kwargs: Any
    ) -> ToolResult:
        command = kwargs["command"]
        description = kwargs.get("description", "")
        timeout_ms = kwargs.get("timeout", self.DEFAULT_TIMEOUT_MS)
        run_in_background = kwargs.get("run_in_background", False)

        # Validate timeout
        if timeout_ms > self.MAX_TIMEOUT_MS:
            return ToolResult.fail(
                f"Timeout exceeds maximum: {self.MAX_TIMEOUT_MS}ms"
            )

        # Security check
        security_error = self._check_dangerous_command(command)
        if security_error:
            return ToolResult.fail(security_error)

        # Dry run mode
        if context.dry_run:
            return ToolResult.ok(
                f"[Dry Run] Would execute: {command}",
                command=command,
                description=description,
                dry_run=True,
            )

        # Execute
        if run_in_background:
            return await self._run_background(command, context.working_dir)
        else:
            return await self._run_foreground(
                command, context.working_dir, timeout_ms
            )

    async def _run_foreground(
        self, command: str, working_dir: str, timeout_ms: int
    ) -> ToolResult:
        """Run command in foreground with timeout.

        Args:
            command: Shell command to execute.
            working_dir: Working directory for execution.
            timeout_ms: Timeout in milliseconds (from LLM parameter).
                        Converted to seconds for asyncio.wait_for().
        """
        timeout_sec = timeout_ms / 1000  # Convert ms -> seconds for asyncio

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_sec
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult.fail(
                    f"Command timed out after {timeout_ms}ms",
                    command=command,
                    timeout_ms=timeout_ms,
                )

            # Decode output
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')

            # Combine output
            output = stdout_str
            if stderr_str:
                output += f"\n[stderr]\n{stderr_str}"

            # Truncate if needed
            truncated = False
            if len(output) > self.MAX_OUTPUT_SIZE:
                output = output[:self.MAX_OUTPUT_SIZE]
                output += f"\n\n[Output truncated at {self.MAX_OUTPUT_SIZE} characters]"
                truncated = True

            # Determine success
            exit_code = process.returncode
            if exit_code == 0:
                return ToolResult.ok(
                    output,
                    command=command,
                    exit_code=exit_code,
                    truncated=truncated,
                )
            else:
                return ToolResult.fail(
                    f"Command failed with exit code {exit_code}\n{output}",
                    command=command,
                    exit_code=exit_code,
                    truncated=truncated,
                )

        except Exception as e:
            return ToolResult.fail(
                f"Failed to execute command: {str(e)}",
                command=command,
            )

    async def _run_background(
        self, command: str, working_dir: str
    ) -> ToolResult:
        """Run command in background."""
        try:
            shell = await ShellManager.create_shell(command, working_dir)

            return ToolResult.ok(
                f"Started background shell: {shell.id}\n"
                f"Command: {command}\n"
                f"Use BashOutput tool with bash_id='{shell.id}' to read output.",
                bash_id=shell.id,
                command=command,
            )
        except Exception as e:
            return ToolResult.fail(
                f"Failed to start background shell: {str(e)}",
                command=command,
            )

    def _check_dangerous_command(self, command: str) -> str | None:
        """
        Check if command matches dangerous patterns.

        Returns error message if dangerous, None if safe.
        """
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return f"Command blocked for security: matches dangerous pattern"
        return None
```

### Step 4: Implement BashOutputTool

```python
# src/opencode/tools/execution/bash_output.py
"""Tool for retrieving output from background shells."""

from __future__ import annotations

import re
from typing import Any, List

from opencode.tools.base import (
    BaseTool,
    ToolParameter,
    ToolResult,
    ExecutionContext,
    ToolCategory,
)
from opencode.tools.execution.shell_manager import ShellManager


class BashOutputTool(BaseTool):
    """
    Retrieve output from a running or completed background shell.

    Returns only new output since the last check.
    """

    @property
    def name(self) -> str:
        return "BashOutput"

    @property
    def description(self) -> str:
        return """Retrieves output from a running or completed background bash shell.

Usage:
- Takes a bash_id parameter identifying the shell
- Returns only new output since the last check
- Returns stdout and stderr output along with shell status
- Supports optional regex filtering to show only matching lines
- Shell IDs can be found from BashTool output or /tasks command"""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.EXECUTION

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="bash_id",
                type="string",
                description="The ID of the background shell to retrieve output from",
                required=True,
            ),
            ToolParameter(
                name="filter",
                type="string",
                description="Optional regex to filter output lines. "
                "Non-matching lines will be discarded.",
                required=False,
            ),
        ]

    async def _execute(
        self, context: ExecutionContext, **kwargs: Any
    ) -> ToolResult:
        bash_id = kwargs["bash_id"]
        filter_pattern = kwargs.get("filter")

        # Get shell
        shell = ShellManager.get_shell(bash_id)
        if shell is None:
            return ToolResult.fail(
                f"Shell not found: {bash_id}. "
                "The shell may have been cleaned up or the ID is incorrect."
            )

        # Read any pending output
        if shell.is_running:
            await shell.read_output()

        # Get new output
        output = shell.get_new_output()

        # Apply filter if provided
        if filter_pattern and output:
            try:
                regex = re.compile(filter_pattern)
                lines = output.splitlines()
                filtered_lines = [line for line in lines if regex.search(line)]
                output = "\n".join(filtered_lines)
            except re.error as e:
                return ToolResult.fail(f"Invalid filter regex: {str(e)}")

        # Build status message
        status_msg = f"Status: {shell.status.value}"
        if shell.exit_code is not None:
            status_msg += f", Exit code: {shell.exit_code}"
        if shell.duration_ms:
            status_msg += f", Duration: {shell.duration_ms:.0f}ms"

        return ToolResult.ok(
            f"{status_msg}\n\n{output}" if output else status_msg,
            bash_id=bash_id,
            status=shell.status.value,
            exit_code=shell.exit_code,
            is_running=shell.is_running,
        )
```

### Step 5: Implement KillShellTool

```python
# src/opencode/tools/execution/kill_shell.py
"""Tool for killing background shells."""

from __future__ import annotations

from typing import Any, List

from opencode.tools.base import (
    BaseTool,
    ToolParameter,
    ToolResult,
    ExecutionContext,
    ToolCategory,
)
from opencode.tools.execution.shell_manager import ShellManager


class KillShellTool(BaseTool):
    """
    Kill a running background bash shell by its ID.
    """

    @property
    def name(self) -> str:
        return "KillShell"

    @property
    def description(self) -> str:
        return """Kills a running background bash shell by its ID.

Usage:
- Takes a shell_id parameter identifying the shell to kill
- Returns success or failure status
- Use this to terminate long-running commands
- Shell IDs can be found from BashTool output or /tasks command"""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.EXECUTION

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="shell_id",
                type="string",
                description="The ID of the background shell to kill",
                required=True,
            ),
        ]

    async def _execute(
        self, context: ExecutionContext, **kwargs: Any
    ) -> ToolResult:
        shell_id = kwargs["shell_id"]

        # Get shell
        shell = ShellManager.get_shell(shell_id)
        if shell is None:
            return ToolResult.fail(
                f"Shell not found: {shell_id}. "
                "The shell may have already completed or been killed."
            )

        # Check if already stopped
        if not shell.is_running:
            return ToolResult.ok(
                f"Shell {shell_id} already stopped (status: {shell.status.value})",
                shell_id=shell_id,
                status=shell.status.value,
                already_stopped=True,
            )

        # Kill the shell
        try:
            shell.kill()

            return ToolResult.ok(
                f"Shell {shell_id} terminated",
                shell_id=shell_id,
                command=shell.command,
                duration_ms=shell.duration_ms,
            )
        except Exception as e:
            return ToolResult.fail(
                f"Failed to kill shell {shell_id}: {str(e)}"
            )
```

### Step 6: Update Package Exports

```python
# src/opencode/tools/__init__.py (updated)
"""OpenCode tool system."""

from opencode.tools.base import (
    BaseTool,
    ToolParameter,
    ToolResult,
    ExecutionContext,
    ToolCategory,
    ToolExecution,
)
from opencode.tools.registry import ToolRegistry
from opencode.tools.executor import ToolExecutor

# File tools
from opencode.tools.file import (
    ReadTool,
    WriteTool,
    EditTool,
    GlobTool,
    GrepTool,
    register_file_tools,
)

# Execution tools
from opencode.tools.execution import (
    BashTool,
    BashOutputTool,
    KillShellTool,
    ShellManager,
    ShellProcess,
    ShellStatus,
    register_execution_tools,
)

__all__ = [
    # Base classes
    "BaseTool",
    "ToolParameter",
    "ToolResult",
    "ExecutionContext",
    "ToolCategory",
    "ToolExecution",
    # Registry and executor
    "ToolRegistry",
    "ToolExecutor",
    # File tools
    "ReadTool",
    "WriteTool",
    "EditTool",
    "GlobTool",
    "GrepTool",
    "register_file_tools",
    # Execution tools
    "BashTool",
    "BashOutputTool",
    "KillShellTool",
    "ShellManager",
    "ShellProcess",
    "ShellStatus",
    "register_execution_tools",
]


def register_all_tools(registry: ToolRegistry) -> None:
    """Register all built-in tools with the registry."""
    register_file_tools(registry)
    register_execution_tools(registry)
```

---

## Testing Strategy

### Unit Tests

1. **BashTool Tests**
   - Execute simple command
   - Execute command with timeout
   - Execute command that times out
   - Execute background command
   - Dangerous command blocked
   - Command failure handling
   - Output truncation
   - Dry run mode

2. **BashOutputTool Tests**
   - Get output from running shell
   - Get output from completed shell
   - Shell not found error
   - Output filtering with regex
   - Invalid filter regex error

3. **KillShellTool Tests**
   - Kill running shell
   - Kill already stopped shell
   - Shell not found error

4. **ShellManager Tests**
   - Create shell
   - Get shell by ID
   - List shells
   - Cleanup completed shells
   - Kill all shells
   - Singleton pattern

### Integration Tests

1. Run command, check output
2. Run background command, poll output, verify completion
3. Run background command, kill it, verify killed
4. Multiple concurrent background commands

---

## Security Considerations

1. **Command Injection**: Validate and sanitize commands
2. **Dangerous Commands**: Block destructive patterns
3. **Resource Limits**: Timeout and output size limits
4. **Working Directory**: Restrict to allowed paths
5. **Environment Variables**: Sanitize sensitive vars
6. **Process Cleanup**: Ensure zombies are reaped
