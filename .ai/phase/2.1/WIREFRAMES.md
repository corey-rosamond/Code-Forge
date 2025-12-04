# Phase 2.1: Tool System Foundation - Wireframes

**Phase:** 2.1
**Name:** Tool System Foundation
**Dependencies:** Phase 1.1, Phase 1.2, Phase 1.3

---

## Overview

Phase 2.1 focuses on the internal architecture of the tool system. Unlike UI-focused phases, this phase primarily deals with code structures and data formats. The wireframes below illustrate:

1. Schema output formats (JSON)
2. Tool result display formats
3. Debug/diagnostic output
4. Error message formats

---

## 1. OpenAI Tool Schema Format

The tool system generates schemas for LLM integration. Below is the expected output format:

### Simple Tool Schema
```json
{
  "type": "function",
  "function": {
    "name": "Read",
    "description": "Read contents of a file from the filesystem",
    "parameters": {
      "type": "object",
      "properties": {
        "file_path": {
          "type": "string",
          "description": "Absolute path to the file to read"
        },
        "offset": {
          "type": "integer",
          "description": "Line number to start reading from",
          "minimum": 0
        },
        "limit": {
          "type": "integer",
          "description": "Maximum number of lines to read",
          "minimum": 1,
          "maximum": 10000
        }
      },
      "required": ["file_path"]
    }
  }
}
```

### Tool with Enum Parameter
```json
{
  "type": "function",
  "function": {
    "name": "Bash",
    "description": "Execute a bash command",
    "parameters": {
      "type": "object",
      "properties": {
        "command": {
          "type": "string",
          "description": "The command to execute"
        },
        "timeout": {
          "type": "integer",
          "description": "Timeout in milliseconds",
          "default": 120000,
          "minimum": 1000,
          "maximum": 600000
        },
        "run_in_background": {
          "type": "boolean",
          "description": "Run command in background",
          "default": false
        }
      },
      "required": ["command"]
    }
  }
}
```

---

## 2. Anthropic Tool Schema Format

### Simple Tool Schema
```json
{
  "name": "Read",
  "description": "Read contents of a file from the filesystem",
  "input_schema": {
    "type": "object",
    "properties": {
      "file_path": {
        "type": "string",
        "description": "Absolute path to the file to read"
      },
      "offset": {
        "type": "integer",
        "description": "Line number to start reading from",
        "minimum": 0
      },
      "limit": {
        "type": "integer",
        "description": "Maximum number of lines to read",
        "minimum": 1,
        "maximum": 10000
      }
    },
    "required": ["file_path"]
  }
}
```

---

## 3. Tool Result Display Formats

### Successful Result
```
┌─────────────────────────────────────────────────────────────────────┐
│ Tool: Read                                                          │
│ Status: ✓ Success                                                   │
├─────────────────────────────────────────────────────────────────────┤
│ Output:                                                             │
│ Line 1: Hello, World!                                               │
│ Line 2: This is a test file.                                        │
│ Line 3: It has multiple lines.                                      │
├─────────────────────────────────────────────────────────────────────┤
│ Duration: 12ms                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Failed Result
```
┌─────────────────────────────────────────────────────────────────────┐
│ Tool: Read                                                          │
│ Status: ✗ Failed                                                    │
├─────────────────────────────────────────────────────────────────────┤
│ Error: File not found: /path/to/missing/file.txt                    │
├─────────────────────────────────────────────────────────────────────┤
│ Duration: 3ms                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Dry Run Result
```
┌─────────────────────────────────────────────────────────────────────┐
│ Tool: Write                                                         │
│ Status: ◐ Dry Run                                                   │
├─────────────────────────────────────────────────────────────────────┤
│ [Dry Run] Would write 150 bytes to /path/to/file.txt                │
├─────────────────────────────────────────────────────────────────────┤
│ Duration: 1ms                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Timeout Result
```
┌─────────────────────────────────────────────────────────────────────┐
│ Tool: Bash                                                          │
│ Status: ⏱ Timed Out                                                 │
├─────────────────────────────────────────────────────────────────────┤
│ Error: Tool timed out after 120s                                    │
│ Command: sleep 300                                                  │
├─────────────────────────────────────────────────────────────────────┤
│ Duration: 120000ms                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Tool List Display

