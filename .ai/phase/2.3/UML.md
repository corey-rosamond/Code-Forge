# Phase 2.3: Execution Tools - UML Diagrams

**Phase:** 2.3
**Name:** Execution Tools
**Dependencies:** Phase 2.1 (Tool System Foundation)

---

## 1. Class Diagram - Execution Tools Overview

```mermaid
classDiagram
    class BaseTool {
        <<abstract>>
        +name: str*
        +description: str*
        +category: ToolCategory*
        +parameters: List~ToolParameter~*
        +execute(context, **kwargs) ToolResult
        #_execute(context, **kwargs)* ToolResult
    }

    class BashTool {
        +name = "Bash"
        +category = EXECUTION
        +DEFAULT_TIMEOUT_MS = 120000
        +MAX_TIMEOUT_MS = 600000
        +MAX_OUTPUT_SIZE = 30000
        +DANGEROUS_PATTERNS: List~str~
        #_execute(context, **kwargs) ToolResult
        -_run_foreground(cmd, dir, timeout) ToolResult
        -_run_background(cmd, dir) ToolResult
        -_check_dangerous_command(cmd) str?
    }

    class BashOutputTool {
        +name = "BashOutput"
        +category = EXECUTION
        #_execute(context, **kwargs) ToolResult
    }

    class KillShellTool {
        +name = "KillShell"
        +category = EXECUTION
        #_execute(context, **kwargs) ToolResult
    }

    class ShellManager {
        <<singleton>>
        -_instance: ShellManager
        -_shells: Dict~str,ShellProcess~
        -_lock: asyncio.Lock
        +create_shell(cmd, dir, env)$ ShellProcess
        +get_shell(id)$ ShellProcess?
        +list_shells()$ List~ShellProcess~
        +list_running()$ List~ShellProcess~
        +cleanup_completed(max_age)$ int
        +kill_all()$ int
        +reset()$ void
    }

    class ShellProcess {
        +id: str
        +command: str
        +working_dir: str
        +process: Process?
        +status: ShellStatus
        +exit_code: int?
        +stdout_buffer: str
        +stderr_buffer: str
        +created_at: float
        +started_at: float?
        +completed_at: float?
        +get_new_output() str
        +get_all_output() str
        +read_output() bool
        +wait(timeout) int
        +kill() void
        +terminate() void
        +is_running: bool
        +duration_ms: float?
    }

    class ShellStatus {
        <<enumeration>>
        PENDING
        RUNNING
        COMPLETED
        FAILED
        KILLED
        TIMEOUT
    }

    BaseTool <|-- BashTool
    BaseTool <|-- BashOutputTool
    BaseTool <|-- KillShellTool
    BashTool --> ShellManager : uses
    BashOutputTool --> ShellManager : uses
    KillShellTool --> ShellManager : uses
    ShellManager --> ShellProcess : manages
    ShellProcess --> ShellStatus : has
```

---

## 2. Class Diagram - BashTool Details

```mermaid
classDiagram
    class BashTool {
        +name: str
        +description: str
        +category: ToolCategory
        +parameters: List~ToolParameter~
        +DEFAULT_TIMEOUT_MS: int = 120000
        +MAX_TIMEOUT_MS: int = 600000
        +MAX_OUTPUT_SIZE: int = 30000
        +DANGEROUS_PATTERNS: List~str~
        #_execute(context, **kwargs) ToolResult
        -_run_foreground(cmd, dir, timeout) ToolResult
        -_run_background(cmd, dir) ToolResult
        -_check_dangerous_command(cmd) str?
    }

    class BashParams {
        <<parameters>>
        +command: string [required]
        +description: string [optional]
        +timeout: integer [optional, 1000-600000]
        +run_in_background: boolean [optional, default=false]
    }

    class ForegroundResult {
        <<result>>
        +output: stdout + stderr
        +exit_code: int
        +truncated: bool
        +command: str
    }

    class BackgroundResult {
        <<result>>
        +bash_id: str
        +command: str
        +message: str
    }

    BashTool --> BashParams : validates
    BashTool --> ForegroundResult : returns (foreground)
    BashTool --> BackgroundResult : returns (background)
```

