# Phase 2.3: Execution Tools - Wireframes

**Phase:** 2.3
**Name:** Execution Tools
**Dependencies:** Phase 2.1 (Tool System Foundation)

---

## Overview

This document shows the expected output formats and user-visible results from the execution tools. These wireframes demonstrate how tool results will appear in the REPL.

---

## 1. Bash Tool Output - Foreground

### Successful Command
```
┌─────────────────────────────────────────────────────────────────────┐
│ Bash: ls -la                                                        │
├─────────────────────────────────────────────────────────────────────┤
│ total 32                                                            │
│ drwxr-xr-x  5 user user 4096 Jan 15 10:30 .                        │
│ drwxr-xr-x 45 user user 4096 Jan 15 10:00 ..                       │
│ -rw-r--r--  1 user user  156 Jan 15 10:30 README.md                │
│ drwxr-xr-x  3 user user 4096 Jan 15 10:30 src                      │
│ -rw-r--r--  1 user user 1024 Jan 15 10:30 pyproject.toml           │
├─────────────────────────────────────────────────────────────────────┤
│ Exit code: 0 | Duration: 12ms                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Failed Command
```
┌─────────────────────────────────────────────────────────────────────┐
│ Bash: cat /nonexistent/file.txt                                     │
├─────────────────────────────────────────────────────────────────────┤
│ [stderr]                                                            │
│ cat: /nonexistent/file.txt: No such file or directory               │
├─────────────────────────────────────────────────────────────────────┤
│ ✗ Exit code: 1 | Duration: 5ms                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Command with Both stdout and stderr
```
┌─────────────────────────────────────────────────────────────────────┐
│ Bash: npm install                                                   │
├─────────────────────────────────────────────────────────────────────┤
│ added 156 packages in 4.5s                                          │
│                                                                     │
│ [stderr]                                                            │
│ npm WARN deprecated package@1.0.0: This package is deprecated       │
├─────────────────────────────────────────────────────────────────────┤
│ Exit code: 0 | Duration: 4523ms                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Command Timed Out
```
┌─────────────────────────────────────────────────────────────────────┐
│ Bash: npm run build (timed out)                                     │
├─────────────────────────────────────────────────────────────────────┤
│ Building project...                                                 │
│ Compiling TypeScript...                                             │
│ Processing 150 files...                                             │
│                                                                     │
│ ⏱ Command timed out after 120000ms                                  │
├─────────────────────────────────────────────────────────────────────┤
│ ✗ Timeout | Duration: 120000ms                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Output Truncated
```
┌─────────────────────────────────────────────────────────────────────┐
│ Bash: find / -type f                                                │
├─────────────────────────────────────────────────────────────────────┤
│ /usr/bin/bash                                                       │
│ /usr/bin/cat                                                        │
│ /usr/bin/chmod                                                      │
│ ...                                                                 │
│ /var/log/syslog                                                     │
│                                                                     │
│ [Output truncated at 30000 characters]                              │
├─────────────────────────────────────────────────────────────────────┤
│ Exit code: 0 | Duration: 5432ms | Truncated                         │
└─────────────────────────────────────────────────────────────────────┘
```

### Dry Run Mode
```
┌─────────────────────────────────────────────────────────────────────┐
│ Bash: npm install [DRY RUN]                                         │
├─────────────────────────────────────────────────────────────────────┤
│ [Dry Run] Would execute: npm install                                │
│                                                                     │
│ No command was executed                                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Bash Tool Output - Background

### Background Command Started
```
┌─────────────────────────────────────────────────────────────────────┐
│ Bash: npm run build [Background]                                    │
├─────────────────────────────────────────────────────────────────────┤
│ ✓ Started background shell: shell_a1b2c3d4                          │
│                                                                     │
│ Command: npm run build                                              │
│                                                                     │
│ Use BashOutput tool with bash_id='shell_a1b2c3d4' to read output.   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. BashOutput Tool Output

### Output from Running Shell
```
┌─────────────────────────────────────────────────────────────────────┐
│ BashOutput: shell_a1b2c3d4                                          │
├─────────────────────────────────────────────────────────────────────┤
│ Status: running                                                     │
│                                                                     │
│ > Building for production...                                        │
│ > Compiling TypeScript files...                                     │
│ > Processing src/main.ts                                            │
│ > Processing src/config.ts                                          │
├─────────────────────────────────────────────────────────────────────┤
│ Shell: shell_a1b2c3d4 | Status: running                             │
└─────────────────────────────────────────────────────────────────────┘
```

