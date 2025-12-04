# Phase 10.1: Plugin System - Implementation Plan

**Phase:** 10.1
**Name:** Plugin System
**Dependencies:** Phase 2.1 (Tool System), Phase 4.2 (Hooks System), Phase 6.1 (Slash Commands)

---

## Overview

This document provides the complete implementation plan for the OpenCode plugin system, enabling extensibility through third-party plugins that can add tools, commands, hooks, and other capabilities.

---

## Implementation Order

1. Exceptions (exceptions.py)
2. Plugin Base Class (base.py)
3. Manifest Parsing (manifest.py)
4. Plugin Discovery (discovery.py)
5. Plugin Configuration (config.py)
6. Plugin Loader (loader.py)
7. Plugin Registry (registry.py)
8. Plugin Manager (manager.py)
9. Package exports (__init__.py)

---

## File Implementations

### 1. exceptions.py - Plugin Exceptions

```python
"""Plugin system exceptions."""
from __future__ import annotations


class PluginError(Exception):
    """Base exception for plugin errors."""

    def __init__(self, message: str, plugin_id: str | None = None):
        super().__init__(message)
        self.plugin_id = plugin_id


class PluginNotFoundError(PluginError):
    """Plugin not found."""
    pass


class PluginLoadError(PluginError):
    """Failed to load plugin."""
    pass


class PluginManifestError(PluginError):
    """Invalid plugin manifest."""
    pass


class PluginDependencyError(PluginError):
    """Plugin dependency error."""
    pass


class PluginConfigError(PluginError):
    """Plugin configuration error."""
    pass


class PluginLifecycleError(PluginError):
    """Plugin lifecycle error."""
    pass
```

### 2. base.py - Plugin Base Class

```python
"""Plugin base class and related types."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from opencode.tools.base import Tool
    from opencode.commands.base import Command


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
    opencode_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "email": self.email,
            "license": self.license,
            "homepage": self.homepage,
            "repository": self.repository,
            "keywords": self.keywords,
            "opencode_version": self.opencode_version,
        }


@dataclass
class PluginCapabilities:
    """Plugin capabilities declaration."""
    tools: bool = False
    commands: bool = False
    hooks: bool = False
    subagents: bool = False
    skills: bool = False
    system_access: bool = False

    def to_dict(self) -> dict[str, bool]:
        """Convert to dictionary."""
        return {
            "tools": self.tools,
            "commands": self.commands,
            "hooks": self.hooks,
            "subagents": self.subagents,
            "skills": self.skills,
            "system_access": self.system_access,
        }


@dataclass
class PluginContext:
    """Context provided to plugins."""
    plugin_id: str
    data_dir: Path
    config: dict[str, Any]
    logger: logging.Logger

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def ensure_data_dir(self) -> Path:
        """Ensure data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir


class Plugin(ABC):
    """Base class for OpenCode plugins."""

    def __init__(self):
        """Initialize plugin."""
        self._context: PluginContext | None = None

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        ...

    @property
    def capabilities(self) -> PluginCapabilities:
        """Return plugin capabilities."""
        return PluginCapabilities()

    @property
    def context(self) -> PluginContext:
        """Get plugin context."""
        if self._context is None:
            raise RuntimeError("Plugin not initialized with context")
        return self._context

    def set_context(self, context: PluginContext) -> None:
        """Set plugin context."""
        self._context = context

    def on_load(self) -> None:
        """Called when plugin is loaded."""
        pass

    def on_activate(self) -> None:
        """Called when plugin is activated."""
        pass

    def on_deactivate(self) -> None:
        """Called when plugin is deactivated."""
        pass

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        pass

    def register_tools(self) -> list["Tool"]:
        """Return list of tools to register."""
        return []

    def register_commands(self) -> list["Command"]:
        """Return list of commands to register."""
        return []

    def register_hooks(self) -> dict[str, list[Callable]]:
        """Return hooks to register. Key is event name."""
        return {}

    def get_config_schema(self) -> dict | None:
        """Return JSON schema for plugin config."""
        return None
```

### 3. manifest.py - Manifest Parsing

