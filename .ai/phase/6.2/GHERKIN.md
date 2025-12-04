# Phase 6.2: Operating Modes - Gherkin Specifications

**Phase:** 6.2
**Name:** Operating Modes
**Dependencies:** Phase 1.3 (Basic REPL Shell), Phase 3.2 (LangChain Integration)

---

## Feature: Mode Base Classes

### Scenario: Create mode with default config
```gherkin
Given a NormalMode class
When I instantiate NormalMode()
Then mode.name should be ModeName.NORMAL
And mode.config should have default values
And mode.is_active should be False
```

### Scenario: Activate mode
```gherkin
Given a Mode instance
And a ModeContext
When I call mode.activate(context)
Then mode.is_active should be True
And mode.state.active should be True
```

### Scenario: Deactivate mode
```gherkin
Given an activated Mode instance
When I call mode.deactivate(context)
Then mode.is_active should be False
And mode.state.data should be empty
```

### Scenario: Modify prompt
```gherkin
Given a Mode with system_prompt_addition "Extra instructions"
And base_prompt "You are helpful"
When I call mode.modify_prompt(base_prompt)
Then result should contain "You are helpful"
And result should contain "Extra instructions"
```

### Scenario: Save and restore state
```gherkin
Given a Mode with state data
When I call mode.save_state()
And I call mode.restore_state(saved_data)
Then mode.state should match original state
```

---

## Feature: Mode Manager

### Scenario: Get singleton instance
```gherkin
When I call ModeManager.get_instance() twice
Then I should get the same instance both times
```

### Scenario: Register mode
```gherkin
Given an empty ModeManager
When I register PlanMode
Then manager should contain PLAN mode
And list_modes() should include PlanMode
```

### Scenario: Prevent duplicate registration
```gherkin
Given a ModeManager with PlanMode registered
When I try to register PlanMode again
Then it should raise ValueError
```

### Scenario: Switch mode
```gherkin
Given a ModeManager in NORMAL mode
And a ModeContext
When I call switch_mode(PLAN, context)
Then current_mode_name should be PLAN
And PlanMode should be activated
```

### Scenario: Push and pop mode stack
```gherkin
Given a ModeManager in NORMAL mode
When I switch_mode(PLAN, context, push=True)
Then mode_stack should contain NORMAL
When I call pop_mode(context)
Then current_mode_name should be NORMAL
And mode_stack should be empty
```

### Scenario: Reset mode
```gherkin
Given a ModeManager in PLAN mode with stack
When I call reset_mode(context)
Then current_mode_name should be NORMAL
And mode_stack should be empty
```

### Scenario: Get modified system prompt
```gherkin
Given a ModeManager in PLAN mode
And base_prompt "You are helpful"
When I call get_system_prompt(base_prompt)
Then result should contain plan mode instructions
```

### Scenario: Mode change callback
```gherkin
Given a ModeManager with registered callback
When I switch from NORMAL to PLAN
Then callback should be called with (NORMAL, PLAN)
```

---

## Feature: Plan Mode

### Scenario: Enter plan mode
```gherkin
Given a ModeManager
And a ModeContext
When I switch to PLAN mode
Then output should contain "Entered plan mode"
And output should contain instructions
```

### Scenario: Auto-detect planning request
```gherkin
Given a PlanMode
When I call should_auto_activate("Plan how to add authentication")
Then it should return True
When I call should_auto_activate("Hello world")
Then it should return False
```

### Scenario: Create and store plan
```gherkin
Given an active PlanMode
When I call set_plan with a Plan object
Then get_plan() should return that Plan
And state.data should contain plan
```

### Scenario: Show plan as markdown
```gherkin
Given a PlanMode with current_plan
When I call show_plan()
Then result should be markdown formatted
And result should contain plan title
And result should contain steps
```

### Scenario: Execute plan to todos
```gherkin
Given a PlanMode with a 3-step plan
When I call execute_plan()
Then result should be list of 3 todo items
And each item should have content, status, activeForm
```

### Scenario: Cancel plan
```gherkin
Given a PlanMode with current_plan
When I call cancel_plan()
Then current_plan should be None
And state.data should not contain plan
```

---

## Feature: Plan Data Structures

### Scenario: Create plan step
```gherkin
Given step data: number=1, description="First step"
When I create PlanStep
Then step.number should be 1
And step.completed should be False
```

