# Phase 6.1: Slash Commands - UML Diagrams

**Phase:** 6.1
**Name:** Slash Commands
**Dependencies:** Phase 1.3 (Basic REPL Shell), Phase 5.1 (Session Management)

---

## 1. Class Diagram - Command Parsing

```mermaid
classDiagram
    class ParsedCommand {
        +name: str
        +args: list~str~
        +kwargs: dict~str, str~
        +flags: set~str~
        +raw: str
        +has_args: bool
        +subcommand: str?
        +rest_args: list~str~
        +get_arg(index, default) str?
        +get_kwarg(name, default) str?
        +has_flag(name) bool
    }

    class CommandParser {
        +COMMAND_PREFIX: str$
        +is_command(text) bool
        +parse(text) ParsedCommand
        +suggest_command(text, available) str?
        -_similarity(s1, s2) float
    }

    CommandParser --> ParsedCommand : creates
```

---

## 2. Class Diagram - Command Base

```mermaid
classDiagram
    class ArgumentType {
        <<enumeration>>
        STRING = "string"
        INTEGER = "integer"
        BOOLEAN = "boolean"
        CHOICE = "choice"
        PATH = "path"
    }

    class CommandArgument {
        +name: str
        +description: str
        +required: bool
        +default: Any
        +type: ArgumentType
        +choices: list~str~
        +validate(value) tuple
    }

    class CommandCategory {
        <<enumeration>>
        GENERAL = "general"
        SESSION = "session"
        CONTEXT = "context"
        CONTROL = "control"
        CONFIG = "config"
        DEBUG = "debug"
    }

    class CommandResult {
        +success: bool
        +output: str
        +error: str?
        +data: Any
        +ok(output, data)$ CommandResult
        +fail(error, output)$ CommandResult
    }

    class Command {
        <<abstract>>
        +name: str
        +aliases: list~str~
        +description: str
        +usage: str
        +category: CommandCategory
        +arguments: list~CommandArgument~
        +execute(parsed, context)* CommandResult
        +validate(parsed) list~str~
        +get_help() str
    }

    class SubcommandHandler {
        +subcommands: dict~str, Command~
        +execute(parsed, context) CommandResult
        +execute_default(parsed, context) CommandResult
        +get_help() str
    }

    Command <|-- SubcommandHandler
    Command --> CommandCategory : has
    Command --> CommandArgument : has
    Command --> CommandResult : returns
    CommandArgument --> ArgumentType : has
```

---

## 3. Class Diagram - Command Registry

```mermaid
classDiagram
    class CommandRegistry {
        -_instance: CommandRegistry$
        -_commands: dict~str, Command~
        -_aliases: dict~str, str~
        +get_instance()$ CommandRegistry
        +reset_instance()$ void
        +register(command) void
        +unregister(name) bool
        +get(name) Command?
        +resolve(name) Command?
        +list_commands(category?) list~Command~
        +list_names() list~str~
        +search(query) list~Command~
        +get_categories() dict
    }

    CommandRegistry o-- Command : contains
```

---

## 4. Class Diagram - Command Execution

```mermaid
classDiagram
    class CommandContext {
        +session_manager: SessionManager?
        +context_manager: ContextManager?
        +config: Configuration?
        +llm: OpenRouterLLM?
        +repl: REPL?
        +output: Callable
        +print(text) void
    }

    class CommandExecutor {
        +registry: CommandRegistry
        +parser: CommandParser
        +__init__(registry?, parser?)
        +execute(input_text, context) CommandResult
        +can_execute(name) bool
        +is_command(text) bool
    }

    CommandExecutor --> CommandRegistry : uses
    CommandExecutor --> CommandParser : uses
    CommandExecutor --> CommandContext : receives
    CommandExecutor --> CommandResult : returns
```

---

## 5. Class Diagram - Built-in Commands

```mermaid
classDiagram
    class Command {
        <<abstract>>
    }

    class HelpCommand {
        +name: "help"
        +aliases: ["?", "h"]
        +execute(parsed, context) CommandResult
    }

    class SessionCommand {
        +name: "session"
        +aliases: ["sess", "s"]
        +subcommands: dict
    }

    class SessionListCommand {
        +name: "list"
    }

    class SessionNewCommand {
        +name: "new"
    }

    class SessionResumeCommand {
        +name: "resume"
    }

    class ContextCommand {
        +name: "context"
        +subcommands: dict
    }

    class ClearCommand {
        +name: "clear"
        +aliases: ["cls"]
    }

    class ExitCommand {
        +name: "exit"
        +aliases: ["quit", "q"]
    }

    class ConfigCommand {
        +name: "config"
    }

    class DebugCommand {
        +name: "debug"
    }

    Command <|-- HelpCommand
    Command <|-- SessionCommand
    Command <|-- ContextCommand
    Command <|-- ClearCommand
    Command <|-- ExitCommand
    Command <|-- ConfigCommand
    Command <|-- DebugCommand

    SubcommandHandler <|-- SessionCommand
    SubcommandHandler <|-- ContextCommand

    SessionCommand --> SessionListCommand
    SessionCommand --> SessionNewCommand
    SessionCommand --> SessionResumeCommand
```

