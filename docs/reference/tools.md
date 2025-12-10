# Tool Reference

OpenCode provides built-in tools for common operations.

## File Tools

### Read

Read file contents.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| file_path | string | Yes | Absolute path to file |
| offset | integer | No | Line to start from |
| limit | integer | No | Max lines to read |

**Examples:**
```
Read the file /home/user/project/main.py
Read main.py from line 50 with limit 20 lines
```

### Write

Create or overwrite a file.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| file_path | string | Yes | Absolute path to file |
| content | string | Yes | Content to write |

**Examples:**
```
Create a new file at /home/user/project/utils.py with the function...
Write "hello world" to output.txt
```

### Edit

Make targeted edits to a file.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| file_path | string | Yes | Absolute path to file |
| old_string | string | Yes | Text to replace |
| new_string | string | Yes | Replacement text |
| replace_all | boolean | No | Replace all occurrences |

**Examples:**
```
In main.py, change "old_name" to "new_name"
Replace all occurrences of "TODO" with "DONE" in utils.py
```

### Glob

Find files matching a pattern.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| pattern | string | Yes | Glob pattern |
| path | string | No | Directory to search |

**Examples:**
```
Find all Python files: **/*.py
Find test files in src/: src/**/test_*.py
```

### Grep

Search file contents.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| pattern | string | Yes | Regex pattern |
| path | string | Yes | File or directory |

**Examples:**
```
Search for "def main" in the project
Find all imports of pandas in src/
```

## Execution Tools

### Bash

Execute shell commands.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| command | string | Yes | Command to execute |
| timeout | integer | No | Timeout in ms |
| run_in_background | boolean | No | Run in background |

**Examples:**
```
Run the tests: pytest tests/
Install dependencies: pip install -r requirements.txt
Start server in background: python server.py
```

### BashOutput

Get output from background processes.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| bash_id | string | Yes | ID of background process |

### KillShell

Terminate a background process.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| shell_id | string | Yes | ID of process to kill |

## Permission Levels

Tools have different permission levels:

| Level | Description |
|-------|-------------|
| Allow | No confirmation required |
| Ask | Requires user confirmation |
| Deny | Blocked entirely |

Default permissions:
- **Allow**: Read, Glob, Grep
- **Ask**: Write, Edit, Bash

## Safety Features

### File Tools
- Path traversal prevention
- Automatic directory creation for Write
- Atomic file operations

### Bash Tool
- Dangerous command blocking (rm -rf /, etc.)
- Timeout enforcement
- Working directory isolation
