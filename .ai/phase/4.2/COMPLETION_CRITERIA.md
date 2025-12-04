# Phase 4.2: Hooks System - Completion Criteria

**Phase:** 4.2
**Name:** Hooks System
**Dependencies:** Phase 2.1 (Tool System Foundation), Phase 4.1 (Permission System)

---

## Definition of Done

All of the following criteria must be met before Phase 4.2 is considered complete.

---

## Checklist

### Event Types (src/opencode/hooks/events.py)
- [ ] EventType enum defined with all event types
- [ ] Tool events: pre_execute, post_execute, error
- [ ] LLM events: pre_request, post_response, stream_start, stream_end
- [ ] Session events: start, end, message
- [ ] Permission events: check, prompt, granted, denied
- [ ] User events: prompt_submit, interrupt
- [ ] HookEvent dataclass with type, timestamp, data
- [ ] HookEvent.to_env() returns environment variables
- [ ] HookEvent.to_json() serializes to JSON
- [ ] Factory methods for common events

### Hook Definition (src/opencode/hooks/registry.py)
- [ ] Hook dataclass with pattern, command, timeout
- [ ] Hook.matches() for exact event match
- [ ] Hook.matches() for glob patterns (tool:*)
- [ ] Hook.matches() for tool-specific (tool:event:name)
- [ ] Hook.matches() for comma-separated patterns
- [ ] Hook.matches() for catch-all (*)
- [ ] Hook.to_dict() serialization
- [ ] Hook.from_dict() deserialization

### Hook Registry (src/opencode/hooks/registry.py)
- [ ] HookRegistry class implemented
- [ ] Singleton pattern via get_instance()
- [ ] register() adds hooks
- [ ] unregister() removes by pattern
- [ ] get_hooks() returns matching enabled hooks
- [ ] clear() removes all hooks
- [ ] load_hooks() adds multiple hooks

### Hook Executor (src/opencode/hooks/executor.py)
- [ ] HookResult dataclass with exit_code, stdout, stderr
- [ ] HookResult.success property
- [ ] HookResult.should_continue property
- [ ] HookExecutor class implemented
- [ ] execute_hooks() runs all matching hooks
- [ ] _execute_hook() runs single hook in subprocess
- [ ] Environment variables set correctly
- [ ] Working directory set correctly
- [ ] Timeout handling kills process
- [ ] stop_on_failure parameter works
- [ ] HookBlockedError exception class
- [ ] fire_event() convenience function

### Configuration (src/opencode/hooks/config.py)
- [ ] HookConfig.load_global() loads from user config
- [ ] HookConfig.load_project() loads from project config
- [ ] HookConfig.save_global() saves hooks
- [ ] HookConfig.save_project() saves hooks
- [ ] HookConfig.load_all() combines both sources
- [ ] HOOK_TEMPLATES dictionary with examples
- [ ] Handle missing config files gracefully
- [ ] Handle corrupted config files gracefully

### Package Structure
- [ ] src/opencode/hooks/__init__.py exports all public classes
- [ ] All imports work correctly
- [ ] No circular dependencies

### Testing
- [ ] Unit tests for EventType enum
- [ ] Unit tests for HookEvent factory methods
- [ ] Unit tests for HookEvent.to_env()
- [ ] Unit tests for Hook pattern matching
- [ ] Unit tests for glob patterns
- [ ] Unit tests for tool-specific patterns
- [ ] Unit tests for HookRegistry
- [ ] Unit tests for HookExecutor
- [ ] Unit tests for timeout handling
- [ ] Unit tests for blocking hooks
- [ ] Unit tests for config loading
- [ ] Test coverage ≥ 90%

---

## Verification Commands