### All Tools
```
┌─────────────────────────────────────────────────────────────────────┐
│ Available Tools (12)                                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ FILE (5)                                                            │
│   Read         Read contents of a file                              │
│   Write        Write content to a file                              │
│   Edit         Edit a file with find/replace                        │
│   Glob         Find files matching a pattern                        │
│   Grep         Search file contents                                 │
│                                                                     │
│ EXECUTION (3)                                                       │
│   Bash         Execute a bash command                               │
│   BashOutput   Get output from background shell                     │
│   KillShell    Kill a background shell                              │
│                                                                     │
│ WEB (2)                                                             │
│   WebSearch    Search the web                                       │
│   WebFetch     Fetch a URL                                          │
│                                                                     │
│ TASK (1)                                                            │
│   Task         Launch a subagent                                    │
│                                                                     │
│ NOTEBOOK (1)                                                        │
│   NotebookEdit Edit Jupyter notebook cells                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Tool Details
```
┌─────────────────────────────────────────────────────────────────────┐
│ Tool: Read                                                          │
│ Category: FILE                                                      │
├─────────────────────────────────────────────────────────────────────┤
│ Description:                                                        │
│ Read contents of a file from the filesystem. Supports reading       │
│ partial files with offset and limit parameters.                     │
├─────────────────────────────────────────────────────────────────────┤
│ Parameters:                                                         │
│                                                                     │
│   file_path (string) [required]                                     │
│     Absolute path to the file to read                               │
│                                                                     │
│   offset (integer) [optional, default: 0]                           │
│     Line number to start reading from                               │
│     Constraints: minimum=0                                          │
│                                                                     │
│   limit (integer) [optional, default: 2000]                         │
│     Maximum number of lines to read                                 │
│     Constraints: minimum=1, maximum=10000                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Validation Error Messages

### Missing Required Parameter
```
┌─────────────────────────────────────────────────────────────────────┐
│ Validation Error                                                    │
├─────────────────────────────────────────────────────────────────────┤
│ Tool: Read                                                          │
│ Error: Missing required parameter: file_path                        │
│                                                                     │
│ Required parameters:                                                │
│   • file_path (string) - Absolute path to the file to read          │
└─────────────────────────────────────────────────────────────────────┘
```

### Invalid Type
```
┌─────────────────────────────────────────────────────────────────────┐
│ Validation Error                                                    │
├─────────────────────────────────────────────────────────────────────┤
│ Tool: Read                                                          │
│ Error: Invalid type for offset: expected integer                    │
│                                                                     │
│ Received: "100" (string)                                            │
│ Expected: integer                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Invalid Enum Value
```
┌─────────────────────────────────────────────────────────────────────┐
│ Validation Error                                                    │
├─────────────────────────────────────────────────────────────────────┤
│ Tool: SchemaGenerator                                               │
│ Error: Invalid value for format: must be one of ['openai',          │
│        'anthropic', 'langchain']                                    │
│                                                                     │
│ Received: "unknown"                                                 │
│ Valid options: openai, anthropic, langchain                         │
└─────────────────────────────────────────────────────────────────────┘
```

### Out of Range
```
┌─────────────────────────────────────────────────────────────────────┐
│ Validation Error                                                    │
├─────────────────────────────────────────────────────────────────────┤
│ Tool: Read                                                          │
│ Error: Value for limit exceeds maximum: 10000                       │
│                                                                     │
│ Received: 50000                                                     │
│ Constraints: minimum=1, maximum=10000                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Registry State Display (Debug)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Tool Registry State                                                 │
├─────────────────────────────────────────────────────────────────────┤
│ Instance ID: 0x7f8b4c0d1e90                                         │
│ Total Tools: 12                                                     │
│                                                                     │
│ By Category:                                                        │
│   FILE:       5 tools                                               │
│   EXECUTION:  3 tools                                               │
│   WEB:        2 tools                                               │
│   TASK:       1 tool                                                │
│   NOTEBOOK:   1 tool                                                │
│   MCP:        0 tools                                               │
│   OTHER:      0 tools                                               │
│                                                                     │
│ Registered Tools:                                                   │
│   Bash, BashOutput, Edit, Glob, Grep, KillShell, NotebookEdit,     │
│   Read, Task, WebFetch, WebSearch, Write                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. Execution History Display (Debug)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Tool Execution History                                              │
├─────────────────────────────────────────────────────────────────────┤
│ Total Executions: 5                                                 │
│                                                                     │
│ #1  [2024-01-15 10:23:45]                                          │
│     Tool: Read                                                      │
│     Params: {"file_path": "/home/user/test.py"}                     │
│     Status: Success                                                 │
│     Duration: 12ms                                                  │
│                                                                     │
│ #2  [2024-01-15 10:23:47]                                          │
│     Tool: Bash                                                      │
│     Params: {"command": "python test.py"}                           │
│     Status: Success                                                 │
│     Duration: 1543ms                                                │
│                                                                     │
│ #3  [2024-01-15 10:23:50]                                          │
│     Tool: Write                                                     │
│     Params: {"file_path": "/home/user/output.txt", ...}             │
│     Status: Failed                                                  │
│     Error: Permission denied                                        │
│     Duration: 5ms                                                   │
│                                                                     │
│ #4  [2024-01-15 10:23:52]                                          │
│     Tool: Read                                                      │
│     Params: {"file_path": "/home/user/missing.txt"}                 │
│     Status: Failed                                                  │
│     Error: File not found                                           │
│     Duration: 3ms                                                   │
│                                                                     │
│ #5  [2024-01-15 10:24:00]                                          │
│     Tool: Bash                                                      │
│     Params: {"command": "sleep 300", "timeout": 5000}               │
│     Status: Timed Out                                               │
│     Duration: 5000ms                                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Context Display (Debug)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Execution Context                                                   │
├─────────────────────────────────────────────────────────────────────┤
│ Working Directory: /home/user/my-project                            │
│ Session ID:        sess_abc123def456                                │
│ Agent ID:          agent_main_001                                   │
│ Dry Run:           false                                            │
│ Timeout:           120s                                             │
│ Max Output Size:   100,000 bytes                                    │
│                                                                     │
│ Metadata:                                                           │
│   user_id: user_12345                                               │
│   request_id: req_xyz789                                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 9. Error Display

