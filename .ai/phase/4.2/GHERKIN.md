# Phase 4.2: Hooks System - Gherkin Specifications

**Phase:** 4.2
**Name:** Hooks System
**Dependencies:** Phase 2.1 (Tool System Foundation), Phase 4.1 (Permission System)

---

## Feature: Event Types

### Scenario: Tool event types defined
```gherkin
Given the EventType enum
Then it should include "tool:pre_execute"
And it should include "tool:post_execute"
And it should include "tool:error"
```

### Scenario: LLM event types defined
```gherkin
Given the EventType enum
Then it should include "llm:pre_request"
And it should include "llm:post_response"
And it should include "llm:stream_start"
And it should include "llm:stream_end"
```

### Scenario: Session event types defined
```gherkin
Given the EventType enum
Then it should include "session:start"
And it should include "session:end"
And it should include "session:message"
```

### Scenario: Permission event types defined
```gherkin
Given the EventType enum
Then it should include "permission:check"
And it should include "permission:prompt"
And it should include "permission:granted"
And it should include "permission:denied"
```

### Scenario: User event types defined
```gherkin
Given the EventType enum
Then it should include "user:prompt_submit"
And it should include "user:interrupt"
```

---

## Feature: Hook Events

### Scenario: Create tool pre-execute event
```gherkin
Given I need to create a tool pre-execute event
When I call HookEvent.tool_pre_execute("bash", {"command": "ls"})
Then the event type should be "tool:pre_execute"
And the tool_name should be "bash"
And the data should contain "tool_args"
```

### Scenario: Create tool post-execute event
```gherkin
Given I need to create a tool post-execute event
When I call HookEvent.tool_post_execute("bash", {"command": "ls"}, {"success": true})
Then the event type should be "tool:post_execute"
And the data should contain "tool_args"
And the data should contain "tool_result"
```

### Scenario: Create tool error event
```gherkin
Given I need to create a tool error event
When I call HookEvent.tool_error("bash", {"command": "ls"}, "Command failed")
Then the event type should be "tool:error"
And the data should contain "error"
```

### Scenario: Convert event to environment variables
```gherkin
Given a HookEvent for tool:pre_execute with tool "bash"
When I call event.to_env()
Then the result should contain "OPENCODE_EVENT" = "tool:pre_execute"
And the result should contain "OPENCODE_TOOL_NAME" = "bash"
And the result should contain "OPENCODE_TOOL_ARGS" as JSON
```

### Scenario: Serialize event to JSON
```gherkin
Given a HookEvent with type and data
When I call event.to_json()
Then the result should be valid JSON
And it should contain "type", "timestamp", "data"
```

---

## Feature: Hook Pattern Matching

### Scenario: Exact event match
```gherkin
Given a Hook with event_pattern "tool:pre_execute"
And a HookEvent with type "tool:pre_execute"
When I call hook.matches(event)
Then the result should be True
```

### Scenario: Exact match fails for different event
```gherkin
Given a Hook with event_pattern "tool:pre_execute"
And a HookEvent with type "tool:post_execute"
When I call hook.matches(event)
Then the result should be False
```

### Scenario: Wildcard matches all in category
```gherkin
Given a Hook with event_pattern "tool:*"
And a HookEvent with type "tool:pre_execute"
When I call hook.matches(event)
Then the result should be True

When I test with type "tool:post_execute"
Then the result should be True

When I test with type "llm:pre_request"
Then the result should be False
```

### Scenario: Tool-specific pattern
```gherkin
Given a Hook with event_pattern "tool:pre_execute:bash"
And a HookEvent with type "tool:pre_execute" and tool_name "bash"
When I call hook.matches(event)
Then the result should be True

When I test with tool_name "read"
Then the result should be False
```

### Scenario: Multiple patterns (comma-separated)
```gherkin
Given a Hook with event_pattern "session:start,session:end"
When I test with event type "session:start"
Then it should match

When I test with event type "session:end"
Then it should match

When I test with event type "session:message"
Then it should not match
```

### Scenario: Catch-all pattern
```gherkin
Given a Hook with event_pattern "*"
When I test with any event type
Then it should always match
```

---

## Feature: Hook Registry

### Scenario: Register a hook
```gherkin
Given an empty HookRegistry
When I register a Hook with pattern "tool:pre_execute"
Then the registry should contain 1 hook
```