### Scenario: Step to markdown
```gherkin
Given a PlanStep with files and dependencies
When I call to_markdown()
Then result should contain checkbox
And result should contain files list
And result should contain dependencies
```

### Scenario: Create plan
```gherkin
Given plan data with title, summary, steps
When I create Plan
Then plan.progress should be (0, total_steps)
And plan.progress_percentage should be 0
```

### Scenario: Mark step complete
```gherkin
Given a Plan with 3 steps
When I call mark_step_complete(1)
Then step 1 should be completed
And plan.progress should be (1, 3)
And plan.updated_at should be updated
```

### Scenario: Serialize and deserialize plan
```gherkin
Given a Plan with steps
When I call to_dict()
And I call Plan.from_dict(data)
Then restored plan should match original
```

---

## Feature: Thinking Mode

### Scenario: Enter thinking mode
```gherkin
Given a ModeManager
When I switch to THINKING mode
Then output should contain "Entered thinking mode"
And timer should be started
```

### Scenario: Enter deep thinking mode
```gherkin
Given a ThinkingMode
When I call set_deep_mode(True)
Then thinking_config.deep_mode should be True
And system_prompt should contain deep thinking instructions
```

### Scenario: Set thinking budget
```gherkin
Given a ThinkingMode
When I call set_thinking_budget(5000)
Then thinking_config.max_thinking_tokens should be 5000
```

### Scenario: Process thinking response
```gherkin
Given a ThinkingMode
And response "<thinking>Analysis here</thinking><response>Answer</response>"
When I call modify_response(response)
Then result should contain "Thinking Process" section
And result should contain analysis
And result should contain answer
```

### Scenario: Response without thinking tags
```gherkin
Given a ThinkingMode
And response "Plain response without tags"
When I call modify_response(response)
Then result should be unchanged
```

### Scenario: Get last thinking result
```gherkin
Given a ThinkingMode that processed a response
When I call get_last_thinking()
Then result should contain thinking text
And result should contain response text
And result should have time_seconds
```

---

## Feature: Headless Mode

### Scenario: Enter headless mode with file input
```gherkin
Given HeadlessConfig with input_file="input.txt"
When I activate HeadlessMode
Then input stream should be opened from file
```

### Scenario: Enter headless mode without files
```gherkin
Given HeadlessConfig with no files specified
When I activate HeadlessMode
Then input stream should be stdin
And output stream should be stdout
```

### Scenario: Read input
```gherkin
Given an activated HeadlessMode with input file
When I call read_input()
Then I should get file contents
```

### Scenario: Write JSON output
```gherkin
Given HeadlessConfig with output_format=JSON
And a HeadlessResult
When I call write_output(result)
Then output should be valid JSON
And JSON should contain status, message, output
```

### Scenario: Write text output
```gherkin
Given HeadlessConfig with output_format=TEXT
And a HeadlessResult
When I call write_output(result)
Then output should be human-readable text
```

### Scenario: Handle safe permission request
```gherkin
Given HeadlessConfig with auto_approve_safe=True
When I call handle_permission_request("read file", is_safe=True)
Then it should return True
```

### Scenario: Handle unsafe permission request
```gherkin
Given HeadlessConfig with fail_on_unsafe=True
When I call handle_permission_request("delete all", is_safe=False)
Then it should return False
```

### Scenario: Check timeout
```gherkin
Given HeadlessConfig with timeout=10
And HeadlessMode activated 15 seconds ago
When I call check_timeout()
Then it should return True
```

### Scenario: Create success result
```gherkin
Given an activated HeadlessMode
When I call create_result(success=True, message="Done", output="Result")
Then result.success should be True
And result.exit_code should be 0
And result.execution_time should be > 0
```

### Scenario: Create failure result
```gherkin
Given an activated HeadlessMode
When I call create_result(success=False, message="Failed", error="Error msg")
Then result.success should be False
And result.exit_code should be 1
And result.error should be "Error msg"
```

---

## Feature: Mode Commands

### Scenario: Show current mode
```gherkin
Given ModeManager in PLAN mode
When user executes "/mode"
Then output should show "Current mode: plan"
And output should show mode description
```

### Scenario: Switch mode via command
```gherkin
Given ModeManager in NORMAL mode
When user executes "/mode plan"
Then mode should switch to PLAN
And output should confirm switch
```

### Scenario: Enter plan mode via shortcut
```gherkin
Given ModeManager in NORMAL mode
When user executes "/plan"
Then mode should switch to PLAN
```

