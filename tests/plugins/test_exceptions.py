"""Tests for plugin exceptions."""


from opencode.plugins.exceptions import (
    PluginConfigError,
    PluginDependencyError,
    PluginError,
    PluginLifecycleError,
    PluginLoadError,
    PluginManifestError,
    PluginNotFoundError,
)


class TestPluginError:
    """Tests for PluginError base exception."""

    def test_init_with_message(self) -> None:
        """Test error with message only."""
        error = PluginError("test message")
        assert str(error) == "test message"
        assert error.plugin_id is None

    def test_init_with_plugin_id(self) -> None:
        """Test error with plugin ID."""
        error = PluginError("test message", plugin_id="my-plugin")
        assert str(error) == "test message"
        assert error.plugin_id == "my-plugin"

    def test_inheritance(self) -> None:
        """Test all exceptions inherit from PluginError."""
        exceptions = [
            PluginNotFoundError,
            PluginLoadError,
            PluginManifestError,
            PluginDependencyError,
            PluginConfigError,
            PluginLifecycleError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, PluginError)
            assert issubclass(exc_class, Exception)


class TestSpecificExceptions:
    """Tests for specific plugin exceptions."""

    def test_plugin_not_found_error(self) -> None:
        """Test PluginNotFoundError."""
        error = PluginNotFoundError("Plugin not found", plugin_id="missing")
        assert error.plugin_id == "missing"

    def test_plugin_load_error(self) -> None:
        """Test PluginLoadError."""
        error = PluginLoadError("Failed to load", plugin_id="bad-plugin")
        assert error.plugin_id == "bad-plugin"

    def test_plugin_manifest_error(self) -> None:
        """Test PluginManifestError."""
        error = PluginManifestError("Invalid manifest")
        assert str(error) == "Invalid manifest"

    def test_plugin_dependency_error(self) -> None:
        """Test PluginDependencyError."""
        error = PluginDependencyError("Missing dependency", plugin_id="dep-plugin")
        assert error.plugin_id == "dep-plugin"

    def test_plugin_config_error(self) -> None:
        """Test PluginConfigError."""
        error = PluginConfigError("Invalid config")
        assert str(error) == "Invalid config"

    def test_plugin_lifecycle_error(self) -> None:
        """Test PluginLifecycleError."""
        error = PluginLifecycleError("Lifecycle failed", plugin_id="lifecycle-plugin")
        assert error.plugin_id == "lifecycle-plugin"
