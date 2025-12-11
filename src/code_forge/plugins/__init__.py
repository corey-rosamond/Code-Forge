"""Plugin system for Code-Forge.

This module provides extensibility through third-party plugins that can
add tools, commands, hooks, and other capabilities.

Example plugin:

    from code_forge.plugins import Plugin, PluginMetadata, PluginCapabilities

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

        def register_tools(self) -> list:
            return [MyTool()]
"""

from .base import (
    Plugin,
    PluginCapabilities,
    PluginContext,
    PluginMetadata,
)
from .config import (
    PluginConfig,
    PluginConfigManager,
)
from .discovery import (
    DiscoveredPlugin,
    PluginDiscovery,
)
from .exceptions import (
    PluginConfigError,
    PluginDependencyError,
    PluginError,
    PluginLifecycleError,
    PluginLoadError,
    PluginManifestError,
    PluginNotFoundError,
)
from .loader import (
    LoadedPlugin,
    PluginLoader,
)
from .manager import PluginManager
from .manifest import (
    ManifestParser,
    PluginManifest,
)
from .registry import PluginRegistry

__all__ = [
    "DiscoveredPlugin",
    "LoadedPlugin",
    "ManifestParser",
    "Plugin",
    "PluginCapabilities",
    "PluginConfig",
    "PluginConfigError",
    "PluginConfigManager",
    "PluginContext",
    "PluginDependencyError",
    "PluginDiscovery",
    "PluginError",
    "PluginLifecycleError",
    "PluginLoadError",
    "PluginLoader",
    "PluginManager",
    "PluginManifest",
    "PluginManifestError",
    "PluginMetadata",
    "PluginNotFoundError",
    "PluginRegistry",
]
