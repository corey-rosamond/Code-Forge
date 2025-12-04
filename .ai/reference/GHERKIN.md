# OpenCode Gherkin Specifications
## Behavior-Driven Development Test Scenarios

**Version:** 1.0
**Date:** December 2025
**Standard:** Gherkin Syntax v6

---

## Table of Contents

1. [Core REPL Features](#1-core-repl-features)
2. [Slash Commands](#2-slash-commands)
3. [Tool Execution](#3-tool-execution)
4. [Permission System](#4-permission-system)
5. [Operating Modes](#5-operating-modes)
6. [Session Management](#6-session-management)
7. [Context Management](#7-context-management)
8. [Hooks System](#8-hooks-system)
9. [Subagents and Skills](#9-subagents-and-skills)
10. [MCP Protocol](#10-mcp-protocol)
11. [OpenRouter Integration](#11-openrouter-integration)
12. [Configuration System](#12-configuration-system)
13. [Git Integration](#13-git-integration)
14. [Error Handling](#14-error-handling)
15. [Security Features](#15-security-features)

---

## 1. Core REPL Features

### Feature: Interactive Command Line Interface

```gherkin
Feature: Interactive REPL Interface
  As a developer
  I want an interactive command line interface
  So that I can communicate with the AI assistant naturally

  Background:
    Given OpenCode is installed and configured
    And I have a valid OpenRouter API key
    And I am in a project directory

  @smoke @repl
  Scenario: Start OpenCode REPL
    When I run "opencode" in the terminal
    Then I should see the OpenCode welcome message
    And I should see the input prompt
    And the status bar should show "Ready"

  @repl @input
  Scenario: Submit a simple query
    Given I have started the OpenCode REPL
    When I type "Hello, how are you?"
    And I press Enter
    Then the agent should respond with a greeting
    And the response should stream to the terminal
    And the input prompt should reappear after completion

  @repl @multiline
  Scenario: Enter multiline input
    Given I have started the OpenCode REPL
    When I type "Here is my code:"
    And I press Shift+Enter
    And I type "def hello():"
    And I press Shift+Enter
    And I type "    print('hello')"
    And I press Enter
    Then the entire multiline input should be sent as one message

  @repl @interrupt
  Scenario: Cancel ongoing generation
    Given I have started the OpenCode REPL
    And the agent is generating a response
    When I press Ctrl+C
    Then the generation should stop
    And I should see "Generation cancelled"
    And the input prompt should reappear

  @repl @history
  Scenario: Navigate command history
    Given I have started the OpenCode REPL
    And I have previously entered "command one"
    And I have previously entered "command two"
    When I press the Up arrow key
    Then I should see "command two" in the input
    When I press the Up arrow key again
    Then I should see "command one" in the input
    When I press the Down arrow key
    Then I should see "command two" in the input

  @repl @search
  Scenario: Reverse search command history
    Given I have started the OpenCode REPL
    And I have previously entered "find all Python files"
    When I press Ctrl+R
    And I type "Python"
    Then I should see "find all Python files" as a match
    When I press Enter
    Then the matched command should be placed in the input

  @repl @paste
  Scenario: Paste image into terminal
    Given I have started the OpenCode REPL
    And I have an image in my clipboard
    When I press Ctrl+V
    Then the image should be attached to the message
    And I should see "[Image attached]" indicator
    When I type "What's in this image?" and press Enter
    Then the agent should analyze the image

  @repl @vim
  Scenario: Enable vim mode
    Given I have started the OpenCode REPL
    When I type "/vim" and press Enter
    Then vim mode should be enabled
    And I should see "Vim mode enabled"
    When I press Escape
    Then I should be in vim normal mode
    When I press "i"
    Then I should be in vim insert mode

  @repl @shortcuts
  Scenario: Display keyboard shortcuts
    Given I have started the OpenCode REPL
    When I press "?"
    Then I should see a list of available keyboard shortcuts
    And the list should include "Esc - Stop generation"
    And the list should include "Ctrl+C - Cancel"
    And the list should include "Shift+Tab - Cycle modes"
```

### Feature: Keyboard Shortcuts

```gherkin
Feature: Keyboard Shortcuts
  As a power user
  I want keyboard shortcuts for common actions
  So that I can work more efficiently

  Background:
    Given I have started the OpenCode REPL

  @shortcuts @escape
  Scenario: Stop generation with Escape
    Given the agent is generating a long response
    When I press Escape
    Then the generation should stop immediately
    And partial output should be preserved

  @shortcuts @escape-twice
  Scenario: Jump to previous messages with double Escape
    Given I have a conversation with multiple messages
    When I press Escape twice quickly
    Then I should see a message picker
    And I should be able to select a previous message

  @shortcuts @clear
  Scenario: Clear screen with Ctrl+L
    Given the terminal has scrolled content
    When I press Ctrl+L
    Then the terminal should be cleared
    And the input prompt should be at the top

  @shortcuts @exit
  Scenario: Exit with Ctrl+D
    Given I am at an empty input prompt
    When I press Ctrl+D
    Then OpenCode should exit gracefully
    And the session should be saved

  @shortcuts @background
  Scenario: Move task to background with Ctrl+B
    Given the agent is executing a long-running bash command
    When I press Ctrl+B
    Then the task should move to background
    And I should see "Task moved to background: [task_id]"
    And I should be able to continue with new input

  @shortcuts @emacs
  Scenario Outline: Emacs-style navigation
    Given I have typed "hello world" in the input
    When I press <shortcut>
    Then the cursor should <action>

    Examples:
      | shortcut | action                    |
      | Ctrl+A   | move to the beginning     |
      | Ctrl+E   | move to the end           |
      | Ctrl+B   | move back one character   |
      | Ctrl+F   | move forward one character|
      | Ctrl+U   | delete the entire line    |
      | Ctrl+W   | delete the previous word  |
```

---

## 2. Slash Commands

### Feature: Built-in Slash Commands

```gherkin
Feature: Built-in Slash Commands
  As a user
  I want to use slash commands for quick actions
  So that I can control OpenCode efficiently

  Background:
    Given I have started the OpenCode REPL

  @commands @help
  Scenario: Display help
    When I type "/help" and press Enter
    Then I should see a list of all available commands
    And each command should have a description
    And custom commands should be listed separately

  @commands @clear
  Scenario: Clear conversation history
    Given I have an active conversation with 10 messages
    When I type "/clear" and press Enter
    Then the conversation history should be cleared
    And I should see "Conversation cleared"
    And the session should remain active

  @commands @compact
  Scenario: Compact conversation context
    Given I have a long conversation approaching context limits
    When I type "/compact" and press Enter
    Then the conversation should be summarized
    And token usage should decrease
    And I should see "Context compacted: X tokens saved"

  @commands @context
  Scenario: View context status
    When I type "/context" and press Enter
    Then I should see current token usage
    And I should see maximum context size
    And I should see a usage percentage
    And I should see model information

  @commands @model
  Scenario: Change model
    Given I am using "gpt-5" model
    When I type "/model claude-4" and press Enter
    Then the model should change to "claude-4"
    And I should see "Model changed to claude-4"

  @commands @model-list
  Scenario: List available models
    When I type "/model" and press Enter without arguments
    Then I should see a list of available models
    And each model should show its capabilities
    And the current model should be highlighted

  @commands @export
  Scenario: Export conversation
    Given I have an active conversation
    When I type "/export" and press Enter
    Then I should be prompted for export format
    When I select "markdown"
    Then the conversation should be exported to a markdown file
    And I should see the file path

  @commands @init
  Scenario: Initialize project context
    Given I am in a new project directory
    And no OPENCODE.md file exists
    When I type "/init" and press Enter
    Then an OPENCODE.md file should be created
    And it should contain project analysis
    And it should include recommended settings

  @commands @mcp
  Scenario: Configure MCP servers
    When I type "/mcp" and press Enter
    Then I should see the MCP configuration menu
    And I should see currently connected servers
    And I should have options to add/remove servers

  @commands @hooks
  Scenario: Configure hooks
    When I type "/hooks" and press Enter
    Then I should see the hooks configuration menu
    And I should see currently configured hooks
    And I should have options to add/edit/remove hooks

  @commands @agents
  Scenario: Manage subagents
    When I type "/agents" and press Enter
    Then I should see the subagent management menu
    And I should see available subagent types
    And I should be able to create new subagents

  @commands @usage
  Scenario: View usage statistics
    When I type "/usage" and press Enter
    Then I should see token usage breakdown
    And I should see cost estimates
    And I should see usage by model

  @commands @continue
  Scenario: Continue previous session
    Given I previously had a session in this directory
    When I run "opencode --continue"
    Then the previous session should be restored
    And I should see the conversation history
    And the context should be intact

  @commands @resume
  Scenario: Resume specific session
    Given I have multiple previous sessions
    When I run "opencode --resume"
    Then I should see a session picker
    When I select a session
    Then that session should be restored
```

### Feature: Custom Slash Commands

```gherkin
Feature: Custom Slash Commands
  As a developer
  I want to create custom slash commands
  So that I can automate repetitive tasks

  Background:
    Given I have started the OpenCode REPL

  @custom-commands @create
  Scenario: Create custom command from file
    Given I create a file ".opencode/commands/greet.md" with content:
      """
      Say hello and introduce yourself as a helpful assistant
      """
    When I type "/greet" and press Enter
    Then the agent should greet and introduce itself

  @custom-commands @parameters
  Scenario: Custom command with parameters
    Given I create a file ".opencode/commands/review.md" with content:
      """
      Review the pull request at $1 and provide feedback
      """
    When I type "/review https://github.com/user/repo/pull/123"
    Then the agent should review PR #123
    And the URL should be substituted for $1

  @custom-commands @namespace
  Scenario: Namespaced custom commands
    Given I create ".opencode/commands/git/status.md"
    And I create ".opencode/commands/git/diff.md"
    When I type "/git/status" and press Enter
    Then the git/status command should execute
    When I type "/git/diff" and press Enter
    Then the git/diff command should execute

  @custom-commands @project-vs-user
  Scenario: Project commands override user commands
    Given I have a user command "~/.opencode/commands/test.md"
    And I have a project command ".opencode/commands/test.md"
    When I type "/test" and press Enter
    Then the project command should execute
    And the user command should be ignored
```

---

## 3. Tool Execution

### Feature: File Operations

```gherkin
Feature: File Operations
  As a developer
  I want the agent to read and modify files
  So that I can get help with my code

  Background:
    Given I have started the OpenCode REPL
    And I am in a project directory with source files

  @tools @read
  Scenario: Read a file
    Given a file "src/main.py" exists with 100 lines
    When I ask "Read the file src/main.py"
    Then the agent should use the Read tool
    And the file contents should be displayed
    And line numbers should be shown

  @tools @read-partial
  Scenario: Read specific lines from a file
    Given a file "src/main.py" exists with 500 lines
    When I ask "Show me lines 100-150 of src/main.py"
    Then the agent should use Read with offset and limit
    And only lines 100-150 should be displayed

  @tools @write
  Scenario: Write a new file
    Given no file "src/helper.py" exists
    When I ask "Create a file src/helper.py with a hello function"
    Then the agent should request permission to create the file
    When I approve the operation
    Then the file should be created with the content
    And I should see "File created: src/helper.py"

  @tools @edit
  Scenario: Edit an existing file
    Given a file "src/main.py" contains "def old_function():"
    When I ask "Rename old_function to new_function"
    Then the agent should use the Edit tool
    And the file should contain "def new_function():"
    And I should see the diff of changes

  @tools @edit-multiple
  Scenario: Edit multiple occurrences
    Given a file "src/config.py" contains "DEBUG = True" twice
    When I ask "Change all DEBUG to False"
    Then the agent should use Edit with replace_all=true
    And all occurrences should be replaced

  @tools @glob
  Scenario: Search files by pattern
    Given I have files matching "**/*.py"
    When I ask "Find all Python files"
    Then the agent should use the Glob tool
    And all matching files should be listed
    And results should be sorted by modification time

  @tools @grep
  Scenario: Search file contents
    Given I have Python files containing "TODO"
    When I ask "Find all TODO comments in the codebase"
    Then the agent should use the Grep tool
    And matching lines should be displayed
    And file paths and line numbers should be shown

  @tools @grep-context
  Scenario: Search with context lines
    When I ask "Find 'def main' with surrounding context"
    Then the agent should use Grep with context flags
    And lines before and after matches should be shown
```

### Feature: Bash Execution

```gherkin
Feature: Bash Command Execution
  As a developer
  I want the agent to execute shell commands
  So that I can automate development tasks

  Background:
    Given I have started the OpenCode REPL
    And bash execution is permitted

  @tools @bash
  Scenario: Execute simple command
    When I ask "Run git status"
    Then the agent should use the Bash tool
    And the command output should be displayed
    And the exit code should be shown

  @tools @bash-timeout
  Scenario: Handle command timeout
    When I ask "Run a command that takes 5 minutes"
    And the timeout is set to 2 minutes
    Then the command should timeout
    And I should see "Command timed out after 120 seconds"

  @tools @bash-background
  Scenario: Run command in background
    When I ask "Run the tests in background"
    Then the command should run in background
    And I should receive a task ID
    And I should be able to continue with other work

  @tools @bash-output
  Scenario: Retrieve background task output
    Given I have a background task running with ID "task_123"
    When I ask "Show output of background task task_123"
    Then the agent should use BashOutput tool
    And I should see the accumulated output

  @tools @bash-kill
  Scenario: Kill background process
    Given I have a background task running with ID "task_123"
    When I ask "Stop the background task task_123"
    Then the agent should use KillShell tool
    And the process should be terminated
    And I should see "Task task_123 terminated"
```

### Feature: Web Operations

```gherkin
Feature: Web Operations
  As a developer
  I want the agent to search and fetch web content
  So that I can get up-to-date information

  Background:
    Given I have started the OpenCode REPL
    And web operations are permitted

  @tools @websearch
  Scenario: Search the web
    When I ask "Search for Python 3.12 new features"
    Then the agent should use WebSearch tool
    And search results should be displayed
    And sources should be cited with links

  @tools @websearch-domain
  Scenario: Search with domain filter
    When I ask "Search for React hooks on official docs only"
    Then the agent should search with domain filtering
    And results should only be from react.dev

  @tools @webfetch
  Scenario: Fetch web page content
    When I ask "Fetch and summarize https://example.com/docs"
    Then the agent should use WebFetch tool
    And the page content should be retrieved
    And a summary should be provided

  @tools @webfetch-redirect
  Scenario: Handle redirects
    Given a URL redirects to a different host
    When I ask the agent to fetch that URL
    Then the agent should inform me of the redirect
    And offer to fetch the new URL
```

### Feature: Task Management

```gherkin
Feature: Task Management Tools
  As a developer
  I want the agent to manage task lists
  So that I can track work progress

  Background:
    Given I have started the OpenCode REPL

  @tools @todo-write
  Scenario: Create todo list
    When I ask "Create a todo list for implementing user auth"
    Then the agent should use TodoWrite tool
    And a structured todo list should be created
    And each item should have status and description

  @tools @todo-progress
  Scenario: Update task progress
    Given I have a todo list with pending items
    When the agent completes a task
    Then the todo should be marked as completed
    And I should see the updated progress

  @tools @memory
  Scenario: Store information in memory
    When I ask "Remember that the API key format is ABC-123"
    Then the agent should use the Memory tool
    And the information should be stored
    When I later ask "What was the API key format?"
    Then the agent should recall "ABC-123"
```

---

## 4. Permission System

### Feature: Permission Management

```gherkin
Feature: Permission System
  As a system administrator
  I want granular permission controls
  So that I can ensure safe operation

  Background:
    Given I have started the OpenCode REPL

  @permissions @allow
  Scenario: Allowlisted operation executes immediately
    Given "Bash(git status)" is in the allow list
    When the agent needs to run "git status"
    Then the command should execute without prompting
    And the output should be shown

  @permissions @deny
  Scenario: Denylisted operation is blocked
    Given "Bash(rm -rf:*)" is in the deny list
    When the agent attempts to run "rm -rf /important"
    Then the operation should be blocked
    And I should see "Operation denied by security policy"
    And a security event should be logged

  @permissions @ask
  Scenario: Asklisted operation prompts for confirmation
    Given "Bash(git push:*)" is in the ask list
    When the agent needs to run "git push origin main"
    Then I should see a permission prompt
    And the prompt should describe the action
    When I approve the operation
    Then the command should execute

  @permissions @ask-reject
  Scenario: User rejects permission request
    Given "FileWrite(*)" is in the ask list
    When the agent wants to create a file
    Then I should see a permission prompt
    When I reject the operation
    Then the file should not be created
    And the agent should acknowledge the rejection

  @permissions @timeout
  Scenario: Permission prompt timeout
    Given a permission prompt is displayed
    And no response is given for 30 seconds
    Then the operation should be cancelled
    And I should see "Permission request timed out"

  @permissions @pattern
  Scenario Outline: Pattern matching in permissions
    Given permission pattern "<pattern>" is in the <list> list
    When the agent attempts "<action>"
    Then the result should be "<result>"

    Examples:
      | pattern              | list  | action                    | result   |
      | Bash(git:*)          | allow | git commit -m "test"      | allowed  |
      | Bash(npm:*)          | allow | npm install lodash        | allowed  |
      | Read(./src/**)       | allow | Read ./src/main.py        | allowed  |
      | Read(./secrets/**)   | deny  | Read ./secrets/api.key    | blocked  |
      | Bash(docker run:*)   | ask   | docker run nginx          | prompted |

  @permissions @default-deny
  Scenario: Unmatched operations are denied by default
    Given a command that matches no permission rules
    When the agent attempts that command
    Then a permission prompt should appear
    And the default action should be "deny"
```

### Feature: Sandboxing

```gherkin
Feature: Sandboxing
  As a security-conscious user
  I want execution sandboxing
  So that operations are isolated

  Background:
    Given I have started the OpenCode REPL
    And sandboxing is enabled

  @sandbox @filesystem
  Scenario: Filesystem access is restricted
    Given the sandbox restricts access to "/home/user/project"
    When the agent attempts to read "/etc/passwd"
    Then the operation should be blocked
    And I should see "Access denied: outside sandbox"

  @sandbox @network
  Scenario: Network access is controlled
    Given network access is restricted to specific hosts
    When the agent attempts to fetch from an unauthorized host
    Then the operation should be blocked

  @sandbox @docker
  Scenario: Docker sandbox execution
    Given docker sandbox mode is enabled
    When the agent executes a bash command
    Then the command should run inside a container
    And the container should have limited privileges
    And filesystem changes should not persist
```

---

## 5. Operating Modes

### Feature: Plan Mode

```gherkin
Feature: Plan Mode
  As a developer
  I want a planning mode for complex tasks
  So that I can review plans before execution

  Background:
    Given I have started the OpenCode REPL

  @modes @plan-enter
  Scenario: Enter Plan Mode
    When I press Shift+Tab twice
    Then I should enter Plan Mode
    And I should see "Plan Mode: Research & Planning Only"
    And the status bar should indicate Plan Mode

  @modes @plan-restrictions
  Scenario: Plan Mode restricts to read-only tools
    Given I am in Plan Mode
    When the agent tries to use the Write tool
    Then the operation should be blocked
    And the agent should only use read-only tools
    And the agent should explain what it would do

  @modes @plan-workflow
  Scenario: Complete planning workflow
    Given I am in Plan Mode
    When I ask "Help me implement user authentication"
    Then the agent should:
      | Step | Action                           |
      | 1    | Research existing auth patterns  |
      | 2    | Analyze current codebase         |
      | 3    | Draft implementation plan        |
      | 4    | Present plan for approval        |
    And I should see a structured plan document

  @modes @plan-approve
  Scenario: Approve and execute plan
    Given I have a plan awaiting approval
    When I type "Approve this plan"
    Then Plan Mode should exit
    And execution should begin
    And the agent should follow the approved plan

  @modes @plan-exit
  Scenario: Exit Plan Mode without executing
    Given I am in Plan Mode
    When I press Shift+Tab
    Then I should exit Plan Mode
    And no changes should be made
```

### Feature: Extended Thinking Mode

```gherkin
Feature: Extended Thinking Mode
  As a developer working on complex problems
  I want extended thinking capabilities
  So that the agent can reason more deeply

  Background:
    Given I have started the OpenCode REPL

  @modes @thinking-toggle
  Scenario: Toggle extended thinking
    When I press Tab
    Then extended thinking should be enabled
    And I should see "Extended Thinking: On"
    When I press Tab again
    Then extended thinking should be disabled

  @modes @thinking-levels
  Scenario Outline: Progressive thinking levels
    When I type "<trigger>" in my prompt
    Then thinking budget should be set to <tokens> tokens
    And the agent should think more deeply

    Examples:
      | trigger       | tokens |
      | think         | 1000   |
      | think hard    | 5000   |
      | think harder  | 10000  |
      | ultrathink    | 50000  |

  @modes @thinking-complex
  Scenario: Complex problem with extended thinking
    Given extended thinking is enabled with "ultrathink"
    When I ask about a complex algorithm design
    Then the agent should show thinking process
    And the response should be more thorough
    And reasoning steps should be visible
```

### Feature: Permission Mode Cycling

```gherkin
Feature: Permission Mode Cycling
  As a user
  I want to quickly switch permission modes
  So that I can control agent autonomy

  Background:
    Given I have started the OpenCode REPL

  @modes @cycle
  Scenario: Cycle through permission modes
    Given I am in Normal mode
    When I press Shift+Tab
    Then I should be in Plan mode
    When I press Shift+Tab
    Then I should be in Read-Only mode
    When I press Shift+Tab
    Then I should be back in Normal mode

  @modes @auto-accept
  Scenario: Auto-accept mode
    Given I enable auto-accept mode
    When the agent needs permission for an action
    Then the action should execute automatically
    And no confirmation should be required
    And a log entry should be created

  @modes @read-only
  Scenario: Read-only mode
    Given I am in Read-Only mode
    When the agent attempts to modify a file
    Then the modification should be blocked
    And the agent should only read and analyze
```

### Feature: Headless Mode

```gherkin
Feature: Headless Mode
  As a DevOps engineer
  I want to run OpenCode in CI/CD pipelines
  So that I can automate development tasks

  @modes @headless
  Scenario: Run in headless mode
    When I run 'opencode -p "List all Python files"'
    Then the command should execute non-interactively
    And the output should be printed to stdout
    And the process should exit with code 0

  @modes @headless-json
  Scenario: Streaming JSON output
    When I run 'opencode -p "Analyze code" --output-format stream-json'
    Then output should be in streaming JSON format
    And each line should be valid JSON
    And tool calls should be included in output

  @modes @headless-error
  Scenario: Handle errors in headless mode
    When I run 'opencode -p "Invalid request"' and it fails
    Then the error should be printed to stderr
    And the process should exit with non-zero code
```

---

## 6. Session Management

### Feature: Session Persistence

```gherkin
Feature: Session Persistence
  As a developer
  I want my sessions to persist
  So that I can continue work across terminal sessions

  Background:
    Given I have started the OpenCode REPL

  @session @save
  Scenario: Auto-save session
    Given I have an active conversation
    When I exit OpenCode with Ctrl+D
    Then the session should be automatically saved
    And the session should be stored in ~/.opencode/sessions/

  @session @resume-recent
  Scenario: Resume most recent session
    Given I had a previous session in this directory
    When I run "opencode --continue"
    Then the most recent session should be loaded
    And I should see the previous conversation
    And context should be restored

  @session @resume-picker
  Scenario: Resume with session picker
    Given I have multiple previous sessions
    When I run "opencode --resume"
    Then I should see a session picker
    And sessions should show date and preview
    When I select a session
    Then that session should be loaded

  @session @export-md
  Scenario: Export session to markdown
    Given I have an active conversation
    When I type "/export markdown"
    Then a markdown file should be created
    And it should contain the full conversation
    And code blocks should be properly formatted

  @session @export-json
  Scenario: Export session to JSON
    Given I have an active conversation
    When I type "/export json"
    Then a JSON file should be created
    And it should contain structured session data
    And metadata should be included
```

### Feature: Session Analytics

```gherkin
Feature: Session Analytics
  As a user
  I want to track session metrics
  So that I can understand usage patterns

  Background:
    Given I have completed several sessions

  @session @usage
  Scenario: View usage statistics
    When I type "/usage"
    Then I should see total tokens used
    And I should see cost breakdown by model
    And I should see usage over time

  @session @cost
  Scenario: Track session costs
    Given I have used multiple models in a session
    When I type "/usage session"
    Then I should see cost for current session
    And costs should be broken down by model
    And input/output tokens should be shown separately
```

---

## 7. Context Management

### Feature: Context Optimization

```gherkin
Feature: Context Optimization
  As a developer in a long session
  I want automatic context management
  So that I don't run out of context space

  Background:
    Given I have started the OpenCode REPL

  @context @status
  Scenario: Check context status
    When I type "/context"
    Then I should see current token count
    And I should see maximum tokens
    And I should see usage percentage
    And I should see warnings if approaching limit

  @context @auto-compact
  Scenario: Automatic context compaction
    Given context usage is above 80%
    When I submit a new message
    Then automatic compaction should trigger
    And older messages should be summarized
    And important information should be preserved

  @context @manual-compact
  Scenario: Manual context compaction
    Given I have a long conversation
    When I type "/compact"
    Then the conversation should be summarized
    And I should see tokens before and after
    And I should see "Context compacted: X tokens saved"

  @context @preserve-important
  Scenario: Preserve important context during compaction
    Given I have told the agent "Remember: API uses v2 format"
    When context compaction occurs
    Then the important fact should be preserved
    And I should be able to reference it later

  @context @overflow
  Scenario: Handle context overflow gracefully
    Given context is at 100% capacity
    When I submit a new large message
    Then aggressive compaction should occur
    And the new message should fit
    And I should see a warning about compression
```

### Feature: Project Context

```gherkin
Feature: Project Context (OPENCODE.md)
  As a developer
  I want persistent project context
  So that the agent understands my project

  Background:
    Given I am in a project directory

  @context @opencode-md
  Scenario: Auto-load OPENCODE.md
    Given an OPENCODE.md file exists in the project root
    When I start OpenCode
    Then the OPENCODE.md content should be loaded
    And the agent should be aware of project context

  @context @init
  Scenario: Initialize project context
    Given no OPENCODE.md exists
    When I type "/init"
    Then the agent should analyze the project
    And an OPENCODE.md file should be created
    And it should contain project structure
    And it should contain coding standards

  @context @readme
  Scenario: Include README in context
    Given a README.md exists in the project
    When I start OpenCode
    Then README content should be included in context
    And the agent should reference documentation
```

---

## 8. Hooks System

### Feature: Hook Configuration

```gherkin
Feature: Hook System
  As a developer
  I want to configure hooks
  So that I can customize agent behavior

  Background:
    Given I have started the OpenCode REPL

  @hooks @pretool
  Scenario: PreToolUse hook
    Given I have configured a PreToolUse hook for FileWrite
    When the agent attempts to write a file
    Then the hook should execute before the write
    And hook output should be displayed
    And the write should proceed if hook succeeds

  @hooks @posttool
  Scenario: PostToolUse hook
    Given I have configured a PostToolUse hook for FileWrite
    And the hook runs "prettier --write $FILE"
    When the agent writes a file
    Then the file should be written first
    And then prettier should format the file

  @hooks @block
  Scenario: Hook blocks operation
    Given I have a PreToolUse hook that validates changes
    When the agent attempts an invalid change
    Then the hook should return "blocked"
    And the operation should not proceed
    And I should see the hook's message

  @hooks @userprompt
  Scenario: UserPromptSubmit hook
    Given I have a hook that adds context to prompts
    When I submit a message
    Then the hook should add additional context
    And the enhanced prompt should be sent to the agent

  @hooks @parallel
  Scenario: Multiple hooks execute in parallel
    Given I have 3 hooks configured for the same event
    When the event triggers
    Then all 3 hooks should run in parallel
    And results should be aggregated
    And the operation should wait for all hooks

  @hooks @timeout
  Scenario: Hook timeout handling
    Given I have a hook that takes too long
    And the timeout is set to 60 seconds
    When the hook runs for 70 seconds
    Then the hook should be terminated
    And I should see "Hook timed out"
    And the operation should proceed based on policy

  @hooks @configure
  Scenario: Configure hooks via menu
    When I type "/hooks"
    Then I should see the hooks menu
    And I should see existing hooks
    When I add a new hook
    Then it should be saved to settings.json
```

---

## 9. Subagents and Skills

### Feature: Subagent Management

```gherkin
Feature: Subagent System
  As a developer
  I want specialized subagents
  So that complex tasks can be delegated

  Background:
    Given I have started the OpenCode REPL

  @subagents @explore
  Scenario: Use Explore subagent
    When I ask "Find all files related to authentication"
    Then the Explore subagent should be invoked
    And it should search the codebase efficiently
    And results should be returned to the main agent

  @subagents @plan
  Scenario: Use Plan subagent in Plan Mode
    Given I am in Plan Mode
    When I request a complex implementation
    Then the Plan subagent should be used
    And it should create a detailed plan
    And the plan should be presented for approval

  @subagents @parallel
  Scenario: Parallel subagent execution
    When I ask for a comprehensive code review
    Then multiple subagents should run in parallel
    And one should check code style
    And one should check security
    And one should check performance
    And results should be aggregated

  @subagents @custom
  Scenario: Create custom subagent
    Given I create ".opencode/agents/api-expert.yaml" with:
      """
      name: api-expert
      description: Expert in REST API design
      model: gpt-5
      tools:
        - Read
        - Grep
        - WebSearch
      system_prompt: You are an expert in REST API design...
      """
    When I ask a question about API design
    Then the api-expert subagent may be invoked
    And it should use its specialized knowledge

  @subagents @isolation
  Scenario: Subagent context isolation
    Given a subagent is processing a task
    Then it should have its own isolated context
    And it should not pollute the main agent's context
    And only the result should be shared
```

### Feature: Skills System

```gherkin
Feature: Skills System
  As a developer
  I want reusable skills
  So that agents can acquire specialized knowledge

  Background:
    Given I have started the OpenCode REPL

  @skills @load
  Scenario: Load skill dynamically
    Given a skill "python-testing" is available
    When I ask about Python testing best practices
    Then the skill should be detected as relevant
    And the skill instructions should be loaded
    And the agent should use the skill's knowledge

  @skills @progressive
  Scenario: Progressive skill loading
    Given a complex skill with many resources
    When the skill is activated
    Then only metadata should be loaded first
    And full instructions loaded when needed
    And resources loaded on demand

  @skills @create
  Scenario: Create custom skill
    Given I create ".opencode/skills/my-skill/SKILL.md"
    When I type "/skills"
    Then my-skill should be listed
    And I should be able to activate it

  @skills @marketplace
  Scenario: Install skill from marketplace
    When I type "/skills install react-patterns"
    Then the skill should be downloaded
    And it should be available for use
    And I should see "Skill 'react-patterns' installed"
```

---

## 10. MCP Protocol

### Feature: MCP Server Management

```gherkin
Feature: MCP Protocol Integration
  As a developer
  I want to connect MCP servers
  So that I can extend agent capabilities

  Background:
    Given I have started the OpenCode REPL

  @mcp @add-stdio
  Scenario: Add MCP server via stdio
    When I run "opencode mcp add --transport stdio github -- npx @mcp/github"
    Then the GitHub MCP server should be added
    And it should appear in /mcp list
    And its tools should be available

  @mcp @add-streamable-http
  Scenario: Add MCP server via Streamable HTTP
    When I run "opencode mcp add --transport streamable-http myserver https://mcp.example.com"
    Then the Streamable HTTP MCP server should be added
    And OAuth 2.1 authentication should be initiated
    And connection should be established after auth
    And tools should be discovered

  @mcp @oauth21
  Scenario: OAuth 2.1 authentication for remote MCP server
    Given I add a remote MCP server at "https://mcp.example.com"
    When the server requires OAuth 2.1 authentication
    Then an OAuth authorization flow should start
    And I should be redirected to authenticate
    When authentication succeeds
    Then the access token should be stored securely
    And the MCP server should connect successfully

  @mcp @oauth21-refresh
  Scenario: OAuth 2.1 token refresh
    Given I have a connected MCP server with OAuth 2.1
    And the access token is about to expire
    When a tool invocation is requested
    Then the token should be automatically refreshed
    And the tool invocation should proceed
    And no user intervention should be required

  @mcp @jsonrpc-batch
  Scenario: JSON-RPC batching for efficiency
    Given an MCP server supports batching
    When the agent needs to invoke multiple tools
    Then tool calls should be batched into a single request
    And responses should be properly correlated
    And performance should improve over individual calls

  @mcp @list
  Scenario: List MCP servers
    Given I have configured MCP servers
    When I type "/mcp"
    Then I should see all configured servers
    And I should see their connection status
    And I should see available tools per server

  @mcp @invoke
  Scenario: Invoke MCP tool
    Given the GitHub MCP server is connected
    When I ask "Create a new issue in my repo"
    Then the agent should use the GitHub MCP tool
    And the issue should be created
    And I should see confirmation

  @mcp @disconnect
  Scenario: Handle MCP server disconnection
    Given an MCP server loses connection
    Then I should see a notification
    And the agent should handle gracefully
    And reconnection should be attempted

  @mcp @project-scope
  Scenario: Project-scoped MCP configuration
    Given I have ".mcp.json" in the project root
    When I start OpenCode in this project
    Then project-specific MCP servers should connect
    And they should be available only for this project
```

---

## 11. OpenRouter Integration

### Feature: OpenRouter API Integration

```gherkin
Feature: OpenRouter Integration
  As a developer
  I want access to multiple AI models
  So that I can choose the best model for each task

  Background:
    Given I have a valid OpenRouter API key
    And I have started the OpenCode REPL

  @openrouter @models
  Scenario: List available models
    When I type "/model"
    Then I should see available models
    And models should include GPT-5
    And models should include Claude 4
    And models should include Gemini 2.5

  @openrouter @switch
  Scenario: Switch models mid-conversation
    Given I am using "gpt-5"
    When I type "/model claude-4"
    Then the model should switch to Claude 4
    And subsequent requests should use Claude 4
    And context should be preserved

  @openrouter @routing
  Scenario Outline: Use routing variants
    When I use model "<base>:<variant>"
    Then the routing variant should be applied
    And the behavior should match "<expected>"

    Examples:
      | base  | variant  | expected                    |
      | gpt-5 | exacto   | High-quality endpoint       |
      | gpt-5 | nitro    | Fastest response time       |
      | gpt-5 | floor    | Lowest cost option          |
      | gpt-5 | thinking | Extended reasoning          |
      | gpt-5 | online   | Web-enhanced responses      |

  @openrouter @fallback
  Scenario: Automatic model fallback
    Given the primary model is unavailable
    When I send a request
    Then OpenRouter should fallback to another provider
    And I should see a notification of the fallback
    And the request should complete successfully

  @openrouter @cost
  Scenario: Track API costs
    When I complete a conversation
    Then token usage should be tracked
    And costs should be calculated
    And I should see cost in /usage

  @openrouter @multimodal
  Scenario: Use multimodal features
    Given I attach an image to my message
    When I ask "Describe this image"
    Then the image should be sent to a vision-capable model
    And I should receive an image description

  @openrouter @streaming
  Scenario: Stream responses
    When I send a message
    Then the response should stream in real-time
    And I should see tokens appear progressively
    And final token count should be accurate
```

---

## 12. Configuration System

### Feature: Configuration Hierarchy

```gherkin
Feature: Configuration System
  As a user
  I want flexible configuration
  So that I can customize OpenCode behavior

  Background:
    Given I have started the OpenCode REPL

  @config @hierarchy
  Scenario: Configuration hierarchy is respected
    Given enterprise settings set "model" to "gpt-5"
    And user settings set "model" to "claude-4"
    And project settings set "model" to "gemini-2.5"
    When I check the active model
    Then it should be "gpt-5" (enterprise overrides all)

  @config @local-override
  Scenario: Local settings override project settings
    Given project settings are version-controlled
    And I create ".opencode/settings.local.json"
    When I add personal preferences to local settings
    Then local settings should override project settings
    And local settings should be gitignored

  @config @reload
  Scenario: Live configuration reload
    Given I modify ".opencode/settings.json"
    Then the changes should be detected automatically
    And the new configuration should be applied
    And I should see "Configuration reloaded"

  @config @validate
  Scenario: Validate configuration
    Given I have an invalid configuration value
    When OpenCode loads the configuration
    Then a validation error should be shown
    And default values should be used for invalid fields
    And I should see which fields are invalid

  @config @env
  Scenario: Environment variables override
    Given I set OPENCODE_MODEL="gpt-5"
    When I start OpenCode
    Then the model should be set from environment variable
```

---

## 13. Git Integration

### Feature: Git Operations

```gherkin
Feature: Git Integration
  As a developer
  I want seamless Git integration
  So that I can manage version control efficiently

  Background:
    Given I have started the OpenCode REPL
    And I am in a Git repository

  @git @status
  Scenario: Check Git status
    When I ask "What's the git status?"
    Then the agent should run git status
    And I should see modified files
    And I should see untracked files

  @git @commit
  Scenario: Create a commit
    Given I have staged changes
    When I ask "Commit these changes"
    Then the agent should analyze the changes
    And generate an appropriate commit message
    And create the commit with proper attribution

  @git @commit-message
  Scenario: Commit message format
    When the agent creates a commit
    Then the message should summarize the changes
    And it should end with the Claude Code attribution
    And it should include Co-Authored-By header

  @git @pr
  Scenario: Create pull request
    Given I have committed changes on a feature branch
    When I ask "Create a PR for these changes"
    Then the agent should push the branch
    And create a PR using gh CLI
    And include a summary and test plan
    And return the PR URL

  @git @review
  Scenario: Review pull request
    When I ask "Review PR #123"
    Then the agent should fetch PR details
    And analyze the changes
    And provide feedback and suggestions
```

---

## 14. Error Handling

### Feature: Error Handling

```gherkin
Feature: Error Handling
  As a user
  I want graceful error handling
  So that I can recover from issues

  Background:
    Given I have started the OpenCode REPL

  @errors @api
  Scenario: Handle API errors
    Given the OpenRouter API returns an error
    Then I should see a helpful error message
    And the error should be logged
    And I should be able to retry

  @errors @network
  Scenario: Handle network disconnection
    Given the network connection is lost
    When I send a message
    Then I should see "Network error: Unable to connect"
    And the system should retry automatically
    And I should be notified when connection is restored

  @errors @tool-failure
  Scenario: Handle tool execution failure
    Given a tool execution fails
    Then the agent should handle the error gracefully
    And inform me of the failure
    And suggest alternatives if available

  @errors @recovery
  Scenario: Session recovery after crash
    Given OpenCode crashes unexpectedly
    When I restart OpenCode
    Then I should be offered to recover the session
    And unsaved work should be recoverable

  @errors @validation
  Scenario: Handle invalid user input
    Given I provide invalid input
    Then I should see a clear error message
    And the error should explain what's wrong
    And suggest how to fix it
```

---

## 15. Security Features

### Feature: Security

```gherkin
Feature: Security Features
  As a security-conscious user
  I want robust security measures
  So that my data and system are protected

  Background:
    Given I have started the OpenCode REPL

  @security @api-keys
  Scenario: API keys are stored securely
    Given I configure my OpenRouter API key
    Then the key should be encrypted at rest
    And the key should not appear in logs
    And the key should not be exposed in error messages

  @security @injection
  Scenario: Prevent command injection
    Given a malicious prompt attempts command injection
    Then the injection should be sanitized
    And no unauthorized commands should execute
    And a security event should be logged

  @security @prompt-injection
  Scenario: Prevent prompt injection from web content
    Given I fetch a webpage with malicious content
    Then prompt injection attempts should be detected
    And the content should be sanitized
    And the agent should not follow injected instructions

  @security @audit
  Scenario: Audit trail
    Given I perform sensitive operations
    Then all operations should be logged
    And logs should include timestamps
    And logs should include operation details
    And logs should be tamper-evident

  @security @secrets
  Scenario: Detect potential secrets
    Given a file contains what appears to be an API key
    When the agent attempts to commit it
    Then a warning should be shown
    And the commit should require explicit confirmation

  @security @sandbox-escape
  Scenario: Prevent sandbox escape
    Given sandbox mode is enabled
    When the agent attempts to escape the sandbox
    Then the attempt should be blocked
    And a security alert should be raised
```

---

## Appendix A: Tag Reference

| Tag | Description |
|-----|-------------|
| @smoke | Critical path tests |
| @repl | REPL interface tests |
| @commands | Slash command tests |
| @tools | Tool execution tests |
| @permissions | Permission system tests |
| @modes | Operating mode tests |
| @session | Session management tests |
| @context | Context management tests |
| @hooks | Hooks system tests |
| @subagents | Subagent tests |
| @skills | Skills system tests |
| @mcp | MCP protocol tests |
| @openrouter | OpenRouter integration tests |
| @config | Configuration tests |
| @git | Git integration tests |
| @errors | Error handling tests |
| @security | Security tests |

---

## Appendix B: Test Data Requirements

### Sample Files
- `src/main.py` - Main Python file (100+ lines)
- `src/config.py` - Configuration file
- `tests/test_main.py` - Test file
- `README.md` - Project documentation
- `OPENCODE.md` - Project context

### Sample Configurations
- `.opencode/settings.json` - Project settings
- `~/.opencode/settings.json` - User settings
- `.mcp.json` - MCP configuration

### Mock Services
- Mock OpenRouter API
- Mock GitHub API
- Mock MCP servers

---

*Document Version: 1.0*
*Last Updated: December 2025*
*Test Framework: pytest-bdd*