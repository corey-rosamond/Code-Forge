# Phase 10.1: Plugin System - Requirements

**Phase:** 10.1
**Name:** Plugin System
**Dependencies:** Phase 2.1 (Tool System), Phase 4.2 (Hooks System), Phase 6.1 (Slash Commands)

---

## Overview

Phase 10.1 implements a plugin system for OpenCode, enabling third-party extensions that add tools, commands, hooks, and other functionality. This creates an extensible architecture where users and the community can enhance OpenCode's capabilities.

---

## Goals

1. Define plugin architecture and interfaces
2. Implement plugin discovery and loading
3. Support plugin lifecycle management
4. Enable plugin configuration
5. Provide plugin isolation and security
6. Create plugin development toolkit

---

## Non-Goals (This Phase)

- Plugin marketplace/registry
- Plugin signing/verification
- Remote plugin installation
- Plugin auto-updates
- Plugin sandboxing (security boundary)
- Plugin GUI configuration

---

## Functional Requirements

### FR-1: Plugin Definition

**FR-1.1:** Plugin structure
- Plugin manifest (plugin.yaml or pyproject.toml)
- Plugin entry point
- Plugin metadata (name, version, author)
- Dependency declarations

**FR-1.2:** Plugin capabilities
- Register tools
- Register slash commands
- Register hooks
- Provide configuration schema
- Add subagent types
- Add skills

**FR-1.3:** Plugin metadata
- Unique identifier (namespace)
- Version (semver)
- Description
- Author information
- License
- OpenCode version compatibility

### FR-2: Plugin Discovery

**FR-2.1:** Discovery locations
- User plugin directory (~/.src/opencode/plugins/)
- Project plugin directory (.src/opencode/plugins/)
- Installed Python packages (entry points)
- Explicit plugin paths in config

**FR-2.2:** Discovery process
- Scan directories for plugin manifests
- Load entry points from installed packages
- Validate plugin manifests
- Report discovery errors

**FR-2.3:** Plugin filtering
- Enable/disable by name
- Filter by capability
- Version compatibility checking

### FR-3: Plugin Loading

**FR-3.1:** Load process
- Parse plugin manifest
- Import plugin module
- Validate plugin interface
- Initialize plugin instance

**FR-3.2:** Load ordering
- Respect dependency order
- Handle circular dependencies
- Load core plugins first
- User plugins last

**FR-3.3:** Error handling
- Continue on plugin failure
- Log plugin errors
- Provide degraded operation
- Report failed plugins

### FR-4: Plugin Lifecycle

**FR-4.1:** Lifecycle hooks
- on_load: Plugin loaded
- on_activate: Plugin activated
- on_deactivate: Plugin deactivated
- on_unload: Plugin unloaded

**FR-4.2:** State management
- Plugin enabled/disabled state
- Plugin configuration storage
- Plugin data directory

**FR-4.3:** Runtime control
- Enable/disable at runtime
- Reload plugin
- List active plugins

### FR-5: Plugin Configuration

**FR-5.1:** Configuration schema
- Plugin declares config schema
- Schema validation
- Default values
- Type coercion

**FR-5.2:** Configuration sources
- Plugin defaults
- User config file
- Environment variables
- Runtime overrides

**FR-5.3:** Configuration access
- Typed config access
- Config change notifications
- Hot reload support

### FR-6: Plugin Isolation

**FR-6.1:** Namespace isolation
- Plugin namespace prefix
- Tool name prefixing
- Command name prefixing
- No global state pollution

**FR-6.2:** Resource isolation
- Dedicated data directory
- Logging namespace
- Error isolation

**FR-6.3:** Capability restrictions
- Declare required capabilities
- Warn on dangerous capabilities
- Configurable restrictions

---

## Non-Functional Requirements

### NFR-1: Performance
- Plugin discovery < 500ms
- Plugin loading < 100ms per plugin
- No startup impact for disabled plugins
- Lazy loading where possible

### NFR-2: Reliability
- Graceful plugin failure handling
- Core functionality unaffected by plugin errors
- Clear error messages
- Plugin crash isolation

### NFR-3: Usability
- Simple plugin creation
- Clear documentation
- Example plugins
- Plugin template generator

---

## Technical Specifications

### Package Structure

```
src/opencode/plugins/
├── __init__.py           # Package exports
├── base.py               # Plugin base class
├── manifest.py           # Manifest parsing
├── discovery.py          # Plugin discovery
├── loader.py             # Plugin loader
├── manager.py            # Plugin manager
├── registry.py           # Plugin registry
├── config.py             # Plugin configuration
└── exceptions.py         # Plugin exceptions
```

### Plugin Directory Structure

