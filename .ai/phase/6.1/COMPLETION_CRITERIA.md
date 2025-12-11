# Phase 6.1: Slash Commands - Completion Criteria

**Phase:** 6.1
**Name:** Slash Commands
**Dependencies:** Phase 1.3 (Basic REPL Shell), Phase 5.1 (Session Management)

---

## Completion Checklist

### 1. Command Parsing (parser.py)

- [ ] `ParsedCommand` dataclass implemented
  - [ ] `name: str` - command name (lowercase)
  - [ ] `args: list[str]` - positional arguments
  - [ ] `kwargs: dict[str, str]` - keyword arguments
  - [ ] `flags: set[str]` - boolean flags
  - [ ] `raw: str` - original input
  - [ ] `has_args` property returns True if args exist
  - [ ] `subcommand` property returns first arg or None
  - [ ] `rest_args` property returns args after subcommand
  - [ ] `get_arg(index, default)` returns arg or default
  - [ ] `get_kwarg(name, default)` returns kwarg or default
  - [ ] `has_flag(name)` returns True if flag present

- [ ] `CommandParser` class implemented
  - [ ] `COMMAND_PREFIX = "/"` constant defined
  - [ ] `is_command(text)` detects `/` prefix with alpha
  - [ ] `is_command()` rejects `/` alone
  - [ ] `is_command()` rejects `/123` (number after slash)
  - [ ] `parse(text)` returns ParsedCommand
  - [ ] Parse handles quoted strings with spaces
  - [ ] Parse handles `--key value` syntax
  - [ ] Parse handles `--key=value` syntax
  - [ ] Parse handles `--flag` boolean flags
  - [ ] Parse handles `-f` short flags
  - [ ] Parse is case-insensitive for command name
  - [ ] `suggest_command(text, available)` uses Levenshtein distance

### 2. Command Base Classes (base.py)

- [ ] `ArgumentType` enum implemented
  - [ ] STRING, INTEGER, BOOLEAN, CHOICE, PATH types

- [ ] `CommandArgument` dataclass implemented
  - [ ] `name: str` - argument name
  - [ ] `description: str` - help text
  - [ ] `required: bool = True`
  - [ ] `default: Any = None`
  - [ ] `type: ArgumentType = STRING`
  - [ ] `choices: list[str] = None`
  - [ ] `validate(value)` returns (success, error)

- [ ] `CommandCategory` enum implemented
  - [ ] GENERAL, SESSION, CONTEXT, CONTROL, CONFIG, DEBUG

- [ ] `CommandResult` dataclass implemented
  - [ ] `success: bool`
  - [ ] `output: str = ""`
  - [ ] `error: str | None = None`
  - [ ] `data: Any = None`
  - [ ] `ok(output, data)` class method
  - [ ] `fail(error, output)` class method

- [ ] `Command` abstract base class implemented
  - [ ] `name: str` property
  - [ ] `aliases: list[str] = []` property
  - [ ] `description: str` property
  - [ ] `usage: str` property
  - [ ] `category: CommandCategory` property
  - [ ] `arguments: list[CommandArgument]` property
  - [ ] `execute(parsed, context)` abstract async method
  - [ ] `validate(parsed)` returns list of errors
  - [ ] `get_help()` returns formatted help string

- [ ] `SubcommandHandler` class implemented
  - [ ] `subcommands: dict[str, Command]`
  - [ ] `execute()` dispatches to subcommand
  - [ ] `execute_default()` called when no subcommand
  - [ ] `get_help()` includes subcommand listing

### 3. Command Registry (registry.py)

- [ ] `CommandRegistry` singleton implemented
  - [ ] `_instance` class variable for singleton
  - [ ] `_commands: dict[str, Command]` storage
  - [ ] `_aliases: dict[str, str]` alias mapping
  - [ ] `get_instance()` returns singleton
  - [ ] `reset_instance()` clears singleton (for tests)
  - [ ] `register(command)` adds command
  - [ ] `register()` adds aliases to alias map
  - [ ] `register()` raises ValueError on duplicate
  - [ ] `unregister(name)` removes command
  - [ ] `get(name)` returns command or None
  - [ ] `resolve(name)` checks aliases too
  - [ ] `list_commands(category)` filters by category
  - [ ] `list_names()` returns all command names
  - [ ] `search(query)` finds matching commands
  - [ ] `get_categories()` returns grouped commands

