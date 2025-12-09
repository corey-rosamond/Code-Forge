"""Tests for plugin commands."""

from unittest.mock import MagicMock

import pytest

from opencode.plugins.commands import (
    PluginDisableCommand,
    PluginEnableCommand,
    PluginInfoCommand,
    PluginListCommand,
    PluginReloadCommand,
    PluginsCommand,
    get_commands,
)


class TestPluginListCommand:
    """Tests for PluginListCommand."""

    @pytest.fixture
    def command(self) -> PluginListCommand:
        """Create command instance."""
        return PluginListCommand()

    @pytest.fixture
    def context(self) -> MagicMock:
        """Create mock context."""
        context = MagicMock()
        context.plugin_manager = MagicMock()
        return context

    @pytest.fixture
    def parsed(self) -> MagicMock:
        """Create mock parsed command."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value=None)
        return parsed

    @pytest.mark.asyncio
    async def test_no_plugin_manager(
        self, command: PluginListCommand, parsed: MagicMock
    ) -> None:
        """Test when plugin manager not available."""
        context = MagicMock()
        context.plugin_manager = None

        result = await command.execute(parsed, context)
        assert not result.success
        assert "not available" in result.error

    @pytest.mark.asyncio
    async def test_no_plugins(
        self, command: PluginListCommand, context: MagicMock, parsed: MagicMock
    ) -> None:
        """Test when no plugins loaded."""
        context.plugin_manager.list_plugins.return_value = []
        context.plugin_manager.get_load_errors.return_value = {}

        result = await command.execute(parsed, context)
        assert result.success
        assert "No plugins" in result.output

    @pytest.mark.asyncio
    async def test_with_plugins(
        self, command: PluginListCommand, context: MagicMock, parsed: MagicMock
    ) -> None:
        """Test listing plugins."""
        plugin = MagicMock()
        plugin.id = "test-plugin"
        plugin.manifest.version = "1.0.0"
        plugin.manifest.description = "Test plugin"
        plugin.active = True
        plugin.enabled = True
        plugin.source = "user"

        context.plugin_manager.list_plugins.return_value = [plugin]
        context.plugin_manager.get_load_errors.return_value = {}

        result = await command.execute(parsed, context)
        assert result.success
        assert "test-plugin" in result.output
        assert "1.0.0" in result.output
        assert "active" in result.output

    @pytest.mark.asyncio
    async def test_with_disabled_plugin(
        self, command: PluginListCommand, context: MagicMock, parsed: MagicMock
    ) -> None:
        """Test listing disabled plugin."""
        plugin = MagicMock()
        plugin.id = "disabled-plugin"
        plugin.manifest.version = "1.0.0"
        plugin.manifest.description = "Disabled plugin"
        plugin.active = False
        plugin.enabled = False
        plugin.source = "user"

        context.plugin_manager.list_plugins.return_value = [plugin]
        context.plugin_manager.get_load_errors.return_value = {}

        result = await command.execute(parsed, context)
        assert result.success
        assert "disabled" in result.output

    @pytest.mark.asyncio
    async def test_with_inactive_plugin(
        self, command: PluginListCommand, context: MagicMock, parsed: MagicMock
    ) -> None:
        """Test listing inactive plugin (enabled but not active)."""
        plugin = MagicMock()
        plugin.id = "inactive-plugin"
        plugin.manifest.version = "1.0.0"
        plugin.manifest.description = "Inactive plugin"
        plugin.active = False
        plugin.enabled = True  # enabled but not active
        plugin.source = "user"

        context.plugin_manager.list_plugins.return_value = [plugin]
        context.plugin_manager.get_load_errors.return_value = {}

        result = await command.execute(parsed, context)
        assert result.success
        assert "inactive" in result.output

    @pytest.mark.asyncio
    async def test_with_load_errors(
        self, command: PluginListCommand, context: MagicMock, parsed: MagicMock
    ) -> None:
        """Test showing load errors."""
        # Need at least one plugin to see load errors section
        plugin = MagicMock()
        plugin.id = "good-plugin"
        plugin.manifest.version = "1.0.0"
        plugin.manifest.description = "Good plugin"
        plugin.active = True
        plugin.enabled = True
        plugin.source = "user"

        context.plugin_manager.list_plugins.return_value = [plugin]
        context.plugin_manager.get_load_errors.return_value = {
            "bad-plugin": "Import error"
        }

        result = await command.execute(parsed, context)
        assert result.success
        assert "Failed to load" in result.output
        assert "bad-plugin" in result.output


class TestPluginInfoCommand:
    """Tests for PluginInfoCommand."""

    @pytest.fixture
    def command(self) -> PluginInfoCommand:
        """Create command instance."""
        return PluginInfoCommand()

    @pytest.fixture
    def context(self) -> MagicMock:
        """Create mock context."""
        context = MagicMock()
        context.plugin_manager = MagicMock()
        return context

    @pytest.mark.asyncio
    async def test_no_plugin_manager(self, command: PluginInfoCommand) -> None:
        """Test when plugin manager not available."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value="test")
        context = MagicMock()
        context.plugin_manager = None

        result = await command.execute(parsed, context)
        assert not result.success
        assert "not available" in result.error

    @pytest.mark.asyncio
    async def test_no_plugin_name(
        self, command: PluginInfoCommand, context: MagicMock
    ) -> None:
        """Test when no plugin name provided."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value=None)

        result = await command.execute(parsed, context)
        assert not result.success
        assert "required" in result.error

    @pytest.mark.asyncio
    async def test_plugin_not_found(
        self, command: PluginInfoCommand, context: MagicMock
    ) -> None:
        """Test when plugin not found."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value="missing")
        context.plugin_manager.get_plugin.return_value = None

        result = await command.execute(parsed, context)
        assert not result.success
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_show_plugin_info(
        self, command: PluginInfoCommand, context: MagicMock
    ) -> None:
        """Test showing plugin info."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value="test-plugin")

        plugin = MagicMock()
        plugin.id = "test-plugin"
        plugin.active = True
        plugin.enabled = True
        plugin.source = "user"
        plugin.manifest.metadata.name = "test-plugin"
        plugin.manifest.metadata.version = "1.0.0"
        plugin.manifest.metadata.description = "Test plugin"
        plugin.manifest.metadata.author = "Test Author"
        plugin.manifest.metadata.email = None
        plugin.manifest.metadata.license = "MIT"
        plugin.manifest.metadata.homepage = None
        plugin.manifest.metadata.repository = None
        plugin.manifest.metadata.keywords = ["test"]
        plugin.manifest.capabilities.tools = True
        plugin.manifest.capabilities.commands = False
        plugin.manifest.capabilities.hooks = False
        plugin.manifest.capabilities.subagents = False
        plugin.manifest.capabilities.skills = False
        plugin.manifest.capabilities.system_access = False

        context.plugin_manager.get_plugin.return_value = plugin
        context.plugin_manager.registry.list_plugins_contributions.return_value = {
            "tools": ["test-plugin__tool1"],
            "commands": [],
            "hooks": {},
            "subagents": [],
            "skills": [],
        }

        result = await command.execute(parsed, context)
        assert result.success
        assert "test-plugin" in result.output
        assert "1.0.0" in result.output
        assert "MIT" in result.output
        assert "tools" in result.output

    @pytest.mark.asyncio
    async def test_show_plugin_info_all_metadata(
        self, command: PluginInfoCommand, context: MagicMock
    ) -> None:
        """Test showing plugin info with all optional metadata."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value="full-plugin")

        plugin = MagicMock()
        plugin.id = "full-plugin"
        plugin.active = False
        plugin.enabled = True
        plugin.source = "project"
        plugin.manifest.metadata.name = "full-plugin"
        plugin.manifest.metadata.version = "2.0.0"
        plugin.manifest.metadata.description = "Full plugin"
        plugin.manifest.metadata.author = "Full Author"
        plugin.manifest.metadata.email = "author@example.com"
        plugin.manifest.metadata.license = "Apache-2.0"
        plugin.manifest.metadata.homepage = "https://example.com"
        plugin.manifest.metadata.repository = "https://github.com/example/plugin"
        plugin.manifest.metadata.keywords = []  # Empty keywords
        plugin.manifest.capabilities.tools = False
        plugin.manifest.capabilities.commands = True
        plugin.manifest.capabilities.hooks = True
        plugin.manifest.capabilities.subagents = True
        plugin.manifest.capabilities.skills = True
        plugin.manifest.capabilities.system_access = True

        context.plugin_manager.get_plugin.return_value = plugin
        context.plugin_manager.registry.list_plugins_contributions.return_value = {
            "tools": [],
            "commands": ["full-plugin:cmd1", "full-plugin:cmd2"],
            "hooks": {"before_execute": 2, "after_execute": 1},
            "subagents": ["full-plugin:agent1"],
            "skills": ["full-plugin:skill1"],
        }

        result = await command.execute(parsed, context)
        assert result.success
        assert "full-plugin" in result.output
        assert "author@example.com" in result.output
        assert "https://example.com" in result.output
        assert "https://github.com/example/plugin" in result.output
        assert "Commands:" in result.output
        assert "Hooks: 3 handlers" in result.output
        assert "Subagents:" in result.output
        assert "Skills:" in result.output

    @pytest.mark.asyncio
    async def test_show_plugin_no_capabilities(
        self, command: PluginInfoCommand, context: MagicMock
    ) -> None:
        """Test showing plugin with no capabilities."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value="empty-plugin")

        plugin = MagicMock()
        plugin.id = "empty-plugin"
        plugin.active = False
        plugin.enabled = False
        plugin.source = "user"
        plugin.manifest.metadata.name = "empty-plugin"
        plugin.manifest.metadata.version = "1.0.0"
        plugin.manifest.metadata.description = "Empty plugin"
        plugin.manifest.metadata.author = None
        plugin.manifest.metadata.email = None
        plugin.manifest.metadata.license = None
        plugin.manifest.metadata.homepage = None
        plugin.manifest.metadata.repository = None
        plugin.manifest.metadata.keywords = []
        plugin.manifest.capabilities.tools = False
        plugin.manifest.capabilities.commands = False
        plugin.manifest.capabilities.hooks = False
        plugin.manifest.capabilities.subagents = False
        plugin.manifest.capabilities.skills = False
        plugin.manifest.capabilities.system_access = False

        context.plugin_manager.get_plugin.return_value = plugin
        context.plugin_manager.registry.list_plugins_contributions.return_value = {
            "tools": [],
            "commands": [],
            "hooks": {},
            "subagents": [],
            "skills": [],
        }

        result = await command.execute(parsed, context)
        assert result.success
        assert "Capabilities:" in result.output
        assert "none" in result.output


class TestPluginEnableCommand:
    """Tests for PluginEnableCommand."""

    @pytest.fixture
    def command(self) -> PluginEnableCommand:
        """Create command instance."""
        return PluginEnableCommand()

    @pytest.mark.asyncio
    async def test_no_plugin_manager(self, command: PluginEnableCommand) -> None:
        """Test when plugin manager not available."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value="test")
        context = MagicMock()
        context.plugin_manager = None

        result = await command.execute(parsed, context)
        assert not result.success
        assert "not available" in result.error

    @pytest.mark.asyncio
    async def test_no_plugin_name(self, command: PluginEnableCommand) -> None:
        """Test when no plugin name provided."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value=None)
        context = MagicMock()
        context.plugin_manager = MagicMock()

        result = await command.execute(parsed, context)
        assert not result.success
        assert "required" in result.error

    @pytest.mark.asyncio
    async def test_enable_success(self, command: PluginEnableCommand) -> None:
        """Test successful enable."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value="test-plugin")
        context = MagicMock()
        context.plugin_manager = MagicMock()

        result = await command.execute(parsed, context)
        assert result.success
        assert "Enabled" in result.output
        context.plugin_manager.enable.assert_called_once_with("test-plugin")

    @pytest.mark.asyncio
    async def test_enable_failure(self, command: PluginEnableCommand) -> None:
        """Test enable failure."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value="bad-plugin")
        context = MagicMock()
        context.plugin_manager = MagicMock()
        context.plugin_manager.enable.side_effect = Exception("Plugin not found")

        result = await command.execute(parsed, context)
        assert not result.success
        assert "Failed" in result.error


class TestPluginDisableCommand:
    """Tests for PluginDisableCommand."""

    @pytest.fixture
    def command(self) -> PluginDisableCommand:
        """Create command instance."""
        return PluginDisableCommand()

    @pytest.mark.asyncio
    async def test_no_plugin_manager(self, command: PluginDisableCommand) -> None:
        """Test when plugin manager not available."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value="test")
        context = MagicMock()
        context.plugin_manager = None

        result = await command.execute(parsed, context)
        assert not result.success
        assert "not available" in result.error

    @pytest.mark.asyncio
    async def test_no_plugin_name(self, command: PluginDisableCommand) -> None:
        """Test when no plugin name provided."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value=None)
        context = MagicMock()
        context.plugin_manager = MagicMock()

        result = await command.execute(parsed, context)
        assert not result.success
        assert "required" in result.error

    @pytest.mark.asyncio
    async def test_disable_success(self, command: PluginDisableCommand) -> None:
        """Test successful disable."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value="test-plugin")
        context = MagicMock()
        context.plugin_manager = MagicMock()

        result = await command.execute(parsed, context)
        assert result.success
        assert "Disabled" in result.output
        context.plugin_manager.disable.assert_called_once_with("test-plugin")

    @pytest.mark.asyncio
    async def test_disable_failure(self, command: PluginDisableCommand) -> None:
        """Test disable failure."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value="bad-plugin")
        context = MagicMock()
        context.plugin_manager = MagicMock()
        context.plugin_manager.disable.side_effect = Exception("Plugin not found")

        result = await command.execute(parsed, context)
        assert not result.success
        assert "Failed" in result.error


class TestPluginReloadCommand:
    """Tests for PluginReloadCommand."""

    @pytest.fixture
    def command(self) -> PluginReloadCommand:
        """Create command instance."""
        return PluginReloadCommand()

    @pytest.mark.asyncio
    async def test_no_plugin_manager(self, command: PluginReloadCommand) -> None:
        """Test when plugin manager not available."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value="test")
        context = MagicMock()
        context.plugin_manager = None

        result = await command.execute(parsed, context)
        assert not result.success
        assert "not available" in result.error

    @pytest.mark.asyncio
    async def test_no_plugin_name(self, command: PluginReloadCommand) -> None:
        """Test when no plugin name provided."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value=None)
        context = MagicMock()
        context.plugin_manager = MagicMock()

        result = await command.execute(parsed, context)
        assert not result.success
        assert "required" in result.error

    @pytest.mark.asyncio
    async def test_reload_success(self, command: PluginReloadCommand) -> None:
        """Test successful reload."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value="test-plugin")
        context = MagicMock()
        context.plugin_manager = MagicMock()

        result = await command.execute(parsed, context)
        assert result.success
        assert "Reloaded" in result.output
        context.plugin_manager.reload.assert_called_once_with("test-plugin")

    @pytest.mark.asyncio
    async def test_reload_failure(self, command: PluginReloadCommand) -> None:
        """Test reload failure."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value="bad-plugin")
        context = MagicMock()
        context.plugin_manager = MagicMock()
        context.plugin_manager.reload.side_effect = Exception("Plugin not found")

        result = await command.execute(parsed, context)
        assert not result.success
        assert "Failed" in result.error


class TestPluginsCommand:
    """Tests for PluginsCommand (handler)."""

    @pytest.fixture
    def command(self) -> PluginsCommand:
        """Create command instance."""
        return PluginsCommand()

    def test_subcommands_registered(self, command: PluginsCommand) -> None:
        """Test subcommands are registered."""
        assert "list" in command.subcommands
        assert "info" in command.subcommands
        assert "enable" in command.subcommands
        assert "disable" in command.subcommands
        assert "reload" in command.subcommands

    def test_command_metadata(self, command: PluginsCommand) -> None:
        """Test command metadata."""
        assert command.name == "plugins"
        assert "plugin" in command.aliases

    @pytest.mark.asyncio
    async def test_default_lists_plugins(self, command: PluginsCommand) -> None:
        """Test default behavior lists plugins."""
        parsed = MagicMock()
        parsed.get_arg = MagicMock(return_value=None)
        context = MagicMock()
        context.plugin_manager = MagicMock()
        context.plugin_manager.list_plugins.return_value = []
        context.plugin_manager.get_load_errors.return_value = {}

        result = await command.execute_default(parsed, context)
        assert result.success


class TestGetCommands:
    """Tests for get_commands function."""

    def test_get_commands(self) -> None:
        """Test getting all commands."""
        commands = get_commands()
        assert len(commands) == 1
        assert isinstance(commands[0], PluginsCommand)
