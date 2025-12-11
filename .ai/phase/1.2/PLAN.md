# Phase 1.2: Configuration System - Architectural Plan

**Phase:** 1.2
**Name:** Configuration System
**Dependencies:** Phase 1.1 (Project Foundation)

---

## Architectural Overview

The configuration system follows the Repository pattern with a layered loading strategy. It implements the `IConfigLoader` interface from Phase 1.1 and uses Pydantic for validation.

---

## Design Patterns Applied

### Repository Pattern
Configuration is accessed through a repository that abstracts the storage mechanism:
- `ConfigRepository` manages configuration lifecycle
- Concrete loaders handle different file formats
- Clean separation between loading and access

### Strategy Pattern
Different configuration sources use different loading strategies:
- `JsonConfigStrategy` for JSON files
- `YamlConfigStrategy` for YAML files
- `EnvConfigStrategy` for environment variables

### Observer Pattern
Configuration changes are broadcast to interested parties:
- File watcher detects changes
- Observers are notified of updates
- Components can react to config changes

---

## Class Design

### Configuration Models

```python
from pydantic import BaseModel, Field, SecretStr, field_validator
from typing import Dict, List, Any, Optional
from pathlib import Path
from enum import Enum

class TransportType(str, Enum):
    """MCP transport types."""
    STDIO = "stdio"
    STREAMABLE_HTTP = "streamable-http"

class RoutingVariant(str, Enum):
    """OpenRouter routing variants."""
    NITRO = "nitro"
    FLOOR = "floor"
    EXACTO = "exacto"
    THINKING = "thinking"
    ONLINE = "online"

class ModelConfig(BaseModel):
    """Model-related configuration."""
    default: str = "gpt-5"
    fallback: List[str] = Field(default_factory=lambda: ["claude-4", "gemini-2.5-pro"])
    max_tokens: int = Field(default=8192, ge=1, le=200000)
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    routing_variant: Optional[RoutingVariant] = None

    @field_validator('default', 'fallback')
    @classmethod
    def validate_model_name(cls, v):
        """Validate model name format."""
        if isinstance(v, list):
            return v
        if not v or not isinstance(v, str):
            raise ValueError("Model name must be a non-empty string")
        return v

class PermissionRule(BaseModel):
    """Single permission rule."""
    pattern: str
    description: Optional[str] = None

class PermissionConfig(BaseModel):
    """Permission system configuration."""
    allow: List[str] = Field(default_factory=list)
    ask: List[str] = Field(default_factory=list)
    deny: List[str] = Field(default_factory=list)

class HookType(str, Enum):
    """Hook execution type."""
    COMMAND = "command"
    PROMPT = "prompt"

class HookConfig(BaseModel):
    """Single hook configuration."""
    type: HookType
    matcher: Optional[str] = None  # Tool pattern to match
    command: Optional[str] = None  # For command hooks
    prompt: Optional[str] = None   # For prompt hooks
    timeout: int = Field(default=60, ge=1, le=300)

    @field_validator('command', 'prompt')
    @classmethod
    def validate_hook_content(cls, v, info):
        """Validate that command or prompt is provided based on type."""
        return v

class HooksConfig(BaseModel):
    """All hooks configuration."""
    pre_tool_use: List[HookConfig] = Field(default_factory=list)
    post_tool_use: List[HookConfig] = Field(default_factory=list)
    user_prompt_submit: List[HookConfig] = Field(default_factory=list)
    stop: List[HookConfig] = Field(default_factory=list)
    subagent_stop: List[HookConfig] = Field(default_factory=list)
    notification: List[HookConfig] = Field(default_factory=list)

class MCPServerConfig(BaseModel):
    """MCP server configuration."""
    transport: TransportType
    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    env: Dict[str, str] = Field(default_factory=dict)
    oauth_client_id: Optional[str] = None  # For OAuth 2.1

    @field_validator('command')
    @classmethod
    def validate_stdio_has_command(cls, v, info):
        """Stdio transport requires command."""
        return v

class DisplayConfig(BaseModel):
    """Display/UI configuration."""
    theme: str = "dark"
    show_tokens: bool = True
    show_cost: bool = True
    streaming: bool = True
    vim_mode: bool = False
    status_line: bool = True

class SessionConfig(BaseModel):
    """Session management configuration."""
    auto_save: bool = True
    save_interval: int = Field(default=60, ge=10, le=3600)
    max_history: int = Field(default=100, ge=1, le=10000)
    session_dir: Optional[Path] = None
    compress_after: int = Field(default=50, ge=10)  # Messages before compression

class Code-ForgeConfig(BaseModel):
    """Root configuration model."""
    model: ModelConfig = Field(default_factory=ModelConfig)
    permissions: PermissionConfig = Field(default_factory=PermissionConfig)
    hooks: HooksConfig = Field(default_factory=HooksConfig)
    mcp_servers: Dict[str, MCPServerConfig] = Field(default_factory=dict)
    display: DisplayConfig = Field(default_factory=DisplayConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)

    # Sensitive - use SecretStr to prevent logging
    api_key: Optional[SecretStr] = None

    class Config:
        """Pydantic config."""
        validate_assignment = True
        extra = "ignore"  # Ignore unknown fields
```