### Scenario: Get matching hooks
```gherkin
Given a HookRegistry with hooks:
  | pattern          |
  | tool:pre_execute |
  | tool:*           |
  | llm:pre_request  |
When I call get_hooks() with a tool:pre_execute event
Then I should get 2 hooks (tool:pre_execute and tool:*)
```

### Scenario: Disabled hooks not returned
```gherkin
Given a HookRegistry with a disabled Hook for "tool:pre_execute"
When I call get_hooks() with a tool:pre_execute event
Then I should get 0 hooks
```

### Scenario: Unregister a hook
```gherkin
Given a HookRegistry with a Hook for "tool:pre_execute"
When I call unregister("tool:pre_execute")
Then the result should be True
And the registry should be empty
```

### Scenario: Clear all hooks
```gherkin
Given a HookRegistry with multiple hooks
When I call clear()
Then the registry should be empty
```

### Scenario: Singleton instance
```gherkin
Given no existing HookRegistry instance
When I call HookRegistry.get_instance() twice
Then both calls should return the same instance
```

---

## Feature: Hook Execution

### Scenario: Execute successful hook
```gherkin
Given a Hook with command "echo 'hello'"
And an event to trigger it
When I execute the hook
Then the result exit_code should be 0
And the result stdout should contain "hello"
And the result success should be True
```

### Scenario: Execute failing hook
```gherkin
Given a Hook with command "exit 1"
And an event to trigger it
When I execute the hook
Then the result exit_code should be 1
And the result success should be False
And the result should_continue should be False
```

### Scenario: Hook receives environment variables
```gherkin
Given a Hook with command "echo $OPENCODE_TOOL_NAME"
And an event with tool_name "bash"
When I execute the hook
Then the stdout should contain "bash"
```

### Scenario: Hook timeout
```gherkin
Given a Hook with command "sleep 10" and timeout 1.0
When I execute the hook
Then the result timed_out should be True
And the process should be killed
```

### Scenario: Execute multiple hooks
```gherkin
Given a HookRegistry with 3 matching hooks
When I call execute_hooks(event)
Then I should get 3 HookResults
```

### Scenario: Stop on first failure
```gherkin
Given a HookRegistry with hooks:
  | pattern          | command    |
  | tool:pre_execute | echo ok    |
  | tool:pre_execute | exit 1     |
  | tool:pre_execute | echo after |
When I call execute_hooks(event, stop_on_failure=True)
Then I should get 2 results
And the third hook should not execute
```

### Scenario: Continue after failure
```gherkin
Given a HookRegistry with hooks:
  | pattern          | command    |
  | tool:pre_execute | echo ok    |
  | tool:pre_execute | exit 1     |
  | tool:pre_execute | echo after |
When I call execute_hooks(event, stop_on_failure=False)
Then I should get 3 results
And all hooks should execute
```

---

## Feature: Blocking Hooks

### Scenario: Pre-execute hook blocks operation
```gherkin
Given a Hook with pattern "tool:pre_execute" and command "exit 1"
When I fire a tool:pre_execute event
Then the hook result should_continue should be False
And the tool executor should raise HookBlockedError
```

### Scenario: Pre-execute hook allows operation
```gherkin
Given a Hook with pattern "tool:pre_execute" and command "exit 0"
When I fire a tool:pre_execute event
Then the hook result should_continue should be True
And the tool executor should proceed with execution
```

### Scenario: Hook can output blocking reason
```gherkin
Given a Hook with command:
  """
  echo "Blocked: dangerous command detected"
  exit 1
  """
When the hook blocks execution
Then the HookBlockedError should contain the stdout message
```

---

## Feature: Hook Configuration

### Scenario: Load global hooks
```gherkin
Given a global hooks.json file with 2 hooks
When I call HookConfig.load_global()
Then I should get 2 Hook objects
```

### Scenario: Load project hooks
```gherkin
Given a project with .src/opencode/hooks.json containing 1 hook
When I call HookConfig.load_project(project_root)
Then I should get 1 Hook object
```

### Scenario: Load all hooks
```gherkin
Given 2 global hooks and 1 project hook
When I call HookConfig.load_all(project_root)
Then I should get 3 Hook objects
```

### Scenario: Save hooks
```gherkin
Given a list of Hook objects
When I call HookConfig.save_global(hooks)
Then the hooks should be persisted to JSON
And load_global() should return the same hooks
```