```python
"""Plugin manifest parsing."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .base import PluginMetadata, PluginCapabilities
from .exceptions import PluginManifestError


@dataclass
class PluginManifest:
    """Parsed plugin manifest."""
    name: str
    version: str
    description: str
    entry_point: str
    metadata: PluginMetadata
    capabilities: PluginCapabilities
    dependencies: list[str] = field(default_factory=list)
    config_schema: dict | None = None
    path: Path | None = None

    @classmethod
    def from_yaml(cls, path: Path) -> "PluginManifest":
        """Load manifest from YAML file."""
        if not path.exists():
            raise PluginManifestError(f"Manifest not found: {path}")

        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise PluginManifestError(f"Invalid YAML: {e}")

        return cls._from_dict(data, path.parent)

    @classmethod
    def from_pyproject(cls, path: Path) -> "PluginManifest":
        """Load manifest from pyproject.toml."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        if not path.exists():
            raise PluginManifestError(f"pyproject.toml not found: {path}")

        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            raise PluginManifestError(f"Invalid TOML: {e}")

        plugin_data = data.get("tool", {}).get("opencode", {}).get("plugin")
        if not plugin_data:
            raise PluginManifestError("No [tool.opencode.plugin] section")

        return cls._from_dict(plugin_data, path.parent)

    @classmethod
    def _from_dict(cls, data: dict, base_path: Path) -> "PluginManifest":
        """Create manifest from dictionary."""
        required = ["name", "version", "description", "entry_point"]
        for key in required:
            if key not in data:
                raise PluginManifestError(f"Missing required field: {key}")

        # Parse capabilities
        cap_data = data.get("capabilities", {})
        capabilities = PluginCapabilities(
            tools=cap_data.get("tools", False),
            commands=cap_data.get("commands", False),
            hooks=cap_data.get("hooks", False),
            subagents=cap_data.get("subagents", False),
            skills=cap_data.get("skills", False),
            system_access=cap_data.get("system_access", False),
        )

        # Parse metadata
        metadata = PluginMetadata(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            author=data.get("author"),
            email=data.get("email"),
            license=data.get("license"),
            homepage=data.get("homepage"),
            repository=data.get("repository"),
            keywords=data.get("keywords", []),
            opencode_version=data.get("opencode_version"),
        )

        # Parse config schema
        config_schema = None
        if "config" in data:
            config_schema = data["config"].get("schema")

        return cls(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            entry_point=data["entry_point"],
            metadata=metadata,
            capabilities=capabilities,
            dependencies=data.get("dependencies", []),
            config_schema=config_schema,
            path=base_path,
        )


class ManifestParser:
    """Parse plugin manifests."""

    MANIFEST_FILES = ["plugin.yaml", "plugin.yml", "pyproject.toml"]

    def find_manifest(self, plugin_dir: Path) -> Path | None:
        """Find manifest file in directory."""
        for name in self.MANIFEST_FILES:
            path = plugin_dir / name
            if path.exists():
                return path
        return None

    def parse(self, path: Path) -> PluginManifest:
        """Parse manifest from path."""
        if path.name in ("plugin.yaml", "plugin.yml"):
            return PluginManifest.from_yaml(path)
        elif path.name == "pyproject.toml":
            return PluginManifest.from_pyproject(path)
        else:
            raise PluginManifestError(f"Unknown manifest type: {path.name}")

    def validate(self, manifest: PluginManifest) -> list[str]:
        """Validate manifest, return list of errors."""
        errors = []

        # Validate name
        if not manifest.name:
            errors.append("Plugin name is required")
        elif not manifest.name.replace("-", "").replace("_", "").isalnum():
            errors.append("Plugin name must be alphanumeric with - or _")

        # Validate version
        if not manifest.version:
            errors.append("Plugin version is required")
        else:
            try:
                self._parse_version(manifest.version)
            except ValueError:
                errors.append("Invalid version format (use semver)")

        # Validate entry point
        if not manifest.entry_point:
            errors.append("Entry point is required")
        elif ":" not in manifest.entry_point:
            errors.append("Entry point must be 'module:class' format")

        return errors

    def _parse_version(self, version: str) -> tuple[int, int, int]:
        """Parse semver version."""
        parts = version.split(".")
        if len(parts) != 3:
            raise ValueError("Version must be X.Y.Z format")
        return tuple(int(p) for p in parts)
```

### 4. discovery.py - Plugin Discovery

