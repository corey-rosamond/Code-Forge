# Phase 10.2: Polish and Integration Testing - Gherkin Specifications

**Phase:** 10.2
**Name:** Polish and Integration Testing
**Dependencies:** All previous phases (1.1 - 10.1)

---

## Feature: Tool Execution Integration

### Scenario: Read file through full pipeline
```gherkin
Given the OpenCode application is initialized
And a file "sample.py" exists with content
When the Read tool is executed with file_path="sample.py"
Then the tool execution should succeed
And the output should contain the file content
And the session should record the tool result
```

### Scenario: Edit file with permission check
```gherkin
Given the OpenCode application is initialized
And permissions are set to auto-approve
And a file "sample.py" contains "old_text"
When the Edit tool is executed
  | file_path  | sample.py |
  | old_string | old_text  |
  | new_string | new_text  |
Then the tool execution should succeed
And the file should contain "new_text"
And the file should not contain "old_text"
```

### Scenario: Bash tool with hooks
```gherkin
Given the OpenCode application is initialized
And a hook is registered for "before_tool_execute"
When the Bash tool is executed with command="echo test"
Then the before hook should be called
And the tool execution should succeed
And the output should contain "test"
```

### Scenario: Glob search finds files
```gherkin
Given the OpenCode application is initialized
And the following files exist:
  | file1.py           |
  | file2.py           |
  | subdir/file3.py    |
  | readme.txt         |
When the Glob tool is executed with pattern="**/*.py"
Then the tool execution should succeed
And the output should contain "file1.py"
And the output should contain "file2.py"
And the output should contain "file3.py"
And the output should not contain "readme.txt"
```

### Scenario: Grep search finds content
```gherkin
Given the OpenCode application is initialized
And a file "code.py" contains "def my_function():"
When the Grep tool is executed
  | pattern | def.*\( |
  | path    | code.py |
Then the tool execution should succeed
And the output should contain "my_function"
```

---

## Feature: Tool Permission Integration

### Scenario: Read allowed by default
```gherkin
Given the OpenCode application is initialized
And default permission settings are active
When the Read tool is executed on any file
Then permission should be granted automatically
And the tool should execute successfully
```

### Scenario: Write requires permission
```gherkin
Given the OpenCode application is initialized
And permissions are not auto-approved
When the Write tool is executed
Then permission should be required
And the tool should wait for approval
```

### Scenario: Bash respects allowlist
```gherkin
Given the OpenCode application is initialized
And Bash allowlist contains "echo:*"
When the Bash tool is executed with command="echo hello"
Then permission should be granted automatically
And the tool should execute successfully
```

### Scenario: Dangerous command blocked
```gherkin
Given the OpenCode application is initialized
And default security settings are active
When the Bash tool is executed with command="rm -rf /"
Then the tool execution should be blocked
And an error message should be shown
```

---

## Feature: Session Flow Integration

### Scenario: Create, save, and resume session
```gherkin
Given the OpenCode application is initialized
When a new session is created
And messages are added to the session
And the session is saved
And the session is closed
And the session is resumed by ID
Then the resumed session should contain all messages
And the session ID should match
```

### Scenario: Context compaction triggers automatically
```gherkin
Given the OpenCode application is initialized
And a session is active
When 100 long messages are added
Then context compaction should be triggered
And the token count should be within limits
And older messages should be summarized
```

### Scenario: Session includes system prompt
```gherkin
Given the OpenCode application is initialized
When a new session is created
And the context is retrieved
Then the context should include a system message
And the system message should be first
```

### Scenario: File mentions are tracked
```gherkin
Given the OpenCode application is initialized
And a session is active
When a message mentions "src/main.py"
Then the file mention should be recorded
And get_file_mentions should include "main.py"
```

### Scenario: Session listing works
```gherkin
Given the OpenCode application is initialized
And 3 sessions are created with titles
When list_sessions is called
Then 3 sessions should be returned
And each should have its title
```

### Scenario: Session deletion works
```gherkin
Given the OpenCode application is initialized
And a session exists
When the session is deleted
Then the session should not be in the list
And resume should fail for that ID
```

---

## Feature: Agent Workflow Integration

### Scenario: Explore agent uses file tools
```gherkin
Given the OpenCode application is initialized
And Python files exist in the project
When an explore agent is spawned with prompt="Find Python files"
Then the agent should use Glob or Grep tools
And the agent should return file information
```

### Scenario: Plan agent creates implementation plan
```gherkin
Given the OpenCode application is initialized
When a plan agent is spawned with prompt="Plan feature implementation"
Then the agent should return a structured plan
And the plan should contain steps
```