---

## 3. Class Diagram - ShellProcess Details

```mermaid
classDiagram
    class ShellProcess {
        +id: str
        +command: str
        +working_dir: str
        +process: asyncio.Process?
        +status: ShellStatus
        +exit_code: int?
        +stdout_buffer: str
        +stderr_buffer: str
        +last_read_stdout: int
        +last_read_stderr: int
        +created_at: float
        +started_at: float?
        +completed_at: float?
    }

    class ShellProcessMethods {
        <<methods>>
        +get_new_output(include_stderr) str
        +get_all_output() str
        +read_output() bool
        +wait(timeout) int
        +kill() void
        +terminate() void
    }

    class ShellProcessProperties {
        <<properties>>
        +is_running: bool
        +duration_ms: float?
    }

    ShellProcess --> ShellProcessMethods
    ShellProcess --> ShellProcessProperties
```

---

## 4. Sequence Diagram - Foreground Command Execution

```mermaid
sequenceDiagram
    participant Agent
    participant Executor as ToolExecutor
    participant Bash as BashTool
    participant Subprocess as asyncio.subprocess

    Agent->>Executor: execute("Bash", ctx, command="ls -la")
    Executor->>Bash: execute(ctx, command="ls -la")

    Bash->>Bash: validate_params()
    Bash->>Bash: _check_dangerous_command()

    alt Dangerous command
        Bash-->>Executor: ToolResult.fail("blocked")
    else Safe command
        Bash->>Subprocess: create_subprocess_shell(cmd)
        Subprocess-->>Bash: process

        Bash->>Subprocess: communicate() with timeout

        alt Timeout exceeded
            Bash->>Subprocess: kill()
            Bash-->>Executor: ToolResult.fail("timed out")
        else Command completed
            Subprocess-->>Bash: stdout, stderr

            Bash->>Bash: Combine and truncate output

            alt Exit code 0
                Bash-->>Executor: ToolResult.ok(output)
            else Exit code != 0
                Bash-->>Executor: ToolResult.fail(output)
            end
        end
    end

    Executor-->>Agent: ToolResult
```

---

## 5. Sequence Diagram - Background Command Execution

```mermaid
sequenceDiagram
    participant Agent
    participant Bash as BashTool
    participant Manager as ShellManager
    participant Shell as ShellProcess

    Agent->>Bash: execute(ctx, command="npm run build", run_in_background=true)

    Bash->>Bash: validate_params()
    Bash->>Bash: _check_dangerous_command()

    Bash->>Manager: create_shell(cmd, working_dir)

    Manager->>Manager: Generate shell_id
    Manager->>Shell: Create ShellProcess

    Manager->>Shell: Start asyncio subprocess
    Shell-->>Manager: Process started

    Manager->>Manager: Store shell in _shells dict
    Manager-->>Bash: ShellProcess

    Bash-->>Agent: ToolResult.ok(bash_id="shell_abc123")

    Note over Agent: Later, check output...

    Agent->>BashOutputTool: execute(ctx, bash_id="shell_abc123")
    BashOutputTool->>Manager: get_shell("shell_abc123")
    Manager-->>BashOutputTool: ShellProcess

    BashOutputTool->>Shell: read_output()
    BashOutputTool->>Shell: get_new_output()
    Shell-->>BashOutputTool: new output

    BashOutputTool-->>Agent: ToolResult.ok(output)
```

---

## 6. Sequence Diagram - Kill Shell

```mermaid
sequenceDiagram
    participant Agent
    participant KillTool as KillShellTool
    participant Manager as ShellManager
    participant Shell as ShellProcess

    Agent->>KillTool: execute(ctx, shell_id="shell_abc123")

    KillTool->>Manager: get_shell("shell_abc123")

    alt Shell not found
        Manager-->>KillTool: None
        KillTool-->>Agent: ToolResult.fail("not found")
    else Shell found
        Manager-->>KillTool: ShellProcess

        KillTool->>Shell: is_running?

        alt Already stopped
            Shell-->>KillTool: False
            KillTool-->>Agent: ToolResult.ok("already stopped")
        else Running
            Shell-->>KillTool: True
            KillTool->>Shell: kill()
            Shell->>Shell: process.kill()
            Shell->>Shell: status = KILLED
            KillTool-->>Agent: ToolResult.ok("terminated")
        end
    end
```