### 4. Command Executor (executor.py)

- [ ] `CommandContext` dataclass implemented
  - [ ] `session_manager: SessionManager | None`
  - [ ] `context_manager: ContextManager | None`
  - [ ] `config: Configuration | None`
  - [ ] `llm: OpenRouterLLM | None`
  - [ ] `repl: REPL | None`
  - [ ] `output: Callable[[str], None]`
  - [ ] `print(text)` helper method

- [ ] `CommandExecutor` class implemented
  - [ ] `registry: CommandRegistry`
  - [ ] `parser: CommandParser`
  - [ ] `__init__(registry, parser)` accepts optional params
  - [ ] `execute(input_text, context)` full execution flow
  - [ ] `execute()` parses input
  - [ ] `execute()` resolves command from registry
  - [ ] `execute()` validates arguments
  - [ ] `execute()` calls command.execute()
  - [ ] `execute()` returns CommandResult
  - [ ] `execute()` handles unknown command with suggestion
  - [ ] `can_execute(name)` checks if command exists
  - [ ] `is_command(text)` delegates to parser

### 5. Built-in Commands (builtin/)

#### Help Commands (help.py)

- [ ] `/help` shows all commands by category
- [ ] `/help <command>` shows command-specific help
- [ ] `/help` displays usage examples
- [ ] `/commands` lists all available commands
- [ ] Help aliases: `?`, `h`

#### Session Commands (session.py)

- [ ] `/session` shows current session info
- [ ] `/session list` lists all sessions
- [ ] `/session list --limit N` limits results
- [ ] `/session new` creates new session
- [ ] `/session new --title "text"` with title
- [ ] `/session resume [id]` resumes by ID prefix
- [ ] `/session resume` resumes most recent
- [ ] `/session delete <id>` deletes session
- [ ] `/session title <text>` sets title
- [ ] `/session tag <name>` adds tag
- [ ] `/session untag <name>` removes tag
- [ ] Session aliases: `sess`, `s`

#### Context Commands (context.py)

- [ ] `/context` shows context status
- [ ] `/context compact` triggers compaction
- [ ] `/context reset` clears all messages
- [ ] `/context mode <mode>` sets truncation mode
- [ ] Mode validates against: sliding_window, token_budget, smart, summarize
- [ ] Context aliases: `ctx`, `c`

#### Control Commands (control.py)

- [ ] `/clear` clears screen
- [ ] `/exit` exits application
- [ ] `/exit` saves session before exit
- [ ] `/reset` resets to fresh state
- [ ] `/stop` stops current operation
- [ ] Exit aliases: `quit`, `q`
- [ ] Clear aliases: `cls`

#### Config Commands (config.py)

- [ ] `/config` shows current configuration
- [ ] `/config get <key>` gets config value
- [ ] `/config set <key> <value>` sets config value
- [ ] `/model` shows current model
- [ ] `/model <name>` switches model
- [ ] `/model` updates context limits on switch
- [ ] Config aliases: `cfg`

#### Debug Commands (debug.py)

- [ ] `/debug` toggles debug mode
- [ ] `/tokens` shows token usage
- [ ] `/history` shows message history
- [ ] `/history --limit N` limits results
- [ ] `/tools` lists available tools
- [ ] Debug aliases: `dbg`

### 6. Error Handling

- [ ] Unknown command shows suggestion
- [ ] Missing required argument shows usage
- [ ] Invalid argument value shows valid options
- [ ] Command execution errors captured gracefully
- [ ] All errors include helpful next steps

### 7. Integration

- [ ] REPL detects commands via `is_command()`
- [ ] REPL routes commands to CommandExecutor
- [ ] Commands access session manager via context
- [ ] Commands access context manager via context
- [ ] Commands access configuration via context
- [ ] Commands can output to REPL

### 8. Testing

