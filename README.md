# OpenCode

A Claude Code alternative providing access to 400+ AI models via OpenRouter API with LangChain 1.0 integration for agent orchestration.

## Features

- **Multi-Model Access**: Connect to 400+ AI models through OpenRouter API
- **LangChain Integration**: ReAct-style agent executor with tool loop
- **Comprehensive Tool System**: File operations, shell execution, pattern matching
- **Permission System**: Granular control with glob patterns, regex, and rule hierarchies
- **Hooks System**: Execute custom shell commands on lifecycle events
- **Interactive REPL**: Rich terminal UI with themes and status bar
- **Session Management**: Persistent conversations with SQLite storage (coming soon)

## Installation

```bash
# Clone the repository
git clone git@github.com:corey-rosamond/OpenCode.git
cd OpenCode

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"
```

## Usage

```bash
# Start interactive REPL
opencode

# Show version
opencode --version

# Show help
opencode --help
```

## Project Structure

```
OpenCode/
├── src/opencode/           # Source code
│   ├── core/               # Core interfaces, types, errors, logging
│   ├── config/             # Configuration system
│   ├── cli/                # REPL, themes, status bar
│   ├── tools/              # Tool system
│   │   ├── file/           # Read, Write, Edit, Glob, Grep tools
│   │   └── execution/      # Bash, BashOutput, KillShell tools
│   ├── llm/                # OpenRouter client, streaming
│   ├── langchain/          # LangChain integration, agent
│   ├── permissions/        # Permission checker, rules, prompts
│   └── hooks/              # Event hooks, executor
├── tests/                  # Test suite (1247 tests)
└── .ai/                    # AI planning documentation
```

## Tool System

### File Tools

```python
from opencode.tools.file import ReadTool, WriteTool, EditTool, GlobTool, GrepTool

# Read files with offset/limit support
read = ReadTool()
result = await read.execute(file_path="/path/to/file.py")

# Write files with automatic directory creation
write = WriteTool()
result = await write.execute(file_path="/path/to/new.py", content="...")

# Edit files with find/replace
edit = EditTool()
result = await edit.execute(
    file_path="/path/to/file.py",
    old_string="def old_func",
    new_string="def new_func",
)

# Glob pattern matching
glob = GlobTool()
result = await glob.execute(pattern="**/*.py")

# Content search with regex
grep = GrepTool()
result = await grep.execute(pattern="class.*Tool", path="/src")
```

### Execution Tools

```python
from opencode.tools.execution import BashTool, BashOutputTool, KillShellTool

# Execute shell commands
bash = BashTool()
result = await bash.execute(command="ls -la", timeout=30000)

# Run in background
result = await bash.execute(command="pytest", run_in_background=True)

# Get background output
output = BashOutputTool()
result = await output.execute(bash_id="abc123")

# Kill background process
kill = KillShellTool()
result = await kill.execute(shell_id="abc123")
```

## Permission System

```python
from opencode.permissions import PermissionChecker, PermissionLevel

checker = PermissionChecker()

# Check if tool execution is allowed
result = checker.check("bash", {"command": "ls"})
if result.level == PermissionLevel.ALLOWED:
    # Execute tool
    pass
elif result.level == PermissionLevel.ASK:
    # Prompt user for confirmation
    pass
elif result.level == PermissionLevel.DENIED:
    # Block execution
    pass
```

## Hooks System

Execute custom shell commands in response to lifecycle events.

### Event Types

| Category | Events |
|----------|--------|
| Tool | `tool:pre_execute`, `tool:post_execute`, `tool:error` |
| LLM | `llm:pre_request`, `llm:post_response`, `llm:stream_start`, `llm:stream_end`, `llm:error` |
| Session | `session:start`, `session:end`, `session:save`, `session:load` |
| Permission | `permission:check`, `permission:denied` |
| User | `user:input`, `user:abort` |

### Example Configuration

```json
{
  "hooks": [
    {
      "event": "tool:pre_execute:bash",
      "command": "echo \"Executing: $OPENCODE_TOOL_NAME\"",
      "timeout": 5.0
    },
    {
      "event": "session:start",
      "command": "notify-send 'OpenCode' 'Session started'"
    }
  ]
}
```

### Programmatic Usage

```python
from opencode.hooks import HookRegistry, HookExecutor, HookEvent, Hook, fire_event

# Register a hook
registry = HookRegistry.get_instance()
registry.register(Hook(
    event_pattern="tool:pre_execute",
    command="echo 'Executing tool: $OPENCODE_TOOL_NAME'",
    timeout=10.0,
))

# Fire an event
event = HookEvent.tool_pre_execute("bash", {"command": "ls"})
results = await fire_event(event)

# Check if operation should continue
for result in results:
    if not result.should_continue:
        print(f"Blocked by hook: {result.hook.event_pattern}")
```

## Configuration

Configuration is loaded from multiple sources with precedence:

1. Environment variables (`OPENCODE_*`)
2. Project config (`.opencode/config.toml`)
3. Global config (`~/.config/opencode/config.toml`)

### Example Configuration

```toml
[llm]
model = "anthropic/claude-3-5-sonnet"
temperature = 0.7
max_tokens = 4096

[permissions]
default_level = "ask"

[hooks]
enabled = true
```

## Development

```bash
# Activate virtual environment
source .venv/bin/activate

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src/opencode --cov-report=term-missing

# Type checking (strict mode)
mypy src/opencode/

# Linting
ruff check src/opencode/

# Format code
ruff format src/opencode/
```

### Quality Gates

All code must pass:
- **mypy**: Strict mode with no errors
- **ruff**: No linting violations
- **pytest**: All tests passing
- **coverage**: Minimum 90% code coverage

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI (REPL)                          │
├─────────────────────────────────────────────────────────────┤
│                    LangChain Agent                          │
├──────────────────┬──────────────────┬───────────────────────┤
│   Tool System    │  Permission Sys  │     Hooks System      │
├──────────────────┼──────────────────┼───────────────────────┤
│   File Tools     │   Rule Matcher   │   Event Executor      │
│   Exec Tools     │   Checker        │   Registry            │
├──────────────────┴──────────────────┴───────────────────────┤
│                   OpenRouter Client                         │
├─────────────────────────────────────────────────────────────┤
│                    Core Foundation                          │
│            (Interfaces, Types, Errors, Logging)             │
└─────────────────────────────────────────────────────────────┘
```

## Roadmap

| Phase | Name | Status |
|-------|------|--------|
| 1.1 | Core Foundation | Complete |
| 1.2 | Configuration System | Complete |
| 1.3 | Basic REPL Shell | Complete |
| 2.1 | Tool System Foundation | Complete |
| 2.2 | File Tools | Complete |
| 2.3 | Execution Tools | Complete |
| 3.1 | OpenRouter Client | Complete |
| 3.2 | LangChain Integration | Complete |
| 4.1 | Permission System | Complete |
| 4.2 | Hooks System | Complete |
| 5.1 | Session Management | Planned |
| 5.2 | Context Management | Planned |
| 6.1 | Slash Commands | Planned |
| 6.2 | Operating Modes | Planned |
| 7.1 | Subagents System | Planned |
| 7.2 | Skills System | Planned |
| 8.1 | MCP Protocol Support | Planned |
| 8.2 | Web Tools | Planned |
| 9.1 | Git Integration | Planned |
| 9.2 | GitHub Integration | Planned |
| 10.1 | Plugin System | Planned |
| 10.2 | Polish & Integration | Planned |

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome! Please read the planning documentation in `.ai/` before making significant changes.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure all quality gates pass
5. Submit a pull request
