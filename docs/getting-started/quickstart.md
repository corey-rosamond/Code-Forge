# Quick Start Guide

This guide will get you up and running with Code-Forge in 5 minutes.

## Starting Code-Forge

After installation, start Code-Forge:

```bash
forge
```

You'll see a welcome message and a prompt.

## Basic Usage

### Reading Files

Ask Code-Forge to read a file:

```
You: Read the README.md file

[Reading README.md...]

# My Project
This is my project...
```

### Searching Code

Search for files:

```
You: Find all Python files in src/

[Searching src/**/*.py...]

Found 15 files:
- src/main.py
- src/utils.py
...
```

Search for content:

```
You: Search for "def main" in the codebase

[Searching for "def main"...]

Found in 3 files:
- src/main.py:15
- src/cli.py:42
...
```

### Editing Files

Make targeted edits:

```
You: In src/main.py, change the function name from "process" to "handle"

[Editing src/main.py...]

Successfully replaced "def process" with "def handle"
```

### Running Commands

Execute shell commands:

```
You: Run the tests

[Running: pytest tests/]

======================== 100 passed in 5.2s ========================
```

## Slash Commands

Use slash commands for quick actions:

| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/session list` | List sessions |
| `/session new` | Start new session |
| `/model <name>` | Change AI model |
| `/clear` | Clear screen |
| `/exit` | Exit Code-Forge |

## Session Management

Sessions persist your conversation:

```
# List sessions
/session list

# Resume a session
/session resume abc123

# Start fresh
/session new --title "Bug fix"
```

## Changing Models

Switch between AI models:

```
/model anthropic/claude-3-opus
```

## Tips for Effective Use

1. **Be specific** - Tell Code-Forge exactly what file and what change you want
2. **Verify changes** - Ask to read a file after editing to confirm
3. **Use sessions** - Resume sessions to continue previous work
4. **Leverage search** - Use glob and grep before editing to find the right location

## Next Steps

- Read the [User Guide](../user-guide/commands.md) for detailed command usage
- Check [Tool Reference](../reference/tools.md) for available tools
- Learn about [Configuration](../reference/configuration.md) options
