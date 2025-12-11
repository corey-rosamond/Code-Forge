"""Tests for plugin discovery."""

from pathlib import Path
from unittest.mock import patch

from code_forge.plugins.discovery import DiscoveredPlugin, PluginDiscovery


class TestDiscoveredPlugin:
    """Tests for DiscoveredPlugin."""

    def test_id_property(self, tmp_path: Path) -> None:
        """Test id property returns manifest name."""
        from code_forge.plugins.base import PluginCapabilities, PluginMetadata
        from code_forge.plugins.manifest import PluginManifest

        manifest = PluginManifest(
            name="test-plugin",
            version="1.0.0",
            description="Test",
            entry_point="test:Plugin",
            metadata=PluginMetadata(
                name="test-plugin",
                version="1.0.0",
                description="Test",
            ),
            capabilities=PluginCapabilities(),
        )
        discovered = DiscoveredPlugin(
            path=tmp_path,
            manifest=manifest,
            source="user",
        )
        assert discovered.id == "test-plugin"


class TestPluginDiscovery:
    """Tests for PluginDiscovery."""

    def test_default_directories(self) -> None:
        """Test default plugin directories."""
        discovery = PluginDiscovery()
        assert discovery.user_dir == Path.home() / ".forge" / "plugins"
        assert discovery.project_dir == Path(".forge") / "plugins"

    def test_custom_directories(self, tmp_path: Path) -> None:
        """Test custom plugin directories."""
        user_dir = tmp_path / "user_plugins"
        project_dir = tmp_path / "project_plugins"
        discovery = PluginDiscovery(
            user_dir=user_dir,
            project_dir=project_dir,
        )
        assert discovery.user_dir == user_dir
        assert discovery.project_dir == project_dir

    def test_discover_user_plugins(self, tmp_path: Path) -> None:
        """Test discovering plugins in user directory."""
        user_dir = tmp_path / "user_plugins"
        plugin_dir = user_dir / "my-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.yaml").write_text("""
name: my-plugin
version: 1.0.0
description: My plugin
entry_point: my_plugin:Plugin
""")
        discovery = PluginDiscovery(user_dir=user_dir)
        plugins = discovery.discover_user_plugins()
        assert len(plugins) == 1
        assert plugins[0].id == "my-plugin"
        assert plugins[0].source == "user"

    def test_discover_project_plugins(self, tmp_path: Path) -> None:
        """Test discovering plugins in project directory."""
        project_dir = tmp_path / "project_plugins"
        plugin_dir = project_dir / "project-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.yaml").write_text("""
name: project-plugin
version: 1.0.0
description: Project plugin
entry_point: project_plugin:Plugin
""")
        discovery = PluginDiscovery(project_dir=project_dir)
        plugins = discovery.discover_project_plugins()
        assert len(plugins) == 1
        assert plugins[0].id == "project-plugin"
        assert plugins[0].source == "project"

    def test_discover_extra_plugins(self, tmp_path: Path) -> None:
        """Test discovering plugins from extra paths."""
        extra_dir = tmp_path / "extra_plugins"
        plugin_dir = extra_dir / "extra-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.yaml").write_text("""
name: extra-plugin
version: 1.0.0
description: Extra plugin
entry_point: extra_plugin:Plugin
""")
        discovery = PluginDiscovery(extra_paths=[extra_dir])
        plugins = discovery.discover_extra_plugins()
        assert len(plugins) == 1
        assert plugins[0].id == "extra-plugin"
        assert plugins[0].source == "extra"

    def test_discover_all(self, tmp_path: Path) -> None:
        """Test discovering from all sources."""
        user_dir = tmp_path / "user"
        project_dir = tmp_path / "project"

        # Create user plugin
        user_plugin = user_dir / "user-plugin"
        user_plugin.mkdir(parents=True)
        (user_plugin / "plugin.yaml").write_text("""
name: user-plugin
version: 1.0.0
description: User plugin
entry_point: user:Plugin
""")

        # Create project plugin
        project_plugin = project_dir / "project-plugin"
        project_plugin.mkdir(parents=True)
        (project_plugin / "plugin.yaml").write_text("""
name: project-plugin
version: 1.0.0
description: Project plugin
entry_point: project:Plugin
""")

        discovery = PluginDiscovery(user_dir=user_dir, project_dir=project_dir)
        plugins = discovery.discover()
        assert len(plugins) == 2
        plugin_ids = {p.id for p in plugins}
        assert plugin_ids == {"user-plugin", "project-plugin"}

    def test_skip_directory_without_manifest(self, tmp_path: Path) -> None:
        """Test directories without manifests are skipped."""
        user_dir = tmp_path / "user"
        (user_dir / "not-a-plugin").mkdir(parents=True)
        (user_dir / "not-a-plugin" / "some_file.txt").write_text("not a manifest")

        discovery = PluginDiscovery(user_dir=user_dir)
        plugins = discovery.discover_user_plugins()
        assert len(plugins) == 0

    def test_skip_invalid_manifest(self, tmp_path: Path) -> None:
        """Test plugins with invalid manifests are skipped."""
        user_dir = tmp_path / "user"
        plugin_dir = user_dir / "invalid-plugin"
        plugin_dir.mkdir(parents=True)
        # Missing required fields
        (plugin_dir / "plugin.yaml").write_text("""
name: invalid-plugin
# Missing version, description, entry_point
""")
        discovery = PluginDiscovery(user_dir=user_dir)
        plugins = discovery.discover_user_plugins()
        assert len(plugins) == 0

    def test_skip_malformed_yaml(self, tmp_path: Path) -> None:
        """Test plugins with malformed YAML are skipped."""
        user_dir = tmp_path / "user"
        plugin_dir = user_dir / "bad-yaml"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.yaml").write_text("invalid: yaml: :")

        discovery = PluginDiscovery(user_dir=user_dir)
        plugins = discovery.discover_user_plugins()
        assert len(plugins) == 0

    def test_skip_non_directories(self, tmp_path: Path) -> None:
        """Test non-directory items are skipped."""
        user_dir = tmp_path / "user"
        user_dir.mkdir(parents=True)
        (user_dir / "file.txt").write_text("not a directory")

        discovery = PluginDiscovery(user_dir=user_dir)
        plugins = discovery.discover_user_plugins()
        assert len(plugins) == 0

    def test_discover_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test discovering from non-existent directory."""
        discovery = PluginDiscovery(user_dir=tmp_path / "nonexistent")
        plugins = discovery.discover_user_plugins()
        assert plugins == []

    def test_multiple_plugins_in_directory(self, tmp_path: Path) -> None:
        """Test discovering multiple plugins."""
        user_dir = tmp_path / "user"

        for i in range(3):
            plugin_dir = user_dir / f"plugin-{i}"
            plugin_dir.mkdir(parents=True)
            (plugin_dir / "plugin.yaml").write_text(f"""
