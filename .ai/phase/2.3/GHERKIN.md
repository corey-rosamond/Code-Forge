# Phase 2.3: Execution Tools - Gherkin Specifications

**Phase:** 2.3
**Name:** Execution Tools
**Dependencies:** Phase 2.1 (Tool System Foundation)

---

## Feature: Bash Tool - Foreground Execution

### Scenario: Execute simple command
```gherkin
Given an execution context with working_dir="/home/user/project"
When I execute BashTool with command="echo hello"
Then the result should be successful
And the output should contain "hello"
And metadata should contain exit_code=0
```

### Scenario: Execute command with output
```gherkin
Given a directory with files
When I execute BashTool with command="ls -la"
Then the result should be successful
And the output should list the files
And metadata should contain exit_code=0
```

### Scenario: Execute command that fails
```gherkin
Given an execution context
When I execute BashTool with command="exit 1"
Then the result should be failed
And metadata should contain exit_code=1
And the error should indicate the command failed
```

### Scenario: Execute command with stderr
```gherkin
Given an execution context
When I execute BashTool with command="echo error >&2"
Then the result should be successful
And the output should contain "[stderr]"
And the output should contain "error"
```

### Scenario: Execute chained commands with &&
```gherkin
Given an execution context
When I execute BashTool with command="echo first && echo second"
Then the result should be successful
And the output should contain "first"
And the output should contain "second"
```

### Scenario: Execute chained commands with failing first
```gherkin
Given an execution context
When I execute BashTool with command="exit 1 && echo second"
Then the result should be failed
And the output should NOT contain "second"
```

### Scenario: Execute command with timeout
```gherkin
Given an execution context
When I execute BashTool with:
  | command | sleep 1 && echo done |
  | timeout | 5000                 |
Then the result should be successful
And the output should contain "done"
```

### Scenario: Execute command that times out
```gherkin
Given an execution context
When I execute BashTool with:
  | command | sleep 10     |
  | timeout | 1000         |
Then the result should be failed
And the error should contain "timed out"
And the error should contain "1000ms"
```

### Scenario: Execute command with description
```gherkin
Given an execution context
When I execute BashTool with:
  | command     | npm install           |
  | description | Install dependencies  |
Then the result metadata should contain description="Install dependencies"
```

### Scenario: Execute command with large output
```gherkin
Given an execution context
When I execute BashTool with command that produces 50000 characters
Then the result should be successful
And the output should be truncated at 30000 characters
And the output should contain "[Output truncated"
And metadata should contain truncated=true
```

### Scenario: Execute command in dry run mode
```gherkin
Given an execution context with dry_run=true
When I execute BashTool with command="rm -rf /tmp/test"
Then the result should be successful
And the output should contain "[Dry Run]"
And the command should NOT be executed
```

---

## Feature: Bash Tool - Security

### Scenario: Block dangerous rm -rf /
```gherkin
Given an execution context
When I execute BashTool with command="rm -rf /"
Then the result should be failed
And the error should contain "blocked"
And the error should contain "dangerous"
```

### Scenario: Block dangerous rm -rf /*
```gherkin
Given an execution context
When I execute BashTool with command="rm -rf /*"
Then the result should be failed
And the error should contain "blocked"
```

### Scenario: Block fork bomb
```gherkin
Given an execution context
When I execute BashTool with command=":(){ :|:& };:"
Then the result should be failed
And the error should contain "blocked"
```

### Scenario: Block mkfs command
```gherkin
Given an execution context
When I execute BashTool with command="mkfs.ext4 /dev/sda1"
Then the result should be failed
And the error should contain "blocked"
```

### Scenario: Allow safe rm command
```gherkin
Given an execution context with a temp file
When I execute BashTool with command="rm /tmp/test_file.txt"
Then the result should NOT be blocked for security
```

### Scenario: Allow git commands
```gherkin
Given an execution context with a git repository
When I execute BashTool with command="git status"
Then the result should be successful
And the output should contain git status information
```

### Scenario: Allow npm commands
```gherkin
Given an execution context with package.json
When I execute BashTool with command="npm --version"
Then the result should be successful
And the output should contain a version number
```

---

