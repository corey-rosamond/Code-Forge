"""Tests for plugin loader."""

import sys
from pathlib import Path

import pytest

from opencode.plugins.base import Plugin, PluginCapabilities, PluginMetadata
from opencode.plugins.config import PluginConfig, PluginConfigManager
from opencode.plugins.discovery import DiscoveredPlugin
from opencode.plugins.exceptions import PluginLoadError
from opencode.plugins.loader import LoadedPlugin, PluginLoader
from opencode.plugins.manifest import PluginManifest


class SamplePlugin(Plugin):
    """Sample plugin for testing."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="sample-plugin",
            version="1.0.0",
            description="Sample plugin",
        )

    @property
    def capabilities(self) -> PluginCapabilities:
        return PluginCapabilities(tools=True)


class TestLoadedPlugin:
    """Tests for LoadedPlugin dataclass."""

    def test_loaded_plugin_creation(self, tmp_path: Path) -> None:
        """Test creating LoadedPlugin."""
        import logging

        from opencode.plugins.base import PluginContext

        manifest = PluginManifest(
            name="test",
            version="1.0.0",
            description="Test",
            entry_point="test:Plugin",
            metadata=PluginMetadata(
                name="test",
                version="1.0.0",
                description="Test",
            ),
            capabilities=PluginCapabilities(),
        )
        context = PluginContext(
            plugin_id="test",
            data_dir=tmp_path,
            config={},
            logger=logging.getLogger("test"),
        )
        plugin = SamplePlugin()

        loaded = LoadedPlugin(
            id="test",
            manifest=manifest,
            instance=plugin,
            context=context,
            source="user",
            enabled=True,
            active=False,
        )

        assert loaded.id == "test"
        assert loaded.manifest is manifest
        assert loaded.instance is plugin
        assert loaded.context is context
        assert loaded.source == "user"
        assert loaded.enabled is True
        assert loaded.active is False


class TestPluginLoader:
    """Tests for PluginLoader."""

    @pytest.fixture
    def config_manager(self, tmp_path: Path) -> PluginConfigManager:
        """Create config manager."""
        config = PluginConfig()
        return PluginConfigManager(config, data_dir=tmp_path / "plugin_data")

    @pytest.fixture
    def loader(self, config_manager: PluginConfigManager) -> PluginLoader:
        """Create plugin loader."""
        return PluginLoader(config_manager)

    def test_load_plugin(self, loader: PluginLoader, tmp_path: Path) -> None:
        """Test loading a plugin."""
        # Create plugin directory
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()

        # Create plugin module
        plugin_file = plugin_dir / "test_plugin.py"
        plugin_file.write_text("""
from opencode.plugins.base import Plugin, PluginMetadata, PluginCapabilities

class TestPlugin(Plugin):
    @property
    def metadata(self):
        return PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
        )

    @property
    def capabilities(self):
        return PluginCapabilities(tools=True)
""")

        manifest = PluginManifest(
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
            entry_point="test_plugin:TestPlugin",
            metadata=PluginMetadata(
                name="test-plugin",
                version="1.0.0",
                description="Test plugin",
            ),
            capabilities=PluginCapabilities(tools=True),
            path=plugin_dir,
        )
        discovered = DiscoveredPlugin(
            path=plugin_dir,
            manifest=manifest,
            source="user",
        )

        loaded = loader.load(discovered)

        assert loaded.id == "test-plugin"
        assert loaded.manifest.name == "test-plugin"
        assert loaded.instance.metadata.name == "test-plugin"
        assert loaded.enabled is True
        assert loaded.active is False

        # Cleanup sys.path
        if str(plugin_dir) in sys.path:
            sys.path.remove(str(plugin_dir))

    def test_load_disabled_plugin(
        self, tmp_path: Path, config_manager: PluginConfigManager
    ) -> None:
        """Test loading a disabled plugin."""
        config_manager.disable_plugin("disabled-plugin")
        loader = PluginLoader(config_manager)

        # Create plugin directory
        plugin_dir = tmp_path / "disabled-plugin"
        plugin_dir.mkdir()

        plugin_file = plugin_dir / "disabled_plugin.py"
        plugin_file.write_text("""
from opencode.plugins.base import Plugin, PluginMetadata

class DisabledPlugin(Plugin):
    @property
    def metadata(self):
        return PluginMetadata(
            name="disabled-plugin",
            version="1.0.0",
            description="Disabled plugin",
        )
""")

        manifest = PluginManifest(
            name="disabled-plugin",
            version="1.0.0",
            description="Disabled plugin",
            entry_point="disabled_plugin:DisabledPlugin",
            metadata=PluginMetadata(
                name="disabled-plugin",
                version="1.0.0",
                description="Disabled plugin",
            ),
            capabilities=PluginCapabilities(),
            path=plugin_dir,
        )
        discovered = DiscoveredPlugin(
            path=plugin_dir,
            manifest=manifest,
            source="user",
        )

        loaded = loader.load(discovered)
        assert loaded.enabled is False

        # Cleanup
        if str(plugin_dir) in sys.path:
            sys.path.remove(str(plugin_dir))

    def test_load_plugin_import_error(self, loader: PluginLoader) -> None:
        """Test loading plugin with import error."""
        manifest = PluginManifest(
            name="bad-plugin",
            version="1.0.0",
            description="Bad plugin",
            entry_point="nonexistent_module:Plugin",
            metadata=PluginMetadata(
                name="bad-plugin",
                version="1.0.0",
                description="Bad plugin",
            ),
            capabilities=PluginCapabilities(),
        )
        discovered = DiscoveredPlugin(
            path=None,
            manifest=manifest,
            source="package",
        )

        with pytest.raises(PluginLoadError, match="Failed to import"):
            loader.load(discovered)

    def test_load_plugin_class_not_found(
        self, loader: PluginLoader, tmp_path: Path
    ) -> None:
        """Test loading plugin with missing class."""
        plugin_dir = tmp_path / "missing-class"
        plugin_dir.mkdir()

        plugin_file = plugin_dir / "missing_class.py"
        plugin_file.write_text("""
