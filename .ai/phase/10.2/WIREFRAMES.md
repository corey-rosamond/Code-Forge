# Phase 10.2: Polish and Integration Testing - Wireframes & Usage Examples

**Phase:** 10.2
**Name:** Polish and Integration Testing
**Dependencies:** All previous phases (1.1 - 10.1)

---

## 1. Test Execution Output

### Running Unit Tests

```
$ pytest tests/unit/ -v

================================ test session starts ================================
platform linux -- Python 3.11.0, pytest-8.0.0, pluggy-1.0.0
rootdir: /home/user/forge
plugins: asyncio-0.23.0, cov-4.1.0
collected 245 items

tests/unit/tools/test_read.py::TestReadTool::test_read_file PASSED          [  0%]
tests/unit/tools/test_read.py::TestReadTool::test_read_with_offset PASSED   [  0%]
tests/unit/tools/test_read.py::TestReadTool::test_read_nonexistent PASSED   [  1%]
tests/unit/tools/test_write.py::TestWriteTool::test_write_new_file PASSED   [  1%]
tests/unit/tools/test_write.py::TestWriteTool::test_write_overwrite PASSED  [  2%]
tests/unit/tools/test_edit.py::TestEditTool::test_edit_single PASSED        [  2%]
tests/unit/tools/test_edit.py::TestEditTool::test_edit_replace_all PASSED   [  3%]
...
tests/unit/session/test_manager.py::TestSessionManager::test_create PASSED  [ 95%]
tests/unit/session/test_manager.py::TestSessionManager::test_save PASSED    [ 96%]
tests/unit/session/test_manager.py::TestSessionManager::test_resume PASSED  [ 97%]
tests/unit/plugins/test_loader.py::TestPluginLoader::test_load PASSED       [ 98%]
tests/unit/plugins/test_manager.py::TestPluginManager::test_enable PASSED   [ 99%]
tests/unit/plugins/test_manager.py::TestPluginManager::test_disable PASSED  [100%]

================================ 245 passed in 12.34s ================================
```

### Running Integration Tests

```
$ pytest tests/integration/ -v

================================ test session starts ================================
platform linux -- Python 3.11.0, pytest-8.0.0, pluggy-1.0.0
rootdir: /home/user/forge
plugins: asyncio-0.23.0, cov-4.1.0
collected 78 items

tests/integration/test_tool_execution.py::TestToolExecutionFlow::test_read_file_flow PASSED
tests/integration/test_tool_execution.py::TestToolExecutionFlow::test_edit_with_permission PASSED
tests/integration/test_tool_execution.py::TestToolExecutionFlow::test_bash_with_hooks PASSED
tests/integration/test_session_flow.py::TestSessionFlow::test_create_save_resume PASSED
tests/integration/test_session_flow.py::TestSessionFlow::test_context_compaction PASSED
tests/integration/test_agent_workflow.py::TestAgentWorkflow::test_explore_agent PASSED
tests/integration/test_agent_workflow.py::TestAgentWorkflow::test_plan_agent PASSED
tests/integration/test_git_workflow.py::TestGitWorkflow::test_git_status_flow PASSED
tests/integration/test_git_workflow.py::TestGitWorkflow::test_git_commit_flow PASSED
tests/integration/test_plugin_system.py::TestPluginIntegration::test_discovery_and_load PASSED
tests/integration/test_plugin_system.py::TestPluginIntegration::test_tool_registration PASSED
...

================================ 78 passed in 45.67s =================================
```

### Running E2E Tests

```
$ pytest tests/e2e/ -v

================================ test session starts ================================
platform linux -- Python 3.11.0, pytest-8.0.0, pluggy-1.0.0
collected 15 items

tests/e2e/test_file_editing.py::TestFileEditingWorkflow::test_read_edit_verify PASSED
tests/e2e/test_file_editing.py::TestFileEditingWorkflow::test_create_new_file PASSED
tests/e2e/test_file_editing.py::TestFileEditingWorkflow::test_search_and_edit PASSED
tests/e2e/test_git_commit.py::TestGitCommitWorkflow::test_full_commit_workflow PASSED
tests/e2e/test_git_commit.py::TestGitCommitWorkflow::test_branch_and_commit PASSED
tests/e2e/test_full_session.py::TestFullSession::test_complete_workflow PASSED
...

================================ 15 passed in 23.45s =================================
```

---

## 2. Performance Test Output

### Startup Performance

