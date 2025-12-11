# Phase 5.1: Session Management - Completion Criteria

**Phase:** 5.1
**Name:** Session Management
**Dependencies:** Phase 3.2 (LangChain Integration), Phase 4.2 (Hooks System)

---

## Definition of Done

All of the following criteria must be met before Phase 5.1 is considered complete.

---

## Checklist

### Session Model (src/forge/sessions/models.py)
- [ ] ToolInvocation dataclass defined
- [ ] ToolInvocation.to_dict() serialization
- [ ] ToolInvocation.from_dict() deserialization
- [ ] SessionMessage dataclass defined
- [ ] SessionMessage supports all roles (system, user, assistant, tool)
- [ ] SessionMessage handles tool_calls and tool_call_id
- [ ] Session dataclass defined with all fields
- [ ] Session.add_message() works correctly
- [ ] Session.add_message_from_dict() convenience method
- [ ] Session.add_tool_invocation() works correctly
- [ ] Session.record_tool_call() convenience method
- [ ] Session.update_usage() updates token counts
- [ ] Session.total_tokens property works
- [ ] Session.message_count property works
- [ ] Session._mark_updated() updates timestamp
- [ ] Session.to_dict() serialization
- [ ] Session.to_json() JSON serialization
- [ ] Session.from_dict() deserialization
- [ ] Session.from_json() JSON deserialization
- [ ] Datetime fields use timezone-aware UTC

### Session Storage (src/forge/sessions/storage.py)
- [ ] SessionStorageError exception class
- [ ] SessionNotFoundError exception class
- [ ] SessionCorruptedError exception class
- [ ] SessionStorage class implemented
- [ ] get_default_dir() returns XDG-compliant path
- [ ] get_project_dir() returns project-local path
- [ ] get_path() returns session file path
- [ ] get_backup_path() returns backup file path
- [ ] exists() checks file existence
- [ ] save() writes session atomically
- [ ] save() creates backup of existing file
- [ ] save() sets secure file permissions
- [ ] load() reads and deserializes session
- [ ] load() raises SessionNotFoundError if missing
- [ ] load() raises SessionCorruptedError if invalid JSON
- [ ] load_or_none() returns None on error
- [ ] delete() removes session and backup files
- [ ] list_session_ids() returns all session IDs
- [ ] recover_from_backup() restores from backup
- [ ] get_storage_size() returns total size
- [ ] cleanup_old_sessions() removes old sessions
- [ ] Storage directory created with 700 permissions
- [ ] Session files created with 600 permissions

### Session Index (src/forge/sessions/index.py)
- [ ] SessionSummary dataclass defined
- [ ] SessionSummary.to_dict() serialization
- [ ] SessionSummary.from_dict() deserialization
- [ ] SessionSummary.from_session() factory method
- [ ] SessionIndex class implemented
- [ ] Index loads from disk on init
- [ ] Index rebuilds if version mismatch
- [ ] Index rebuilds if corrupted
- [ ] add() adds session to index
- [ ] update() updates session in index
- [ ] remove() removes session from index
- [ ] get() returns SessionSummary by ID
- [ ] count() returns session count
- [ ] list() with limit/offset pagination
- [ ] list() with sort_by parameter
- [ ] list() with descending parameter
- [ ] list() with tags filter
- [ ] list() with search filter
- [ ] list() with working_dir filter
- [ ] get_recent() returns most recent sessions
- [ ] get_by_working_dir() filters by directory
- [ ] save_if_dirty() persists changes
- [ ] __len__ returns count
- [ ] __contains__ checks membership

