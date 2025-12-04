# Phase 5.1: Session Management - Gherkin Specifications

**Phase:** 5.1
**Name:** Session Management
**Dependencies:** Phase 3.2 (LangChain Integration), Phase 4.2 (Hooks System)

---

## Feature: Session Model

### Scenario: Create a new session
```gherkin
Given I need to create a new session
When I instantiate a Session
Then it should have a unique UUID id
And it should have created_at set to now
And it should have updated_at set to now
And it should have empty messages list
And it should have empty tool_history list
And it should have zero token counts
```

### Scenario: Add message to session
```gherkin
Given a Session exists
When I call session.add_message_from_dict("user", "Hello")
Then the session should have 1 message
And the message role should be "user"
And the message content should be "Hello"
And the session updated_at should be updated
```

### Scenario: Add tool invocation to session
```gherkin
Given a Session exists
When I call session.record_tool_call("bash", {"command": "ls"}, result={"output": "..."})
Then the session should have 1 tool invocation
And the invocation tool_name should be "bash"
And the invocation should have a timestamp
```

### Scenario: Update token usage
```gherkin
Given a Session with 100 prompt tokens and 50 completion tokens
When I call session.update_usage(200, 100)
Then total_prompt_tokens should be 300
And total_completion_tokens should be 150
And total_tokens should be 450
```

### Scenario: Serialize session to dict
```gherkin
Given a Session with messages and tool history
When I call session.to_dict()
Then the result should contain "id", "title", "created_at"
And the result should contain "messages" as a list
And the result should contain "tool_history" as a list
And dates should be ISO format strings
```

### Scenario: Deserialize session from dict
```gherkin
Given a valid session dictionary
When I call Session.from_dict(data)
Then I should get a Session object
And all fields should be restored correctly
And datetime strings should be parsed to datetime objects
```

### Scenario: Serialize session to JSON
```gherkin
Given a Session
When I call session.to_json()
Then the result should be a valid JSON string
And it should contain all session fields
```

---

## Feature: Session Message

### Scenario: Create session message
```gherkin
Given I need to create a message
When I instantiate SessionMessage(role="user", content="test")
Then it should have a unique id
And it should have timestamp set to now
```

### Scenario: Message with tool calls
```gherkin
Given I need to create an assistant message with tool calls
When I create SessionMessage with tool_calls=[{"id": "1", "name": "bash"}]
Then to_dict() should include the tool_calls field
```

### Scenario: Tool result message
```gherkin
Given I need to create a tool result message
When I create SessionMessage(role="tool", content="result", tool_call_id="abc")
Then to_dict() should include tool_call_id
```

---

## Feature: Tool Invocation

### Scenario: Create tool invocation
```gherkin
Given I need to record a tool call
When I instantiate ToolInvocation(tool_name="read", arguments={"file": "test.py"})
Then it should have a unique id
And it should have success=True by default
And timestamp should be set to now
```

### Scenario: Record failed tool invocation
```gherkin
Given I need to record a failed tool call
When I create ToolInvocation with success=False and error="File not found"
Then to_dict() should contain error message
And success should be False
```

### Scenario: Serialize tool invocation
```gherkin
Given a ToolInvocation with result
When I call invocation.to_dict()
Then the result should contain all fields
And timestamp should be ISO format string
```

---

## Feature: Session Storage

### Scenario: Get default storage directory
```gherkin
Given no custom storage directory
When I call SessionStorage.get_default_dir()
Then it should return ~/.local/share/src/opencode/sessions/
```

### Scenario: Create storage directory
```gherkin
Given a SessionStorage with non-existent directory
When the storage is initialized
Then the directory should be created
And it should have secure permissions (700)
```

### Scenario: Save session
```gherkin
Given a SessionStorage and a Session
When I call storage.save(session)
Then a JSON file should be created
And the file should be named {session_id}.json
And the file should have secure permissions (600)
```

### Scenario: Atomic save with backup
```gherkin
Given a SessionStorage with an existing session file
When I call storage.save(session) with updated data
Then a backup file should be created
And the new data should be written atomically
```

### Scenario: Load session
```gherkin
Given a SessionStorage with a saved session
When I call storage.load(session_id)
Then I should get the Session object
And all data should be correctly deserialized
```

### Scenario: Load non-existent session
```gherkin
Given a SessionStorage
When I call storage.load("nonexistent-id")
Then SessionNotFoundError should be raised
```

### Scenario: Load corrupted session
```gherkin
Given a SessionStorage with a corrupted session file
When I call storage.load(session_id)
Then SessionCorruptedError should be raised
```

### Scenario: Load or none
```gherkin
Given a SessionStorage
When I call storage.load_or_none("nonexistent-id")
Then it should return None
And no exception should be raised
```