### Scenario: Agent inherits session context
```gherkin
Given the OpenCode application is initialized
And a session has context about "authentication"
When an agent is spawned with that session
Then the agent should have access to the context
And the agent response should be context-aware
```

### Scenario: Agent respects timeout
```gherkin
Given the OpenCode application is initialized
And a slow operation is mocked
When an agent is spawned with timeout=100ms
Then a TimeoutError should be raised
And the system should remain responsive
```

---

## Feature: Git Workflow Integration

### Scenario: Git status through tool system
```gherkin
Given the OpenCode application is initialized
And a git repository exists
And a new file is created
When git status is executed via Bash tool
Then the output should show the new file
And the file should be marked as untracked
```

### Scenario: Git diff shows changes
```gherkin
Given the OpenCode application is initialized
And a git repository exists
And a tracked file is modified
When git diff is executed via Bash tool
Then the output should show the changes
And the diff should contain + and - lines
```

### Scenario: Full commit workflow
```gherkin
Given the OpenCode application is initialized
And permissions are auto-approved
And a git repository exists
When a new file is created
And git add is executed
And git commit is executed with message
Then the commit should succeed
And git log should show the commit
```

### Scenario: Git safety guards are active
```gherkin
Given the OpenCode application is initialized
And a git repository exists
When git push --force is attempted
Then the operation should be blocked or warned
And destructive action should be prevented
```

### Scenario: Branch creation and switching
```gherkin
Given the OpenCode application is initialized
And a git repository exists
When a new branch is created
And changes are committed on the branch
And we switch back to main
Then main should not have the branch commits
```

---

## Feature: Plugin System Integration

### Scenario: Plugin discovery and loading
```gherkin
Given the OpenCode application is initialized
And a valid plugin exists in the plugins directory
When discover_and_load is called
Then the plugin should be discovered
And the plugin should be loaded
And the plugin should be active
```

### Scenario: Plugin tool registration
```gherkin
Given the OpenCode application is initialized
And a plugin with tools is loaded
Then the plugin tools should be in the registry
And tool names should be prefixed with plugin ID
```

### Scenario: Plugin tool execution
```gherkin
Given the OpenCode application is initialized
And a plugin tool is registered
When the plugin tool is executed
Then the tool should work correctly
And the result should be returned
```

### Scenario: Plugin enable and disable
```gherkin
Given the OpenCode application is initialized
And a plugin is active
When the plugin is disabled
Then the plugin should be inactive
And plugin tools should be unregistered
When the plugin is enabled
Then the plugin should be active again
And plugin tools should be re-registered
```

### Scenario: Plugin reload
```gherkin
Given the OpenCode application is initialized
And a plugin is active
When the plugin source is modified
And plugin reload is triggered
Then the new code should be loaded
And the plugin should reflect changes
```

### Scenario: Plugin error isolation
```gherkin
Given the OpenCode application is initialized
And a broken plugin exists
And a good plugin exists
When plugins are loaded
Then the good plugin should work
And the broken plugin should have an error recorded
And the system should continue functioning
```

### Scenario: Plugin data isolation
```gherkin
Given the OpenCode application is initialized
And a plugin is loaded
Then the plugin should have its own data directory
And the data directory should exist
And the path should include the plugin ID
```

---

## Feature: Performance Requirements

### Scenario: Cold start under 2 seconds
```gherkin
Given a fresh OpenCode installation
When the application is started
Then startup should complete in under 2 seconds
```

### Scenario: Warm start under 500ms
```gherkin
Given the OpenCode application was recently started
When a new session is created
Then session creation should complete in under 500ms
```

### Scenario: Config load under 100ms
```gherkin
Given configuration files exist
When the configuration is loaded
Then loading should complete in under 100ms
```

### Scenario: Tool overhead under 100ms
```gherkin
Given the OpenCode application is initialized
When a simple Read tool is executed multiple times
Then average overhead should be under 100ms
```

### Scenario: Glob search under 500ms
```gherkin
Given the OpenCode application is initialized
And 100 files exist in the project
When Glob search is executed
Then search should complete in under 500ms
```

### Scenario: Grep search under 1 second
```gherkin
Given the OpenCode application is initialized
And 50 files with content exist
When Grep search is executed
Then search should complete in under 1 second
```

### Scenario: Idle memory under 100MB
```gherkin
Given the OpenCode application is initialized
When the application is idle
Then memory usage should be under 100MB
```

### Scenario: Active memory under 500MB
```gherkin
Given the OpenCode application is initialized
And multiple sessions are active
Then peak memory should be under 500MB
```