```bash
# 1. Verify module structure
ls -la src/opencode/hooks/
# Expected: __init__.py, events.py, registry.py, executor.py, config.py

# 2. Test imports
python -c "
from opencode.hooks import (
    EventType,
    HookEvent,
    Hook,
    HookRegistry,
    HookResult,
    HookExecutor,
    HookBlockedError,
    fire_event,
    HookConfig,
    HOOK_TEMPLATES,
)
print('All hooks imports successful')
"

# 3. Test EventType enum
python -c "
from opencode.hooks import EventType

assert EventType.TOOL_PRE_EXECUTE.value == 'tool:pre_execute'
assert EventType.LLM_POST_RESPONSE.value == 'llm:post_response'
assert EventType.SESSION_START.value == 'session:start'
assert EventType.PERMISSION_CHECK.value == 'permission:check'
assert EventType.USER_PROMPT_SUBMIT.value == 'user:prompt_submit'

print('EventType enum: OK')
"

# 4. Test HookEvent creation
python -c "
from opencode.hooks import HookEvent, EventType

# Factory method
event = HookEvent.tool_pre_execute('bash', {'command': 'ls'}, 'sess_123')
assert event.type == EventType.TOOL_PRE_EXECUTE
assert event.tool_name == 'bash'
assert 'tool_args' in event.data

# Environment variables
env = event.to_env()
assert env['OPENCODE_EVENT'] == 'tool:pre_execute'
assert env['OPENCODE_TOOL_NAME'] == 'bash'
assert 'OPENCODE_TOOL_ARGS' in env

# JSON serialization
json_str = event.to_json()
import json
data = json.loads(json_str)
assert data['type'] == 'tool:pre_execute'

print('HookEvent: OK')
"

# 5. Test Hook pattern matching
python -c "
from opencode.hooks import Hook, HookEvent

# Exact match
hook = Hook(event_pattern='tool:pre_execute', command='echo test')
event = HookEvent.tool_pre_execute('bash', {})
assert hook.matches(event) == True

# Different event
event2 = HookEvent.tool_post_execute('bash', {}, {})
assert hook.matches(event2) == False

# Glob pattern
hook = Hook(event_pattern='tool:*', command='echo test')
assert hook.matches(event) == True
assert hook.matches(event2) == True

# Tool-specific
hook = Hook(event_pattern='tool:pre_execute:bash', command='echo test')
assert hook.matches(event) == True

event_read = HookEvent.tool_pre_execute('read', {})
assert hook.matches(event_read) == False

# Catch-all
hook = Hook(event_pattern='*', command='echo test')
assert hook.matches(event) == True
assert hook.matches(event2) == True

# Comma-separated
hook = Hook(event_pattern='session:start,session:end', command='echo test')
start_event = HookEvent.session_start('sess_123')
end_event = HookEvent.session_end('sess_123')
assert hook.matches(start_event) == True
assert hook.matches(end_event) == True

print('Hook pattern matching: OK')
"

# 6. Test HookRegistry
python -c "
from opencode.hooks import HookRegistry, Hook, HookEvent

# Reset singleton
HookRegistry.reset_instance()
registry = HookRegistry.get_instance()

# Register
registry.register(Hook(event_pattern='tool:pre_execute', command='echo 1'))
registry.register(Hook(event_pattern='tool:*', command='echo 2'))
assert len(registry) == 2

# Get matching
event = HookEvent.tool_pre_execute('bash', {})
matching = registry.get_hooks(event)
assert len(matching) == 2

# Unregister
assert registry.unregister('tool:pre_execute') == True
assert len(registry) == 1

# Clear
registry.clear()
assert len(registry) == 0

print('HookRegistry: OK')
"

# 7. Test Hook serialization
python -c "
from opencode.hooks import Hook

hook = Hook(
    event_pattern='tool:pre_execute',
    command='echo hello',
    timeout=5.0,
    description='Test hook',
)

data = hook.to_dict()
assert data['event'] == 'tool:pre_execute'
assert data['command'] == 'echo hello'
assert data['timeout'] == 5.0

hook2 = Hook.from_dict(data)
assert hook2.event_pattern == hook.event_pattern
assert hook2.timeout == hook.timeout

print('Hook serialization: OK')
"

# 8. Test HookResult properties
python -c "
from opencode.hooks import HookResult, Hook

hook = Hook(event_pattern='test', command='test')

# Success
result = HookResult(hook=hook, exit_code=0, stdout='ok', stderr='', duration=0.1)
assert result.success == True
assert result.should_continue == True

# Failure
result = HookResult(hook=hook, exit_code=1, stdout='blocked', stderr='', duration=0.1)
assert result.success == False
assert result.should_continue == False

# Timeout
result = HookResult(hook=hook, exit_code=-1, stdout='', stderr='', duration=10.0, timed_out=True)
assert result.success == False
assert result.should_continue == False

print('HookResult: OK')
"

# 9. Test hook execution
python -c "
import asyncio
from opencode.hooks import HookExecutor, HookRegistry, Hook, HookEvent

async def test():
    HookRegistry.reset_instance()
    registry = HookRegistry.get_instance()
    registry.register(Hook(event_pattern='tool:pre_execute', command='echo hello'))

    executor = HookExecutor(registry=registry)
    event = HookEvent.tool_pre_execute('bash', {})

    results = await executor.execute_hooks(event)
    assert len(results) == 1
    assert results[0].exit_code == 0
    assert 'hello' in results[0].stdout

    print('Hook execution: OK')

asyncio.run(test())
"

# 10. Test blocking hook
python -c "
import asyncio
from opencode.hooks import HookExecutor, HookRegistry, Hook, HookEvent

async def test():
    HookRegistry.reset_instance()
    registry = HookRegistry.get_instance()
    registry.register(Hook(event_pattern='tool:pre_execute', command='exit 1'))

    executor = HookExecutor(registry=registry)
    event = HookEvent.tool_pre_execute('bash', {})

    results = await executor.execute_hooks(event, stop_on_failure=True)
    assert len(results) == 1
    assert results[0].exit_code == 1
    assert results[0].should_continue == False

    print('Blocking hook: OK')

asyncio.run(test())
"

# 11. Test timeout
python -c "
import asyncio
from opencode.hooks import HookExecutor, HookRegistry, Hook, HookEvent

async def test():
    HookRegistry.reset_instance()
    registry = HookRegistry.get_instance()
    registry.register(Hook(event_pattern='tool:pre_execute', command='sleep 10', timeout=0.5))

    executor = HookExecutor(registry=registry)
    event = HookEvent.tool_pre_execute('bash', {})

    results = await executor.execute_hooks(event)
    assert len(results) == 1
    assert results[0].timed_out == True
    assert results[0].success == False

    print('Hook timeout: OK')

asyncio.run(test())
"

# 12. Test fire_event convenience function
python -c "
import asyncio
from opencode.hooks import fire_event, HookRegistry, Hook, HookEvent

async def test():
    HookRegistry.reset_instance()
    registry = HookRegistry.get_instance()
    registry.register(Hook(event_pattern='tool:*', command='echo fired'))

    event = HookEvent.tool_pre_execute('bash', {})
    results = await fire_event(event)

    assert len(results) == 1
    assert results[0].success == True

    print('fire_event: OK')

asyncio.run(test())
"

# 13. Test disabled hooks filtered
python -c "
from opencode.hooks import HookRegistry, Hook, HookEvent

HookRegistry.reset_instance()
registry = HookRegistry.get_instance()
registry.register(Hook(event_pattern='tool:pre_execute', command='echo 1', enabled=False))
registry.register(Hook(event_pattern='tool:pre_execute', command='echo 2', enabled=True))

event = HookEvent.tool_pre_execute('bash', {})
matching = registry.get_hooks(event)
assert len(matching) == 1

print('Disabled hooks filtered: OK')
"

# 14. Test environment variables in hook
python -c "
import asyncio
from opencode.hooks import HookExecutor, HookRegistry, Hook, HookEvent

async def test():
    HookRegistry.reset_instance()
    registry = HookRegistry.get_instance()
    registry.register(Hook(
        event_pattern='tool:pre_execute',
        command='echo \"Tool: \$OPENCODE_TOOL_NAME\"',
    ))

    executor = HookExecutor(registry=registry)
    event = HookEvent.tool_pre_execute('bash', {'command': 'ls'})

    results = await executor.execute_hooks(event)
    assert 'bash' in results[0].stdout

    print('Environment variables in hook: OK')

asyncio.run(test())
"

# 15. Run all unit tests
pytest tests/unit/hooks/ -v --cov=opencode.hooks --cov-report=term-missing

# Expected: All tests pass, coverage ≥ 90%

# 16. Type checking
mypy src/opencode/hooks/ --strict
# Expected: No errors

# 17. Linting
ruff check src/opencode/hooks/
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

---

## Files to Create

| File | Purpose |
|------|---------|
| `src/opencode/hooks/__init__.py` | Package exports |
| `src/opencode/hooks/events.py` | Event types and data |
| `src/opencode/hooks/registry.py` | Hook registration |
| `src/opencode/hooks/executor.py` | Hook execution |
| `src/opencode/hooks/config.py` | Hook configuration |
| `tests/unit/hooks/__init__.py` | Test package |
| `tests/unit/hooks/test_events.py` | Event tests |
| `tests/unit/hooks/test_registry.py` | Registry tests |
| `tests/unit/hooks/test_executor.py` | Executor tests |
| `tests/unit/hooks/test_config.py` | Config tests |

---

## Dependencies to Verify

No additional dependencies required beyond Python standard library.

---

## Manual Testing Checklist

- [ ] Create hook programmatically
- [ ] Pattern matching works correctly
- [ ] Hook executes shell command
- [ ] Environment variables passed to hook
- [ ] Hook stdout captured
- [ ] Hook stderr captured
- [ ] Timeout kills hung hook
- [ ] Blocking hook prevents operation
- [ ] Configuration file loads correctly
- [ ] Multiple hooks execute in order
- [ ] stop_on_failure stops chain

---

## Integration Points

Phase 4.2 provides the hooks system for:

| Consumer | What It Uses |
|----------|--------------|
| Phase 2.1 (Tools) | ToolExecutor fires hook events |
| Phase 3.1 (OpenRouter) | LLM client fires hook events |
| Phase 5.1 (Sessions) | Session manager fires hook events |
| Phase 6.2 (Modes) | Headless mode hook handling |

---

## Sign-Off

Phase 4.2 is complete when:

1. [ ] All checklist items above are checked
2. [ ] All verification commands pass
3. [ ] All quality gates are met
4. [ ] Manual testing completed
5. [ ] Code has been reviewed (if applicable)
6. [ ] No TODO comments remain in Phase 4.2 code

---

## Next Phase

After completing Phase 4.2, proceed to:
- **Phase 5.1: Session Management**

Phase 5.1 will implement:
- Session model and storage
- Session persistence
- Session resume functionality
- Conversation history management
- Session lifecycle events