```python
"""Plugin discovery from various sources."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from importlib.metadata import entry_points
from pathlib import Path
from typing import Iterator

from .manifest import PluginManifest, ManifestParser
from .exceptions import PluginManifestError


@dataclass
class DiscoveredPlugin:
    """Discovered plugin information."""
    path: Path | None
    manifest: PluginManifest
    source: str  # "user", "project", "package"

    @property
    def id(self) -> str:
        """Get plugin ID."""
        return self.manifest.name


class PluginDiscovery:
    """Discover plugins from various sources."""

    USER_PLUGIN_DIR = Path.home() / ".opencode" / "plugins"
    PROJECT_PLUGIN_DIR = Path(".opencode") / "plugins"
    ENTRY_POINT_GROUP = "opencode.plugins"

    def __init__(
        self,
        user_dir: Path | None = None,
        project_dir: Path | None = None,
        extra_paths: list[Path] | None = None
    ):
        """
        Initialize plugin discovery.

        Args:
            user_dir: User plugin directory. Default ~/.src/opencode/plugins
            project_dir: Project plugin directory. Default .src/opencode/plugins
            extra_paths: Additional paths to search.
        """
        self.user_dir = user_dir or self.USER_PLUGIN_DIR
        self.project_dir = project_dir or self.PROJECT_PLUGIN_DIR
        self.extra_paths = extra_paths or []
        self.parser = ManifestParser()

    def discover(self) -> list[DiscoveredPlugin]:
        """Discover all plugins from all sources."""
        plugins = []

        # Discover from directories
        plugins.extend(self.discover_user_plugins())
        plugins.extend(self.discover_project_plugins())
        plugins.extend(self.discover_extra_plugins())

        # Discover from installed packages
        plugins.extend(self.discover_package_plugins())

        return plugins

    def discover_user_plugins(self) -> list[DiscoveredPlugin]:
        """Discover plugins in user directory."""
        return list(self._discover_from_dir(self.user_dir, "user"))

    def discover_project_plugins(self) -> list[DiscoveredPlugin]:
        """Discover plugins in project directory."""
        return list(self._discover_from_dir(self.project_dir, "project"))

    def discover_extra_plugins(self) -> list[DiscoveredPlugin]:
        """Discover plugins from extra paths."""
        plugins = []
        for path in self.extra_paths:
            plugins.extend(self._discover_from_dir(path, "extra"))
        return plugins

    def discover_package_plugins(self) -> list[DiscoveredPlugin]:
        """Discover plugins from installed packages."""
        plugins = []

        try:
            eps = entry_points(group=self.ENTRY_POINT_GROUP)
        except TypeError:
            # Python 3.9 compatibility
            eps = entry_points().get(self.ENTRY_POINT_GROUP, [])

        for ep in eps:
            try:
                # Load the entry point to get the plugin class
                plugin_class = ep.load()

                # Create a manifest from the plugin class
                if hasattr(plugin_class, "metadata"):
                    instance = plugin_class()
                    meta = instance.metadata
                    caps = instance.capabilities

                    manifest = PluginManifest(
                        name=meta.name,
                        version=meta.version,
                        description=meta.description,
                        entry_point=f"{ep.value}",
                        metadata=meta,
                        capabilities=caps,
                    )

                    plugins.append(DiscoveredPlugin(
                        path=None,
                        manifest=manifest,
                        source="package",
                    ))

            except Exception as e:
                # Log but continue
                import logging
                logging.getLogger(__name__).warning(
                    f"Failed to load plugin entry point {ep.name}: {e}"
                )

        return plugins

    def _discover_from_dir(
        self,
        directory: Path,
        source: str
    ) -> Iterator[DiscoveredPlugin]:
        """Discover plugins from a directory."""
        if not directory.exists():
            return

        for item in directory.iterdir():
            if not item.is_dir():
                continue

            manifest_path = self.parser.find_manifest(item)
            if manifest_path is None:
                continue

            try:
                manifest = self.parser.parse(manifest_path)

                # Validate manifest
                errors = self.parser.validate(manifest)
                if errors:
                    import logging
                    logging.getLogger(__name__).warning(
                        f"Invalid manifest in {item}: {errors}"
                    )
                    continue

                yield DiscoveredPlugin(
                    path=item,
                    manifest=manifest,
                    source=source,
                )

            except PluginManifestError as e:
                import logging
                logging.getLogger(__name__).warning(
                    f"Failed to parse manifest in {item}: {e}"
                )
```

### 5. config.py - Plugin Configuration