### Scenario: Handle missing config file
```gherkin
Given no hooks.json file exists
When I call HookConfig.load_global()
Then I should get an empty list (or defaults)
And no error should be raised
```

### Scenario: Handle corrupted config file
```gherkin
Given a hooks.json file with invalid JSON
When I call HookConfig.load_global()
Then I should get default hooks
And a warning should be logged
```

---

## Feature: Hook Serialization

### Scenario: Serialize hook to dict
```gherkin
Given a Hook with:
  | event_pattern | tool:pre_execute        |
  | command       | echo hello              |
  | timeout       | 5.0                     |
  | description   | Test hook               |
When I call hook.to_dict()
Then the result should contain:
  | key         | value            |
  | event       | tool:pre_execute |
  | command     | echo hello       |
  | timeout     | 5.0              |
  | description | Test hook        |
```

### Scenario: Deserialize hook from dict
```gherkin
Given a dictionary with hook data:
  """json
  {
    "event": "tool:pre_execute",
    "command": "echo hello",
    "timeout": 5.0
  }
  """
When I call Hook.from_dict(data)
Then I should get a Hook object
And the event_pattern should be "tool:pre_execute"
And the timeout should be 5.0
```

### Scenario: Default values when deserializing
```gherkin
Given a minimal hook dictionary:
  """json
  {
    "event": "tool:*",
    "command": "true"
  }
  """
When I call Hook.from_dict(data)
Then the timeout should be 10.0 (default)
And enabled should be True
```

---

## Feature: Integration with Tool Executor

### Scenario: Tool executor fires pre-execute hook
```gherkin
Given a registered hook for "tool:pre_execute"
When I execute a tool
Then the hook should receive the event
And the event should contain tool_name and tool_args
```

### Scenario: Tool executor fires post-execute hook
```gherkin
Given a registered hook for "tool:post_execute"
When I execute a tool successfully
Then the hook should receive the event
And the event should contain tool_result
```

### Scenario: Tool executor fires error hook
```gherkin
Given a registered hook for "tool:error"
When a tool execution fails
Then the hook should receive the error event
And the event should contain the error message
```

### Scenario: Pre-execute hook blocks tool
```gherkin
Given a blocking hook for "tool:pre_execute:bash"
When I try to execute the bash tool
Then HookBlockedError should be raised
And the tool should not execute
```

---

## Feature: Environment Variables in Hooks

### Scenario: Tool args available as JSON
```gherkin
Given a hook with command that uses $OPENCODE_TOOL_ARGS
And tool arguments {"file": "/tmp/test", "content": "hello"}
When the hook executes
Then OPENCODE_TOOL_ARGS should be valid JSON
And it should contain the file and content keys
```

### Scenario: Working directory set
```gherkin
Given a hook with no explicit working_dir
When the hook executes
Then OPENCODE_WORKING_DIR should be set
And the process should run in that directory
```

### Scenario: Session ID available
```gherkin
Given a hook that uses $OPENCODE_SESSION_ID
And an event with session_id "sess_123"
When the hook executes
Then OPENCODE_SESSION_ID should be "sess_123"
```

---

## Feature: Hook Templates

### Scenario: Log all events template
```gherkin
Given the HOOK_TEMPLATES dictionary
When I access HOOK_TEMPLATES["log_all"]
Then I should get a Hook that matches "*"
And it should log to a file
```

### Scenario: Git auto-commit template
```gherkin
Given the HOOK_TEMPLATES dictionary
When I access HOOK_TEMPLATES["git_auto_commit"]
Then I should get a Hook for "tool:post_execute:write"
And it should run git commit
```

### Scenario: Block sudo template
```gherkin
Given the HOOK_TEMPLATES dictionary
When I access HOOK_TEMPLATES["block_sudo"]
Then I should get a Hook for "tool:pre_execute:bash"
And it should exit 1 for sudo commands
```

---

## Feature: Fire Event Convenience Function

### Scenario: Fire event with default executor
```gherkin
Given registered hooks
When I call fire_event(event)
Then hooks should execute
And I should get results
```

### Scenario: Fire event with custom executor
```gherkin
Given a custom HookExecutor
When I call fire_event(event, executor=custom)
Then it should use the custom executor
```