---

## 7. State Diagram - Shell Process Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Pending: ShellProcess created

    Pending --> Running: subprocess started

    Running --> Completed: exit_code == 0
    Running --> Failed: exit_code != 0
    Running --> Timeout: wait timeout exceeded
    Running --> Killed: kill() called

    Completed --> [*]: cleanup
    Failed --> [*]: cleanup
    Timeout --> [*]: cleanup
    Killed --> [*]: cleanup

    note right of Running
        Output buffers being filled
        read_output() pulls data
    end note

    note right of Completed
        Final output available
        duration_ms calculated
    end note
```

---

## 8. State Diagram - Bash Execution Flow

```mermaid
stateDiagram-v2
    [*] --> ValidatingParams: execute() called

    ValidatingParams --> CheckingSecurity: params valid
    ValidatingParams --> Error: params invalid

    CheckingSecurity --> DryRun: dry_run=true
    CheckingSecurity --> Blocked: dangerous command
    CheckingSecurity --> SelectMode: command safe

    DryRun --> [*]: Return preview

    Blocked --> [*]: Return error

    SelectMode --> Foreground: run_in_background=false
    SelectMode --> Background: run_in_background=true

    Foreground --> StartProcess: create subprocess
    StartProcess --> WaitingOutput: communicate()

    WaitingOutput --> TimedOut: timeout exceeded
    WaitingOutput --> ProcessOutput: completed

    TimedOut --> KillProcess: kill()
    KillProcess --> [*]: Return timeout error

    ProcessOutput --> TruncateOutput: output > MAX_SIZE
    ProcessOutput --> CheckExitCode: output ok

    TruncateOutput --> CheckExitCode: truncated

    CheckExitCode --> Success: exit_code == 0
    CheckExitCode --> Failure: exit_code != 0

    Success --> [*]: Return success
    Failure --> [*]: Return failure

    Background --> CreateShell: ShellManager.create_shell()
    CreateShell --> [*]: Return bash_id
```

---

## 9. Component Diagram - Execution Tools

```mermaid
flowchart TB
    subgraph ExecutionTools["Execution Tools Package"]
        BASH[BashTool]
        BASHOUT[BashOutputTool]
        KILL[KillShellTool]
        MANAGER[ShellManager]
        PROCESS[ShellProcess]
    end

    subgraph Core["Core (Phase 2.1)"]
        BASE[BaseTool]
        PARAM[ToolParameter]
        RESULT[ToolResult]
        CTX[ExecutionContext]
        REG[ToolRegistry]
    end

    subgraph External["External/System"]
        ASYNCIO[asyncio.subprocess]
        OS[os module]
        RE[re module]
    end

    BASH --> BASE
    BASHOUT --> BASE
    KILL --> BASE

    BASE --> PARAM
    BASE --> RESULT
    BASE --> CTX

    BASH --> MANAGER
    BASHOUT --> MANAGER
    KILL --> MANAGER

    MANAGER --> PROCESS
    MANAGER --> ASYNCIO
    PROCESS --> ASYNCIO

    BASH --> RE
    BASHOUT --> RE

    REG --> BASH
    REG --> BASHOUT
    REG --> KILL
```

---

## 10. Activity Diagram - Background Shell Monitoring

```mermaid
flowchart TD
    START([Start Background Command]) --> CREATE[Create ShellProcess]
    CREATE --> STORE[Store in ShellManager]
    STORE --> RETURN_ID[Return bash_id to agent]

    RETURN_ID --> WAIT{Agent needs output?}

    WAIT -->|No| WAIT
    WAIT -->|Yes| CHECK[BashOutputTool: get_shell]

    CHECK --> FOUND{Shell found?}
    FOUND -->|No| ERROR[Return error]
    FOUND -->|Yes| READ[read_output from buffers]

    READ --> GET_NEW[get_new_output]
    GET_NEW --> FILTER{Filter specified?}

    FILTER -->|Yes| APPLY[Apply regex filter]
    FILTER -->|No| RETURN

    APPLY --> RETURN[Return output + status]

    RETURN --> RUNNING{Still running?}
    RUNNING -->|Yes| WAIT
    RUNNING -->|No| COMPLETE([Shell complete])

    ERROR --> END([End])
    COMPLETE --> END