```python
"""Plugin configuration management."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema


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
        user_dir = None
        if data.get("user_dir"):
            user_dir = Path(data["user_dir"]).expanduser()

        project_dir = None
        if data.get("project_dir"):
            project_dir = Path(data["project_dir"])

        return cls(
            enabled=data.get("enabled", True),
            user_dir=user_dir,
            project_dir=project_dir,
            disabled_plugins=data.get("disabled_plugins", []),
            plugin_configs=data.get("plugin_configs", {}),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "enabled": self.enabled,
            "user_dir": str(self.user_dir) if self.user_dir else None,
            "project_dir": str(self.project_dir) if self.project_dir else None,
            "disabled_plugins": self.disabled_plugins,
            "plugin_configs": self.plugin_configs,
        }


class PluginConfigManager:
    """Manage plugin configurations."""

    def __init__(
        self,
        base_config: PluginConfig,
        data_dir: Path | None = None
    ):
        """
        Initialize config manager.

        Args:
            base_config: Base plugin configuration.
            data_dir: Base directory for plugin data.
        """
        self.base_config = base_config
        self.data_dir = data_dir or Path.home() / ".opencode" / "plugin_data"

    def get_plugin_config(
        self,
        plugin_id: str,
        schema: dict | None = None,
        defaults: dict | None = None
    ) -> dict[str, Any]:
        """
        Get configuration for a plugin.

        Args:
            plugin_id: Plugin identifier.
            schema: JSON schema to apply defaults from.
            defaults: Default values.

        Returns:
            Plugin configuration dictionary.
        """
        config = self.base_config.plugin_configs.get(plugin_id, {})

        # Apply defaults
        if defaults:
            merged = dict(defaults)
            merged.update(config)
            config = merged

        # Apply schema defaults
        if schema:
            config = self._apply_schema_defaults(config, schema)

        return config

    def set_plugin_config(
        self,
        plugin_id: str,
        config: dict[str, Any]
    ) -> None:
        """Set configuration for a plugin."""
        self.base_config.plugin_configs[plugin_id] = config

    def get_plugin_data_dir(self, plugin_id: str) -> Path:
        """Get data directory for a plugin."""
        plugin_dir = self.data_dir / plugin_id
        plugin_dir.mkdir(parents=True, exist_ok=True)
        return plugin_dir

    def validate_config(
        self,
        config: dict[str, Any],
        schema: dict
    ) -> list[str]:
        """
        Validate config against JSON schema.

        Returns:
            List of validation errors.
        """
        errors = []
        try:
            jsonschema.validate(config, schema)
        except jsonschema.ValidationError as e:
            errors.append(str(e.message))
        except jsonschema.SchemaError as e:
            errors.append(f"Invalid schema: {e.message}")
        return errors

    def _apply_schema_defaults(
        self,
        config: dict[str, Any],
        schema: dict
    ) -> dict[str, Any]:
        """Apply default values from JSON schema."""
        result = dict(config)

        if schema.get("type") == "object":
            properties = schema.get("properties", {})
            for key, prop_schema in properties.items():
                if key not in result and "default" in prop_schema:
                    result[key] = prop_schema["default"]

        return result

    def is_plugin_disabled(self, plugin_id: str) -> bool:
        """Check if plugin is disabled."""
        return plugin_id in self.base_config.disabled_plugins

    def disable_plugin(self, plugin_id: str) -> None:
        """Add plugin to disabled list."""
        if plugin_id not in self.base_config.disabled_plugins:
            self.base_config.disabled_plugins.append(plugin_id)

    def enable_plugin(self, plugin_id: str) -> None:
        """Remove plugin from disabled list."""
        if plugin_id in self.base_config.disabled_plugins:
            self.base_config.disabled_plugins.remove(plugin_id)
```

### 6. loader.py - Plugin Loader