## Feature: Bash Tool - Background Execution

### Scenario: Start background command
```gherkin
Given an execution context
When I execute BashTool with:
  | command           | sleep 5 && echo done |
  | run_in_background | true                 |
Then the result should be successful
And the output should contain "Started background shell"
And the output should contain a bash_id
And metadata should contain bash_id matching "shell_*"
```

### Scenario: Background command returns immediately
```gherkin
Given an execution context
When I execute BashTool with:
  | command           | sleep 60             |
  | run_in_background | true                 |
Then the execution should complete in less than 1 second
And a background shell should be running
```

---

## Feature: BashOutput Tool

### Scenario: Get output from running shell
```gherkin
Given a background shell running "while true; do echo tick; sleep 1; done"
When I execute BashOutputTool with bash_id="{shell_id}"
Then the result should be successful
And the output should contain "tick"
And metadata should contain status="running"
And metadata should contain is_running=true
```

### Scenario: Get output from completed shell
```gherkin
Given a background shell that ran "echo hello" and completed
When I execute BashOutputTool with bash_id="{shell_id}"
Then the result should be successful
And the output should contain "hello"
And metadata should contain status="completed"
And metadata should contain exit_code=0
And metadata should contain is_running=false
```

### Scenario: Get only new output since last read
```gherkin
Given a background shell producing continuous output
When I execute BashOutputTool with bash_id="{shell_id}"
And I note the output
And I execute BashOutputTool again with bash_id="{shell_id}"
Then the second result should only contain NEW output
And the second result should NOT contain output from first read
```

### Scenario: Shell not found
```gherkin
Given no shell exists with id "shell_nonexistent"
When I execute BashOutputTool with bash_id="shell_nonexistent"
Then the result should be failed
And the error should contain "not found"
```

### Scenario: Filter output with regex
```gherkin
Given a background shell that produced output with "error" and "info" lines
When I execute BashOutputTool with:
  | bash_id | {shell_id} |
  | filter  | error      |
Then the result should be successful
And the output should contain "error" lines
And the output should NOT contain "info" lines
```

### Scenario: Invalid filter regex
```gherkin
Given a background shell
When I execute BashOutputTool with:
  | bash_id | {shell_id}         |
  | filter  | [invalid(regex     |
Then the result should be failed
And the error should contain "Invalid filter regex"
```

### Scenario: Get output with duration info
```gherkin
Given a background shell that completed
When I execute BashOutputTool with bash_id="{shell_id}"
Then the output should contain "Duration:"
And metadata should contain exit_code
```

---

## Feature: KillShell Tool

### Scenario: Kill running shell
```gherkin
Given a background shell running "sleep 300"
When I execute KillShellTool with shell_id="{shell_id}"
Then the result should be successful
And the output should contain "terminated"
And the shell status should be "killed"
And the shell should no longer be running
```

### Scenario: Kill already stopped shell
```gherkin
Given a background shell that already completed
When I execute KillShellTool with shell_id="{shell_id}"
Then the result should be successful
And the output should contain "already stopped"
And metadata should contain already_stopped=true
```

### Scenario: Kill non-existent shell
```gherkin
Given no shell exists with id "shell_nonexistent"
When I execute KillShellTool with shell_id="shell_nonexistent"
Then the result should be failed
And the error should contain "not found"
```

### Scenario: Kill shell returns metadata
```gherkin
Given a background shell running "sleep 300"
When I execute KillShellTool with shell_id="{shell_id}"
Then metadata should contain shell_id
And metadata should contain command
And metadata should contain duration_ms
```

---

## Feature: Shell Manager

### Scenario: Create shell
```gherkin
Given a ShellManager instance
When I call create_shell("echo test", "/tmp")
Then a ShellProcess should be returned
And the shell should have a unique id
And the shell status should be "running"
And the shell should be tracked in the manager
```

### Scenario: Get shell by ID
```gherkin
Given a ShellManager with a shell "shell_abc123"
When I call get_shell("shell_abc123")
Then the correct ShellProcess should be returned
```

### Scenario: Get non-existent shell
```gherkin
Given a ShellManager with no shell "shell_xyz"
When I call get_shell("shell_xyz")
Then None should be returned
```

