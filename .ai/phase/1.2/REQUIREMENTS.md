# Phase 1.2: Configuration System - Requirements

**Phase:** 1.2
**Name:** Configuration System
**Status:** Not Started
**Dependencies:** Phase 1.1 (Project Foundation)

---

## Overview

This phase implements the configuration system with hierarchical loading, validation, and live reload. Configuration controls all aspects of OpenCode behavior.

---

## Functional Requirements

### FR-1.2.1: Configuration File Support
- Load configuration from JSON files
- Load configuration from YAML files
- Support for `.src/opencode/settings.json` (project)
- Support for `~/.src/opencode/settings.json` (user)
- Support for `.src/opencode/settings.local.json` (local overrides, gitignored)
- Support for enterprise configuration path

### FR-1.2.2: Configuration Hierarchy
- Enterprise settings (highest priority)
- User settings (~/.src/opencode/)
- Project settings (.src/opencode/)
- Local overrides (.src/opencode/settings.local.json)
- Environment variables (OPENCODE_* prefix)
- Default values (lowest priority)

### FR-1.2.3: Environment Variable Support
- OPENCODE_API_KEY - OpenRouter API key
- OPENCODE_MODEL - Default model
- OPENCODE_LOG_LEVEL - Logging level
- OPENCODE_CONFIG_PATH - Custom config path
- Parse environment variables and merge into config

### FR-1.2.4: Configuration Schema
- Define Pydantic models for all configuration sections
- Validate configuration on load
- Provide helpful validation error messages
- Support default values for all optional fields

### FR-1.2.5: Configuration Sections
- `model` - Default model settings
- `permissions` - Allow/ask/deny lists
- `hooks` - Hook configurations
- `mcp_servers` - MCP server definitions
- `plugins` - Plugin configurations
- `display` - UI/display preferences
- `session` - Session management settings

### FR-1.2.6: Live Reload
- Watch configuration files for changes
- Reload configuration without restart
- Emit events on configuration change
- Validate before applying changes

### FR-1.2.7: Configuration Access
- Provide typed access to configuration values
- Support dot-notation for nested values
- Cache configuration for performance
- Thread-safe configuration access

---

## Non-Functional Requirements

### NFR-1.2.1: Performance
- Configuration load time < 100ms
- Watch mechanism uses minimal resources
- Cached access for hot paths

### NFR-1.2.2: Reliability
- Graceful fallback to defaults on error
- Never crash on invalid configuration
- Log warnings for issues
- Preserve working config on failed reload

### NFR-1.2.3: Security
- No secrets in plain text (warn if detected)
- Secure API key handling
- Don't log sensitive values

---

## Technical Specifications

### Configuration Schema

```python
from pydantic import BaseModel, Field
from typing import Dict, List, Any
from pathlib import Path

class ModelConfig(BaseModel):
    """Model-related configuration."""
    default: str = "gpt-5"
    fallback: List[str] = ["claude-4", "gemini-2.5-pro"]
    max_tokens: int = 8192
    temperature: float = 1.0
    routing_variant: str | None = None  # :nitro, :floor, :exacto, etc.

class PermissionConfig(BaseModel):
    """Permission system configuration."""
    allow: List[str] = []  # Patterns for auto-allow
    ask: List[str] = []    # Patterns requiring confirmation
    deny: List[str] = []   # Patterns to block

class HookConfig(BaseModel):
    """Single hook configuration."""
    type: str  # "command" or "prompt"
    command: str | None = None
    prompt: str | None = None
    timeout: int = 60

class HooksConfig(BaseModel):
    """All hooks configuration."""
    pre_tool_use: List[HookConfig] = []
    post_tool_use: List[HookConfig] = []
    user_prompt_submit: List[HookConfig] = []
    stop: List[HookConfig] = []

class MCPServerConfig(BaseModel):
    """MCP server configuration."""
    transport: str  # "stdio" or "streamable-http"
    command: str | None = None  # For stdio
    args: List[str] = []
    url: str | None = None  # For HTTP
    env: Dict[str, str] = {}

class DisplayConfig(BaseModel):
    """Display/UI configuration."""
    theme: str = "dark"
    show_tokens: bool = True
    show_cost: bool = True
    streaming: bool = True
    vim_mode: bool = False

class SessionConfig(BaseModel):
    """Session management configuration."""
    auto_save: bool = True
    save_interval: int = 60  # seconds
    max_history: int = 100
    session_dir: str | None = None

class OpenCodeConfig(BaseModel):
    """Root configuration model."""
    model: ModelConfig = Field(default_factory=ModelConfig)
    permissions: PermissionConfig = Field(default_factory=PermissionConfig)
    hooks: HooksConfig = Field(default_factory=HooksConfig)
    mcp_servers: Dict[str, MCPServerConfig] = {}
    display: DisplayConfig = Field(default_factory=DisplayConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)

    # API Keys (prefer environment variables)
    api_key: str | None = None
```