```python
"""Plugin loading."""
from __future__ import annotations

import importlib
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .base import Plugin, PluginContext
from .manifest import PluginManifest
from .config import PluginConfigManager
from .exceptions import PluginLoadError

if TYPE_CHECKING:
    from .discovery import DiscoveredPlugin


@dataclass
class LoadedPlugin:
    """Loaded plugin instance."""
    id: str
    manifest: PluginManifest
    instance: Plugin
    context: PluginContext
    source: str
    enabled: bool = True
    active: bool = False
    # Track if we added a path to sys.path so we can clean it up on unload
    added_sys_path: str | None = None


class PluginLoader:
    """Load plugin instances."""

    def __init__(
        self,
        config_manager: PluginConfigManager
    ):
        """
        Initialize plugin loader.

        Args:
            config_manager: Plugin configuration manager.
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)

    def load(self, discovered: "DiscoveredPlugin") -> LoadedPlugin:
        """
        Load a discovered plugin.

        Args:
            discovered: Discovered plugin information.

        Returns:
            Loaded plugin instance.

        Raises:
            PluginLoadError: If plugin fails to load.
        """
        manifest = discovered.manifest
        plugin_id = manifest.name
        added_path: str | None = None

        try:
            # Add plugin path to sys.path if needed
            # Track what we add so we can clean up on unload
            if discovered.path:
                plugin_path = str(discovered.path)
                if plugin_path not in sys.path:
                    sys.path.insert(0, plugin_path)
                    added_path = plugin_path  # Remember for cleanup

            # Import plugin module
            module_name, class_name = manifest.entry_point.split(":")
            module = importlib.import_module(module_name)

            # Get plugin class
            if not hasattr(module, class_name):
                raise PluginLoadError(
                    f"Plugin class {class_name} not found in {module_name}",
                    plugin_id=plugin_id,
                )

            plugin_class = getattr(module, class_name)

            # Validate it's a Plugin subclass
            if not issubclass(plugin_class, Plugin):
                raise PluginLoadError(
                    f"{class_name} is not a Plugin subclass",
                    plugin_id=plugin_id,
                )

            # Create instance
            instance = plugin_class()

            # Create context
            context = self.create_context(plugin_id, manifest)

            # Set context on instance
            instance.set_context(context)

            # Check if disabled
            enabled = not self.config_manager.is_plugin_disabled(plugin_id)

            return LoadedPlugin(
                id=plugin_id,
                manifest=manifest,
                instance=instance,
                context=context,
                source=discovered.source,
                enabled=enabled,
                added_sys_path=added_path,  # Track for cleanup
            )

        except ImportError as e:
            raise PluginLoadError(
                f"Failed to import plugin: {e}",
                plugin_id=plugin_id,
            )
        except Exception as e:
            raise PluginLoadError(
                f"Failed to load plugin: {e}",
                plugin_id=plugin_id,
            )

    def create_context(
        self,
        plugin_id: str,
        manifest: PluginManifest
    ) -> PluginContext:
        """Create context for a plugin."""
        # Get plugin config
        config = self.config_manager.get_plugin_config(
            plugin_id,
            schema=manifest.config_schema,
        )

        # Get plugin data directory
        data_dir = self.config_manager.get_plugin_data_dir(plugin_id)

        # Create logger for plugin
        logger = logging.getLogger(f"opencode.plugins.{plugin_id}")

        return PluginContext(
            plugin_id=plugin_id,
            data_dir=data_dir,
            config=config,
            logger=logger,
        )

    def unload(self, plugin: LoadedPlugin) -> None:
        """Unload a plugin and clean up sys.path modifications."""
        try:
            if plugin.active:
                plugin.instance.on_deactivate()
                plugin.active = False

            plugin.instance.on_unload()

        except Exception as e:
            self.logger.warning(
                f"Error unloading plugin {plugin.id}: {e}"
            )

        # Clean up sys.path entry we added during load
        # This prevents sys.path from growing indefinitely as plugins are
        # loaded/unloaded/reloaded, and avoids potential import conflicts
        if plugin.added_sys_path and plugin.added_sys_path in sys.path:
            try:
                sys.path.remove(plugin.added_sys_path)
                self.logger.debug(
                    f"Removed {plugin.added_sys_path} from sys.path"
                )
            except ValueError:
                pass  # Already removed (shouldn't happen, but be defensive)
```

### 7. registry.py - Plugin Registry