```
$ pytest tests/performance/test_startup.py -v

================================ test session starts ================================
collected 3 items

tests/performance/test_startup.py::TestStartupPerformance::test_cold_start_under_2s PASSED
  Startup time: 1.23s (target: <2.0s) ✓

tests/performance/test_startup.py::TestStartupPerformance::test_initialization_under_2s PASSED
  Initialization time: 1.45s (target: <2.0s) ✓

tests/performance/test_startup.py::TestStartupPerformance::test_config_load_under_100ms PASSED
  Config load time: 0.042s (target: <0.1s) ✓

================================ 3 passed in 5.12s ==================================
```

### Response Time Performance

```
$ pytest tests/performance/test_response_time.py -v

================================ test session starts ================================
collected 3 items

tests/performance/test_response_time.py::TestResponseTime::test_tool_overhead_under_100ms PASSED
  Tool overhead: 0.045s (target: <0.1s) ✓

tests/performance/test_response_time.py::TestResponseTime::test_glob_under_500ms PASSED
  Glob search time: 0.234s (target: <0.5s) ✓

tests/performance/test_response_time.py::TestResponseTime::test_grep_under_1s PASSED
  Grep search time: 0.567s (target: <1.0s) ✓

================================ 3 passed in 8.34s ==================================
```

### Memory Performance

```
$ pytest tests/performance/test_memory.py -v

================================ test session starts ================================
collected 2 items

tests/performance/test_memory.py::TestMemoryUsage::test_idle_memory_under_100mb PASSED
  Idle memory: 67.3MB (target: <100MB) ✓

tests/performance/test_memory.py::TestMemoryUsage::test_session_memory_growth PASSED
  Peak memory: 234.5MB (target: <500MB) ✓

================================ 2 passed in 12.56s =================================
```

---

## 3. Coverage Report

### Coverage Summary

```
$ pytest tests/ --cov=forge --cov-report=term-missing

================================ test session starts ================================
collected 338 items

...

================================ 338 passed in 89.23s ===============================

---------- coverage: platform linux, python 3.11.0 -----------
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
src/forge/__init__.py                        5      0   100%
src/forge/cli.py                            45      2    96%   78-79
src/forge/core/app.py                      123      5    96%   234-238
src/forge/core/config.py                    89      3    97%   145-147
src/forge/tools/__init__.py                 12      0   100%
src/forge/tools/base.py                     67      2    97%   89-90
src/forge/tools/read.py                     45      0   100%
src/forge/tools/write.py                    52      1    98%   67
src/forge/tools/edit.py                     78      3    96%   102-104
src/forge/tools/glob.py                     34      0   100%
src/forge/tools/grep.py                     56      2    96%   78-79
src/forge/tools/bash.py                     89      4    96%   145-148
src/forge/session/__init__.py                8      0   100%
src/forge/session/manager.py               112      5    96%   189-193
src/forge/session/context.py                87      3    97%   134-136
src/forge/permissions/__init__.py            6      0   100%
src/forge/permissions/system.py             78      3    96%   112-114
src/forge/hooks/__init__.py                  5      0   100%
src/forge/hooks/manager.py                  56      2    96%   89-90
src/forge/plugins/__init__.py               15      0   100%
src/forge/plugins/base.py                   67      2    97%   98-99
src/forge/plugins/manager.py                98      4    96%   167-170
src/forge/plugins/loader.py                 54      2    96%   78-79
src/forge/plugins/registry.py               45      1    98%   67
src/forge/git/__init__.py                    8      0   100%
src/forge/git/operations.py                 89      4    96%   145-148
src/forge/github/__init__.py                10      0   100%
src/forge/github/client.py                 123      6    95%   189-194
---------------------------------------------------------------------
TOTAL                                    1678     54    97%

Required coverage: 90%
Actual coverage: 97% ✓
```

---

## 4. Type Checking Output

### MyPy Results

```
$ mypy src/forge/

src/forge/cli.py: Success: no issues found in 1 source file
src/forge/core/app.py: Success: no issues found in 1 source file
src/forge/core/config.py: Success: no issues found in 1 source file
src/forge/tools/__init__.py: Success: no issues found in 1 source file
src/forge/tools/base.py: Success: no issues found in 1 source file
src/forge/tools/read.py: Success: no issues found in 1 source file
src/forge/tools/write.py: Success: no issues found in 1 source file
src/forge/tools/edit.py: Success: no issues found in 1 source file
src/forge/tools/glob.py: Success: no issues found in 1 source file
src/forge/tools/grep.py: Success: no issues found in 1 source file
src/forge/tools/bash.py: Success: no issues found in 1 source file
src/forge/session/__init__.py: Success: no issues found in 1 source file
src/forge/session/manager.py: Success: no issues found in 1 source file
src/forge/session/context.py: Success: no issues found in 1 source file
src/forge/permissions/__init__.py: Success: no issues found in 1 source file
src/forge/permissions/system.py: Success: no issues found in 1 source file
src/forge/hooks/__init__.py: Success: no issues found in 1 source file
src/forge/hooks/manager.py: Success: no issues found in 1 source file
src/forge/plugins/__init__.py: Success: no issues found in 1 source file
src/forge/plugins/base.py: Success: no issues found in 1 source file
src/forge/plugins/manager.py: Success: no issues found in 1 source file
src/forge/plugins/loader.py: Success: no issues found in 1 source file
src/forge/plugins/registry.py: Success: no issues found in 1 source file
src/forge/git/__init__.py: Success: no issues found in 1 source file
src/forge/git/operations.py: Success: no issues found in 1 source file
src/forge/github/__init__.py: Success: no issues found in 1 source file
src/forge/github/client.py: Success: no issues found in 1 source file

Success: no issues found in 27 source files ✓
```

