"""Plugin configuration management."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import jsonschema

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


@dataclass
class PluginConfig:
    """Plugin system configuration.

    Controls plugin system behavior and stores per-plugin configurations.

    Attributes:
        enabled: Whether the plugin system is enabled.
        user_dir: User plugin directory (overrides default).
        project_dir: Project plugin directory (overrides default).
        disabled_plugins: List of plugin IDs that should not be activated.
        plugin_configs: Per-plugin configuration dictionaries.
    """

    enabled: bool = True
    user_dir: Path | None = None
    project_dir: Path | None = None
    disabled_plugins: list[str] = field(default_factory=list)
    plugin_configs: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PluginConfig:
        """Create from dictionary.

        Args:
            data: Configuration dictionary.

        Returns:
            PluginConfig instance.
        """
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

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Configuration dictionary.
        """
        return {
            "enabled": self.enabled,
            "user_dir": str(self.user_dir) if self.user_dir else None,
            "project_dir": str(self.project_dir) if self.project_dir else None,
            "disabled_plugins": self.disabled_plugins,
            "plugin_configs": self.plugin_configs,
        }


class PluginConfigManager:
    """Manage plugin configurations.

    Provides methods for getting and setting plugin configurations,
    managing data directories, and validating configurations against schemas.

    Attributes:
        base_config: Base plugin system configuration.
        data_dir: Base directory for plugin data storage.
    """

    def __init__(
        self,
        base_config: PluginConfig,
        data_dir: Path | None = None,
    ) -> None:
        """Initialize config manager.

        Args:
            base_config: Base plugin configuration.
            data_dir: Base directory for plugin data.
        """
        self.base_config = base_config
        self.data_dir = data_dir or Path.home() / ".forge" / "plugin_data"

    def get_plugin_config(
        self,
        plugin_id: str,
        schema: dict[str, Any] | None = None,
        defaults: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get configuration for a plugin.

        Merges defaults with user configuration and applies schema defaults.

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
            merged: dict[str, Any] = dict(defaults)
            merged.update(config)
            config = merged

        # Apply schema defaults
        if schema:
            config = self._apply_schema_defaults(config, schema)

        return config

    def set_plugin_config(
        self,
        plugin_id: str,
        config: dict[str, Any],
    ) -> None:
        """Set configuration for a plugin.

        Args:
            plugin_id: Plugin identifier.
            config: Configuration dictionary to set.
        """
        self.base_config.plugin_configs[plugin_id] = config

    def get_plugin_data_dir(self, plugin_id: str) -> Path:
        """Get data directory for a plugin.

        Creates the directory if it doesn't exist.

        Args:
            plugin_id: Plugin identifier.

        Returns:
            Path to plugin's data directory.
        """
        plugin_dir = self.data_dir / plugin_id
        plugin_dir.mkdir(parents=True, exist_ok=True)
        return plugin_dir

    def validate_config(
        self,
        config: dict[str, Any],
        schema: dict[str, Any],
    ) -> list[str]:
        """Validate config against JSON schema.

        Args:
            config: Configuration to validate.
            schema: JSON schema to validate against.

        Returns:
            List of validation errors (empty if valid).
        """
        if not HAS_JSONSCHEMA:
            # If jsonschema not installed, skip validation
            return []

        errors: list[str] = []
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
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Apply default values from JSON schema.

        Args:
            config: Configuration dictionary.
            schema: JSON schema with default values.

        Returns:
            Configuration with defaults applied.
        """
        result = dict(config)

        if schema.get("type") == "object":
            properties = schema.get("properties", {})
            for key, prop_schema in properties.items():
                if key not in result and "default" in prop_schema:
                    result[key] = prop_schema["default"]

        return result

    def is_plugin_disabled(self, plugin_id: str) -> bool:
        """Check if plugin is disabled.

        Args:
            plugin_id: Plugin identifier.

        Returns:
            True if plugin is in disabled list.
        """
        return plugin_id in self.base_config.disabled_plugins

    def disable_plugin(self, plugin_id: str) -> None:
        """Add plugin to disabled list.

        Args:
            plugin_id: Plugin identifier to disable.
        """
        if plugin_id not in self.base_config.disabled_plugins:
            self.base_config.disabled_plugins.append(plugin_id)

    def enable_plugin(self, plugin_id: str) -> None:
        """Remove plugin from disabled list.

        Args:
            plugin_id: Plugin identifier to enable.
        """
        if plugin_id in self.base_config.disabled_plugins:
            self.base_config.disabled_plugins.remove(plugin_id)