### Scenario: Delete session
```gherkin
Given a SessionStorage with a saved session
When I call storage.delete(session_id)
Then the file should be removed
And the backup file should be removed
And it should return True
```

### Scenario: List session IDs
```gherkin
Given a SessionStorage with 3 saved sessions
When I call storage.list_session_ids()
Then I should get a list of 3 session IDs
```

### Scenario: Recover from backup
```gherkin
Given a session with a backup file
When I call storage.recover_from_backup(session_id)
Then the backup should be copied to the main file
And it should return True
```

---

## Feature: Session Index

### Scenario: Create index
```gherkin
Given a SessionStorage with sessions
When I create a SessionIndex
Then it should load existing index
Or rebuild from session files
```

### Scenario: Add session to index
```gherkin
Given a SessionIndex
When I call index.add(session)
Then the session summary should be in the index
And the index should be marked dirty
```

### Scenario: Remove session from index
```gherkin
Given a SessionIndex with a session
When I call index.remove(session_id)
Then the session should no longer be in the index
And it should return True
```

### Scenario: Get session summary
```gherkin
Given a SessionIndex with sessions
When I call index.get(session_id)
Then I should get a SessionSummary
And it should contain id, title, message_count, etc.
```

### Scenario: List sessions with default sorting
```gherkin
Given a SessionIndex with multiple sessions
When I call index.list()
Then sessions should be sorted by updated_at descending
And it should return up to 50 sessions
```

### Scenario: List sessions with pagination
```gherkin
Given a SessionIndex with 100 sessions
When I call index.list(limit=10, offset=20)
Then I should get sessions 21-30
```

### Scenario: List sessions filtered by tags
```gherkin
Given sessions with tags ["python"], ["python", "api"], ["javascript"]
When I call index.list(tags=["python"])
Then I should get 2 sessions
```

### Scenario: List sessions with search
```gherkin
Given sessions with titles containing "refactor" and "implement"
When I call index.list(search="refactor")
Then I should get only sessions with "refactor" in title
```

### Scenario: Rebuild index
```gherkin
Given an empty or corrupted index
When I call index.rebuild()
Then the index should be populated from session files
And the index file should be saved
```

---

## Feature: Session Manager

### Scenario: Get singleton instance
```gherkin
Given no existing SessionManager instance
When I call SessionManager.get_instance() twice
Then both calls should return the same instance
```

### Scenario: Create new session
```gherkin
Given a SessionManager
When I call manager.create(title="Test", model="gpt-4")
Then a new Session should be created
And it should be saved to storage
And it should be added to the index
And it should be set as current_session
And session:start hook should be fired
```

### Scenario: Create session with auto-generated working directory
```gherkin
Given a SessionManager
When I call manager.create() without working_dir
Then working_dir should be set to current directory
```

### Scenario: Resume session
```gherkin
Given a SessionManager with a saved session
When I call manager.resume(session_id)
Then the Session should be loaded
And updated_at should be refreshed
And it should be set as current_session
And session:start hook should be fired
```

### Scenario: Resume non-existent session
```gherkin
Given a SessionManager
When I call manager.resume("nonexistent-id")
Then SessionNotFoundError should be raised
```

### Scenario: Resume latest session
```gherkin
Given a SessionManager with multiple sessions
When I call manager.resume_latest()
Then the most recently updated session should be loaded
```

### Scenario: Resume latest with no sessions
```gherkin
Given a SessionManager with no sessions
When I call manager.resume_latest()
Then it should return None
```

### Scenario: Resume or create
```gherkin
Given a SessionManager with sessions
When I call manager.resume_or_create()
Then it should resume the latest session

Given a SessionManager with no sessions
When I call manager.resume_or_create()
Then it should create a new session
```

### Scenario: Save session
```gherkin
Given a SessionManager with a current session
When I call manager.save()
Then the session should be saved to storage
And the index should be updated
And session:save hook should be fired
```

### Scenario: Close session
```gherkin
Given a SessionManager with a current session
When I call manager.close()
Then the session should be saved
And session:end hook should be fired
And auto-save should be stopped
And current_session should be None
```

### Scenario: Delete session
```gherkin
Given a SessionManager with a saved session
When I call manager.delete(session_id)
Then the session should be removed from storage
And the session should be removed from index
And it should return True
```

### Scenario: Delete current session
```gherkin
Given a SessionManager with current_session
When I call manager.delete(current_session.id)
Then auto-save should be stopped
And current_session should be None
And the session should be deleted
```

### Scenario: List sessions
```gherkin
Given a SessionManager with sessions
When I call manager.list_sessions(limit=10, sort_by="title")
Then I should get up to 10 SessionSummary objects
And they should be sorted by title
```

### Scenario: Add message to current session
```gherkin
Given a SessionManager with a current session
When I call manager.add_message("user", "Hello")
Then a message should be added to current_session
And session:message hook should be fired
```

