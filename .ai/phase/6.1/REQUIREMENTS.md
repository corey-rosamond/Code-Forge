# Phase 6.1: Slash Commands - Requirements

**Phase:** 6.1
**Name:** Slash Commands
**Dependencies:** Phase 1.3 (Basic REPL Shell), Phase 5.1 (Session Management)

---

## Overview

Phase 6.1 implements the slash command system for Code-Forge, providing built-in commands that users can invoke with `/command` syntax. Commands provide quick access to common operations, session management, context control, and system configuration.

---

## Goals

1. Parse and dispatch slash commands
2. Implement core built-in commands
3. Support command arguments and options
4. Enable custom command registration
5. Provide command help and discovery
6. Support command aliases

---

## Non-Goals (This Phase)

- Custom user-defined commands (file-based)
- Command macros
- Command chaining/piping
- Interactive command dialogs
- Command history persistence

---

## Functional Requirements

### FR-1: Command Parsing

**FR-1.1:** Command detection
- Commands start with `/`
- Case-insensitive command names
- Commands can have arguments
- Support quoted arguments

**FR-1.2:** Argument parsing
- Positional arguments
- Named arguments (`--name value`)
- Flag arguments (`--flag`)
- Quoted strings for spaces

**FR-1.3:** Validation
- Validate command exists
- Validate required arguments
- Type checking for arguments
- Helpful error messages

### FR-2: Built-in Commands

**FR-2.1:** Help and Discovery
- `/help` - Show all commands
- `/help <command>` - Show command details
- `/commands` - List available commands

**FR-2.2:** Session Commands
- `/session` - Show current session info
- `/session list` - List all sessions
- `/session new` - Create new session
- `/session resume [id]` - Resume session
- `/session delete <id>` - Delete session
- `/session title <text>` - Set session title
- `/session tag <name>` - Add tag
- `/session untag <name>` - Remove tag

**FR-2.3:** Context Commands
- `/context` - Show context status
- `/context compact` - Compact context
- `/context reset` - Clear context
- `/context mode <mode>` - Set truncation mode

**FR-2.4:** Control Commands
- `/clear` - Clear screen
- `/exit` or `/quit` - Exit application
- `/reset` - Reset to fresh state
- `/stop` - Stop current operation

**FR-2.5:** Configuration Commands
- `/config` - Show current config
- `/config get <key>` - Get config value
- `/config set <key> <value>` - Set config value
- `/model` - Show current model
- `/model <name>` - Switch model

**FR-2.6:** Debug Commands
- `/debug` - Toggle debug mode
- `/tokens` - Show token usage
- `/history` - Show message history
- `/tools` - List available tools

### FR-3: Command Registry

**FR-3.1:** Registration
- Register commands at startup
- Register commands dynamically
- Unregister commands

**FR-3.2:** Metadata
- Command name and aliases
- Description and usage
- Argument specifications
- Permission requirements

**FR-3.3:** Discovery
- List all registered commands
- Filter by category
- Search commands

### FR-4: Command Execution

**FR-4.1:** Execution context
- Access to REPL state
- Access to session manager
- Access to configuration
- Access to LLM client

**FR-4.2:** Output formatting
- Text output
- Structured output (tables)
- Color and styling
- Error formatting

**FR-4.3:** Async support
- Commands can be async
- Support for long-running commands
- Cancellation support

### FR-5: Custom Commands

**FR-5.1:** Plugin commands
- Plugins can register commands
- Commands isolated by namespace

**FR-5.2:** Validation
- Validate command names unique
- Validate no conflicts with built-ins

---

## Non-Functional Requirements

### NFR-1: Performance
- Command parsing < 1ms
- Command lookup < 1ms
- Built-in commands complete < 100ms

### NFR-2: Usability
- Tab completion for commands
- Fuzzy matching for typos
- Helpful error suggestions

### NFR-3: Extensibility
- Easy to add new commands
- Commands are modular
- Clear extension points

---

## Technical Specifications

### Package Structure

```
src/forge/commands/
├── __init__.py           # Package exports
├── parser.py             # Command parsing
├── registry.py           # Command registry
├── base.py               # Base command class
├── executor.py           # Command execution
└── builtin/              # Built-in commands
    ├── __init__.py
    ├── help.py           # Help commands
    ├── session.py        # Session commands
    ├── context.py        # Context commands
    ├── control.py        # Control commands
    ├── config.py         # Config commands
    └── debug.py          # Debug commands
```

### Class Signatures

