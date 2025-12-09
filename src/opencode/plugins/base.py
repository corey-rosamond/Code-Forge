"""Plugin base class and related types."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from opencode.commands.base import Command
    from opencode.tools.base import BaseTool


@dataclass
class PluginMetadata:
    """Plugin metadata.

    Contains identifying information about a plugin including
    name, version, description, and author details.

    Attributes:
        name: Unique plugin identifier.
        version: Semver version string (X.Y.Z).
        description: Human-readable description.
        author: Optional author name.
        email: Optional author email.
        license: Optional license identifier (e.g., MIT, Apache-2.0).
        homepage: Optional URL to plugin homepage.
        repository: Optional URL to source repository.
        keywords: Search keywords for discovery.
        opencode_version: Optional version constraint (e.g., ">=1.0.0").
    """

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
        """Convert to dictionary.

        Returns:
            Dictionary representation of metadata.
        """
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
    """Plugin capabilities declaration.

    Declares what types of extensions the plugin provides.
    Used for filtering and security checks.

    Attributes:
        tools: Plugin provides tools.
        commands: Plugin provides slash commands.
        hooks: Plugin provides hook handlers.
        subagents: Plugin provides subagent types.
        skills: Plugin provides skills.
        system_access: Plugin requires system access (requires approval).
    """

    tools: bool = False
    commands: bool = False
    hooks: bool = False
    subagents: bool = False
    skills: bool = False
    system_access: bool = False

    def to_dict(self) -> dict[str, bool]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of capabilities.
        """
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
    """Context provided to plugins.

    Provides plugins with access to configuration, data storage,
    and logging facilities.

    Attributes:
        plugin_id: Unique plugin identifier.
        data_dir: Directory for plugin data storage.
        config: Plugin configuration dictionary.
        logger: Logger instance for the plugin.
    """

    plugin_id: str
    data_dir: Path
    config: dict[str, Any]
    logger: logging.Logger

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key.
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        return self.config.get(key, default)

    def ensure_data_dir(self) -> Path:
        """Ensure data directory exists.

        Creates the data directory if it doesn't exist.

        Returns:
            Path to the data directory.
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir


class Plugin(ABC):
    """Base class for OpenCode plugins.

    Plugins extend OpenCode by providing tools, commands, hooks,
    and other functionality. Subclasses must implement the metadata
    property and may override lifecycle hooks and registration methods.

    Lifecycle:
        1. on_load() - Called when plugin is loaded
        2. on_activate() - Called when plugin is activated
        3. on_deactivate() - Called when plugin is deactivated
        4. on_unload() - Called when plugin is unloaded

    Example:
        class MyPlugin(Plugin):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="my-plugin",
                    version="1.0.0",
                    description="A sample plugin"
                )

            @property
            def capabilities(self) -> PluginCapabilities:
                return PluginCapabilities(tools=True)

            def register_tools(self) -> list[BaseTool]:
                return [MyTool()]
    """

    def __init__(self) -> None:
        """Initialize plugin."""
        self._context: PluginContext | None = None

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        Returns:
            PluginMetadata instance with plugin information.
        """
        ...

    @property
    def capabilities(self) -> PluginCapabilities:
        """Return plugin capabilities.

        Override to declare what the plugin provides.

        Returns:
            PluginCapabilities declaring provided features.
        """
        return PluginCapabilities()

    @property
    def context(self) -> PluginContext:
        """Get plugin context.

        Returns:
            The plugin's context.

        Raises:
            RuntimeError: If plugin not initialized with context.
        """
        if self._context is None:
            raise RuntimeError("Plugin not initialized with context")
        return self._context

    def set_context(self, context: PluginContext) -> None:
        """Set plugin context.

        Called by the plugin loader during initialization.

        Args:
            context: Plugin context to set.
        """
        self._context = context

    def on_load(self) -> None:  # noqa: B027
        """Called when plugin is loaded.

        Override to perform initialization tasks.
        This is called before activation.
        """

    def on_activate(self) -> None:  # noqa: B027
        """Called when plugin is activated.

        Override to perform activation tasks.
        This is called after on_load and after tools/commands are registered.
        """

    def on_deactivate(self) -> None:  # noqa: B027
        """Called when plugin is deactivated.

        Override to perform cleanup before deactivation.
        This is called before tools/commands are unregistered.
        """

    def on_unload(self) -> None:  # noqa: B027
        """Called when plugin is unloaded.

        Override to perform final cleanup.
        This is called after deactivation.
        """

    def register_tools(self) -> list[BaseTool]:
        """Return list of tools to register.

        Override to provide tools from this plugin.
        Only called if capabilities.tools is True.

        Returns:
            List of BaseTool instances to register.
        """
        return []

    def register_commands(self) -> list[Command]:
        """Return list of commands to register.

        Override to provide commands from this plugin.
        Only called if capabilities.commands is True.

        Returns:
            List of Command instances to register.
        """
        return []

    def register_hooks(self) -> dict[str, list[Callable[..., Any]]]:
        """Return hooks to register.

        Override to provide hook handlers from this plugin.
        Only called if capabilities.hooks is True.

        Returns:
            Dictionary mapping event names to lists of handler functions.
        """
        return {}

    def get_config_schema(self) -> dict[str, Any] | None:
        """Return JSON schema for plugin configuration.

        Override to provide a configuration schema for validation.

        Returns:
            JSON Schema dict or None if no schema.
        """
        return None
