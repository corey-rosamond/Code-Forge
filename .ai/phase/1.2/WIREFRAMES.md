# Phase 1.2: Configuration System - Wireframes

**Phase:** 1.2
**Name:** Configuration System
**Dependencies:** Phase 1.1

---

## Overview

Phase 1.2 has no interactive UI. Configuration is loaded from files and environment variables. This document shows configuration file formats and error messages.

---

## 1. Configuration File Format - JSON

```json
// .src/opencode/settings.json
{
  "model": {
    "default": "gpt-5",
    "fallback": ["claude-4", "gemini-2.5-pro"],
    "max_tokens": 8192,
    "temperature": 1.0,
    "routing_variant": "nitro"
  },
  "permissions": {
    "allow": [
      "Read(*)",
      "Glob(*)",
      "Grep(*)",
      "Bash(git status)",
      "Bash(git diff)"
    ],
    "ask": [
      "Write(*)",
      "Edit(*)",
      "Bash(git commit:*)",
      "Bash(git push:*)"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(sudo:*)"
    ]
  },
  "hooks": {
    "post_tool_use": [
      {
        "type": "command",
        "matcher": "Write(*.py)",
        "command": "ruff check $FILE",
        "timeout": 30
      }
    ]
  },
  "mcp_servers": {
    "github": {
      "transport": "stdio",
      "command": "npx",
      "args": ["@mcp/github"]
    }
  },
  "display": {
    "theme": "dark",
    "show_tokens": true,
    "show_cost": true,
    "streaming": true,
    "vim_mode": false
  },
  "session": {
    "auto_save": true,
    "save_interval": 60,
    "max_history": 100
  }
}
```

---

## 2. Configuration File Format - YAML

```yaml
# .src/opencode/settings.yaml
model:
  default: gpt-5
  fallback:
    - claude-4
    - gemini-2.5-pro
  max_tokens: 8192
  temperature: 1.0
  routing_variant: nitro

permissions:
  allow:
    - "Read(*)"
    - "Glob(*)"
    - "Grep(*)"
    - "Bash(git status)"
    - "Bash(git diff)"
  ask:
    - "Write(*)"
    - "Edit(*)"
    - "Bash(git commit:*)"
  deny:
    - "Bash(rm -rf:*)"
    - "Bash(sudo:*)"

hooks:
  post_tool_use:
    - type: command
      matcher: "Write(*.py)"
      command: "ruff check $FILE"
      timeout: 30

mcp_servers:
  github:
    transport: stdio
    command: npx
    args:
      - "@mcp/github"

display:
  theme: dark
  show_tokens: true
  show_cost: true
  streaming: true
  vim_mode: false

session:
  auto_save: true
  save_interval: 60
  max_history: 100
```

---

## 3. Local Override File

```json
// .src/opencode/settings.local.json
// This file should be gitignored
{
  "model": {
    "default": "my-preferred-model"
  },
  "api_key": "sk-my-personal-key"
}
```

---

## 4. Error Messages

### Invalid JSON Syntax

```
┌─────────────────────────────────────────────────────────────────┐
│ $ opencode                                                      │
│                                                                 │
│ Warning: Failed to load .src/opencode/settings.json                 │
│   Error: Expecting ',' delimiter at line 5, column 3            │
│   Using default configuration                                   │
│                                                                 │
│ >                                                               │
└─────────────────────────────────────────────────────────────────┘
```

### Validation Error

```
┌─────────────────────────────────────────────────────────────────┐
│ $ opencode                                                      │
│                                                                 │
│ Warning: Invalid configuration in .src/opencode/settings.json       │
│   - model.max_tokens: Input should be a valid integer           │
│     (got 'not-a-number')                                        │
│   - model.temperature: Input should be less than or equal to 2  │
│     (got 3.5)                                                   │
│   Using default values for invalid fields                       │
│                                                                 │
│ >                                                               │
└─────────────────────────────────────────────────────────────────┘
```

### Configuration Reload

```
┌─────────────────────────────────────────────────────────────────┐
│ > (working...)                                                  │
│                                                                 │
│ [Config] Reloaded .src/opencode/settings.json                       │
│ [Config] Model changed: gpt-5 → claude-4                        │
│                                                                 │
│ >                                                               │
└─────────────────────────────────────────────────────────────────┘
```

### Failed Reload (Keep Old Config)

```
┌─────────────────────────────────────────────────────────────────┐
│ > (working...)                                                  │
│                                                                 │
│ [Config] Failed to reload .src/opencode/settings.json               │
│   Error: Invalid JSON syntax                                    │
│   Keeping previous configuration                                │
│                                                                 │
│ >                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. File Hierarchy Visual

```
Configuration Load Order (displayed on --debug flag)
════════════════════════════════════════════════════

┌─ Priority ─┬─ Source ─────────────────────────────┬─ Status ─┐
│ 1 (lowest) │ Built-in defaults                    │ Loaded   │
│ 2          │ /etc/src/opencode/settings.json          │ Not found│
│ 3          │ ~/.src/opencode/settings.json            │ Loaded   │
│ 4          │ .src/opencode/settings.json              │ Loaded   │
│ 5          │ .src/opencode/settings.local.json        │ Loaded   │
│ 6 (highest)│ Environment variables                │ 2 vars   │
└────────────┴──────────────────────────────────────┴──────────┘

Merged Configuration:
  model.default = "gpt-5" (from: environment)
  model.max_tokens = 16384 (from: .src/opencode/settings.json)
  display.theme = "light" (from: ~/.src/opencode/settings.json)
```

---

## 6. Environment Variables Reference

```
┌─────────────────────────────────────────────────────────────────┐
│ Environment Variables                                           │
├─────────────────────────────────────────────────────────────────┤
│ OPENCODE_API_KEY      OpenRouter API key                        │
│ OPENCODE_MODEL        Default model (e.g., gpt-5, claude-4)     │
│ OPENCODE_MAX_TOKENS   Maximum tokens per request                │
│ OPENCODE_THEME        Display theme (dark, light)               │
│ OPENCODE_LOG_LEVEL    Logging level (DEBUG, INFO, WARNING)      │
│ OPENCODE_CONFIG_PATH  Custom configuration file path            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Directory Structure

```
User Configuration:
~/.src/opencode/
├── settings.json        ← User preferences
├── sessions/            ← Session storage (Phase 5.1)
├── cache/               ← Cached data
└── commands/            ← User custom commands (Phase 6.1)

Project Configuration:
.src/opencode/
├── settings.json        ← Project settings (version controlled)
├── settings.local.json  ← Local overrides (gitignored)
├── commands/            ← Project custom commands
├── agents/              ← Custom agent definitions
└── OPENCODE.md          ← Project context document
```

---

## 8. Minimal Configuration Examples

### Just Change Default Model
```json
{
  "model": {
    "default": "claude-4"
  }
}
```

### Just Add Permission Rules
```json
{
  "permissions": {
    "allow": ["Bash(npm:*)"]
  }
}
```

### Just Configure Display
```json
{
  "display": {
    "theme": "light",
    "vim_mode": true
  }
}
```

---

## Notes

- No interactive configuration UI in Phase 1.2
- All configuration is file-based or environment variables
- Error messages are shown at startup only
- Live reload shows minimal notification
- Detailed debug output available with `--debug` flag (future)