```python
# parser.py
from dataclasses import dataclass

@dataclass
class ParsedCommand:
    """Parsed command structure."""
    name: str
    args: list[str]
    kwargs: dict[str, str]
    flags: set[str]
    raw: str

    @property
    def has_args(self) -> bool: ...
    def get_arg(self, index: int, default: str | None = None) -> str | None: ...
    def get_kwarg(self, name: str, default: str | None = None) -> str | None: ...
    def has_flag(self, name: str) -> bool: ...


class CommandParser:
    """Parses slash command input."""

    def is_command(self, text: str) -> bool:
        """Check if text is a command."""
        ...

    def parse(self, text: str) -> ParsedCommand:
        """Parse command text into structured form."""
        ...


# base.py
from abc import ABC, abstractmethod
from typing import Any

@dataclass
class CommandArgument:
    """Command argument specification."""
    name: str
    description: str
    required: bool = True
    default: Any = None
    type: type = str


@dataclass
class CommandResult:
    """Result of command execution."""
    success: bool
    output: str = ""
    error: str | None = None
    data: Any = None


class Command(ABC):
    """Base class for commands."""

    name: str
    aliases: list[str] = []
    description: str = ""
    usage: str = ""
    category: str = "general"
    arguments: list[CommandArgument] = []

    @abstractmethod
    async def execute(
        self,
        parsed: ParsedCommand,
        context: "CommandContext",
    ) -> CommandResult:
        """Execute the command."""
        ...

    def validate(self, parsed: ParsedCommand) -> list[str]:
        """Validate arguments, return errors."""
        ...


# registry.py
class CommandRegistry:
    """Registry of available commands."""

    _commands: dict[str, Command]
    _aliases: dict[str, str]

    def __init__(self): ...
    def register(self, command: Command) -> None: ...
    def unregister(self, name: str) -> bool: ...
    def get(self, name: str) -> Command | None: ...
    def resolve(self, name: str) -> Command | None: ...
    def list_commands(self, category: str | None = None) -> list[Command]: ...
    def search(self, query: str) -> list[Command]: ...

    @classmethod
    def get_instance(cls) -> "CommandRegistry": ...


# executor.py
@dataclass
class CommandContext:
    """Context provided to command execution."""
    session_manager: Any  # SessionManager
    context_manager: Any  # ContextManager
    config: Any          # Configuration
    llm: Any             # OpenRouterLLM
    repl: Any            # REPL instance
    output: Callable[[str], None]


class CommandExecutor:
    """Executes parsed commands."""

    registry: CommandRegistry

    def __init__(self, registry: CommandRegistry | None = None): ...

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Execute a parsed command."""
        ...

    def can_execute(self, name: str) -> bool:
        """Check if command can be executed."""
        ...
```

---

## Built-in Commands Reference

### Help Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all available commands |
| `/help <cmd>` | Show help for specific command |
| `/commands` | List all commands with descriptions |

### Session Commands

| Command | Description |
|---------|-------------|
| `/session` | Show current session info |
| `/session list` | List all sessions |
| `/session new` | Start new session |
| `/session resume [id]` | Resume session by ID |
| `/session delete <id>` | Delete a session |
| `/session title <text>` | Set session title |
| `/session tag <name>` | Add tag to session |
| `/session untag <name>` | Remove tag from session |

### Context Commands

| Command | Description |
|---------|-------------|
| `/context` | Show context status |
| `/context compact` | Compact context via summarization |
| `/context reset` | Clear all context |
| `/context mode <m>` | Set truncation mode |

### Control Commands

| Command | Description |
|---------|-------------|
| `/clear` | Clear screen |
| `/exit`, `/quit` | Exit application |
| `/reset` | Reset to fresh state |
| `/stop` | Stop current operation |

### Config Commands

| Command | Description |
|---------|-------------|
| `/config` | Show current configuration |
| `/config get <key>` | Get config value |
| `/config set <key> <val>` | Set config value |
| `/model` | Show current model |
| `/model <name>` | Switch to model |

### Debug Commands

| Command | Description |
|---------|-------------|
| `/debug` | Toggle debug mode |
| `/tokens` | Show token usage |
| `/history` | Show message history |
| `/tools` | List available tools |

---

## Command Output Format

```
/help

Code-Forge Commands
================

Session:
  /session          Show current session info
  /session list     List all sessions
  /session new      Start new session
  ...

Context:
  /context          Show context status
  /context compact  Compact context
  ...

Type "/help <command>" for detailed help.
```

```
/help session

/session - Session Management

Usage:
  /session              Show current session info
  /session list         List all sessions
  /session new          Create new session
  /session resume [id]  Resume session by ID
  /session delete <id>  Delete a session
  /session title <text> Set session title
  /session tag <name>   Add tag to session
  /session untag <name> Remove tag from session

Examples:
  /session list
  /session resume abc123
  /session title "Refactoring API"
```

---

## Error Messages

| Scenario | Message |
|----------|---------|
| Unknown command | `Unknown command: /foo. Type /help for available commands.` |
| Missing argument | `Missing required argument: <id>. Usage: /session delete <id>` |
| Invalid argument | `Invalid value for --model: 'xyz'. Valid options: gpt-4, claude-3, ...` |
| Command failed | `Command failed: <error message>` |

---

## Integration Points

### With REPL (Phase 1.3)
- REPL detects command input
- Commands access REPL state
- Commands can modify REPL behavior

### With Session Management (Phase 5.1)
- Session commands manage sessions
- Commands access current session
- Session state affects commands

### With Context Management (Phase 5.2)
- Context commands manage context
- Commands can compact/reset context

### With Configuration (Phase 1.2)
- Config commands read/write settings
- Model switching updates config

---

## Testing Requirements

1. Unit tests for CommandParser
2. Unit tests for CommandRegistry
3. Unit tests for each built-in command
4. Unit tests for CommandExecutor
5. Integration tests with REPL
6. Test coverage ≥ 90%

---

## Acceptance Criteria

1. Commands parsed correctly
2. All built-in commands work
3. Help system complete
4. Argument validation works
5. Error messages helpful
6. Commands can be registered dynamically
7. Command aliases work
8. Async commands supported
9. Output formatting consistent
10. Tab completion available (if terminal supports)
