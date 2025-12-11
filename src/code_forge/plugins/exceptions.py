"""Plugin system exceptions."""

from __future__ import annotations


class PluginError(Exception):
    """Base exception for plugin errors."""

    def __init__(self, message: str, plugin_id: str | None = None) -> None:
        """Initialize plugin error.

        Args:
            message: Error message.
            plugin_id: Optional plugin identifier.
        """
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