### Tool Not Found
```
┌─────────────────────────────────────────────────────────────────────┐
│ Error: Tool Not Found                                               │
├─────────────────────────────────────────────────────────────────────┤
│ The tool "UnknownTool" is not registered.                           │
│                                                                     │
│ Did you mean one of these?                                          │
│   • Task                                                            │
│   • Bash                                                            │
│                                                                     │
│ Use /tools to see all available tools.                              │
└─────────────────────────────────────────────────────────────────────┘
```

### Tool Already Registered
```
┌─────────────────────────────────────────────────────────────────────┐
│ Error: Registration Failed                                          │
├─────────────────────────────────────────────────────────────────────┤
│ Cannot register tool "Read": a tool with this name already exists.  │
│                                                                     │
│ To replace an existing tool:                                        │
│   1. Deregister the existing tool first                             │
│   2. Register the new tool                                          │
│                                                                     │
│ Or use a different tool name.                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Execution Error
```
┌─────────────────────────────────────────────────────────────────────┐
│ Error: Tool Execution Failed                                        │
├─────────────────────────────────────────────────────────────────────┤
│ Tool: Bash                                                          │
│ Command: rm -rf /                                                   │
│                                                                     │
│ Error: Operation not permitted                                      │
│                                                                     │
│ The command failed with exit code 1.                                │
│ Check permissions and try again.                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 10. Log Output Format

### Info Level
```
2024-01-15 10:23:45.123 INFO  [tools] Executing tool: Read
2024-01-15 10:23:45.135 INFO  [tools] Tool Read succeeded
```

### Debug Level
```
2024-01-15 10:23:45.123 DEBUG [tools] Executing tool: Read
2024-01-15 10:23:45.123 DEBUG [tools] Parameters: {"file_path": "/home/user/test.py", "limit": 100}
2024-01-15 10:23:45.124 DEBUG [tools] Context: working_dir=/home/user, timeout=120
2024-01-15 10:23:45.135 DEBUG [tools] Result: success=True, output_size=1234, duration_ms=12
2024-01-15 10:23:45.135 INFO  [tools] Tool Read succeeded
```

### Warning Level
```
2024-01-15 10:23:45.135 WARN  [tools] Tool Read failed: File not found: /path/to/file
```

### Error Level
```
2024-01-15 10:23:45.135 ERROR [tools] Tool Bash raised exception: OSError: [Errno 2] No such file or directory
2024-01-15 10:23:45.135 ERROR [tools] Traceback (most recent call last):
                                        File "tools/base.py", line 45, in execute
                                          result = await self._execute(context, **kwargs)
                                        ...
```

---

## 11. Python Data Structure Examples

### ToolParameter Instance
```python
ToolParameter(
    name="file_path",
    type="string",
    description="Absolute path to the file to read",
    required=True,
    default=None,
    enum=None,
    min_length=1,
    max_length=4096,
    minimum=None,
    maximum=None,
)
```

### ToolResult Instance - Success
```python
ToolResult(
    success=True,
    output="Line 1: Hello\nLine 2: World",
    error=None,
    duration_ms=12.5,
    metadata={
        "lines": 2,
        "bytes": 25,
        "file_path": "/home/user/test.txt"
    }
)
```

### ToolResult Instance - Failure
```python
ToolResult(
    success=False,
    output=None,
    error="File not found: /home/user/missing.txt",
    duration_ms=3.2,
    metadata={
        "file_path": "/home/user/missing.txt",
        "errno": 2
    }
)
```

### ExecutionContext Instance
```python
ExecutionContext(
    working_dir="/home/user/my-project",
    session_id="sess_abc123",
    agent_id="agent_001",
    dry_run=False,
    timeout=120,
    max_output_size=100000,
    metadata={
        "user_id": "user_12345",
        "request_id": "req_xyz789"
    }
)
```

### ToolExecution Record
```python
ToolExecution(
    tool_name="Read",
    parameters={"file_path": "/home/user/test.py"},
    context=ExecutionContext(...),
    result=ToolResult(...),
    started_at=datetime(2024, 1, 15, 10, 23, 45, 123000),
    completed_at=datetime(2024, 1, 15, 10, 23, 45, 135000),
    duration_ms=12.0
)
```

---

## Notes

- These wireframes focus on data formats and debug output rather than interactive UI
- Actual tool implementations come in Phase 2.2 and 2.3
- Rich formatting (panels, tables) may be used for display in the REPL
- Log formats follow the logging system from Phase 1.1
- JSON schemas must exactly match LLM provider expectations
