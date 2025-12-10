# Slash Commands

OpenCode provides slash commands for quick actions during your session.

## Help Commands

### /help

Display help information.

```
/help              # General help
/help <command>    # Help for specific command
```

### /commands

List all available commands.

```
/commands          # List all commands
/commands --search <term>  # Search commands
```

## Session Commands

### /session

Manage sessions.

```
/session list              # List all sessions
/session new               # Start new session
/session new --title "My Session"  # With title
/session resume <id>       # Resume session
/session delete <id>       # Delete session
/session title <new-title> # Rename current session
```

## Context Commands

### /context

Manage conversation context.

```
/context              # Show context info
/context compact      # Compact old messages
/context reset        # Reset context
```

## Configuration Commands

### /config

View and modify configuration.

```
/config               # Show current config
/config get <key>     # Get specific value
/config set <key> <value>  # Set value
```

### /model

Change the AI model.

```
/model                           # Show current model
/model anthropic/claude-3-opus   # Switch model
```

## Control Commands

### /clear

Clear the terminal screen.

```
/clear
```

### /exit

Exit OpenCode.

```
/exit
```

### /reset

Reset the current session (clears messages but keeps session).

```
/reset
```

## Debug Commands

### /debug

Toggle debug mode.

```
/debug          # Toggle debug
/debug on       # Enable
/debug off      # Disable
```

### /tokens

Show token usage for current session.

```
/tokens
```

### /history

Show message history.

```
/history        # Show all
/history 10     # Show last 10
```

### /tools

List available tools.

```
/tools          # List all tools
/tools <name>   # Show tool details
```

## Plugin Commands

### /plugins

Manage plugins.

```
/plugins list           # List all plugins
/plugins info <name>    # Show plugin info
/plugins enable <name>  # Enable plugin
/plugins disable <name> # Disable plugin
/plugins reload <name>  # Reload plugin
```

## Skill Commands

### /skill

Activate specialized skills.

```
/skill list            # List available skills
/skill <name>          # Activate skill
/skill off             # Deactivate current skill
/skill info <name>     # Show skill details
```

## Command Aliases

Many commands have shorter aliases:

| Full Command | Alias |
|--------------|-------|
| /help | /h, /? |
| /session | /s |
| /context | /ctx |
| /config | /cfg |
| /clear | /cls |
| /exit | /quit, /q |