---

## 5. Linting Output

### Ruff Results

```
$ ruff check src/forge/

All checks passed! ✓

$ ruff format --check src/forge/

27 files would be left unchanged ✓
```

### Complexity Check

```
$ flake8 src/forge/ --max-complexity=10 --select=C901

All complexity checks passed! ✓

Complexity Summary:
  Maximum complexity found: 8
  Target complexity: ≤10
  Status: PASSED ✓
```

---

## 6. Error Recovery Examples

### Tool Error Recovery

```
You: Read the file /nonexistent/path.py

[Read tool execution]

Error: File not found: /nonexistent/path.py

The file does not exist. Please check the path and try again.

You: Read the file ./src/main.py

[Read tool execution]

File: src/main.py (45 lines)
─────────────────────────────────
"""Main application module."""

def main():
    """Application entry point."""
    ...
```

### Session Recovery

```
You: /session resume abc123

Resuming session: abc123

Warning: Session file was incomplete. Recovered 15 of 18 messages.
Some context may be missing.

Session resumed. Last message:
  User: "Help me implement the authentication..."

Continue from where you left off? [y/n]
```

### Network Error Handling

```
You: Search the web for Python best practices

[WebSearch tool execution]

Network Error: Unable to reach search service

Retrying (1/3)...
Retrying (2/3)...
Retrying (3/3)...

Failed to complete web search after 3 attempts.
Error: Connection timeout

Suggestion: Check your internet connection and try again.
You can also try /offline mode to work without network features.
```

---

## 7. Documentation Examples

### Getting Started Page

```markdown
# Getting Started with Code-Forge

## Installation

Install Code-Forge using pip:

```bash
pip install forge
```

## Quick Start

1. **Set up your API key:**

   ```bash
   export OPENROUTER_API_KEY="your-api-key"
   ```

2. **Start Code-Forge:**

   ```bash
   forge
   ```

3. **Try a simple command:**

   ```
   You: Read the README.md file

   [Reading README.md...]

   # My Project
   This is my awesome project.
   ```

## Next Steps

- Learn about [Configuration](configuration.md)
- Explore [Available Commands](../user-guide/commands.md)
- Discover [Tools](../user-guide/tools.md)
```

### Tool Reference Page

```markdown
# Tool Reference

## Read

Reads the contents of a file.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file_path | string | Yes | Absolute path to the file |
| offset | integer | No | Line number to start reading from |
| limit | integer | No | Maximum number of lines to read |

### Examples

**Basic usage:**
```
Read file_path="/home/user/project/main.py"
```

**With offset and limit:**
```
Read file_path="/home/user/project/main.py" offset=10 limit=50
```

### Permissions

- Permission level: Allow (no approval required)
- File access: Read-only

---

## Edit

Makes targeted edits to a file.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file_path | string | Yes | Absolute path to the file |
| old_string | string | Yes | Text to replace |
| new_string | string | Yes | Replacement text |
| replace_all | boolean | No | Replace all occurrences (default: false) |

### Examples

**Single replacement:**
```
Edit file_path="/home/user/project/main.py" old_string="old_name" new_string="new_name"
```

**Replace all:**
```
Edit file_path="/home/user/project/main.py" old_string="TODO" new_string="DONE" replace_all=true
```

### Permissions

- Permission level: Ask (requires approval)
- File access: Read/Write
```

---

## 8. Release Notes Example