### Output from Completed Shell
```
┌─────────────────────────────────────────────────────────────────────┐
│ BashOutput: shell_a1b2c3d4                                          │
├─────────────────────────────────────────────────────────────────────┤
│ Status: completed, Exit code: 0, Duration: 15234ms                  │
│                                                                     │
│ > Build completed successfully!                                     │
│ > Output written to dist/                                           │
│ > Total time: 15.2s                                                 │
├─────────────────────────────────────────────────────────────────────┤
│ Shell: shell_a1b2c3d4 | Completed | Exit: 0                         │
└─────────────────────────────────────────────────────────────────────┘
```

### Output from Failed Shell
```
┌─────────────────────────────────────────────────────────────────────┐
│ BashOutput: shell_a1b2c3d4                                          │
├─────────────────────────────────────────────────────────────────────┤
│ Status: failed, Exit code: 1, Duration: 3456ms                      │
│                                                                     │
│ > Building...                                                       │
│ > Error: Cannot find module 'express'                               │
│ > Build failed                                                      │
├─────────────────────────────────────────────────────────────────────┤
│ Shell: shell_a1b2c3d4 | Failed | Exit: 1                            │
└─────────────────────────────────────────────────────────────────────┘
```

### Filtered Output
```
┌─────────────────────────────────────────────────────────────────────┐
│ BashOutput: shell_a1b2c3d4 (filtered: "error|warning")              │
├─────────────────────────────────────────────────────────────────────┤
│ Status: running                                                     │
│                                                                     │
│ > [warning] Deprecated API used in config.ts                        │
│ > [error] Missing dependency: lodash                                │
│ > [warning] Large bundle size detected                              │
├─────────────────────────────────────────────────────────────────────┤
│ Shell: shell_a1b2c3d4 | Filtered output                             │
└─────────────────────────────────────────────────────────────────────┘
```

### No New Output
```
┌─────────────────────────────────────────────────────────────────────┐
│ BashOutput: shell_a1b2c3d4                                          │
├─────────────────────────────────────────────────────────────────────┤
│ Status: running                                                     │
│                                                                     │
│ (no new output since last check)                                    │
├─────────────────────────────────────────────────────────────────────┤
│ Shell: shell_a1b2c3d4 | Status: running                             │
└─────────────────────────────────────────────────────────────────────┘
```

### Shell Not Found
```
┌─────────────────────────────────────────────────────────────────────┐
│ BashOutput Error                                                    │
├─────────────────────────────────────────────────────────────────────┤
│ Shell not found: shell_xyz789                                       │
│                                                                     │
│ The shell may have been cleaned up or the ID is incorrect.          │
│                                                                     │
│ Active shells:                                                      │
│ • shell_a1b2c3d4 (running) - npm run build                         │
│ • shell_e5f6g7h8 (completed) - pytest                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. KillShell Tool Output

### Successfully Killed
```
┌─────────────────────────────────────────────────────────────────────┐
│ KillShell: shell_a1b2c3d4                                           │
├─────────────────────────────────────────────────────────────────────┤
│ ✓ Shell shell_a1b2c3d4 terminated                                   │
│                                                                     │
│ Command: npm run build                                              │
│ Duration: 5234ms (before termination)                               │
└─────────────────────────────────────────────────────────────────────┘
```

### Already Stopped
```
┌─────────────────────────────────────────────────────────────────────┐
│ KillShell: shell_a1b2c3d4                                           │
├─────────────────────────────────────────────────────────────────────┤
│ Shell shell_a1b2c3d4 already stopped                                │
│                                                                     │
│ Status: completed                                                   │
│ Exit code: 0                                                        │
└─────────────────────────────────────────────────────────────────────┘
```

### Shell Not Found
```
┌─────────────────────────────────────────────────────────────────────┐
│ KillShell Error                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ Shell not found: shell_xyz789                                       │
│                                                                     │
│ The shell may have already completed or been killed.                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Security Error Messages

### Dangerous Command Blocked
```
┌─────────────────────────────────────────────────────────────────────┐
│ Bash Security Error                                                 │
├─────────────────────────────────────────────────────────────────────┤
│ Command blocked for security: matches dangerous pattern             │
│                                                                     │
│ Command: rm -rf /                                                   │
│                                                                     │
│ This command has been blocked because it matches a pattern          │
│ known to be destructive. If you need to perform this operation,     │
│ please do so manually outside of Code-Forge.                          │
└─────────────────────────────────────────────────────────────────────┘
```