### Scenario: List all shells
```gherkin
Given a ShellManager with 3 shells
When I call list_shells()
Then a list of 3 ShellProcess objects should be returned
```

### Scenario: List running shells
```gherkin
Given a ShellManager with 2 running and 1 completed shell
When I call list_running()
Then a list of 2 ShellProcess objects should be returned
And all should have is_running=true
```

### Scenario: Cleanup completed shells
```gherkin
Given a ShellManager with shells completed more than 1 hour ago
When I call cleanup_completed(max_age_seconds=3600)
Then old completed shells should be removed
And running shells should be kept
And recently completed shells should be kept
```

### Scenario: Kill all shells
```gherkin
Given a ShellManager with 3 running shells
When I call kill_all()
Then all shells should be killed
And the return value should be 3
```

### Scenario: ShellManager is singleton
```gherkin
Given I create ShellManager instance A
And I create ShellManager instance B
Then A and B should be the same instance
And shells created via A should be visible via B
```

### Scenario: Reset singleton for testing
```gherkin
Given a ShellManager with running shells
When I call ShellManager.reset()
Then all shells should be killed
And the singleton should be cleared
And the next ShellManager() should be a fresh instance
```

---

## Feature: Shell Process

### Scenario: Get new output
```gherkin
Given a ShellProcess with stdout_buffer="line1\nline2\nline3\n"
And last_read_stdout=6 (after "line1\n")
When I call get_new_output()
Then the result should be "line2\nline3\n"
And last_read_stdout should be updated to 18
```

### Scenario: Get new output includes stderr
```gherkin
Given a ShellProcess with stdout and stderr buffers
When I call get_new_output(include_stderr=True)
Then the result should contain stdout content
And the result should contain "[stderr]"
And the result should contain stderr content
```

### Scenario: Shell process lifecycle
```gherkin
Given a new ShellProcess
When I observe the status through execution
Then status should transition:
  | from     | to        | trigger                |
  | PENDING  | RUNNING   | process started        |
  | RUNNING  | COMPLETED | exit_code == 0         |
  | RUNNING  | FAILED    | exit_code != 0         |
  | RUNNING  | TIMEOUT   | wait timeout exceeded  |
  | RUNNING  | KILLED    | kill() called          |
```

### Scenario: Calculate duration
```gherkin
Given a ShellProcess that started at t=0 and completed at t=5000
When I access duration_ms
Then the result should be approximately 5000
```

---

## Feature: Tool Registration

### Scenario: All execution tools are registered
```gherkin
Given the OpenCode application initializes
When I call register_execution_tools(registry)
Then the registry should contain "Bash" tool
And the registry should contain "BashOutput" tool
And the registry should contain "KillShell" tool
And all tools should have category=EXECUTION
```

### Scenario: Execution tools generate valid schemas
```gherkin
Given all execution tools are registered
When I call get_all_schemas("openai")
Then each tool should have a valid OpenAI function schema
And BashTool schema should include command as required
And BashOutputTool schema should include bash_id as required
And KillShellTool schema should include shell_id as required
```

---

## Feature: Integration Tests

### Scenario: Full background command workflow
```gherkin
Given an execution context
When I:
  1. Execute BashTool with run_in_background=true
  2. Note the returned bash_id
  3. Execute BashOutputTool to check progress
  4. Wait for completion
  5. Execute BashOutputTool to get final output
Then all steps should succeed
And the final output should contain command results
```

### Scenario: Kill and verify workflow
```gherkin
Given a background shell running a long command
When I:
  1. Verify shell is running via BashOutputTool
  2. Execute KillShellTool to terminate
  3. Verify shell is stopped via BashOutputTool
Then the shell should transition from running to killed
```

### Scenario: Multiple concurrent shells
```gherkin
Given an execution context
When I start 5 background shells concurrently
Then all shells should have unique IDs
And all shells should be tracked by ShellManager
And I should be able to get output from each independently
```

### Scenario: Timeout does not affect other shells
```gherkin
Given shell A running normally
And shell B that will timeout
When shell B times out
Then shell A should continue running
And shell A output should be unaffected
```