name: plugin-{i}
version: 1.0.0
description: Plugin {i}
entry_point: plugin{i}:Plugin
""")

        discovery = PluginDiscovery(user_dir=user_dir)
        plugins = discovery.discover_user_plugins()
        assert len(plugins) == 3

    def test_discover_package_plugins_empty(self) -> None:
        """Test discovering package plugins when none exist."""
        discovery = PluginDiscovery()
        # This will likely return empty unless packages are installed
        plugins = discovery.discover_package_plugins()
        assert isinstance(plugins, list)

    def test_plugin_yml_extension(self, tmp_path: Path) -> None:
        """Test discovering plugins with .yml extension."""
        user_dir = tmp_path / "user"
        plugin_dir = user_dir / "yml-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.yml").write_text("""
name: yml-plugin
version: 1.0.0
description: YML plugin
entry_point: yml:Plugin
""")
        discovery = PluginDiscovery(user_dir=user_dir)
        plugins = discovery.discover_user_plugins()
        assert len(plugins) == 1
        assert plugins[0].id == "yml-plugin"

    def test_discover_with_manifest_parse_error(self, tmp_path: Path) -> None:
        """Test discovery handles manifest parse error gracefully."""
        from code_forge.plugins.exceptions import PluginManifestError

        user_dir = tmp_path / "user"
        plugin_dir = user_dir / "error-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.yaml").write_text("""
name: error-plugin
version: 1.0.0
description: Error plugin
entry_point: error:Plugin
""")

        discovery = PluginDiscovery(user_dir=user_dir)

        # Mock parser.parse to raise error
        with patch.object(
            discovery.parser, "parse",
            side_effect=PluginManifestError("Parse failed", plugin_id="error-plugin")
        ):
            plugins = discovery.discover_user_plugins()
            # Should skip the plugin and not crash
            assert len(plugins) == 0

    def test_discover_package_plugins_with_error(self) -> None:
        """Test package plugin discovery handles errors gracefully."""
        from unittest.mock import MagicMock

        discovery = PluginDiscovery()

        # Mock entry_points to return an entry point that fails to load
        mock_ep = MagicMock()
        mock_ep.name = "bad-plugin"
        mock_ep.load.side_effect = ImportError("Cannot import")

        with patch("code_forge.plugins.discovery.entry_points", return_value=[mock_ep]):
            plugins = discovery.discover_package_plugins()
            # Should return empty list and not crash
            assert plugins == []

    def test_discover_package_plugins_successful(self) -> None:
        """Test successful package plugin discovery."""
        from unittest.mock import MagicMock

        from code_forge.plugins.base import PluginCapabilities, PluginMetadata

        discovery = PluginDiscovery()

        # Create mock plugin class
        mock_instance = MagicMock()
        mock_instance.metadata = PluginMetadata(
            name="package-plugin",
            version="1.0.0",
            description="Package plugin",
        )
        mock_instance.capabilities = PluginCapabilities(tools=True)

        mock_class = MagicMock()
        mock_class.return_value = mock_instance

        mock_ep = MagicMock()
        mock_ep.name = "package-plugin"
        mock_ep.value = "package_plugin:PackagePlugin"
        mock_ep.load.return_value = mock_class

        with patch("code_forge.plugins.discovery.entry_points", return_value=[mock_ep]):
            plugins = discovery.discover_package_plugins()
            assert len(plugins) == 1
            assert plugins[0].id == "package-plugin"
            assert plugins[0].source == "package"

    def test_discover_package_plugins_no_metadata(self) -> None:
        """Test package plugin without metadata attribute."""
        from unittest.mock import MagicMock

        discovery = PluginDiscovery()

        # Create mock plugin class without metadata
        mock_class = MagicMock(spec=[])  # No metadata attribute

        mock_ep = MagicMock()
        mock_ep.name = "no-meta"
        mock_ep.value = "no_meta:Plugin"
        mock_ep.load.return_value = mock_class

        with patch("code_forge.plugins.discovery.entry_points", return_value=[mock_ep]):
            plugins = discovery.discover_package_plugins()
            # Should skip plugins without metadata
            assert plugins == []