```python
"""Registry of plugin contributions."""
from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from opencode.tools.base import Tool
    from opencode.commands.base import Command


class PluginRegistry:
    """Registry of plugin contributions."""

    def __init__(self):
        """Initialize plugin registry."""
        # Maps tool name to (plugin_id, tool)
        self._tools: dict[str, tuple[str, Any]] = {}

        # Maps command name to (plugin_id, command)
        self._commands: dict[str, tuple[str, Any]] = {}

        # Maps event to list of (plugin_id, priority, handler)
        self._hooks: dict[str, list[tuple[str, int, Callable]]] = defaultdict(
            list
        )

        # Maps subagent type to (plugin_id, subagent_class)
        self._subagents: dict[str, tuple[str, type]] = {}

        # Maps skill name to (plugin_id, skill)
        self._skills: dict[str, tuple[str, Any]] = {}

    def register_tool(
        self,
        plugin_id: str,
        tool: "Tool"
    ) -> str:
        """
        Register a plugin tool.

        Args:
            plugin_id: Plugin identifier.
            tool: Tool instance.

        Returns:
            Prefixed tool name.
        """
        # Prefix tool name with plugin namespace
        prefixed_name = f"{plugin_id}__{tool.name}"
        self._tools[prefixed_name] = (plugin_id, tool)
        return prefixed_name

    def register_command(
        self,
        plugin_id: str,
        command: "Command"
    ) -> str:
        """
        Register a plugin command.

        Args:
            plugin_id: Plugin identifier.
            command: Command instance.

        Returns:
            Prefixed command name.
        """
        prefixed_name = f"{plugin_id}:{command.name}"
        self._commands[prefixed_name] = (plugin_id, command)
        return prefixed_name

    def register_hook(
        self,
        plugin_id: str,
        event: str,
        handler: Callable,
        priority: int = 100
    ) -> None:
        """
        Register a plugin hook handler.

        Args:
            plugin_id: Plugin identifier.
            event: Event name.
            handler: Handler function.
            priority: Handler priority (lower = earlier).
        """
        self._hooks[event].append((plugin_id, priority, handler))
        # Sort by priority
        self._hooks[event].sort(key=lambda x: x[1])

    def register_subagent(
        self,
        plugin_id: str,
        subagent_type: str,
        subagent_class: type
    ) -> str:
        """Register a plugin subagent type."""
        prefixed_type = f"{plugin_id}:{subagent_type}"
        self._subagents[prefixed_type] = (plugin_id, subagent_class)
        return prefixed_type

    def register_skill(
        self,
        plugin_id: str,
        skill: Any
    ) -> str:
        """Register a plugin skill."""
        prefixed_name = f"{plugin_id}:{skill.name}"
        self._skills[prefixed_name] = (plugin_id, skill)
        return prefixed_name

    def unregister_plugin(self, plugin_id: str) -> None:
        """Unregister all contributions from a plugin."""
        # Remove tools
        self._tools = {
            k: v for k, v in self._tools.items()
            if v[0] != plugin_id
        }

        # Remove commands
        self._commands = {
            k: v for k, v in self._commands.items()
            if v[0] != plugin_id
        }

        # Remove hooks
        for event in self._hooks:
            self._hooks[event] = [
                h for h in self._hooks[event]
                if h[0] != plugin_id
            ]

        # Remove subagents
        self._subagents = {
            k: v for k, v in self._subagents.items()
            if v[0] != plugin_id
        }

        # Remove skills
        self._skills = {
            k: v for k, v in self._skills.items()
            if v[0] != plugin_id
        }

    def get_tools(self) -> dict[str, Any]:
        """Get all registered tools."""
        return {name: tool for name, (_, tool) in self._tools.items()}

    def get_tool(self, name: str) -> Any | None:
        """Get a specific tool."""
        entry = self._tools.get(name)
        return entry[1] if entry else None

    def get_commands(self) -> dict[str, Any]:
        """Get all registered commands."""
        return {name: cmd for name, (_, cmd) in self._commands.items()}

    def get_command(self, name: str) -> Any | None:
        """Get a specific command."""
        entry = self._commands.get(name)
        return entry[1] if entry else None

    def get_hooks(self, event: str) -> list[Callable]:
        """Get all handlers for an event."""
        return [handler for _, _, handler in self._hooks.get(event, [])]

    def get_subagents(self) -> dict[str, type]:
        """Get all registered subagent types."""
        return {name: cls for name, (_, cls) in self._subagents.items()}

    def get_skills(self) -> dict[str, Any]:
        """Get all registered skills."""
        return {name: skill for name, (_, skill) in self._skills.items()}

    def list_plugins_contributions(self, plugin_id: str) -> dict:
        """List all contributions from a plugin."""
        return {
            "tools": [
                name for name, (pid, _) in self._tools.items()
                if pid == plugin_id
            ],
            "commands": [
                name for name, (pid, _) in self._commands.items()
                if pid == plugin_id
            ],
            "hooks": {
                event: len([h for h in handlers if h[0] == plugin_id])
                for event, handlers in self._hooks.items()
            },
            "subagents": [
                name for name, (pid, _) in self._subagents.items()
                if pid == plugin_id
            ],
            "skills": [
                name for name, (pid, _) in self._skills.items()
                if pid == plugin_id
            ],
        }
```

### 8. manager.py - Plugin Manager