### Scenario: Add message without current session
```gherkin
Given a SessionManager with no current session
When I call manager.add_message("user", "Hello")
Then ValueError should be raised
```

### Scenario: Record tool call
```gherkin
Given a SessionManager with a current session
When I call manager.record_tool_call("bash", {"command": "ls"}, result={...})
Then a ToolInvocation should be added to current_session
```

### Scenario: Update token usage
```gherkin
Given a SessionManager with a current session
When I call manager.update_usage(100, 50)
Then current_session token counts should be updated
```

### Scenario: Generate title
```gherkin
Given a Session with first user message "Help me refactor the API client"
When I call manager.generate_title(session)
Then it should return "Help me refactor the API client"

Given a Session with long first message
When I call manager.generate_title(session)
Then the title should be truncated to 50 characters

Given a Session with no user messages
When I call manager.generate_title(session)
Then it should return "Session YYYY-MM-DD HH:MM"
```

### Scenario: Set title
```gherkin
Given a SessionManager with a current session
When I call manager.set_title("New Title")
Then current_session.title should be "New Title"
And updated_at should be refreshed
```

### Scenario: Add tag
```gherkin
Given a SessionManager with a current session
When I call manager.add_tag("python")
Then "python" should be in current_session.tags
And updated_at should be refreshed
```

### Scenario: Add duplicate tag
```gherkin
Given a Session with tag "python"
When I call manager.add_tag("python")
Then session.tags should still have only one "python"
```

### Scenario: Remove tag
```gherkin
Given a Session with tag "python"
When I call manager.remove_tag("python")
Then "python" should not be in session.tags
And it should return True
```

---

## Feature: Auto-Save

### Scenario: Auto-save starts on session create
```gherkin
Given a SessionManager with auto_save_interval=60
When I call manager.create()
Then auto-save task should be started
```

### Scenario: Auto-save runs periodically
```gherkin
Given a SessionManager with auto_save_interval=1.0
And a current session with changes
When 1 second passes
Then the session should be auto-saved
```

### Scenario: Auto-save stops on close
```gherkin
Given a SessionManager with running auto-save
When I call manager.close()
Then auto-save task should be cancelled
```

### Scenario: Disabled auto-save
```gherkin
Given a SessionManager with auto_save_interval=0
When I call manager.create()
Then no auto-save task should be started
```

---

## Feature: Session Hooks

### Scenario: Register session hook
```gherkin
Given a SessionManager
When I call manager.register_hook("session:start", callback)
Then the callback should be registered for session:start
```

### Scenario: Hooks fire on session start
```gherkin
Given a registered hook for "session:start"
When I call manager.create() or manager.resume()
Then the hook callback should be called with session
```

### Scenario: Hooks fire on session end
```gherkin
Given a registered hook for "session:end"
When I call manager.close()
Then the hook callback should be called with session
```

### Scenario: Hooks fire on message add
```gherkin
Given a registered hook for "session:message"
When I call manager.add_message()
Then the hook callback should be called with session and message
```

### Scenario: Hooks fire on save
```gherkin
Given a registered hook for "session:save"
When I call manager.save()
Then the hook callback should be called with session
```

### Scenario: Unregister hook
```gherkin
Given a registered hook for "session:start"
When I call manager.unregister_hook("session:start", callback)
Then the callback should be removed
And it should return True
```

### Scenario: Hook error handling
```gherkin
Given a hook that raises an exception
When the hook is fired
Then the error should be logged
And other hooks should still execute
And the main operation should not fail
```

---

## Feature: Session Summary

### Scenario: Create summary from session
```gherkin
Given a Session with messages and tool history
When I call SessionSummary.from_session(session)
Then the summary should contain session id
And the summary should contain message_count
And the summary should contain total_tokens
And the summary should NOT contain full messages
```

### Scenario: Serialize summary
```gherkin
Given a SessionSummary
When I call summary.to_dict()
Then it should contain all summary fields
And datetime should be ISO format
```

---

## Feature: Storage Cleanup

### Scenario: Cleanup old sessions
```gherkin
Given sessions with various ages
When I call storage.cleanup_old_sessions(max_age_days=30, keep_minimum=10)
Then sessions older than 30 days should be deleted
But at least 10 most recent sessions should be kept
```

### Scenario: Get storage size
```gherkin
Given a SessionStorage with session files
When I call storage.get_storage_size()
Then it should return total size in bytes
```

---

## Feature: Project-Local Sessions

### Scenario: Get project session directory
```gherkin
Given a project root path
When I call SessionStorage.get_project_dir(project_root)
Then it should return {project_root}/.src/opencode/sessions/
```

### Scenario: Use project-local storage
```gherkin
Given a SessionStorage with project directory
When I save and load sessions
Then they should be stored in the project directory
```