---

## 6. Package Diagram

```mermaid
flowchart TB
    subgraph CommandsPkg["src/opencode/commands/"]
        INIT["__init__.py"]
        PARSER["parser.py<br/>CommandParser, ParsedCommand"]
        BASE["base.py<br/>Command, CommandResult"]
        REGISTRY["registry.py<br/>CommandRegistry"]
        EXECUTOR["executor.py<br/>CommandExecutor, CommandContext"]

        subgraph BuiltinPkg["builtin/"]
            HELP["help.py"]
            SESSION["session.py"]
            CONTEXT["context.py"]
            CONTROL["control.py"]
            CONFIG["config.py"]
            DEBUG["debug.py"]
        end
    end

    subgraph REPLPkg["src/opencode/repl/"]
        REPL["repl.py"]
    end

    subgraph SessionsPkg["src/opencode/sessions/"]
        SESSION_MGR["manager.py"]
    end

    EXECUTOR --> PARSER
    EXECUTOR --> REGISTRY
    EXECUTOR --> BASE

    REPL --> EXECUTOR

    BuiltinPkg --> BASE
    SESSION --> SESSION_MGR

    INIT --> PARSER
    INIT --> BASE
    INIT --> REGISTRY
    INIT --> EXECUTOR
```

---

## 7. Sequence Diagram - Command Execution

```mermaid
sequenceDiagram
    participant REPL
    participant Executor as CommandExecutor
    participant Parser as CommandParser
    participant Registry as CommandRegistry
    participant Command
    participant Context as CommandContext

    REPL->>Executor: execute("/session list", context)

    Executor->>Parser: parse("/session list")
    Parser-->>Executor: ParsedCommand(name="session", args=["list"])

    Executor->>Registry: resolve("session")
    Registry-->>Executor: SessionCommand

    Executor->>Command: validate(parsed)
    Command-->>Executor: [] (no errors)

    Executor->>Command: execute(parsed, context)

    Command->>Command: Lookup subcommand "list"
    Command->>Context: session_manager.list_sessions()
    Context-->>Command: [SessionSummary, ...]

    Command-->>Executor: CommandResult(success=True, output="...")

    Executor-->>REPL: CommandResult
    REPL->>REPL: Print output
```

---

## 8. Sequence Diagram - Command with Subcommands

```mermaid
sequenceDiagram
    participant Executor as CommandExecutor
    participant Session as SessionCommand
    participant List as SessionListCommand
    participant Context as CommandContext

    Executor->>Session: execute(parsed, context)

    Note over Session: parsed.subcommand = "list"

    Session->>Session: Lookup subcommand "list"

    Session->>List: execute(sub_parsed, context)

    List->>Context: session_manager.list_sessions()
    Context-->>List: [sessions...]

    List->>List: Format output

    List-->>Session: CommandResult(output=...)

    Session-->>Executor: CommandResult
```

---

## 9. Sequence Diagram - Command Parsing

```mermaid
sequenceDiagram
    participant Parser as CommandParser
    participant Shlex

    Parser->>Parser: is_command("/session list --limit 10")

    Note over Parser: Starts with /, has alpha after /

    Parser-->>Parser: True

    Parser->>Parser: parse("/session list --limit 10")

    Parser->>Parser: Remove prefix "/"
    Parser->>Shlex: split("session list --limit 10")
    Shlex-->>Parser: ["session", "list", "--limit", "10"]

    Parser->>Parser: name = "session"

    loop For each token
        Parser->>Parser: Check if --key, -f, or positional
    end

    Parser-->>Parser: ParsedCommand(
        name="session",
        args=["list"],
        kwargs={"limit": "10"},
        flags=set()
    )
```

---

## 10. State Diagram - Command Execution

```mermaid
stateDiagram-v2
    [*] --> Parsing: Input received

    Parsing --> Invalid: Not a command
    Parsing --> Parsed: Valid command

    Invalid --> [*]: Return error

    Parsed --> Lookup: Command parsed

    Lookup --> NotFound: Command unknown
    Lookup --> Found: Command found

    NotFound --> Suggest: Check similar
    Suggest --> [*]: Return error with suggestion

    Found --> Validating: Command found

    Validating --> ValidationFailed: Invalid args
    Validating --> Validated: Args valid

    ValidationFailed --> [*]: Return errors

    Validated --> Executing: Execute command

    Executing --> Success: Command succeeded
    Executing --> Failed: Command failed

    Success --> [*]: Return result
    Failed --> [*]: Return error
```

---

## 11. Activity Diagram - Parse Command