### Configuration Loader

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Callable, List
import json
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class IConfigSource(ABC):
    """Interface for configuration sources."""

    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """Load configuration from source."""
        pass

    @abstractmethod
    def exists(self) -> bool:
        """Check if source exists."""
        pass

class JsonFileSource(IConfigSource):
    """Load configuration from JSON file."""

    def __init__(self, path: Path):
        self._path = path

    def load(self) -> Dict[str, Any]:
        if not self.exists():
            return {}
        with open(self._path, 'r') as f:
            return json.load(f)

    def exists(self) -> bool:
        return self._path.exists() and self._path.is_file()

class YamlFileSource(IConfigSource):
    """Load configuration from YAML file."""

    def __init__(self, path: Path):
        self._path = path

    def load(self) -> Dict[str, Any]:
        if not self.exists():
            return {}
        import yaml
        with open(self._path, 'r') as f:
            return yaml.safe_load(f) or {}

    def exists(self) -> bool:
        return self._path.exists() and self._path.is_file()

class EnvironmentSource(IConfigSource):
    """Load configuration from environment variables."""

    PREFIX = "FORGE_"

    def load(self) -> Dict[str, Any]:
        config: Dict[str, Any] = {}

        # Direct mappings
        mappings = {
            "FORGE_API_KEY": ("api_key", str),
            "FORGE_MODEL": ("model", "default"),
            "FORGE_MAX_TOKENS": ("model", "max_tokens"),
            "FORGE_THEME": ("display", "theme"),
        }

        for env_var, path in mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                self._set_nested(config, path, value)

        return config

    def exists(self) -> bool:
        return True  # Environment always exists

    def _set_nested(self, d: Dict, path: tuple, value: Any) -> None:
        """Set nested dictionary value."""
        if isinstance(path, str):
            d[path] = value
        else:
            key = path[0]
            if len(path) == 2:
                if key not in d:
                    d[key] = {}
                d[key][path[1]] = value

