# Phase 2.3: Execution Tools - Completion Criteria

**Phase:** 2.3
**Name:** Execution Tools
**Dependencies:** Phase 2.1 (Tool System Foundation)

---

## Definition of Done

All of the following criteria must be met before Phase 2.3 is considered complete.

---

## Checklist

### BashTool (src/forge/tools/execution/bash.py)
- [ ] BashTool class extends BaseTool
- [ ] name property returns "Bash"
- [ ] category property returns ToolCategory.EXECUTION
- [ ] parameters include: command (required), description, timeout, run_in_background
- [ ] DEFAULT_TIMEOUT_MS = 120000 (2 minutes)
- [ ] MAX_TIMEOUT_MS = 600000 (10 minutes)
- [ ] MAX_OUTPUT_SIZE = 30000 characters
- [ ] Executes foreground commands with subprocess
- [ ] Captures stdout and stderr
- [ ] Returns exit code in metadata
- [ ] Handles command timeout correctly
- [ ] Truncates large output with indicator
- [ ] Supports background execution mode
- [ ] Returns bash_id for background commands
- [ ] Validates dangerous command patterns
- [ ] Blocks rm -rf /, mkfs, dd, fork bombs
- [ ] Supports dry_run mode
- [ ] Handles command failures gracefully

### BashOutputTool (src/forge/tools/execution/bash_output.py)
- [ ] BashOutputTool class extends BaseTool
- [ ] name property returns "BashOutput"
- [ ] category property returns ToolCategory.EXECUTION
- [ ] parameters include: bash_id (required), filter (optional)
- [ ] Retrieves output from ShellManager
- [ ] Returns only new output since last read
- [ ] Includes shell status in output
- [ ] Includes exit code when available
- [ ] Supports regex filtering of output
- [ ] Returns error for invalid filter regex
- [ ] Returns error for non-existent shell

### KillShellTool (src/forge/tools/execution/kill_shell.py)
- [ ] KillShellTool class extends BaseTool
- [ ] name property returns "KillShell"
- [ ] category property returns ToolCategory.EXECUTION
- [ ] parameters include: shell_id (required)
- [ ] Kills running shell processes
- [ ] Returns success for already stopped shells
- [ ] Returns error for non-existent shells
- [ ] Includes command and duration in metadata

### ShellManager (src/forge/tools/execution/shell_manager.py)
- [ ] ShellManager is a singleton
- [ ] create_shell() creates and starts subprocess
- [ ] create_shell() returns ShellProcess with unique ID
- [ ] get_shell() retrieves shell by ID
- [ ] list_shells() returns all shells
- [ ] list_running() returns only running shells
- [ ] cleanup_completed() removes old completed shells
- [ ] kill_all() terminates all running shells
- [ ] reset() clears singleton for testing
- [ ] Thread-safe operations with asyncio.Lock

### ShellProcess (src/forge/tools/execution/shell_manager.py)
- [ ] ShellProcess dataclass implemented
- [ ] Fields: id, command, working_dir, process, status, exit_code
- [ ] Fields: stdout_buffer, stderr_buffer, last_read positions
- [ ] Fields: created_at, started_at, completed_at
- [ ] get_new_output() returns output since last read
- [ ] get_all_output() returns complete output
- [ ] read_output() reads from process streams
- [ ] wait() waits for completion with timeout
- [ ] kill() terminates the process
- [ ] terminate() sends SIGTERM
- [ ] is_running property works correctly
- [ ] duration_ms property calculates correctly

### ShellStatus Enum
- [ ] PENDING status defined
- [ ] RUNNING status defined
- [ ] COMPLETED status defined
- [ ] FAILED status defined
- [ ] KILLED status defined
- [ ] TIMEOUT status defined

### Package Structure
- [ ] src/forge/tools/execution/__init__.py exists
- [ ] __init__.py exports all tools and classes
- [ ] register_execution_tools() function registers all tools
- [ ] src/forge/tools/__init__.py updated to include execution tools

### Tool Registration
- [ ] All tools can be registered in ToolRegistry
- [ ] All tools generate valid OpenAI schemas
- [ ] All tools generate valid Anthropic schemas
- [ ] No duplicate tool names

### Security
- [ ] Dangerous command patterns are blocked
- [ ] Pattern matching is case-insensitive
- [ ] Timeout prevents runaway processes
- [ ] Process cleanup on timeout

### Testing
- [ ] Unit tests for BashTool (all scenarios)
- [ ] Unit tests for BashOutputTool (all scenarios)
- [ ] Unit tests for KillShellTool (all scenarios)
- [ ] Unit tests for ShellManager (all scenarios)
- [ ] Unit tests for ShellProcess (all scenarios)
- [ ] Integration tests for background workflow
- [ ] Test coverage ≥ 90%