```python
"""Plugin lifecycle management."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .discovery import PluginDiscovery, DiscoveredPlugin
from .loader import PluginLoader, LoadedPlugin
from .registry import PluginRegistry
from .config import PluginConfig, PluginConfigManager
from .exceptions import (
    PluginError,
    PluginNotFoundError,
    PluginLoadError,
    PluginLifecycleError,
)

if TYPE_CHECKING:
    pass


class PluginManager:
    """Manage plugin lifecycle.

    Thread-safe: uses RLock for plugin operations.
    """

    def __init__(
        self,
        config: PluginConfig | None = None,
        registry: PluginRegistry | None = None
    ):
        """
        Initialize plugin manager.

        Args:
            config: Plugin configuration.
            registry: Plugin registry (shared or new).
        """
        import threading

        self.config = config or PluginConfig()
        self.registry = registry or PluginRegistry()
        self.config_manager = PluginConfigManager(self.config)
        self.discovery = PluginDiscovery(
            user_dir=self.config.user_dir,
            project_dir=self.config.project_dir,
        )
        self.loader = PluginLoader(self.config_manager)
        self.logger = logging.getLogger(__name__)

        self._plugins: dict[str, LoadedPlugin] = {}
        self._load_errors: dict[str, str] = {}
        self._lock = threading.RLock()  # Thread-safe plugin operations
        self._loading: set[str] = set()  # Track plugins being loaded (circular import detection)

    @property
    def plugins(self) -> dict[str, LoadedPlugin]:
        """Get all loaded plugins."""
        return dict(self._plugins)

    def discover_and_load(self) -> None:
        """Discover and load all plugins."""
        if not self.config.enabled:
            self.logger.info("Plugin system is disabled")
            return

        discovered = self.discovery.discover()
        self.logger.info(f"Discovered {len(discovered)} plugins")

        for plugin_info in discovered:
            try:
                self._load_plugin(plugin_info)
            except PluginLoadError as e:
                self._load_errors[plugin_info.id] = str(e)
                self.logger.warning(
                    f"Failed to load plugin {plugin_info.id}: {e}"
                )

    def _load_plugin(self, discovered: DiscoveredPlugin) -> LoadedPlugin:
        """Load a single plugin."""
        plugin = self.loader.load(discovered)
        self._plugins[plugin.id] = plugin

        # Call on_load lifecycle hook
        try:
            plugin.instance.on_load()
        except Exception as e:
            self.logger.warning(f"Plugin {plugin.id} on_load failed: {e}")

        # If enabled, activate and register contributions
        if plugin.enabled:
            self._activate_plugin(plugin)

        return plugin

    def _activate_plugin(self, plugin: LoadedPlugin) -> None:
        """Activate a plugin and register its contributions."""
        # Register tools
        if plugin.manifest.capabilities.tools:
            for tool in plugin.instance.register_tools():
                name = self.registry.register_tool(plugin.id, tool)
                self.logger.debug(f"Registered tool: {name}")

        # Register commands
        if plugin.manifest.capabilities.commands:
            for command in plugin.instance.register_commands():
                name = self.registry.register_command(plugin.id, command)
                self.logger.debug(f"Registered command: {name}")

        # Register hooks
        if plugin.manifest.capabilities.hooks:
            for event, handlers in plugin.instance.register_hooks().items():
                for handler in handlers:
                    self.registry.register_hook(plugin.id, event, handler)
                    self.logger.debug(f"Registered hook for {event}")

        # Call on_activate lifecycle hook
        try:
            plugin.instance.on_activate()
            plugin.active = True
        except Exception as e:
            self.logger.warning(f"Plugin {plugin.id} on_activate failed: {e}")

    def _deactivate_plugin(self, plugin: LoadedPlugin) -> None:
        """Deactivate a plugin and unregister its contributions."""
        # Unregister all contributions
        self.registry.unregister_plugin(plugin.id)

        # Call on_deactivate lifecycle hook
        try:
            plugin.instance.on_deactivate()
            plugin.active = False
        except Exception as e:
            self.logger.warning(
                f"Plugin {plugin.id} on_deactivate failed: {e}"
            )

    def get_plugin(self, plugin_id: str) -> LoadedPlugin | None:
        """Get a plugin by ID."""
        return self._plugins.get(plugin_id)

    def enable(self, plugin_id: str) -> None:
        """Enable a plugin."""
        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            raise PluginNotFoundError(
                f"Plugin not found: {plugin_id}",
                plugin_id=plugin_id,
            )

        if plugin.enabled:
            return

        # Enable in config
        self.config_manager.enable_plugin(plugin_id)

        # Activate plugin
        plugin.enabled = True
        self._activate_plugin(plugin)

        self.logger.info(f"Enabled plugin: {plugin_id}")

    def disable(self, plugin_id: str) -> None:
        """Disable a plugin."""
        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            raise PluginNotFoundError(
                f"Plugin not found: {plugin_id}",
                plugin_id=plugin_id,
            )

        if not plugin.enabled:
            return

        # Deactivate plugin
        self._deactivate_plugin(plugin)

        # Disable in config
        self.config_manager.disable_plugin(plugin_id)
        plugin.enabled = False

        self.logger.info(f"Disabled plugin: {plugin_id}")

    def reload(self, plugin_id: str) -> None:
        """Reload a plugin.

        Thread-safe: entire reload operation is atomic.
        Prevents access to plugin during reload.

        Args:
            plugin_id: Plugin ID to reload.

        Raises:
            PluginNotFoundError: If plugin not found.
            PluginLoadError: If reload fails.
        """
        with self._lock:
            # Check for circular reload
            if plugin_id in self._loading:
                raise PluginLoadError(
                    f"Circular reload detected: {plugin_id}",
                    plugin_id=plugin_id,
                )

            plugin = self._plugins.get(plugin_id)
            if plugin is None:
                raise PluginNotFoundError(
                    f"Plugin not found: {plugin_id}",
                    plugin_id=plugin_id,
                )

            # Mark as loading to prevent concurrent access
            self._loading.add(plugin_id)

            try:
                # Unload
                if plugin.active:
                    self._deactivate_plugin(plugin)
                self.loader.unload(plugin)

                # Find the discovered info again
                discovered_list = self.discovery.discover()
                discovered = next(
                    (d for d in discovered_list if d.id == plugin_id),
                    None
                )

                if discovered is None:
                    del self._plugins[plugin_id]
                    raise PluginNotFoundError(
                        f"Plugin no longer found: {plugin_id}",
                        plugin_id=plugin_id,
                    )

                # Reload
                new_plugin = self.loader.load(discovered)
                self._plugins[plugin_id] = new_plugin

            finally:
                # Always remove from loading set
                self._loading.discard(plugin_id)

        new_plugin.instance.on_load()

        if new_plugin.enabled:
            self._activate_plugin(new_plugin)

        self.logger.info(f"Reloaded plugin: {plugin_id}")

    def list_plugins(self) -> list[LoadedPlugin]:
        """List all loaded plugins."""
        return list(self._plugins.values())

    def get_load_errors(self) -> dict[str, str]:
        """Get plugins that failed to load."""
        return dict(self._load_errors)

    def shutdown(self) -> None:
        """Shutdown plugin system."""
        for plugin in self._plugins.values():
            try:
                if plugin.active:
                    self._deactivate_plugin(plugin)
                self.loader.unload(plugin)
            except Exception as e:
                self.logger.warning(
                    f"Error shutting down plugin {plugin.id}: {e}"
                )

        self._plugins.clear()
```