---

## Feature: Error Recovery

### Scenario: Recovery from tool error
```gherkin
Given the OpenCode application is initialized
When a tool execution fails (e.g., file not found)
Then an error should be returned gracefully
And the system should remain functional
And subsequent tool calls should work
```

### Scenario: Recovery from session error
```gherkin
Given the OpenCode application is initialized
And a session exists
When session save fails
Then the error should be handled gracefully
And data should not be lost if possible
```

### Scenario: Handling LLM errors
```gherkin
Given the OpenCode application is initialized
When the LLM returns an error
Then the error should be caught
And a user-friendly message should be shown
And the system should remain responsive
```

### Scenario: Timeout handling
```gherkin
Given the OpenCode application is initialized
When a tool execution times out
Then the operation should be terminated
And resources should be cleaned up
And an appropriate error should be returned
```

### Scenario: Network failure handling
```gherkin
Given the OpenCode application is initialized
When a network operation fails
Then the error should be caught
And retry should be attempted if appropriate
And a helpful message should be shown
```

---

## Feature: End-to-End Workflows

### Scenario: Read-edit-verify workflow
```gherkin
Given the OpenCode application is initialized
And permissions are auto-approved
And a source file exists
When the file is read
And a function is renamed via Edit
And the file is read again
Then the new function name should be present
And the old function name should be gone
```

### Scenario: Create new file workflow
```gherkin
Given the OpenCode application is initialized
And permissions are auto-approved
When a new file is written
And the file is read
Then the file should exist
And the content should match
```

### Scenario: Search and edit workflow
```gherkin
Given the OpenCode application is initialized
And permissions are auto-approved
And multiple files contain "old_name"
When Grep finds all occurrences
And each file is edited to use "new_name"
And Grep is run again
Then all files should have "new_name"
And no files should have "old_name"
```

### Scenario: Full git commit workflow
```gherkin
Given the OpenCode application is initialized
And permissions are auto-approved
And a git repository exists
When changes are made to files
And git status is checked
And changes are staged
And changes are committed
And git log is checked
Then the commit should appear in the log
```

### Scenario: Branch and commit workflow
```gherkin
Given the OpenCode application is initialized
And permissions are auto-approved
And a git repository exists
When a feature branch is created
And changes are committed on the branch
And main branch is checked out
Then main should not have the feature commits
And feature branch should have the commits
```

---

## Feature: Documentation Completeness

### Scenario: User documentation exists
```gherkin
Given the documentation directory
Then installation.md should exist
And quickstart.md should exist
And configuration.md should exist
And commands.md should exist
And tools.md should exist
```

### Scenario: Developer documentation exists
```gherkin
Given the documentation directory
Then architecture.md should exist
And plugins.md should exist
And contributing.md should exist
And testing.md should exist
```

### Scenario: API documentation is complete
```gherkin
Given the API reference documentation
Then all public classes should be documented
And all public methods should be documented
And examples should be provided
```

### Scenario: Changelog is maintained
```gherkin
Given the changelog file
Then it should follow Keep a Changelog format
And it should have version entries
And entries should describe changes
```

---

## Feature: Release Readiness

### Scenario: All tests pass
```gherkin
Given the test suite
When all tests are executed
Then all unit tests should pass
And all integration tests should pass
And all e2e tests should pass
```

### Scenario: Coverage meets threshold
```gherkin
Given the test suite with coverage
When coverage is measured
Then overall coverage should be >= 90%
```

### Scenario: Type checking passes
```gherkin
Given the source code
When mypy is executed
Then there should be no type errors
```

### Scenario: Linting passes
```gherkin
Given the source code
When the linter is executed
Then there should be no linting errors
```

### Scenario: Package is installable
```gherkin
Given the pyproject.toml
When pip install is run
Then installation should succeed
And the CLI should be available
And imports should work
```

### Scenario: CLI works correctly
```gherkin
Given the installed package
When opencode --version is run
Then the version should be displayed
When opencode --help is run
Then help should be displayed
```

---

## Feature: Quality Gates

### Scenario: Complexity within limits
```gherkin
Given the source code
When complexity is measured
Then McCabe complexity should be <= 10 for all functions
```

### Scenario: No unhandled exceptions
```gherkin
Given the application running
When various error conditions occur
Then all exceptions should be handled
And no crashes should occur
```

### Scenario: Graceful shutdown
```gherkin
Given the application running
When shutdown is requested
Then all sessions should be saved
And all resources should be released
And shutdown should complete cleanly
```