---

## Verification Commands

```bash
# 1. Verify module structure
ls -la src/forge/tools/execution/
# Expected: __init__.py, bash.py, bash_output.py, kill_shell.py, shell_manager.py

# 2. Test imports
python -c "
from forge.tools.execution import (
    BashTool, BashOutputTool, KillShellTool,
    ShellManager, ShellProcess, ShellStatus,
    register_execution_tools
)
print('All execution tool imports successful')
"

# 3. Test BashTool foreground execution
python -c "
import asyncio
from forge.tools.execution import BashTool
from forge.tools.base import ExecutionContext

tool = BashTool()
ctx = ExecutionContext(working_dir='/tmp')

# Test simple command
result = asyncio.run(tool.execute(ctx, command='echo hello'))
assert result.success, f'Failed: {result.error}'
assert 'hello' in result.output
assert result.metadata['exit_code'] == 0
print('BashTool foreground: OK')
"

# 4. Test BashTool timeout
python -c "
import asyncio
from forge.tools.execution import BashTool
from forge.tools.base import ExecutionContext

tool = BashTool()
ctx = ExecutionContext(working_dir='/tmp')

# Test timeout
result = asyncio.run(tool.execute(ctx, command='sleep 10', timeout=1000))
assert not result.success
assert 'timed out' in result.error.lower()
print('BashTool timeout: OK')
"

# 5. Test dangerous command blocking
python -c "
import asyncio
from forge.tools.execution import BashTool
from forge.tools.base import ExecutionContext

tool = BashTool()
ctx = ExecutionContext(working_dir='/tmp')

# Test dangerous command
result = asyncio.run(tool.execute(ctx, command='rm -rf /'))
assert not result.success
assert 'blocked' in result.error.lower()
print('BashTool security: OK')
"

# 6. Test BashTool background execution
python -c "
import asyncio
from forge.tools.execution import BashTool, ShellManager
from forge.tools.base import ExecutionContext

ShellManager.reset()
tool = BashTool()
ctx = ExecutionContext(working_dir='/tmp')

# Start background command
result = asyncio.run(tool.execute(
    ctx,
    command='echo background',
    run_in_background=True
))
assert result.success
assert 'bash_id' in result.metadata
bash_id = result.metadata['bash_id']

# Verify shell exists
shell = ShellManager.get_shell(bash_id)
assert shell is not None
print(f'BashTool background: OK (id={bash_id})')

# Cleanup
ShellManager.reset()
"

# 7. Test BashOutputTool
python -c "
import asyncio
import time
from forge.tools.execution import BashTool, BashOutputTool, ShellManager
from forge.tools.base import ExecutionContext

ShellManager.reset()
bash_tool = BashTool()
output_tool = BashOutputTool()
ctx = ExecutionContext(working_dir='/tmp')

# Start background command
result = asyncio.run(bash_tool.execute(
    ctx,
    command='echo test_output && sleep 0.5 && echo done',
    run_in_background=True
))
bash_id = result.metadata['bash_id']

# Wait for some output
time.sleep(1)

# Get output
result = asyncio.run(output_tool.execute(ctx, bash_id=bash_id))
assert result.success
assert 'test_output' in result.output or 'done' in result.output
print('BashOutputTool: OK')

ShellManager.reset()
"

# 8. Test KillShellTool
python -c "
import asyncio
from forge.tools.execution import BashTool, KillShellTool, ShellManager
from forge.tools.base import ExecutionContext

ShellManager.reset()
bash_tool = BashTool()
kill_tool = KillShellTool()
ctx = ExecutionContext(working_dir='/tmp')

# Start background command
result = asyncio.run(bash_tool.execute(
    ctx,
    command='sleep 300',
    run_in_background=True
))
bash_id = result.metadata['bash_id']

# Kill it
result = asyncio.run(kill_tool.execute(ctx, shell_id=bash_id))
assert result.success
assert 'terminated' in result.output.lower()

# Verify killed
shell = ShellManager.get_shell(bash_id)
assert shell.status.value == 'killed'
print('KillShellTool: OK')

ShellManager.reset()
"

# 9. Test ShellManager singleton
python -c "
from forge.tools.execution import ShellManager

ShellManager.reset()

m1 = ShellManager()
m2 = ShellManager()
assert m1 is m2, 'Not a singleton!'
print('ShellManager singleton: OK')
"

# 10. Test tool registration
python -c "
from forge.tools.registry import ToolRegistry
from forge.tools.execution import register_execution_tools

ToolRegistry.reset()
registry = ToolRegistry()
register_execution_tools(registry)

assert registry.exists('Bash')
assert registry.exists('BashOutput')
assert registry.exists('KillShell')
print(f'Tool registration: OK ({registry.count()} tools)')
"

# 11. Test schema generation
python -c "
from forge.tools.execution import BashTool, BashOutputTool, KillShellTool

bash = BashTool()
output = BashOutputTool()
kill = KillShellTool()

# OpenAI schema
schema = bash.to_openai_schema()
assert schema['type'] == 'function'
assert schema['function']['name'] == 'Bash'
assert 'command' in schema['function']['parameters']['required']

schema = output.to_openai_schema()
assert 'bash_id' in schema['function']['parameters']['required']

schema = kill.to_openai_schema()
assert 'shell_id' in schema['function']['parameters']['required']

print('Schema generation: OK')
"

# 12. Test dry run mode
python -c "
import asyncio
from forge.tools.execution import BashTool
from forge.tools.base import ExecutionContext

tool = BashTool()
ctx = ExecutionContext(working_dir='/tmp', dry_run=True)

result = asyncio.run(tool.execute(ctx, command='echo test'))
assert result.success
assert 'Dry Run' in result.output
print('Dry run mode: OK')
"

# 13. Run all unit tests
pytest tests/unit/tools/execution/ -v --cov=forge.tools.execution --cov-report=term-missing

# Expected: All tests pass, coverage ≥ 90%

# 14. Type checking
mypy src/forge/tools/execution/ --strict
# Expected: No errors

# 15. Linting
ruff check src/forge/tools/execution/
# Expected: No errors
```

