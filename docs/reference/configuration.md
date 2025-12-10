# Configuration Reference

OpenCode can be configured via YAML files and environment variables.

## Configuration Files

Configuration is loaded from (in order of priority):

1. Project config: `.opencode/config.yaml` or `.opencode.yaml`
2. User config: `~/.config/opencode/config.yaml`
3. Environment variables

## Full Configuration Schema

```yaml
# Model Configuration
model:
  # Default model to use
  default: "anthropic/claude-3-sonnet"

  # Fallback models if primary fails
  fallback:
    - "anthropic/claude-3-haiku"
    - "openai/gpt-4-turbo"

  # Maximum tokens for completion (1-200000)
  max_tokens: 8192

  # Sampling temperature (0.0-2.0)
  temperature: 1.0

  # OpenRouter routing variant (optional)
  # Options: nitro, floor, exacto, thinking, online
  routing_variant: null

# Display Configuration
display:
  # Color theme: dark, light, or auto
  theme: dark

# Session Configuration
session:
  # Enable automatic saving
  auto_save: true

  # Auto-save interval in seconds
  auto_save_interval: 60

# Permission Configuration
permissions:
  # Patterns to auto-allow (no confirmation)
  allow:
    - "Read(*)"
    - "Glob(*)"
    - "Grep(*)"

  # Patterns requiring confirmation
  ask:
    - "Write(*)"
    - "Edit(*)"
    - "Bash(*)"

  # Patterns to block entirely
  deny:
    - "Bash(rm -rf /)"

# Hooks Configuration
hooks:
  # Pre-execution hooks
  pre:
    - matcher: "Bash(*)"
      command: "echo 'Running: $OPENCODE_COMMAND'"

  # Post-execution hooks
  post:
    - matcher: "*"
      command: "logger 'OpenCode tool executed'"

# MCP Server Configuration
mcp:
  servers:
    my-server:
      transport: stdio
      command: "my-mcp-server"
      args: ["--port", "8080"]
      enabled: true

# Plugin Configuration
plugins:
  # Enable plugin system
  enabled: true

  # Additional plugin directories
  extra_dirs:
    - "~/my-plugins"

  # Plugins to disable
  disabled:
    - "problematic-plugin"
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key | Required |
| `OPENCODE_MODEL` | Default model | claude-3-sonnet |
| `OPENCODE_CONFIG` | Config file path | Auto-detected |
| `OPENCODE_DATA_DIR` | Data directory | ~/.local/share/opencode |
| `OPENCODE_LOG_LEVEL` | Log level | INFO |

## Permission Patterns

Permission patterns support:

- `*` - Match anything
- `Tool(*)` - Match specific tool
- `Tool(arg=value)` - Match with arguments
- Regex patterns with `/pattern/`

Examples:
```yaml
permissions:
  allow:
    - "Read(*)"                    # Allow all Read operations
    - "Bash(echo *)"               # Allow echo commands
    - "/^Bash\\(git /"             # Allow git commands (regex)

  deny:
    - "Bash(rm -rf *)"             # Block recursive delete
    - "Write(/etc/*)"              # Block writing to /etc
```

## Hook Configuration

Hooks execute shell commands on events:

```yaml
hooks:
  pre:
    - matcher: "Bash(*)"
      command: "echo 'Executing: $OPENCODE_TOOL_NAME'"
      timeout: 5  # seconds

  post:
    - matcher: "*"
      command: "notify-send 'Tool completed'"
```

Available environment variables in hooks:
- `OPENCODE_TOOL_NAME` - Tool being executed
- `OPENCODE_TOOL_ARGS` - JSON of arguments
- `OPENCODE_SUCCESS` - "true" or "false" (post hooks)