### Session Manager (src/forge/sessions/manager.py)
- [ ] SessionManager class implemented
- [ ] Singleton pattern via get_instance()
- [ ] reset_instance() for testing
- [ ] create() creates new session
- [ ] create() saves to storage immediately
- [ ] create() adds to index
- [ ] create() sets as current_session
- [ ] create() starts auto-save
- [ ] create() fires session:start hook
- [ ] resume() loads session from storage
- [ ] resume() updates access time
- [ ] resume() sets as current_session
- [ ] resume() starts auto-save
- [ ] resume() fires session:start hook
- [ ] resume() raises SessionNotFoundError if missing
- [ ] resume_latest() resumes most recent session
- [ ] resume_latest() returns None if no sessions
- [ ] resume_or_create() resumes or creates
- [ ] save() saves session to storage
- [ ] save() updates index
- [ ] save() fires session:save hook
- [ ] close() saves session
- [ ] close() fires session:end hook
- [ ] close() stops auto-save
- [ ] close() clears current_session
- [ ] delete() removes session
- [ ] delete() updates index
- [ ] delete() stops auto-save if current
- [ ] list_sessions() delegates to index
- [ ] get_session() loads full session
- [ ] add_message() adds to current session
- [ ] add_message() fires session:message hook
- [ ] add_message() raises ValueError if no session
- [ ] record_tool_call() adds invocation
- [ ] update_usage() updates token counts
- [ ] generate_title() creates title from first message
- [ ] generate_title() truncates long titles
- [ ] generate_title() falls back to timestamp
- [ ] set_title() updates session title
- [ ] add_tag() adds tag to session
- [ ] add_tag() prevents duplicates
- [ ] remove_tag() removes tag from session
- [ ] has_current property works
- [ ] register_hook() registers callback
- [ ] unregister_hook() removes callback
- [ ] _fire_hook() calls registered callbacks
- [ ] Hook errors are logged but don't break flow
- [ ] Auto-save runs periodically when interval > 0
- [ ] Auto-save disabled when interval <= 0

### Package Structure
- [ ] src/forge/sessions/__init__.py exports all public classes
- [ ] All imports work correctly
- [ ] No circular dependencies

### Testing
- [ ] Unit tests for ToolInvocation
- [ ] Unit tests for SessionMessage
- [ ] Unit tests for Session
- [ ] Unit tests for Session serialization/deserialization
- [ ] Unit tests for SessionStorage save/load
- [ ] Unit tests for SessionStorage atomic writes
- [ ] Unit tests for SessionStorage backup/recovery
- [ ] Unit tests for SessionIndex
- [ ] Unit tests for SessionIndex filtering
- [ ] Unit tests for SessionIndex pagination
- [ ] Unit tests for SessionManager create/resume
- [ ] Unit tests for SessionManager lifecycle
- [ ] Unit tests for SessionManager hooks
- [ ] Unit tests for auto-save behavior
- [ ] Integration tests for full session lifecycle
- [ ] Test coverage ≥ 90%

---

## Verification Commands

