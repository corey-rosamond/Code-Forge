# Phase 6.1: Slash Commands - Gherkin Specifications

**Phase:** 6.1
**Name:** Slash Commands
**Dependencies:** Phase 1.3 (Basic REPL Shell), Phase 5.1 (Session Management)

---

## Feature: Command Detection

### Scenario: Detect valid command
```gherkin
Given a CommandParser
When I check is_command("/help")
Then it should return True
```

### Scenario: Detect command with arguments
```gherkin
Given a CommandParser
When I check is_command("/session list --limit 10")
Then it should return True
```

### Scenario: Reject non-command input
```gherkin
Given a CommandParser
When I check is_command("hello world")
Then it should return False
```

### Scenario: Reject slash without command
```gherkin
Given a CommandParser
When I check is_command("/")
Then it should return False
```

### Scenario: Reject slash with number
```gherkin
Given a CommandParser
When I check is_command("/123")
Then it should return False
```

---

## Feature: Command Parsing

### Scenario: Parse simple command
```gherkin
Given a CommandParser
When I parse "/help"
Then parsed.name should be "help"
And parsed.args should be empty
```

### Scenario: Parse command with positional argument
```gherkin
Given a CommandParser
When I parse "/session resume abc123"
Then parsed.name should be "session"
And parsed.args should be ["resume", "abc123"]
```

### Scenario: Parse command with keyword argument
```gherkin
Given a CommandParser
When I parse "/session list --limit 10"
Then parsed.name should be "session"
And parsed.kwargs should contain {"limit": "10"}
```

### Scenario: Parse command with flag
```gherkin
Given a CommandParser
When I parse "/debug --verbose"
Then parsed.name should be "debug"
And parsed.flags should contain "verbose"
```

### Scenario: Parse command with quoted argument
```gherkin
Given a CommandParser
When I parse '/session title "My New Session"'
Then parsed.name should be "session"
And parsed.args should contain "My New Session"
```

### Scenario: Parse command case insensitive
```gherkin
Given a CommandParser
When I parse "/HELP"
Then parsed.name should be "help"
```

### Scenario: Get subcommand
```gherkin
Given a parsed command "/session list --limit 10"
When I access parsed.subcommand
Then it should return "list"
And parsed.rest_args should be empty
```

---

## Feature: Command Registry

### Scenario: Register command
```gherkin
Given an empty CommandRegistry
When I register a HelpCommand
Then the registry should contain "help"
And registry length should be 1
```

### Scenario: Register command with aliases
```gherkin
Given an empty CommandRegistry
When I register a command with aliases ["h", "?"]
Then I should be able to resolve by alias "h"
And I should be able to resolve by alias "?"
```

### Scenario: Prevent duplicate registration
```gherkin
Given a CommandRegistry with "help" registered
When I try to register another "help" command
Then it should raise ValueError
```

### Scenario: Resolve command by name
```gherkin
Given a CommandRegistry with HelpCommand
When I call resolve("help")
Then I should get the HelpCommand instance
```

### Scenario: Resolve command by alias
```gherkin
Given a CommandRegistry with ExitCommand (aliases: ["quit", "q"])
When I call resolve("quit")
Then I should get the ExitCommand instance
When I call resolve("q")
Then I should also get the ExitCommand instance
```

### Scenario: List commands by category
```gherkin
Given a CommandRegistry with mixed category commands
When I call list_commands(category=SESSION)
Then I should only get session category commands
```

### Scenario: Search commands
```gherkin
Given a CommandRegistry with various commands
When I call search("sess")
Then I should get commands with "sess" in name or description
```

---

## Feature: Command Validation

### Scenario: Validate required argument present
```gherkin
Given a command with required argument "id"
When I validate a parsed command with args=["abc123"]
Then validation should pass
And errors should be empty
```

### Scenario: Validate required argument missing
```gherkin
Given a command with required argument "id"
When I validate a parsed command with empty args
Then validation should fail
And errors should contain "Missing required argument: <id>"
```

### Scenario: Validate integer argument
```gherkin
Given a command argument with type=INTEGER
When I validate value "10"
Then validation should pass
When I validate value "abc"
Then validation should fail
```

### Scenario: Validate choice argument
```gherkin
Given a command argument with choices=["a", "b", "c"]
When I validate value "b"
Then validation should pass
When I validate value "d"
Then validation should fail with choice error
```

---

## Feature: Command Execution

### Scenario: Execute valid command
```gherkin
Given a CommandExecutor with registered commands
And a valid CommandContext
When I execute "/help"
Then I should get a successful CommandResult
And result.output should contain help text
```

### Scenario: Execute unknown command
```gherkin
Given a CommandExecutor
When I execute "/unknown"
Then I should get a failed CommandResult
And result.error should contain "Unknown command"
```

### Scenario: Suggest similar command
```gherkin
Given a CommandExecutor with "session" command
When I execute "/sesion" (typo)
Then result.error should suggest "session"
```

### Scenario: Execute command with subcommand
```gherkin
Given a CommandExecutor with session command
When I execute "/session list"
Then the list subcommand should be executed
And result should contain session list
```

### Scenario: Execute command default behavior
```gherkin
Given a CommandExecutor with session command
When I execute "/session" (no subcommand)
Then the default behavior should execute
And result should show current session info
```

---

## Feature: Help Command

### Scenario: Show general help
```gherkin
Given registered commands in various categories
When I execute "/help"
Then I should see all command categories
And I should see commands listed under each category
```