```markdown
# Release Notes - v1.0.0

## Highlights

Code-Forge 1.0.0 is the first stable release, featuring a complete
AI-powered coding assistant with support for 400+ models via OpenRouter.

### Key Features

- **Multi-Model Support**: Connect to Claude, GPT-4, Llama, and 400+ more
- **Powerful Tool System**: Read, write, edit files, run commands
- **Session Management**: Persistent sessions with automatic context management
- **Plugin System**: Extend functionality with custom plugins
- **Git Integration**: Safe git operations with built-in guardrails
- **GitHub Integration**: Create PRs, manage issues, monitor workflows

## What's New

### Core Features

- Complete tool system with Read, Write, Edit, Glob, Grep, Bash
- Session persistence with SQLite storage
- Context compaction for long conversations
- Permission system with allow/ask/deny levels
- Hook system for customization

### Integrations

- OpenRouter API client with streaming support
- LangChain middleware for agent orchestration
- Git repository operations with safety guards
- GitHub API integration for collaborative workflows
- MCP protocol support for tool servers

### Developer Experience

- Plugin system for extending functionality
- Comprehensive API documentation
- Example plugins and tutorials
- Contributing guidelines

## Performance

- Cold start: < 2 seconds
- Tool overhead: < 100ms
- Memory usage: < 500MB typical

## Requirements

- Python 3.11+
- OpenRouter API key

## Upgrade Notes

This is the initial release. No upgrade path required.

## Known Issues

- Web search requires network connectivity
- Large file editing may be slow (> 10MB files)

## Acknowledgments

Thanks to all contributors and testers who helped make this release possible!
```

---

## 9. CI/CD Pipeline Output

### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run linting
        run: ruff check src/forge/

      - name: Run type checking
        run: mypy src/forge/

      - name: Run tests
        run: pytest tests/ --cov=forge --cov-fail-under=90

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pipeline Output

```
CI Pipeline Results
═══════════════════════════════════════════════════════════════

Job: test (Python 3.11)
├── Checkout ................................ ✓ 2s
├── Set up Python ........................... ✓ 15s
├── Install dependencies .................... ✓ 45s
├── Run linting ............................. ✓ 8s
├── Run type checking ....................... ✓ 23s
├── Run tests ............................... ✓ 89s
│   └── 338 passed, 0 failed
│   └── Coverage: 97%
└── Upload coverage ......................... ✓ 5s

Job: test (Python 3.12)
├── Checkout ................................ ✓ 2s
├── Set up Python ........................... ✓ 12s
├── Install dependencies .................... ✓ 42s
├── Run linting ............................. ✓ 7s
├── Run type checking ....................... ✓ 21s
├── Run tests ............................... ✓ 85s
│   └── 338 passed, 0 failed
│   └── Coverage: 97%
└── Upload coverage ......................... ✓ 4s

═══════════════════════════════════════════════════════════════
All jobs completed successfully ✓
Total time: 3m 42s
```

---

## 10. Package Installation

### Installing from PyPI

```
$ pip install forge

Collecting forge
  Downloading forge-1.0.0-py3-none-any.whl (125 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 125.3/125.3 kB 2.1 MB/s eta 0:00:00
Collecting langchain>=0.3.0
  Using cached langchain-0.3.1-py3-none-any.whl (234 kB)
Collecting pydantic>=2.0.0
  Using cached pydantic-2.5.0-py3-none-any.whl (156 kB)
Collecting rich>=13.0.0
  Using cached rich-13.7.0-py3-none-any.whl (240 kB)
...
Successfully installed forge-1.0.0 langchain-0.3.1 pydantic-2.5.0 rich-13.7.0 ...
```

### Verifying Installation

```
$ forge --version
Code-Forge 1.0.0

$ forge --help
Usage: forge [OPTIONS] [COMMAND]

  AI-powered coding assistant with OpenRouter and LangChain.

Options:
  --version           Show version and exit
  --config PATH       Path to config file
  --model TEXT        Model to use (default: anthropic/claude-3.5-sonnet)
  --project PATH      Project directory
  --headless          Run in headless mode
  --help              Show this message and exit

Commands:
  init     Initialize Code-Forge in current directory
  config   Manage configuration
  session  Manage sessions
```

### First Run

```
$ forge

╭──────────────────────────────────────────────────────────────╮
│                     Welcome to Code-Forge                       │
│         AI-powered coding assistant with 400+ models          │
╰──────────────────────────────────────────────────────────────╯

Model: anthropic/claude-3.5-sonnet
Project: /home/user/my-project

Type /help for available commands.

You: Hello!

Hello! I'm ready to help you with coding tasks. I can:

• Read, write, and edit files
• Search through your codebase
• Run shell commands
• Help with git operations
• Create GitHub pull requests

What would you like to work on today?
```

---

## Notes

- All test output shows passing results for production release
- Coverage exceeds 90% threshold requirement
- Performance metrics meet all targets
- Documentation covers user and developer needs
- CI/CD pipeline ensures quality gates