```bash
# 1. Verify module structure
ls -la src/forge/sessions/
# Expected: __init__.py, models.py, storage.py, index.py, manager.py

# 2. Test imports
python -c "
from forge.sessions import (
    Session,
    SessionMessage,
    ToolInvocation,
    SessionStorage,
    SessionStorageError,
    SessionNotFoundError,
    SessionCorruptedError,
    SessionIndex,
    SessionSummary,
    SessionManager,
)
print('All sessions imports successful')
"

# 3. Test Session model
python -c "
from forge.sessions import Session, SessionMessage, ToolInvocation

# Create session
session = Session(title='Test', working_dir='/tmp', model='test-model')
assert session.id is not None
assert session.message_count == 0
assert session.total_tokens == 0

# Add message
session.add_message_from_dict('user', 'Hello')
assert session.message_count == 1

# Add tool invocation
session.record_tool_call('bash', {'command': 'ls'}, result={'output': '...'})
assert len(session.tool_history) == 1

# Update usage
session.update_usage(100, 50)
assert session.total_prompt_tokens == 100
assert session.total_completion_tokens == 50
assert session.total_tokens == 150

print('Session model: OK')
"

# 4. Test Session serialization
python -c "
from forge.sessions import Session
import json

session = Session(title='Test', model='test')
session.add_message_from_dict('user', 'Hello')
session.record_tool_call('read', {'file': 'test.py'})
session.update_usage(100, 50)

# To dict
data = session.to_dict()
assert data['title'] == 'Test'
assert len(data['messages']) == 1
assert len(data['tool_history']) == 1

# To JSON
json_str = session.to_json()
parsed = json.loads(json_str)
assert parsed['id'] == session.id

# From dict
restored = Session.from_dict(data)
assert restored.id == session.id
assert restored.message_count == 1

# From JSON
restored2 = Session.from_json(json_str)
assert restored2.id == session.id

print('Session serialization: OK')
"

# 5. Test SessionStorage
python -c "
import tempfile
from pathlib import Path
from forge.sessions import Session, SessionStorage

with tempfile.TemporaryDirectory() as tmpdir:
    storage = SessionStorage(Path(tmpdir))

    # Save
    session = Session(title='Test')
    storage.save(session)
    assert storage.exists(session.id)

    # Load
    loaded = storage.load(session.id)
    assert loaded.id == session.id
    assert loaded.title == 'Test'

    # List
    ids = storage.list_session_ids()
    assert session.id in ids

    # Delete
    assert storage.delete(session.id)
    assert not storage.exists(session.id)

print('SessionStorage: OK')
"

# 6. Test SessionNotFoundError
python -c "
import tempfile
from pathlib import Path
from forge.sessions import SessionStorage, SessionNotFoundError

with tempfile.TemporaryDirectory() as tmpdir:
    storage = SessionStorage(Path(tmpdir))

    try:
        storage.load('nonexistent-id')
        assert False, 'Should have raised'
    except SessionNotFoundError:
        pass

    result = storage.load_or_none('nonexistent-id')
    assert result is None

print('SessionNotFoundError: OK')
"

# 7. Test SessionIndex
python -c "
import tempfile
from pathlib import Path
from forge.sessions import Session, SessionStorage, SessionIndex

with tempfile.TemporaryDirectory() as tmpdir:
    storage = SessionStorage(Path(tmpdir))
    index = SessionIndex(storage)

    # Create and add sessions
    s1 = Session(title='First', tags=['python'])
    s2 = Session(title='Second', tags=['javascript'])
    s3 = Session(title='Third', tags=['python', 'api'])

    storage.save(s1)
    storage.save(s2)
    storage.save(s3)

    index.add(s1)
    index.add(s2)
    index.add(s3)

    assert index.count() == 3
    assert s1.id in index

    # Filter by tags
    python_sessions = index.list(tags=['python'])
    assert len(python_sessions) == 2

    # Search
    results = index.list(search='First')
    assert len(results) == 1

    # Pagination
    page = index.list(limit=2, offset=0)
    assert len(page) == 2

print('SessionIndex: OK')
"

# 8. Test SessionManager singleton
python -c "
from forge.sessions import SessionManager

SessionManager.reset_instance()
manager1 = SessionManager.get_instance()
manager2 = SessionManager.get_instance()
assert manager1 is manager2

print('SessionManager singleton: OK')
"

# 9. Test SessionManager create/resume
python -c "
import tempfile
from pathlib import Path
from forge.sessions import SessionStorage, SessionManager

with tempfile.TemporaryDirectory() as tmpdir:
    storage = SessionStorage(Path(tmpdir))

    SessionManager.reset_instance()
    manager = SessionManager(storage=storage, auto_save_interval=0)

    # Create
    session = manager.create(title='Test', model='test-model')
    assert manager.has_current
    assert manager.current_session.id == session.id

    session_id = session.id
    manager.close()
    assert not manager.has_current

    # Resume
    resumed = manager.resume(session_id)
    assert resumed.id == session_id
    assert manager.has_current

    manager.close()

print('SessionManager create/resume: OK')
"

# 10. Test SessionManager add_message
python -c "
import tempfile
from pathlib import Path
from forge.sessions import SessionStorage, SessionManager

with tempfile.TemporaryDirectory() as tmpdir:
    storage = SessionStorage(Path(tmpdir))

    SessionManager.reset_instance()
    manager = SessionManager(storage=storage, auto_save_interval=0)

    session = manager.create()

    manager.add_message('user', 'Hello')
    manager.add_message('assistant', 'Hi there!')

    assert session.message_count == 2

    manager.close()

print('SessionManager add_message: OK')
"

# 11. Test SessionManager hooks
python -c "
import tempfile
from pathlib import Path
from forge.sessions import SessionStorage, SessionManager

with tempfile.TemporaryDirectory() as tmpdir:
    storage = SessionStorage(Path(tmpdir))

    SessionManager.reset_instance()
    manager = SessionManager(storage=storage, auto_save_interval=0)

    events = []

    def on_start(session):
        events.append(('start', session.id))

    def on_end(session):
        events.append(('end', session.id))

    manager.register_hook('session:start', on_start)
    manager.register_hook('session:end', on_end)

    session = manager.create()
    manager.close()

    assert len(events) == 2
    assert events[0][0] == 'start'
    assert events[1][0] == 'end'

print('SessionManager hooks: OK')
"

# 12. Test generate_title
python -c "
import tempfile
from pathlib import Path
from forge.sessions import SessionStorage, SessionManager

with tempfile.TemporaryDirectory() as tmpdir:
    storage = SessionStorage(Path(tmpdir))

    SessionManager.reset_instance()
    manager = SessionManager(storage=storage, auto_save_interval=0)

    session = manager.create()
    manager.add_message('user', 'Help me refactor the API client')

    title = manager.generate_title(session)
    assert title == 'Help me refactor the API client'

    # Long title truncation
    session2 = manager.create()
    long_msg = 'x' * 100
    manager.add_message('user', long_msg)
    title2 = manager.generate_title(session2)
    assert len(title2) <= 50

    manager.close()

print('generate_title: OK')
"

# 13. Test list_sessions
python -c "
import tempfile
from pathlib import Path
from forge.sessions import SessionStorage, SessionManager

with tempfile.TemporaryDirectory() as tmpdir:
    storage = SessionStorage(Path(tmpdir))

    SessionManager.reset_instance()
    manager = SessionManager(storage=storage, auto_save_interval=0)

    # Create multiple sessions
    for i in range(5):
        session = manager.create(title=f'Session {i}')
        manager.close()

    # List all
    sessions = manager.list_sessions()
    assert len(sessions) == 5

    # Limit
    limited = manager.list_sessions(limit=3)
    assert len(limited) == 3

print('list_sessions: OK')
"

# 14. Run all unit tests
pytest tests/unit/sessions/ -v --cov=forge.sessions --cov-report=term-missing

# Expected: All tests pass, coverage ≥ 90%

# 15. Type checking
mypy src/forge/sessions/ --strict
# Expected: No errors

# 16. Linting
ruff check src/forge/sessions/
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
| `src/forge/sessions/__init__.py` | Package exports |
| `src/forge/sessions/models.py` | Session data models |
| `src/forge/sessions/storage.py` | Session persistence |
| `src/forge/sessions/index.py` | Session index |
| `src/forge/sessions/manager.py` | Session lifecycle |
| `tests/unit/sessions/__init__.py` | Test package |
| `tests/unit/sessions/test_models.py` | Model tests |
| `tests/unit/sessions/test_storage.py` | Storage tests |
| `tests/unit/sessions/test_index.py` | Index tests |
| `tests/unit/sessions/test_manager.py` | Manager tests |

---

## Dependencies to Verify

No additional dependencies required beyond Python standard library.

---

## Performance Requirements

| Operation | Target |
|-----------|--------|
| Session load | < 100ms for typical session |
| Session save | < 50ms |
| List sessions | < 500ms for 1000 sessions |
| Index lookup | O(1) |

---

## Manual Testing Checklist

- [ ] Create session programmatically
- [ ] Add messages to session
- [ ] Record tool invocations
- [ ] Update token usage
- [ ] Save session to disk
- [ ] Load session from disk
- [ ] Resume session by ID
- [ ] Resume latest session
- [ ] Delete session
- [ ] List sessions with pagination
- [ ] Filter sessions by tags
- [ ] Search sessions by title
- [ ] Auto-save fires periodically
- [ ] Session hooks fire correctly
- [ ] Atomic save prevents corruption
- [ ] Backup recovery works
- [ ] Secure file permissions set
- [ ] Index rebuilds correctly

---

## Integration Points

Phase 5.1 provides session management for:

| Consumer | What It Uses |
|----------|--------------|
| Phase 3.2 (LangChain) | Session backs ConversationMemory |
| Phase 4.2 (Hooks) | Session fires hook events |
| Phase 5.2 (Context) | Session provides messages |
| Phase 6.1 (Commands) | /session slash command |
| Phase 1.3 (REPL) | --resume CLI flag |

---

## Sign-Off

Phase 5.1 is complete when:

1. [ ] All checklist items above are checked
2. [ ] All verification commands pass
3. [ ] All quality gates are met
4. [ ] Performance requirements met
5. [ ] Manual testing completed
6. [ ] Code has been reviewed (if applicable)
7. [ ] No TODO comments remain in Phase 5.1 code

---

## Next Phase

After completing Phase 5.1, proceed to:
- **Phase 5.2: Context Management**

Phase 5.2 will implement:
- Token counting and tracking
- Context window management
- Message truncation strategies
- Context compaction algorithms
- Token budget allocation