```
~/.src/opencode/plugins/my-plugin/
├── plugin.yaml           # Plugin manifest
├── __init__.py           # Plugin entry point
├── tools/                # Plugin tools
│   └── my_tool.py
├── commands/             # Plugin commands
│   └── my_command.md
└── config.schema.yaml    # Config schema (optional)
```

### Class Signatures

```python
# base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class PluginMetadata:
    """Plugin metadata."""
    name: str
    version: str
    description: str
    author: str | None = None
    email: str | None = None
    license: str | None = None
    homepage: str | None = None
    repository: str | None = None
    keywords: list[str] = field(default_factory=list)
    opencode_version: str | None = None  # e.g., ">=1.0.0"


@dataclass
class PluginCapabilities:
    """Plugin capabilities declaration."""
    tools: bool = False
    commands: bool = False
    hooks: bool = False
    subagents: bool = False
    skills: bool = False
    system_access: bool = False  # Requires approval


class Plugin(ABC):
    """Base class for OpenCode plugins."""

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        ...

    @property
    def capabilities(self) -> PluginCapabilities:
        """Return plugin capabilities."""
        return PluginCapabilities()

    def on_load(self, context: "PluginContext") -> None:
        """Called when plugin is loaded."""
        pass

    def on_activate(self, context: "PluginContext") -> None:
        """Called when plugin is activated."""
        pass

    def on_deactivate(self, context: "PluginContext") -> None:
        """Called when plugin is deactivated."""
        pass

    def on_unload(self, context: "PluginContext") -> None:
        """Called when plugin is unloaded."""
        pass

    def register_tools(self) -> list["Tool"]:
        """Return list of tools to register."""
        return []

    def register_commands(self) -> list["Command"]:
        """Return list of commands to register."""
        return []

    def register_hooks(self) -> dict[str, list[Callable]]:
        """Return hooks to register."""
        return {}

    def get_config_schema(self) -> dict | None:
        """Return JSON schema for plugin config."""
        return None


@dataclass
class PluginContext:
    """Context provided to plugins."""
    plugin_id: str
    data_dir: Path
    config: dict[str, Any]
    logger: logging.Logger


# manifest.py
@dataclass
class PluginManifest:
    """Parsed plugin manifest."""
    name: str
    version: str
    description: str
    entry_point: str
    metadata: PluginMetadata
    capabilities: PluginCapabilities
    dependencies: list[str]
    config_schema: dict | None = None

    @classmethod
    def from_yaml(cls, path: Path) -> "PluginManifest":
        """Load manifest from YAML file."""
        ...

    @classmethod
    def from_pyproject(cls, path: Path) -> "PluginManifest":
        """Load manifest from pyproject.toml."""
        ...


class ManifestParser:
    """Parse plugin manifests."""

    def parse(self, path: Path) -> PluginManifest:
        """Parse manifest from path."""
        ...

    def validate(self, manifest: PluginManifest) -> list[str]:
        """Validate manifest, return list of errors."""
        ...


# discovery.py
@dataclass
class DiscoveredPlugin:
    """Discovered plugin information."""
    path: Path
    manifest: PluginManifest
    source: str  # "user", "project", "package"


class PluginDiscovery:
    """Discover plugins from various sources."""

    def __init__(
        self,
        user_dir: Path | None = None,
        project_dir: Path | None = None,
        extra_paths: list[Path] | None = None
    ):
        ...

    def discover(self) -> list[DiscoveredPlugin]:
        """Discover all plugins."""
        ...

    def discover_user_plugins(self) -> list[DiscoveredPlugin]:
        """Discover plugins in user directory."""
        ...

    def discover_project_plugins(self) -> list[DiscoveredPlugin]:
        """Discover plugins in project directory."""
        ...

    def discover_package_plugins(self) -> list[DiscoveredPlugin]:
        """Discover plugins from installed packages."""
        ...


# loader.py
@dataclass
class LoadedPlugin:
    """Loaded plugin instance."""
    id: str
    manifest: PluginManifest
    instance: Plugin
    context: PluginContext
    enabled: bool = True


class PluginLoader:
    """Load plugin instances."""

    def __init__(self, config: "PluginConfig"):
        self.config = config

    def load(self, discovered: DiscoveredPlugin) -> LoadedPlugin:
        """Load a discovered plugin."""
        ...

    def create_context(
        self,
        plugin_id: str,
        manifest: PluginManifest
    ) -> PluginContext:
        """Create plugin context."""
        ...

    def unload(self, plugin: LoadedPlugin) -> None:
        """Unload a plugin."""
        ...


# manager.py
class PluginManager:
    """Manage plugin lifecycle."""

    def __init__(
        self,
        discovery: PluginDiscovery,
        loader: PluginLoader,
        registry: "PluginRegistry"
    ):
        ...

    @property
    def plugins(self) -> dict[str, LoadedPlugin]:
        """Get all loaded plugins."""
        ...

    def discover_and_load(self) -> None:
        """Discover and load all plugins."""
        ...

    def get_plugin(self, plugin_id: str) -> LoadedPlugin | None:
        """Get plugin by ID."""
        ...

    def enable(self, plugin_id: str) -> None:
        """Enable a plugin."""
        ...

    def disable(self, plugin_id: str) -> None:
        """Disable a plugin."""
        ...

    def reload(self, plugin_id: str) -> None:
        """Reload a plugin."""
        ...

    def list_plugins(self) -> list[LoadedPlugin]:
        """List all plugins."""
        ...


# registry.py
class PluginRegistry:
    """Registry of plugin contributions."""

    def __init__(self):
        self._tools: dict[str, tuple[str, Tool]] = {}
        self._commands: dict[str, tuple[str, Command]] = {}
        self._hooks: dict[str, list[tuple[str, Callable]]] = {}

    def register_tool(
        self,
        plugin_id: str,
        tool: "Tool"
    ) -> None:
        """Register a plugin tool."""
        ...

    def register_command(
        self,
        plugin_id: str,
        command: "Command"
    ) -> None:
        """Register a plugin command."""
        ...

    def register_hook(
        self,
        plugin_id: str,
        event: str,
        handler: Callable
    ) -> None:
        """Register a plugin hook."""
        ...

    def unregister_plugin(self, plugin_id: str) -> None:
        """Unregister all contributions from plugin."""
        ...

    def get_tools(self) -> dict[str, Tool]:
        """Get all registered tools."""
        ...

    def get_commands(self) -> dict[str, Command]:
        """Get all registered commands."""
        ...


# config.py
@dataclass
class PluginConfig:
    """Plugin system configuration."""
    enabled: bool = True
    user_dir: Path | None = None
    project_dir: Path | None = None
    disabled_plugins: list[str] = field(default_factory=list)
    plugin_configs: dict[str, dict] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "PluginConfig":
        """Create from dictionary."""
        ...


class PluginConfigManager:
    """Manage plugin configurations."""

    def __init__(self, base_config: PluginConfig):
        self.base_config = base_config

    def get_plugin_config(
        self,
        plugin_id: str,
        schema: dict | None = None
    ) -> dict:
        """Get configuration for plugin."""
        ...

    def set_plugin_config(
        self,
        plugin_id: str,
        config: dict
    ) -> None:
        """Set configuration for plugin."""
        ...

    def validate_config(
        self,
        config: dict,
        schema: dict
    ) -> list[str]:
        """Validate config against schema."""
        ...
```