### Fork Bomb Blocked
```
┌─────────────────────────────────────────────────────────────────────┐
│ Bash Security Error                                                 │
├─────────────────────────────────────────────────────────────────────┤
│ Command blocked for security: matches dangerous pattern             │
│                                                                     │
│ The command appears to be a fork bomb or similar resource           │
│ exhaustion attack. This has been blocked.                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Shell Listing (Debug/Status View)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Background Shells                                                   │
├─────────────────────────────────────────────────────────────────────┤
│ ID              │ Status    │ Command              │ Duration       │
├─────────────────────────────────────────────────────────────────────┤
│ shell_a1b2c3d4  │ running   │ npm run build        │ 45.2s         │
│ shell_e5f6g7h8  │ completed │ pytest               │ 12.8s         │
│ shell_i9j0k1l2  │ failed    │ npm test             │ 5.3s          │
│ shell_m3n4o5p6  │ killed    │ sleep 300            │ 30.0s         │
├─────────────────────────────────────────────────────────────────────┤
│ Total: 4 shells (1 running, 3 completed/stopped)                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. Tool Schema Display

### Bash Tool Schema (OpenAI Format)
```json
{
  "type": "function",
  "function": {
    "name": "Bash",
    "description": "Executes a bash command in a persistent shell session...",
    "parameters": {
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
  }
}
```

---

## 8. Log Output Examples

### Info Level
```
2024-01-15 10:30:45.123 INFO  [tools.exec] Executing Bash: ls -la
2024-01-15 10:30:45.135 INFO  [tools.exec] Bash succeeded: exit_code=0
```

### Debug Level
```
2024-01-15 10:30:45.123 DEBUG [tools.exec] Bash params: command="ls -la", timeout=120000
2024-01-15 10:30:45.124 DEBUG [tools.exec] Security check passed
2024-01-15 10:30:45.125 DEBUG [tools.exec] Starting subprocess in /home/user/project
2024-01-15 10:30:45.135 DEBUG [tools.exec] Process completed: exit_code=0, output_size=512
```

### Background Shell
```
2024-01-15 10:30:45.123 INFO  [tools.exec] Starting background shell: shell_a1b2c3d4
2024-01-15 10:30:45.123 DEBUG [tools.exec] Command: npm run build
2024-01-15 10:30:45.124 INFO  [tools.exec] Background shell started: shell_a1b2c3d4
```

### Security Block
```
2024-01-15 10:30:45.123 WARN  [tools.exec] Blocked dangerous command: rm -rf /
2024-01-15 10:30:45.123 INFO  [tools.exec] Security pattern matched: rm\s+-rf\s+/
```

### Shell Kill
```
2024-01-15 10:30:45.123 INFO  [tools.exec] Killing shell: shell_a1b2c3d4
2024-01-15 10:30:45.125 INFO  [tools.exec] Shell killed: shell_a1b2c3d4, duration=5234ms
```

---

## 9. Terminal Integration Examples

### Running npm install
```
$ forge
> Run npm install

┌─────────────────────────────────────────────────────────────────────┐
│ Bash: npm install                                                   │
├─────────────────────────────────────────────────────────────────────┤
│ npm WARN deprecated package@1.0.0: Use package@2.0.0 instead        │
│                                                                     │
│ added 256 packages, and audited 257 packages in 8s                  │
│                                                                     │
│ 45 packages are looking for funding                                 │
│   run `npm fund` for details                                        │
│                                                                     │
│ found 0 vulnerabilities                                             │
├─────────────────────────────────────────────────────────────────────┤
│ Exit code: 0 | Duration: 8234ms                                     │
└─────────────────────────────────────────────────────────────────────┘

>
```

### Running Tests in Background
```
$ forge
> Run pytest in background

┌─────────────────────────────────────────────────────────────────────┐
│ Bash: pytest [Background]                                           │
├─────────────────────────────────────────────────────────────────────┤
│ ✓ Started background shell: shell_test123                           │
│                                                                     │
│ Command: pytest                                                     │
│ Use BashOutput with bash_id='shell_test123' to check progress.      │
└─────────────────────────────────────────────────────────────────────┘

> Check test progress

┌─────────────────────────────────────────────────────────────────────┐
│ BashOutput: shell_test123                                           │
├─────────────────────────────────────────────────────────────────────┤
│ Status: running                                                     │
│                                                                     │
│ ============================= test session starts ==============    │
│ platform linux -- Python 3.11.0, pytest-8.0.0                       │
│ collected 45 items                                                  │
│                                                                     │
│ tests/test_config.py::test_load_config PASSED                       │
│ tests/test_config.py::test_save_config PASSED                       │
│ tests/test_tools.py::test_read_file ...                            │
├─────────────────────────────────────────────────────────────────────┤
│ Shell: shell_test123 | Status: running                              │
└─────────────────────────────────────────────────────────────────────┘

>
```

---

## Notes

- Output uses Rich library for formatting in the actual REPL
- Exit codes are prominently displayed for debugging
- Duration is shown for performance awareness
- Background shell IDs are easy to copy/reference
- Security errors are informative but don't reveal exploit details
- Truncation indicators help users understand output limits
