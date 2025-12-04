# Phase 2.3: Execution Tools - Requirements

**Phase:** 2.3
**Name:** Execution Tools
**Status:** Not Started
**Dependencies:** Phase 2.1 (Tool System Foundation)

---

## Overview

This phase implements the command execution tools that allow the AI assistant to run shell commands, manage background processes, and interact with the system. These tools provide capabilities for executing commands, monitoring background tasks, and managing long-running processes.

---

## Functional Requirements

### FR-2.3.1: Bash Tool
- Execute shell commands in a persistent shell session
- Support command timeout (configurable, default 120s, max 600s)
- Capture stdout and stderr
- Return exit code in metadata
- Support background execution mode
- Handle command interruption (Ctrl+C equivalent)
- Quote file paths with spaces automatically
- Support working directory context
- Truncate large outputs (>30000 chars)
- Support command chaining (&&, ||, ;)
- Provide clear descriptions for commands

### FR-2.3.2: BashOutput Tool
- Retrieve output from background shell processes
- Support filtering output with regex patterns
- Return only new output since last check
- Return shell status (running, completed, failed)
- Support stdout and stderr separation
- Handle shell not found errors

### FR-2.3.3: KillShell Tool
- Terminate running background shell processes
- Return success/failure status
- Clean up resources properly
- Handle already-terminated shells gracefully

### FR-2.3.4: Shell Session Management
- Maintain persistent shell sessions
- Track background processes by ID
- Clean up completed shells
- Support multiple concurrent shells
- Provide shell listing capability

---

## Non-Functional Requirements

### NFR-2.3.1: Performance
- Command startup latency < 50ms
- Output streaming for long-running commands
- Efficient memory usage for large outputs
- Background process polling < 100ms

### NFR-2.3.2: Security
- Command injection prevention
- No access to dangerous commands by default
- Working directory restrictions
- Environment variable sanitization
- Timeout enforcement to prevent hanging

### NFR-2.3.3: Reliability
- Handle zombie processes
- Recover from shell crashes
- Clean up orphaned processes
- Proper signal handling

---

## Technical Specifications

### Bash Tool

```python
class BashTool(BaseTool):
    """
    Execute bash commands in a persistent shell session.

    Provides command execution with timeout, background execution,
    and output capture capabilities.
    """

    DEFAULT_TIMEOUT = 120000  # 2 minutes in ms
    MAX_TIMEOUT = 600000  # 10 minutes in ms
    MAX_OUTPUT_SIZE = 30000  # characters

    @property
    def name(self) -> str:
        return "Bash"

    @property
    def description(self) -> str:
        return """Executes a given bash command in a persistent shell session.

IMPORTANT: This tool is for terminal operations like git, npm, docker, etc.
DO NOT use it for file operations - use the specialized file tools instead.

Usage notes:
- The command argument is required
- Timeout defaults to 120000ms (2 minutes), max 600000ms (10 minutes)
- Output exceeding 30000 characters will be truncated
- Use run_in_background=true for long-running commands
- Quote file paths with spaces using double quotes
- Use && to chain dependent commands
- Use ; when you don't care if earlier commands fail"""

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
                description="Timeout in milliseconds (max 600000)",
                required=False,
                default=120000,
                minimum=1000,
                maximum=600000,
            ),
            ToolParameter(
                name="run_in_background",
                type="boolean",
                description="Run command in background, use BashOutput to read output",
                required=False,
                default=False,
            ),
        ]

    async def _execute(
        self, context: ExecutionContext, **kwargs
    ) -> ToolResult:
        command = kwargs["command"]
        description = kwargs.get("description", "")
        timeout_ms = kwargs.get("timeout", self.DEFAULT_TIMEOUT)
        run_in_background = kwargs.get("run_in_background", False)

        # Security validation
        if self._is_dangerous_command(command):
            return ToolResult.fail(
                f"Command blocked for security reasons: {command}"
            )

        # Dry run mode
        if context.dry_run:
            return ToolResult.ok(
                f"[Dry Run] Would execute: {command}",
                command=command,
                dry_run=True,
            )

        if run_in_background:
            return await self._run_background(command, context)
        else:
            return await self._run_foreground(command, context, timeout_ms)
```

### BashOutput Tool