### Configuration Loader Implementation

```python
class ConfigLoader(IConfigLoader):
    """
    Concrete implementation of IConfigLoader.
    Handles hierarchical configuration loading.
    """

    def __init__(self):
        self._config: OpenCodeConfig | None = None
        self._watchers: List[Callable] = []

    def load_all(self) -> OpenCodeConfig:
        """Load and merge all configuration sources."""
        config = {}

        # 1. Load defaults
        config = OpenCodeConfig().model_dump()

        # 2. Load user config
        user_config = self._load_user_config()
        config = self.merge(config, user_config)

        # 3. Load project config
        project_config = self._load_project_config()
        config = self.merge(config, project_config)

        # 4. Load local overrides
        local_config = self._load_local_config()
        config = self.merge(config, local_config)

        # 5. Apply environment variables
        config = self._apply_env_vars(config)

        # 6. Validate and return
        return OpenCodeConfig.model_validate(config)
```

### File Locations

```
~/.src/opencode/
├── settings.json          # User settings
├── sessions/              # Session storage
└── cache/                 # Cache directory

.src/opencode/
├── settings.json          # Project settings (version controlled)
├── settings.local.json    # Local overrides (gitignored)
├── commands/              # Custom commands
└── agents/                # Custom agents
```

### Example Configuration File

```json
{
  "model": {
    "default": "gpt-5",
    "fallback": ["claude-4", "gemini-2.5-pro"],
    "max_tokens": 8192
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
  "display": {
    "theme": "dark",
    "show_tokens": true,
    "vim_mode": false
  }
}
```

---

## Acceptance Criteria

### Definition of Done

- [ ] `ConfigLoader` class implements `IConfigLoader` interface
- [ ] Configuration loads from JSON files
- [ ] Configuration loads from YAML files
- [ ] Hierarchy is respected (enterprise > user > project > local > env)
- [ ] Environment variables with OPENCODE_ prefix work
- [ ] Pydantic validation catches invalid config
- [ ] Default values work for missing fields
- [ ] File watcher detects changes
- [ ] Reload applies changes without restart
- [ ] API keys are not logged
- [ ] Tests achieve ≥90% coverage
- [ ] Type checking passes

### Verification Commands

```bash
# Create test config
echo '{"model": {"default": "claude-4"}}' > .src/opencode/settings.json

# Verify config loads (future CLI feature)
python -c "from opencode.config import ConfigLoader; c = ConfigLoader(); print(c.load_all().model.default)"
# Expected: claude-4

# Verify env var override
OPENCODE_MODEL=gpt-5 python -c "from opencode.config import ConfigLoader; c = ConfigLoader(); print(c.load_all().model.default)"
# Expected: gpt-5

# Verify validation
echo '{"model": {"max_tokens": "invalid"}}' > /tmp/bad.json
python -c "from opencode.config import ConfigLoader; ConfigLoader().load(Path('/tmp/bad.json'))"
# Expected: ValidationError

# Run tests
pytest tests/unit/config/ -v --cov=opencode.config
```

---

## Out of Scope

The following are NOT part of Phase 1.2:
- Interactive configuration UI (/config command)
- Configuration migration from old versions
- Configuration encryption
- Remote configuration sources
- Configuration export/import

---

## Notes

Configuration is critical infrastructure that many other phases depend on:
- Phase 3.1 needs API key and model settings
- Phase 4.1 needs permission settings
- Phase 4.2 needs hook settings
- Phase 8.1 needs MCP server settings

Getting the configuration system right early prevents issues later.