# No plugin class here
class SomeOtherClass:
    pass
""")

        manifest = PluginManifest(
            name="missing-class",
            version="1.0.0",
            description="Missing class",
            entry_point="missing_class:MissingPlugin",
            metadata=PluginMetadata(
                name="missing-class",
                version="1.0.0",
                description="Missing class",
            ),
            capabilities=PluginCapabilities(),
            path=plugin_dir,
        )
        discovered = DiscoveredPlugin(
            path=plugin_dir,
            manifest=manifest,
            source="user",
        )

        with pytest.raises(PluginLoadError, match="not found"):
            loader.load(discovered)

        # Cleanup
        if str(plugin_dir) in sys.path:
            sys.path.remove(str(plugin_dir))

    def test_load_plugin_not_subclass(
        self, loader: PluginLoader, tmp_path: Path
    ) -> None:
        """Test loading class that's not a Plugin subclass."""
        plugin_dir = tmp_path / "not-plugin"
        plugin_dir.mkdir()

        plugin_file = plugin_dir / "not_plugin.py"
        plugin_file.write_text("""
class NotAPlugin:
    pass
""")

        manifest = PluginManifest(
            name="not-plugin",
            version="1.0.0",
            description="Not a plugin",
            entry_point="not_plugin:NotAPlugin",
            metadata=PluginMetadata(
                name="not-plugin",
                version="1.0.0",
                description="Not a plugin",
            ),
            capabilities=PluginCapabilities(),
            path=plugin_dir,
        )
        discovered = DiscoveredPlugin(
            path=plugin_dir,
            manifest=manifest,
            source="user",
        )

        with pytest.raises(PluginLoadError, match="not a Plugin subclass"):
            loader.load(discovered)

        # Cleanup
        if str(plugin_dir) in sys.path:
            sys.path.remove(str(plugin_dir))

    def test_load_plugin_invalid_entry_point(self, loader: PluginLoader) -> None:
        """Test loading plugin with invalid entry point format."""
        manifest = PluginManifest(
            name="invalid-entry",
            version="1.0.0",
            description="Invalid entry",
            entry_point="no_colon",  # Invalid - no colon
            metadata=PluginMetadata(
                name="invalid-entry",
                version="1.0.0",
                description="Invalid entry",
            ),
            capabilities=PluginCapabilities(),
        )
        discovered = DiscoveredPlugin(
            path=None,
            manifest=manifest,
            source="package",
        )

        with pytest.raises(PluginLoadError, match="entry point"):
            loader.load(discovered)

    def test_create_context(self, loader: PluginLoader) -> None:
        """Test creating plugin context."""
        manifest = PluginManifest(
            name="context-test",
            version="1.0.0",
            description="Context test",
            entry_point="test:Plugin",
            metadata=PluginMetadata(
                name="context-test",
                version="1.0.0",
                description="Context test",
            ),
            capabilities=PluginCapabilities(),
        )
        context = loader.create_context("context-test", manifest)
        assert context.plugin_id == "context-test"
        assert context.data_dir.exists()
        assert context.config == {}

    def test_unload_plugin(self, loader: PluginLoader, tmp_path: Path) -> None:
        """Test unloading a plugin."""
        import logging

        from opencode.plugins.base import PluginContext

        manifest = PluginManifest(
            name="unload-test",
            version="1.0.0",
            description="Unload test",
            entry_point="test:Plugin",
            metadata=PluginMetadata(
                name="unload-test",
                version="1.0.0",
                description="Unload test",
            ),
            capabilities=PluginCapabilities(),
        )
        context = PluginContext(
            plugin_id="unload-test",
            data_dir=tmp_path,
            config={},
            logger=logging.getLogger("test"),
        )
        plugin = SamplePlugin()
        plugin.set_context(context)

        loaded = LoadedPlugin(
            id="unload-test",
            manifest=manifest,
            instance=plugin,
            context=context,
            source="user",
            enabled=True,
            active=True,
        )

        # Should not raise
        loader.unload(loaded)
        assert loaded.active is False

    def test_unload_cleans_sys_path(
        self, loader: PluginLoader, tmp_path: Path
    ) -> None:
        """Test unload removes added sys.path entry."""
        import logging

        from opencode.plugins.base import PluginContext

        plugin_path = str(tmp_path / "test-plugin")
        manifest = PluginManifest(
            name="path-test",
            version="1.0.0",
            description="Path test",
            entry_point="test:Plugin",
            metadata=PluginMetadata(
                name="path-test",
                version="1.0.0",
                description="Path test",
            ),
            capabilities=PluginCapabilities(),
        )
        context = PluginContext(
            plugin_id="path-test",
            data_dir=tmp_path,
            config={},
            logger=logging.getLogger("test"),
        )
        plugin = SamplePlugin()
        plugin.set_context(context)

        loaded = LoadedPlugin(
            id="path-test",
            manifest=manifest,
            instance=plugin,
            context=context,
            source="user",
            enabled=True,
            active=False,
            added_sys_path=plugin_path,
        )

        # Add to sys.path
        sys.path.insert(0, plugin_path)

        loader.unload(loaded)
        assert plugin_path not in sys.path
