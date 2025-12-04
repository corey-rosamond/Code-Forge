# Phase 1.3: Basic REPL Shell - Gherkin Specifications

**Phase:** 1.3
**Name:** Basic REPL Shell
**Dependencies:** Phase 1.1, Phase 1.2

---

## Feature: REPL Startup

```gherkin
Feature: REPL Startup
  As a user
  I want the REPL to start correctly
  So that I can interact with OpenCode

  Background:
    Given OpenCode is installed
    And configuration is valid

  @phase1.3 @repl @startup @smoke
  Scenario: Start REPL without arguments
    When I run "opencode"
    Then the REPL should start
    And I should see the welcome message
    And I should see the input prompt

  @phase1.3 @repl @startup
  Scenario: Welcome message content
    When I run "opencode"
    Then I should see "OpenCode" in the output
    And I should see the version number
    And I should see the current directory
    And I should see "/help for commands"

  @phase1.3 @repl @startup
  Scenario: Status bar displays on startup
    Given display.status_line is true in config
    When I run "opencode"
    Then the status bar should be visible
    And it should show the default model
    And it should show "Ready" status

  @phase1.3 @repl @startup
  Scenario: Status bar hidden when disabled
    Given display.status_line is false in config
    When I run "opencode"
    Then the status bar should not be visible
```

---

## Feature: Input Handling

```gherkin
Feature: Input Handling
  As a user
  I want to enter commands
  So that I can interact with the assistant

  Background:
    Given the OpenCode REPL is running

  @phase1.3 @input @basic
  Scenario: Submit single-line input
    When I type "Hello world"
    And I press Enter
    Then the input should be processed
    And I should see a response
    And the prompt should reappear

  @phase1.3 @input @multiline
  Scenario: Submit multiline input
    When I type "Line 1"
    And I press Shift+Enter
    And I type "Line 2"
    And I press Shift+Enter
    And I type "Line 3"
    And I press Enter
    Then all three lines should be sent as one input

  @phase1.3 @input @empty
  Scenario: Empty input is ignored
    When I press Enter without typing anything
    Then no processing should occur
    And the prompt should reappear immediately

  @phase1.3 @input @whitespace
  Scenario: Whitespace-only input is ignored
    When I type "   "
    And I press Enter
    Then no processing should occur
    And the prompt should reappear

  @phase1.3 @input @special-chars
  Scenario: Input with special characters
    When I type "echo 'Hello $USER' && ls -la"
    And I press Enter
    Then the special characters should be preserved
    And the input should be processed correctly
```

---

## Feature: Input History

```gherkin
Feature: Input History
  As a user
  I want command history
  So that I can reuse previous commands

  Background:
    Given the OpenCode REPL is running

  @phase1.3 @history @navigate
  Scenario: Navigate history with Up arrow
    Given I have previously entered "command one"
    And I have previously entered "command two"
    When I press the Up arrow
    Then I should see "command two" in the input
    When I press the Up arrow again
    Then I should see "command one" in the input

  @phase1.3 @history @navigate
  Scenario: Navigate history with Down arrow
    Given I have navigated to an older command
    When I press the Down arrow
    Then I should see the next newer command
    When I press Down at the newest command
    Then the input should be empty

  @phase1.3 @history @search
  Scenario: Search history with Ctrl+R
    Given I have previously entered "find all python files"
    When I press Ctrl+R
    And I type "python"
    Then I should see "find all python files" as a match
    When I press Enter
    Then the matched command should be in the input

  @phase1.3 @history @persist
  Scenario: History persists between sessions
    Given I have entered commands in a session
    And I exit and restart OpenCode
    When I press the Up arrow
    Then I should see commands from the previous session

  @phase1.3 @history @file
  Scenario: History stored in correct location
    When I enter several commands
    Then a history file should exist at "~/.src/opencode/history"
```

---

## Feature: Keyboard Shortcuts

```gherkin
Feature: Keyboard Shortcuts
  As a user
  I want keyboard shortcuts
  So that I can work efficiently

  Background:
    Given the OpenCode REPL is running

  @phase1.3 @shortcuts @escape
  Scenario: Escape cancels current input
    Given I have typed "some partial input"
    When I press Escape
    Then the input should be cleared
    And the cursor should be at the prompt

  @phase1.3 @shortcuts @ctrl-c
  Scenario: Ctrl+C interrupts and returns to prompt
    Given I am in the middle of typing
    When I press Ctrl+C
    Then I should see "Interrupted"
    And the prompt should reappear

  @phase1.3 @shortcuts @ctrl-d
  Scenario: Ctrl+D exits on empty input
    Given the input is empty
    When I press Ctrl+D
    Then I should see "Goodbye!"
    And the REPL should exit
    And the exit code should be 0

  @phase1.3 @shortcuts @ctrl-d-nonempty
  Scenario: Ctrl+D does not exit on non-empty input
    Given I have typed "some text"
    When I press Ctrl+D
    Then the REPL should not exit
    And the input should remain

  @phase1.3 @shortcuts @ctrl-l
  Scenario: Ctrl+L clears the screen
    Given there is content on the screen
    When I press Ctrl+L
    Then the screen should be cleared
    And the prompt should be at the top

  @phase1.3 @shortcuts @ctrl-u
  Scenario: Ctrl+U clears the input line
    Given I have typed "text to clear"
    When I press Ctrl+U
    Then the input should be empty
    And the cursor should be at the prompt

  @phase1.3 @shortcuts @help
  Scenario: Question mark shows shortcuts
    Given the input is empty
    When I type "?"
    And I press Enter
    Then I should see the keyboard shortcuts list
    And the list should include "Esc" and "Ctrl+C"
```