### Scenario: Show plan
```gherkin
Given PlanMode with current plan
When user executes "/plan show"
Then output should show formatted plan
```

### Scenario: Execute plan
```gherkin
Given PlanMode with current plan
When user executes "/plan execute"
Then todos should be created from plan
And implementation should begin
```

### Scenario: Cancel plan
```gherkin
Given PlanMode with current plan
When user executes "/plan cancel"
Then plan should be cleared
And mode should return to NORMAL
```

### Scenario: Enter thinking mode
```gherkin
Given ModeManager in NORMAL mode
When user executes "/think"
Then mode should switch to THINKING
```

### Scenario: Enter deep thinking
```gherkin
Given ModeManager in NORMAL mode
When user executes "/think deep"
Then mode should switch to THINKING
And deep_mode should be enabled
```

### Scenario: Return to normal mode
```gherkin
Given ModeManager in PLAN mode
When user executes "/normal"
Then mode should switch to NORMAL
```

---

## Feature: Mode Auto-Activation

### Scenario: Auto-activate plan mode
```gherkin
Given ModeManager in NORMAL mode
When user sends "Plan the steps to refactor authentication"
Then plan mode should auto-activate
And user should be notified of mode switch
```

### Scenario: No auto-activation for simple request
```gherkin
Given ModeManager in NORMAL mode
When user sends "Fix the typo in README"
Then mode should remain NORMAL
```

### Scenario: Suggest thinking for complex problem
```gherkin
Given ModeManager in NORMAL mode
When user sends "Compare the trade-offs between React and Vue"
Then thinking mode may be suggested
```

---

## Feature: Mode State Persistence

### Scenario: Save mode state to session
```gherkin
Given ModeManager with PLAN mode active and current_plan
When I call save_state()
Then result should contain current_mode
And result should contain mode_stack
And result should contain mode_states with plan data
```

### Scenario: Restore mode state from session
```gherkin
Given saved mode state with PLAN mode and plan
And a ModeContext
When I call restore_state(data, context)
Then current_mode should be PLAN
And PlanMode should have restored plan
```

### Scenario: Mode survives context compaction
```gherkin
Given a session in PLAN mode with current plan
When context is compacted
Then mode state should be preserved
And current_plan should still exist
```

---

## Feature: Integration with REPL

### Scenario: REPL uses modified prompt
```gherkin
Given REPL with ModeManager in PLAN mode
When REPL prepares system prompt
Then prompt should include plan mode additions
```

### Scenario: REPL processes mode response
```gherkin
Given REPL with ModeManager in THINKING mode
And LLM response with thinking tags
When REPL receives response
Then response should be processed by ThinkingMode
And output should show formatted thinking
```

### Scenario: REPL handles mode commands
```gherkin
Given REPL receiving "/plan" command
When command is executed
Then ModeManager should switch to PLAN mode
And REPL should update display
```

---

## Feature: Error Handling

### Scenario: Switch to unknown mode
```gherkin
Given a ModeManager
When I try to switch to non-existent mode
Then ModeNotFoundError should be raised
```

### Scenario: Switch to disabled mode
```gherkin
Given a ModeManager with disabled PLAN mode
When I try to switch to PLAN
Then ModeSwitchError should be raised
```

### Scenario: Mode activation fails
```gherkin
Given a Mode with failing activate()
When ModeManager tries to switch to it
Then ModeSwitchError should be raised
And original mode should be restored
```

### Scenario: Headless input file not found
```gherkin
Given HeadlessConfig with non-existent input_file
When I try to activate HeadlessMode
Then FileNotFoundError should be raised
```

---

## Feature: CLI Headless Integration

### Scenario: Start in headless mode via CLI
```gherkin
Given CLI invoked with "--headless" flag
When application starts
Then ModeManager should be in HEADLESS mode
And no interactive prompts should appear
```

### Scenario: Headless with input file
```gherkin
Given CLI invoked with "--headless --input task.txt"
When application starts
Then HeadlessMode should read from task.txt
```

### Scenario: Headless with JSON output
```gherkin
Given CLI invoked with "--headless --json"
When task completes
Then output should be valid JSON
```

### Scenario: Headless exit code on success
```gherkin
Given headless execution that succeeds
When execution completes
Then process should exit with code 0
```

### Scenario: Headless exit code on failure
```gherkin
Given headless execution that fails
When execution completes
Then process should exit with code 1
```
