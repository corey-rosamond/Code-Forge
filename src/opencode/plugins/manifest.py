"""Plugin manifest parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

import yaml

from .base import PluginCapabilities, PluginMetadata
from .exceptions import PluginManifestError


@dataclass
class PluginManifest:
    """Parsed plugin manifest.

    Contains all information from a plugin's manifest file
    including metadata, capabilities, dependencies, and configuration schema.

    Attributes:
        name: Plugin name (unique identifier).
        version: Semver version string.
        description: Human-readable description.
        entry_point: Module and class path (e.g., "my_plugin:MyPlugin").
        metadata: Full plugin metadata.
        capabilities: Plugin capability declarations.
        dependencies: List of Python package dependencies.
        config_schema: Optional JSON Schema for plugin configuration.
        path: Path to the plugin directory.
    """

    name: str
    version: str
    description: str
    entry_point: str
    metadata: PluginMetadata
    capabilities: PluginCapabilities
    dependencies: list[str] = field(default_factory=list)
    config_schema: dict[str, Any] | None = None
    path: Path | None = None

    @classmethod
    def from_yaml(cls, path: Path) -> PluginManifest:
        """Load manifest from YAML file.

        Args:
            path: Path to plugin.yaml or plugin.yml file.

        Returns:
            Parsed PluginManifest.

        Raises:
            PluginManifestError: If file not found or invalid YAML.
        """
        if not path.exists():
            raise PluginManifestError(f"Manifest not found: {path}")

        try:
            with path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise PluginManifestError(f"Invalid YAML: {e}") from e

        if data is None:
            raise PluginManifestError("Empty manifest file")

        return cls._from_dict(data, path.parent)

    @classmethod
    def from_pyproject(cls, path: Path) -> PluginManifest:
        """Load manifest from pyproject.toml.

        Looks for plugin configuration in [tool.opencode.plugin] section.

        Args:
            path: Path to pyproject.toml file.

        Returns:
            Parsed PluginManifest.

        Raises:
            PluginManifestError: If file not found, invalid TOML, or missing section.
        """
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore[import-not-found,no-redef]
            except ImportError as ie:
                raise PluginManifestError(
                    "tomllib/tomli not available for pyproject.toml parsing"
                ) from ie

        if not path.exists():
            raise PluginManifestError(f"pyproject.toml not found: {path}")

        try:
            with path.open("rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            raise PluginManifestError(f"Invalid TOML: {e}") from e

        plugin_data = data.get("tool", {}).get("opencode", {}).get("plugin")
        if not plugin_data:
            raise PluginManifestError("No [tool.opencode.plugin] section")

        return cls._from_dict(plugin_data, path.parent)

    @classmethod
    def _from_dict(cls, data: dict[str, Any], base_path: Path) -> PluginManifest:
        """Create manifest from dictionary.

        Args:
            data: Dictionary with manifest data.
            base_path: Base path for the plugin directory.

        Returns:
            Parsed PluginManifest.

        Raises:
            PluginManifestError: If required fields are missing.
        """
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
    """Parse plugin manifests.

    Supports both plugin.yaml/plugin.yml and pyproject.toml formats.
    Provides validation for manifest content.

    Class Attributes:
        MANIFEST_FILES: List of recognized manifest filenames.
    """

    MANIFEST_FILES: ClassVar[list[str]] = ["plugin.yaml", "plugin.yml", "pyproject.toml"]

    def find_manifest(self, plugin_dir: Path) -> Path | None:
        """Find manifest file in directory.

        Searches for manifest files in priority order:
        plugin.yaml, plugin.yml, pyproject.toml.

        Args:
            plugin_dir: Directory to search.

        Returns:
            Path to manifest file or None if not found.
        """
        for name in self.MANIFEST_FILES:
            path = plugin_dir / name
            if path.exists():
                return path
        return None

    def parse(self, path: Path) -> PluginManifest:
        """Parse manifest from path.

        Automatically detects format based on filename.

        Args:
            path: Path to manifest file.

        Returns:
            Parsed PluginManifest.

        Raises:
            PluginManifestError: If unknown manifest type or parsing fails.
        """
        if path.name in ("plugin.yaml", "plugin.yml"):
            return PluginManifest.from_yaml(path)
        elif path.name == "pyproject.toml":
            return PluginManifest.from_pyproject(path)
        else:
            raise PluginManifestError(f"Unknown manifest type: {path.name}")

    def validate(self, manifest: PluginManifest) -> list[str]:
        """Validate manifest, return list of errors.

        Checks for:
        - Valid plugin name (alphanumeric with - or _)
        - Valid semver version format
        - Valid entry point format (module:class)

        Args:
            manifest: Manifest to validate.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: list[str] = []

        # Validate name
        if not manifest.name:
            errors.append("Plugin name is required")
        elif not self._is_valid_name(manifest.name):
            errors.append("Plugin name must be alphanumeric with - or _")

        # Validate version
        if not manifest.version:
            errors.append("Plugin version is required")
        else:
            try:
                self._parse_version(manifest.version)
            except ValueError:
                errors.append("Invalid version format (use semver X.Y.Z)")

        # Validate entry point
        if not manifest.entry_point:
            errors.append("Entry point is required")
        elif ":" not in manifest.entry_point:
            errors.append("Entry point must be 'module:class' format")

        return errors

    def _is_valid_name(self, name: str) -> bool:
        """Check if name is valid plugin name.

        Args:
            name: Name to validate.

        Returns:
            True if valid plugin name.
        """
        # Allow alphanumeric, hyphens, and underscores
        return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", name))

    def _parse_version(self, version: str) -> tuple[int, int, int]:
        """Parse semver version.

        Args:
            version: Version string (X.Y.Z format).

        Returns:
            Tuple of (major, minor, patch).

        Raises:
            ValueError: If version format is invalid.
        """
        # Support basic semver (X.Y.Z) and pre-release (X.Y.Z-suffix)
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version)
        if not match:
            raise ValueError("Version must be X.Y.Z format")
        return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