---

## Plugin Manifest Format

### plugin.yaml

```yaml
name: my-plugin
version: 1.0.0
description: A sample OpenCode plugin

author: Jane Doe
email: jane@example.com
license: MIT
homepage: https://github.com/jane/my-plugin

entry_point: my_plugin:MyPlugin

capabilities:
  tools: true
  commands: true
  hooks: false

dependencies:
  - requests>=2.28.0

opencode_version: ">=1.0.0"

config:
  schema:
    type: object
    properties:
      api_key:
        type: string
        description: API key for service
      timeout:
        type: integer
        default: 30
    required:
      - api_key
```

---

## Plugin Commands

| Command | Description |
|---------|-------------|
| `/plugins` | List all plugins |
| `/plugin info <name>` | Show plugin details |
| `/plugin enable <name>` | Enable a plugin |
| `/plugin disable <name>` | Disable a plugin |
| `/plugin reload <name>` | Reload a plugin |

---

## Integration Points

### With Tool System (Phase 2.1)
- Plugins register tools
- Tools prefixed with plugin namespace
- Tool schema from plugin

### With Slash Commands (Phase 6.1)
- Plugins register commands
- Commands in plugin namespace
- Command discovery

### With Hooks System (Phase 4.2)
- Plugins register hook handlers
- Hook event subscription
- Hook priority ordering

---

## Testing Requirements

1. Unit tests for Plugin base class
2. Unit tests for ManifestParser
3. Unit tests for PluginDiscovery
4. Unit tests for PluginLoader
5. Unit tests for PluginManager
6. Unit tests for PluginRegistry
7. Integration tests with sample plugins
8. Test coverage >= 90%

---

## Acceptance Criteria

1. Plugins can be created with simple structure
2. Plugins are discovered from all sources
3. Plugin manifests are validated
4. Plugins load in correct order
5. Plugin lifecycle hooks work
6. Plugin tools are registered correctly
7. Plugin commands are registered correctly
8. Plugin hooks are called correctly
9. Plugin configuration works
10. Plugin errors don't crash core
11. Plugins can be enabled/disabled
12. Plugin data is isolated