---

## Feature: Output Display

```gherkin
Feature: Output Display
  As a user
  I want formatted output
  So that responses are easy to read

  Background:
    Given the OpenCode REPL is running

  @phase1.3 @output @basic
  Scenario: Display plain text output
    When I receive a plain text response
    Then it should be displayed in the terminal
    And it should use the theme foreground color

  @phase1.3 @output @code
  Scenario: Syntax highlight code blocks
    When I receive a response with a Python code block
    Then the code should have syntax highlighting
    And it should have line numbers

  @phase1.3 @output @markdown
  Scenario: Render markdown formatting
    When I receive a response with markdown
    Then headers should be bold
    And bullet points should be formatted
    And inline code should be highlighted

  @phase1.3 @output @error
  Scenario: Display errors in red
    When an error occurs
    Then the error should be displayed in red
    And it should be prefixed with "Error:"

  @phase1.3 @output @warning
  Scenario: Display warnings in yellow
    When a warning occurs
    Then the warning should be displayed in yellow
    And it should be prefixed with "Warning:"
```

---

## Feature: Status Bar

```gherkin
Feature: Status Bar
  As a user
  I want a status bar
  So that I can see system state at a glance

  Background:
    Given the OpenCode REPL is running
    And the status bar is enabled

  @phase1.3 @status @model
  Scenario: Status bar shows current model
    Given the default model is "gpt-5"
    Then the status bar should show "gpt-5"

  @phase1.3 @status @tokens
  Scenario: Status bar shows token count
    Then the status bar should show "Tokens: 0/128,000"

  @phase1.3 @status @mode
  Scenario: Status bar shows operating mode
    Given I am in Normal mode
    Then the status bar should show "Normal"

  @phase1.3 @status @ready
  Scenario: Status bar shows ready status
    When the REPL is waiting for input
    Then the status bar should show "Ready"

  @phase1.3 @status @resize
  Scenario: Status bar adapts to terminal width
    Given the terminal is 120 columns wide
    Then the status bar should span 120 columns
    When I resize to 80 columns
    Then the status bar should span 80 columns
```

---

## Feature: Themes

```gherkin
Feature: Theme Support
  As a user
  I want theme options
  So that I can customize the appearance

  @phase1.3 @themes @dark
  Scenario: Dark theme is default
    Given no theme is configured
    When I start the REPL
    Then the dark theme should be active
    And the background should be dark
    And text should be light colored

  @phase1.3 @themes @light
  Scenario: Light theme can be selected
    Given display.theme is "light" in config
    When I start the REPL
    Then the light theme should be active
    And the background should be light
    And text should be dark colored

  @phase1.3 @themes @colors
  Scenario: Theme colors are consistent
    Given a theme is active
    Then errors should use the error color
    And success messages should use the success color
    And warnings should use the warning color
```

---

## Feature: Exit Handling

```gherkin
Feature: Exit Handling
  As a user
  I want clean exit behavior
  So that the application shuts down properly

  @phase1.3 @exit @ctrl-d
  Scenario: Clean exit with Ctrl+D
    Given the REPL is running
    When I press Ctrl+D on empty input
    Then I should see "Goodbye!"
    And the exit code should be 0
    And no error should occur

  @phase1.3 @exit @graceful
  Scenario: Graceful handling of multiple Ctrl+C
    Given the REPL is running
    When I press Ctrl+C multiple times quickly
    Then each should show "Interrupted"
    And the REPL should remain running
```

---

## Test Data Requirements

### Sample Inputs
- Single line: "Hello world"
- Multiline: "Line 1\nLine 2\nLine 3"
- Special chars: "echo $HOME && ls -la"
- Empty: ""
- Whitespace: "   "

### History File
- Location: ~/.src/opencode/history
- Format: Plain text, one command per line

---

## Tag Reference

| Tag | Description |
|-----|-------------|
| @phase1.3 | All Phase 1.3 tests |
| @repl | REPL functionality tests |
| @startup | Startup tests |
| @input | Input handling tests |
| @history | History tests |
| @shortcuts | Keyboard shortcut tests |
| @output | Output display tests |
| @status | Status bar tests |
| @themes | Theme tests |
| @exit | Exit handling tests |
| @smoke | Critical path tests |