- [ ] Unit tests for ParsedCommand
- [ ] Unit tests for CommandParser.is_command()
- [ ] Unit tests for CommandParser.parse()
- [ ] Unit tests for CommandRegistry
- [ ] Unit tests for CommandExecutor
- [ ] Unit tests for each built-in command
- [ ] Integration tests with mock REPL
- [ ] Test coverage ≥ 90%

### 9. Code Quality

- [ ] McCabe complexity ≤ 10 for all functions
- [ ] Type hints on all public methods
- [ ] Docstrings on all public classes/methods
- [ ] No circular imports
- [ ] Follows project code style
- [ ] All imports explicit (no star imports)

---

## Verification Commands

```bash
# Run unit tests
pytest tests/commands/ -v

# Run with coverage
pytest tests/commands/ --cov=src/forge/commands --cov-report=term-missing

# Check coverage threshold
pytest tests/commands/ --cov=src/forge/commands --cov-fail-under=90

# Type checking
mypy src/forge/commands/

# Complexity check
flake8 src/forge/commands/ --max-complexity=10

# Lint check
ruff check src/forge/commands/
```

---

## Test Scenarios

### Command Detection Tests

```python
def test_is_command_valid():
    parser = CommandParser()
    assert parser.is_command("/help") == True
    assert parser.is_command("/session list") == True

def test_is_command_invalid():
    parser = CommandParser()
    assert parser.is_command("hello") == False
    assert parser.is_command("/") == False
    assert parser.is_command("/123") == False
```

### Command Parsing Tests

```python
def test_parse_simple():
    parser = CommandParser()
    result = parser.parse("/help")
    assert result.name == "help"
    assert result.args == []

def test_parse_with_args():
    parser = CommandParser()
    result = parser.parse("/session resume abc123")
    assert result.name == "session"
    assert result.args == ["resume", "abc123"]

def test_parse_with_kwargs():
    parser = CommandParser()
    result = parser.parse("/session list --limit 10")
    assert result.kwargs == {"limit": "10"}

def test_parse_quoted_string():
    parser = CommandParser()
    result = parser.parse('/session title "My Session"')
    assert "My Session" in result.args
```

### Command Registry Tests

```python
def test_register_command():
    registry = CommandRegistry()
    registry.register(HelpCommand())
    assert registry.get("help") is not None

def test_resolve_alias():
    registry = CommandRegistry()
    registry.register(ExitCommand())  # aliases: quit, q
    assert registry.resolve("quit") is not None
    assert registry.resolve("q") is not None

def test_duplicate_registration():
    registry = CommandRegistry()
    registry.register(HelpCommand())
    with pytest.raises(ValueError):
        registry.register(HelpCommand())
```

### Command Execution Tests

```python
async def test_execute_help():
    executor = CommandExecutor()
    context = CommandContext(output=print)
    result = await executor.execute("/help", context)
    assert result.success == True
    assert "Commands" in result.output

async def test_execute_unknown():
    executor = CommandExecutor()
    context = CommandContext(output=print)
    result = await executor.execute("/xyz", context)
    assert result.success == False
    assert "Unknown command" in result.error
```

---

## Definition of Done

Phase 6.1 is complete when:

1. All checklist items are checked off
2. All unit tests pass
3. Test coverage is ≥ 90%
4. Code complexity is ≤ 10
5. Type checking passes with no errors
6. All built-in commands function correctly
7. Commands integrate seamlessly with REPL
8. Error messages are helpful and actionable
9. Documentation is complete and accurate
10. Code review approved

---

## Dependencies Verification

Before starting Phase 6.1, verify:

- [ ] Phase 1.3 (Basic REPL Shell) is complete
  - [ ] REPL input loop functioning
  - [ ] Output display working

- [ ] Phase 5.1 (Session Management) is complete
  - [ ] SessionManager can create/resume/list sessions
  - [ ] Session persistence working

---

## Notes

- Commands are the primary user interface for REPL control
- Command system is designed for extensibility (plugins later)
- Async execution allows for long-running commands
- Context provides access to all system components
- Error handling should guide users to correct usage