```mermaid
flowchart TD
    START([parse called]) --> CHECK{Starts with<br/>/char?}

    CHECK -->|No| ERROR([Raise ValueError])
    CHECK -->|Yes| REMOVE[Remove prefix]

    REMOVE --> SHLEX[Split with shlex]

    SHLEX --> SHLEX_OK{Parse<br/>successful?}

    SHLEX_OK -->|No| FALLBACK[Simple split]
    SHLEX_OK -->|Yes| TOKENS

    FALLBACK --> TOKENS[Get tokens]

    TOKENS --> EMPTY{Empty<br/>tokens?}

    EMPTY -->|Yes| ERROR

    EMPTY -->|No| NAME[First token = name]

    NAME --> LOOP[Process remaining tokens]

    LOOP --> TOKEN{Token type?}

    TOKEN -->|--key=value| KWARG_EQ[Add to kwargs]
    TOKEN -->|--key| CHECK_NEXT{Next is<br/>value?}
    TOKEN -->|-f| FLAG[Add to flags]
    TOKEN -->|other| ARG[Add to args]

    CHECK_NEXT -->|Yes| KWARG_VAL[Add key:value]
    CHECK_NEXT -->|No| FLAG2[Add to flags]

    KWARG_EQ --> MORE{More<br/>tokens?}
    KWARG_VAL --> MORE
    FLAG --> MORE
    FLAG2 --> MORE
    ARG --> MORE

    MORE -->|Yes| LOOP
    MORE -->|No| RESULT([Return ParsedCommand])
```

---

## 12. Activity Diagram - Execute Command

```mermaid
flowchart TD
    START([execute called]) --> PARSE[Parse input]

    PARSE --> PARSE_OK{Parse<br/>successful?}

    PARSE_OK -->|No| PARSE_ERR([Return fail result])
    PARSE_OK -->|Yes| LOOKUP[Lookup command]

    LOOKUP --> FOUND{Command<br/>found?}

    FOUND -->|No| SUGGEST[Check for suggestion]
    SUGGEST --> SUGGEST_ERR([Return fail with hint])

    FOUND -->|Yes| VALIDATE[Validate arguments]

    VALIDATE --> VALID{Valid?}

    VALID -->|No| VALID_ERR([Return validation errors])
    VALID -->|Yes| EXECUTE[Execute command]

    EXECUTE --> EXEC_OK{Execution<br/>successful?}

    EXEC_OK -->|No| EXEC_ERR([Return error result])
    EXEC_OK -->|Yes| SUCCESS([Return success result])
```

---

## 13. Component Diagram - Command Flow

```mermaid
flowchart LR
    subgraph Input
        USER[User Input]
    end

    subgraph Parsing
        PARSER[CommandParser]
        PARSED[ParsedCommand]
    end

    subgraph Dispatch
        REGISTRY[CommandRegistry]
        EXECUTOR[CommandExecutor]
    end

    subgraph Execution
        COMMAND[Command]
        CONTEXT[CommandContext]
    end

    subgraph Output
        RESULT[CommandResult]
        DISPLAY[Output Display]
    end

    USER --> PARSER
    PARSER --> PARSED
    PARSED --> EXECUTOR
    EXECUTOR --> REGISTRY
    REGISTRY --> COMMAND
    COMMAND --> CONTEXT
    COMMAND --> RESULT
    RESULT --> DISPLAY
```

---

## 14. Command Category Organization

```
CommandRegistry
├── GENERAL
│   ├── /help
│   └── /commands
├── SESSION
│   ├── /session
│   ├── /session list
│   ├── /session new
│   ├── /session resume
│   ├── /session delete
│   └── /session title
├── CONTEXT
│   ├── /context
│   ├── /context compact
│   ├── /context reset
│   └── /context mode
├── CONTROL
│   ├── /clear
│   ├── /exit
│   ├── /reset
│   └── /stop
├── CONFIG
│   ├── /config
│   ├── /config get
│   ├── /config set
│   └── /model
└── DEBUG
    ├── /debug
    ├── /tokens
    ├── /history
    └── /tools
```

---

## 15. Command Argument Flow

```mermaid
flowchart TB
    subgraph Input["Input: /session resume abc123 --verbose"]
        RAW[Raw Text]
    end

    subgraph Parsed["ParsedCommand"]
        NAME["name: session"]
        ARGS["args: [resume, abc123]"]
        FLAGS["flags: {verbose}"]
    end

    subgraph Subcommand["SubcommandHandler"]
        SUB["subcommand: resume"]
        SUB_ARGS["rest_args: [abc123]"]
    end

    subgraph Execution["ResumeCommand"]
        SESSION_ID["session_id = abc123"]
        VERBOSE["verbose = true"]
    end

    RAW --> NAME
    RAW --> ARGS
    RAW --> FLAGS

    ARGS --> SUB
    ARGS --> SUB_ARGS

    SUB_ARGS --> SESSION_ID
    FLAGS --> VERBOSE
```

---

## Notes

- Commands are identified by `/` prefix
- Command names are case-insensitive
- Subcommand pattern allows hierarchical commands
- CommandContext provides access to system components
- CommandResult carries success/error and output
- Registry is singleton for consistent state
- Built-in commands organized by category