```

---

## 11. Package Structure Diagram

```mermaid
flowchart TD
    subgraph opencode_tools["src/opencode/tools/"]
        INIT["__init__.py"]
        BASE["base.py"]
        REG["registry.py"]
        EXEC["executor.py"]

        subgraph file_pkg["file/"]
            FILE_TOOLS[Read, Write, Edit, Glob, Grep]
        end

        subgraph exec_pkg["execution/"]
            EXEC_INIT["__init__.py"]
            BASH_PY["bash.py"]
            BASHOUT_PY["bash_output.py"]
            KILL_PY["kill_shell.py"]
            MANAGER_PY["shell_manager.py"]
        end
    end

    subgraph tests_exec["tests/unit/tools/execution/"]
        TEST_BASH["test_bash.py"]
        TEST_BASHOUT["test_bash_output.py"]
        TEST_KILL["test_kill_shell.py"]
        TEST_MANAGER["test_shell_manager.py"]
    end

    INIT --> EXEC_INIT
    EXEC_INIT --> BASH_PY
    EXEC_INIT --> BASHOUT_PY
    EXEC_INIT --> KILL_PY
    EXEC_INIT --> MANAGER_PY

    BASH_PY --> MANAGER_PY
    BASHOUT_PY --> MANAGER_PY
    KILL_PY --> MANAGER_PY

    TEST_BASH --> BASH_PY
    TEST_BASHOUT --> BASHOUT_PY
    TEST_KILL --> KILL_PY
    TEST_MANAGER --> MANAGER_PY
```

---

## 12. Tool Parameter Schemas

### BashTool Parameters
```json
{
  "type": "object",
  "properties": {
    "command": {
      "type": "string",
      "description": "The command to execute",
      "minLength": 1
    },
    "description": {
      "type": "string",
      "description": "Clear, concise description (5-10 words)"
    },
    "timeout": {
      "type": "integer",
      "description": "Timeout in milliseconds",
      "minimum": 1000,
      "maximum": 600000
    },
    "run_in_background": {
      "type": "boolean",
      "description": "Run in background",
      "default": false
    }
  },
  "required": ["command"]
}
```

### BashOutputTool Parameters
```json
{
  "type": "object",
  "properties": {
    "bash_id": {
      "type": "string",
      "description": "ID of the background shell"
    },
    "filter": {
      "type": "string",
      "description": "Regex to filter output lines"
    }
  },
  "required": ["bash_id"]
}
```

### KillShellTool Parameters
```json
{
  "type": "object",
  "properties": {
    "shell_id": {
      "type": "string",
      "description": "ID of the shell to kill"
    }
  },
  "required": ["shell_id"]
}
```

---

## 13. Dangerous Command Patterns

```
┌─────────────────────────────────────────────────────────────────────┐
│ Blocked Command Patterns                                            │
├─────────────────────────────────────────────────────────────────────┤
│ Pattern              │ Description                                  │
├─────────────────────────────────────────────────────────────────────┤
│ rm -rf /             │ Delete entire filesystem                     │
│ rm -rf /*            │ Delete root contents                         │
│ mkfs.*               │ Format filesystem                            │
│ dd if=* of=/dev/sd*  │ Direct disk write                           │
│ > /dev/sd*           │ Redirect to disk device                      │
│ chmod -R 777 /       │ Open permissions on root                     │
│ :(){:|:&};:          │ Fork bomb                                    │
│ mv / *               │ Move root directory                          │
│ chown -R * /         │ Change ownership of root                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Notes

- BashTool supports both foreground and background execution
- ShellManager is a singleton for global shell tracking
- Background shells can be monitored with BashOutputTool
- Output is incrementally read to avoid memory issues
- Dangerous command patterns are blocked at execution time
- Timeouts prevent runaway processes
- Shell cleanup happens automatically for old completed shells