```python
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
- Takes a shell_id parameter identifying the shell
- Returns only new output since last check
- Returns stdout and stderr along with shell status
- Supports optional regex filtering
- Use this to monitor long-running background commands"""

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
                description="Optional regex to filter output lines",
                required=False,
            ),
        ]

    async def _execute(
        self, context: ExecutionContext, **kwargs
    ) -> ToolResult:
        bash_id = kwargs["bash_id"]
        filter_pattern = kwargs.get("filter")

        shell = ShellManager.get_shell(bash_id)
        if shell is None:
            return ToolResult.fail(f"Shell not found: {bash_id}")

        output = shell.get_new_output()

        # Apply filter if provided
        if filter_pattern:
            try:
                import re
                regex = re.compile(filter_pattern)
                lines = output.splitlines()
                output = "\n".join(line for line in lines if regex.search(line))
            except re.error as e:
                return ToolResult.fail(f"Invalid filter regex: {str(e)}")

        return ToolResult.ok(
            output,
            bash_id=bash_id,
            status=shell.status,
            exit_code=shell.exit_code,
        )
```

### KillShell Tool

```python
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
- Use this to terminate long-running commands"""

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
        self, context: ExecutionContext, **kwargs
    ) -> ToolResult:
        shell_id = kwargs["shell_id"]

        shell = ShellManager.get_shell(shell_id)
        if shell is None:
            return ToolResult.fail(f"Shell not found: {shell_id}")

        try:
            shell.kill()
            return ToolResult.ok(
                f"Shell {shell_id} terminated",
                shell_id=shell_id,
            )
        except Exception as e:
            return ToolResult.fail(f"Failed to kill shell: {str(e)}")
```

### Shell Manager

```python
import asyncio
import subprocess
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum


class ShellStatus(str, Enum):
    """Status of a shell process."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED = "killed"


@dataclass
class ShellProcess:
    """Represents a background shell process."""
    id: str
    command: str
    process: asyncio.subprocess.Process
    status: ShellStatus = ShellStatus.RUNNING
    exit_code: Optional[int] = None
    stdout_buffer: str = ""
    stderr_buffer: str = ""
    last_read_position: int = 0
    created_at: float = field(default_factory=lambda: time.time())

    def get_new_output(self) -> str:
        """Get output since last read."""
        output = self.stdout_buffer[self.last_read_position:]
        self.last_read_position = len(self.stdout_buffer)
        return output

    async def read_output(self) -> None:
        """Read available output from process."""
        if self.process.stdout:
            try:
                data = await asyncio.wait_for(
                    self.process.stdout.read(4096),
                    timeout=0.1
                )
                if data:
                    self.stdout_buffer += data.decode('utf-8', errors='replace')
            except asyncio.TimeoutError:
                pass

    def kill(self) -> None:
        """Kill the process."""
        self.process.kill()
        self.status = ShellStatus.KILLED


class ShellManager:
    """
    Manages background shell processes.

    Singleton pattern for global access.
    """
    _instance: Optional["ShellManager"] = None
    _shells: Dict[str, ShellProcess]

    def __new__(cls) -> "ShellManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._shells = {}
        return cls._instance

    @classmethod
    def create_shell(cls, command: str) -> ShellProcess:
        """Create a new background shell."""
        shell_id = f"shell_{uuid.uuid4().hex[:8]}"
        # ... implementation
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
    def cleanup_completed(cls) -> int:
        """Remove completed shells. Returns count removed."""
        manager = cls()
        to_remove = [
            sid for sid, shell in manager._shells.items()
            if shell.status != ShellStatus.RUNNING
        ]
        for sid in to_remove:
            del manager._shells[sid]
        return len(to_remove)
```

---

## Acceptance Criteria

### Definition of Done

- [ ] BashTool implemented and tested
- [ ] BashOutputTool implemented and tested
- [ ] KillShellTool implemented and tested
- [ ] ShellManager implemented and tested
- [ ] All tools registered in ToolRegistry
- [ ] All tools generate valid schemas
- [ ] Security validations in place
- [ ] Timeout handling works correctly
- [ ] Background execution works correctly
- [ ] Tests achieve ≥90% coverage

---

## Security Considerations

### Dangerous Commands (Blocked or Warned)
```python
DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",          # rm -rf /
    r"mkfs\.",                 # Format filesystem
    r"dd\s+if=.+of=/dev/",    # Direct disk write
    r">\s*/dev/sd",           # Write to disk device
    r"chmod\s+-R\s+777\s+/",  # Recursive 777 on root
    r":(){ :|:& };:",         # Fork bomb
]
```

### Allowed Without Confirmation
Commands that are generally safe:
- git commands
- npm/yarn/pnpm commands
- docker commands (non-destructive)
- ls, pwd, echo, cat
- python/node execution
- make, cmake
- grep, find, awk, sed (read operations)

---

## Out of Scope

The following are NOT part of Phase 2.3:
- Interactive shell support (requiring user input)
- PTY allocation
- SSH/remote execution
- Container orchestration
- Service management (systemd, etc.)

---

## Notes

These tools form the foundation for command execution. They are used for:
- Running build commands (npm build, make)
- Git operations (commit, push, pull)
- Testing (pytest, npm test)
- Package management (pip, npm install)
- General system interaction