---

## Quality Gates

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Test Coverage | ≥ 90% | `pytest --cov` |
| Type Hints | 100% public APIs | `mypy --strict` |
| Lint Errors | 0 | `ruff check` |
| McCabe Complexity | ≤ 10 | `ruff check --select=C901` |
| All Tools Registered | 3 tools | Manual verification |

---

## Files to Create

| File | Purpose |
|------|---------|
| `src/forge/tools/execution/__init__.py` | Package exports and registration |
| `src/forge/tools/execution/bash.py` | BashTool implementation |
| `src/forge/tools/execution/bash_output.py` | BashOutputTool implementation |
| `src/forge/tools/execution/kill_shell.py` | KillShellTool implementation |
| `src/forge/tools/execution/shell_manager.py` | ShellManager and ShellProcess |
| `tests/unit/tools/execution/__init__.py` | Test package |
| `tests/unit/tools/execution/test_bash.py` | BashTool tests |
| `tests/unit/tools/execution/test_bash_output.py` | BashOutputTool tests |
| `tests/unit/tools/execution/test_kill_shell.py` | KillShellTool tests |
| `tests/unit/tools/execution/test_shell_manager.py` | ShellManager tests |
| `tests/unit/tools/execution/test_integration.py` | Integration tests |

---

## Dependencies to Verify

Ensure these are in `pyproject.toml`:
```toml
[tool.poetry.dependencies]
# No additional dependencies - uses standard library asyncio

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-asyncio = "^0.23"
pytest-cov = "^4.1"
```

---

## Manual Testing Checklist

- [ ] Execute simple echo command
- [ ] Execute command with stderr output
- [ ] Execute command that fails (non-zero exit)
- [ ] Execute command that times out
- [ ] Start background command
- [ ] Check background command output
- [ ] Kill running background command
- [ ] Verify dangerous commands are blocked
- [ ] Test dry run mode
- [ ] Test output truncation with large output
- [ ] Test multiple concurrent background shells

---

## Integration Points

Phase 2.3 provides tools for:

| Consumer | What It Uses |
|----------|--------------|
| Phase 3.2 (LangChain) | Execution tools for agent actions |
| Phase 4.1 (Permissions) | Tool names for permission rules |
| Phase 4.2 (Hooks) | Before/after command hooks |
| Phase 6.1 (Slash Commands) | Tool execution for commands |

---

## Sign-Off

Phase 2.3 is complete when:

1. [ ] All checklist items above are checked
2. [ ] All verification commands pass
3. [ ] All quality gates are met
4. [ ] Manual testing checklist completed
5. [ ] Code has been reviewed (if applicable)
6. [ ] No TODO comments remain in Phase 2.3 code

---

## Next Phase

After completing Phase 2.3, proceed to:
- **Phase 3.1: OpenRouter Client**

Phase 3.1 will implement:
- OpenRouter API client
- Model routing and selection
- Streaming response handling
- Rate limiting and retries