### 9. __init__.py - Package Exports

```python
"""Plugin system for OpenCode."""
from .base import (
    Plugin,
    PluginMetadata,
    PluginCapabilities,
    PluginContext,
)
from .manifest import (
    PluginManifest,
    ManifestParser,
)
from .discovery import (
    PluginDiscovery,
    DiscoveredPlugin,
)
from .config import (
    PluginConfig,
    PluginConfigManager,
)
from .loader import (
    PluginLoader,
    LoadedPlugin,
)
from .registry import PluginRegistry
from .manager import PluginManager
from .exceptions import (
    PluginError,
    PluginNotFoundError,
    PluginLoadError,
    PluginManifestError,
    PluginDependencyError,
    PluginConfigError,
    PluginLifecycleError,
)

__all__ = [
    # Base
    "Plugin",
    "PluginMetadata",
    "PluginCapabilities",
    "PluginContext",
    # Manifest
    "PluginManifest",
    "ManifestParser",
    # Discovery
    "PluginDiscovery",
    "DiscoveredPlugin",
    # Config
    "PluginConfig",
    "PluginConfigManager",
    # Loader
    "PluginLoader",
    "LoadedPlugin",
    # Registry
    "PluginRegistry",
    # Manager
    "PluginManager",
    # Exceptions
    "PluginError",
    "PluginNotFoundError",
    "PluginLoadError",
    "PluginManifestError",
    "PluginDependencyError",
    "PluginConfigError",
    "PluginLifecycleError",
]
```

---

## Example Plugin

### ~/.src/opencode/plugins/hello-plugin/plugin.yaml

```yaml
name: hello-plugin
version: 1.0.0
description: A simple hello world plugin

author: Example Author
license: MIT

entry_point: hello_plugin:HelloPlugin

capabilities:
  tools: true
  commands: true

config:
  schema:
    type: object
    properties:
      greeting:
        type: string
        default: "Hello"
```

### ~/.src/opencode/plugins/hello-plugin/hello_plugin.py

```python
from opencode.plugins import Plugin, PluginMetadata, PluginCapabilities
from opencode.tools.base import Tool


class HelloTool(Tool):
    name = "hello"
    description = "Say hello"

    async def execute(self, name: str = "World") -> str:
        greeting = self.context.config.get("greeting", "Hello")
        return f"{greeting}, {name}!"


class HelloPlugin(Plugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="hello-plugin",
            version="1.0.0",
            description="A simple hello world plugin",
        )

    @property
    def capabilities(self) -> PluginCapabilities:
        return PluginCapabilities(tools=True)

    def register_tools(self) -> list[Tool]:
        tool = HelloTool()
        tool.context = self.context
        return [tool]
```

---

## Notes

- Plugins are loaded on startup
- Plugin errors don't crash the main application
- Tool and command names are prefixed with plugin namespace
- Plugins have isolated data directories
- Configuration supports JSON schema validation