### Scenario: Show command-specific help
```gherkin
Given a registered "session" command
When I execute "/help session"
Then I should see detailed help for session command
And I should see subcommands listed
And I should see usage examples
```

### Scenario: Help for unknown command
```gherkin
Given no command named "xyz"
When I execute "/help xyz"
Then I should get an error "Unknown command: xyz"
```

---

## Feature: Session Commands

### Scenario: Show current session
```gherkin
Given an active session
When I execute "/session"
Then I should see session ID
And I should see session title
And I should see message count
And I should see token usage
```

### Scenario: Show session when none active
```gherkin
Given no active session
When I execute "/session"
Then I should see "No active session"
```

### Scenario: List sessions
```gherkin
Given 5 existing sessions
When I execute "/session list"
Then I should see a list of sessions
And each session should show ID, title, stats
```

### Scenario: List sessions with limit
```gherkin
Given 20 existing sessions
When I execute "/session list --limit 5"
Then I should see only 5 sessions
```

### Scenario: Create new session
```gherkin
Given an active session
When I execute "/session new"
Then the old session should be closed
And a new session should be created
And I should see confirmation
```

### Scenario: Create new session with title
```gherkin
When I execute '/session new --title "My Session"'
Then a new session should be created
And the title should be "My Session"
```

### Scenario: Resume session by ID
```gherkin
Given a session with ID starting with "abc123"
When I execute "/session resume abc"
Then that session should be resumed
And I should see confirmation
```

### Scenario: Resume latest session
```gherkin
Given multiple sessions exist
When I execute "/session resume"
Then the most recent session should be resumed
```

### Scenario: Delete session
```gherkin
Given a session with ID starting with "xyz"
When I execute "/session delete xyz"
Then that session should be deleted
And I should see confirmation
```

### Scenario: Set session title
```gherkin
Given an active session
When I execute "/session title Refactoring API"
Then the session title should be "Refactoring API"
```

---

## Feature: Context Commands

### Scenario: Show context status
```gherkin
Given a context manager with messages
When I execute "/context"
Then I should see token usage
And I should see available tokens
And I should see usage percentage
```

### Scenario: Compact context
```gherkin
Given a context manager with compaction enabled
When I execute "/context compact"
Then context should be compacted
And I should see new token count
```

### Scenario: Reset context
```gherkin
Given a context manager with messages
When I execute "/context reset"
Then all messages should be cleared
And token count should be 0
```

### Scenario: Set truncation mode
```gherkin
Given a context manager
When I execute "/context mode smart"
Then truncation mode should be "smart"
```

---

## Feature: Control Commands

### Scenario: Clear screen
```gherkin
When I execute "/clear"
Then the screen should be cleared
And cursor should be at top
```

### Scenario: Exit application
```gherkin
Given an active session
When I execute "/exit"
Then the session should be saved
And result.data should contain {"action": "exit"}
```

### Scenario: Reset state
```gherkin
Given an active session with messages
When I execute "/reset"
Then current session should be closed
And a new session should be started
And context should be cleared
```

### Scenario: Stop operation
```gherkin
When I execute "/stop"
Then result.data should contain {"action": "stop"}
```

---

## Feature: Config Commands

### Scenario: Show configuration
```gherkin
Given a configuration
When I execute "/config"
Then I should see current config values
```

### Scenario: Get config value
```gherkin
Given config with model="claude-3-opus"
When I execute "/config get model"
Then I should see "claude-3-opus"
```

### Scenario: Set config value
```gherkin
When I execute "/config set temperature 0.7"
Then temperature should be set to 0.7
And I should see confirmation
```

### Scenario: Show current model
```gherkin
Given model is "claude-3-opus"
When I execute "/model"
Then I should see "claude-3-opus"
```

### Scenario: Switch model
```gherkin
When I execute "/model gpt-4"
Then model should be changed to "gpt-4"
And I should see confirmation
```

---

## Feature: Debug Commands

### Scenario: Toggle debug mode
```gherkin
Given debug mode is off
When I execute "/debug"
Then debug mode should be on
And I should see "Debug mode enabled"
When I execute "/debug" again
Then debug mode should be off
```

### Scenario: Show token usage
```gherkin
Given a session with token usage
When I execute "/tokens"
Then I should see prompt tokens
And I should see completion tokens
And I should see total tokens
```

### Scenario: Show message history
```gherkin
Given a session with messages
When I execute "/history"
Then I should see message list
And each message should show role and content
```

### Scenario: List tools
```gherkin
Given registered tools
When I execute "/tools"
Then I should see list of available tools
And each tool should show name and description
```

---

## Feature: Command Aliases

### Scenario: Use help alias
```gherkin
When I execute "/?"
Then I should get same result as "/help"
```

### Scenario: Use exit alias
```gherkin
When I execute "/q"
Then I should get same result as "/exit"
```

### Scenario: Use session alias
```gherkin
When I execute "/s list"
Then I should get same result as "/session list"
```

---

## Feature: Error Handling

### Scenario: Invalid command syntax
```gherkin
When I execute "/ malformed"
Then I should get a parse error
```

### Scenario: Command execution error
```gherkin
Given a command that throws an exception
When I execute that command
Then I should get a failure result
And result.error should contain error message
```

### Scenario: Missing required argument
```gherkin
When I execute "/session delete" without ID
Then I should get validation error
And error should mention missing argument
And error should show usage
```