class ConfigLoader(IConfigLoader):
    """
    Configuration loader with hierarchical merging.

    Load order (later overrides earlier):
    1. Defaults
    2. Enterprise settings
    3. User settings
    4. Project settings
    5. Local settings
    6. Environment variables

    Thread Safety:
    - Uses threading.Lock to protect config access during reload
    - File watcher runs in separate thread, triggers reload safely
    """

    def __init__(
        self,
        user_dir: Path | None = None,
        project_dir: Path | None = None,
    ):
        import threading
        self._user_dir = user_dir or Path.home() / ".forge"
        self._project_dir = project_dir or Path.cwd() / ".forge"
        self._config: Code-ForgeConfig | None = None
        self._observers: List[Callable[[Code-ForgeConfig], None]] = []
        self._file_watcher: Observer | None = None
        self._lock = threading.Lock()  # Protect config during concurrent access

    @property
    def config(self) -> Code-ForgeConfig:
        """Get current configuration, loading if necessary.

        Thread-safe: uses lock to prevent races during reload.
        """
        with self._lock:
            if self._config is None:
                self._config = self.load_all()
            return self._config

    def load_all(self) -> Code-ForgeConfig:
        """Load and merge all configuration sources."""
        config: Dict[str, Any] = {}

        # 1. Start with defaults
        config = Code-ForgeConfig().model_dump()

        # 2. Load enterprise (if exists)
        enterprise_path = Path("/etc/src/forge/settings.json")
        if enterprise_path.exists():
            enterprise = JsonFileSource(enterprise_path).load()
            config = self.merge(config, enterprise)

        # 3. Load user settings
        user_json = self._user_dir / "settings.json"
        user_yaml = self._user_dir / "settings.yaml"
        if user_json.exists():
            config = self.merge(config, JsonFileSource(user_json).load())
        elif user_yaml.exists():
            config = self.merge(config, YamlFileSource(user_yaml).load())

        # 4. Load project settings
        project_json = self._project_dir / "settings.json"
        project_yaml = self._project_dir / "settings.yaml"
        if project_json.exists():
            config = self.merge(config, JsonFileSource(project_json).load())
        elif project_yaml.exists():
            config = self.merge(config, YamlFileSource(project_yaml).load())

        # 5. Load local overrides
        local_json = self._project_dir / "settings.local.json"
        if local_json.exists():
            config = self.merge(config, JsonFileSource(local_json).load())

        # 6. Apply environment variables
        config = self.merge(config, EnvironmentSource().load())

        # 7. Validate and return
        return Code-ForgeConfig.model_validate(config)

    def load(self, path: Path) -> Dict[str, Any]:
        """Load single configuration file."""
        if path.suffix == ".json":
            return JsonFileSource(path).load()
        elif path.suffix in (".yaml", ".yml"):
            return YamlFileSource(path).load()
        else:
            raise ConfigError(f"Unsupported config format: {path.suffix}")

    def merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge(result[key], value)
            else:
                result[key] = value

        return result

    def validate(self, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate configuration against schema."""
        try:
            Code-ForgeConfig.model_validate(config)
            return True, []
        except Exception as e:
            return False, [str(e)]

    def reload(self) -> None:
        """Reload configuration from all sources.

        Thread-safe: uses lock to prevent races during reload.
        Observers are notified outside the lock to prevent deadlocks.
        """
        try:
            new_config = self.load_all()
            with self._lock:
                self._config = new_config
            # Notify outside lock to prevent deadlocks if observers access config
            self._notify_observers(new_config)
        except Exception as e:
            # Keep old config on error
            get_logger("config").error(f"Failed to reload config: {e}")

    def watch(self) -> None:
        """Start watching configuration files for changes."""
        if self._file_watcher is not None:
            return

        class ConfigChangeHandler(FileSystemEventHandler):
            def __init__(self, loader: 'ConfigLoader'):
                self._loader = loader

            def on_modified(self, event):
                if event.src_path.endswith(('.json', '.yaml', '.yml')):
                    self._loader.reload()

        self._file_watcher = Observer()
        handler = ConfigChangeHandler(self)

        # Watch user and project directories
        for path in [self._user_dir, self._project_dir]:
            if path.exists():
                self._file_watcher.schedule(handler, str(path), recursive=False)

        self._file_watcher.start()

    def stop_watching(self) -> None:
        """Stop watching configuration files.

        Safe to call multiple times. Waits for watcher thread to finish.
        """
        if self._file_watcher:
            self._file_watcher.stop()
            self._file_watcher.join(timeout=5.0)  # Don't hang forever
            self._file_watcher = None

    def __del__(self) -> None:
        """Cleanup: ensure file watcher is stopped."""
        self.stop_watching()

    def add_observer(self, callback: Callable[[Code-ForgeConfig], None]) -> None:
        """Add observer for configuration changes."""
        self._observers.append(callback)

    def remove_observer(self, callback: Callable[[Code-ForgeConfig], None]) -> None:
        """Remove observer."""
        self._observers.remove(callback)

    def _notify_observers(self, config: Code-ForgeConfig) -> None:
        """Notify all observers of config change."""
        for observer in self._observers:
            try:
                observer(config)
            except Exception as e:
                get_logger("config").error(f"Observer error: {e}")
```

---

## Implementation Order

1. Create configuration models in `src/forge/config/models.py`
2. Create config sources in `src/forge/config/sources.py`
3. Implement `ConfigLoader` in `src/forge/config/loader.py`
4. Add file watching support
5. Create `src/forge/config/__init__.py` with exports
6. Write comprehensive tests
7. Integration with CLI (update `--help` to show config path)

---

## File Structure

```
src/forge/config/
├── __init__.py       # Exports: ConfigLoader, Code-ForgeConfig, etc.
├── models.py         # Pydantic configuration models
├── sources.py        # IConfigSource implementations
└── loader.py         # ConfigLoader implementation

tests/unit/config/
├── __init__.py
├── test_models.py    # Model validation tests
├── test_sources.py   # Source loading tests
└── test_loader.py    # Loader integration tests
```

---

## Quality Gates

Before completing Phase 1.2:
- [ ] All config models validate correctly
- [ ] JSON loading works
- [ ] YAML loading works
- [ ] Environment variable override works
- [ ] Hierarchy merging works correctly
- [ ] File watcher detects changes
- [ ] Invalid config falls back gracefully
- [ ] API key is not logged (test with DEBUG level)
- [ ] Tests pass with ≥90% coverage
- [ ] `mypy --strict` passes
- [ ] `ruff check` passes
