"""Tests for plugin registry."""

from unittest.mock import MagicMock

import pytest

from opencode.plugins.registry import PluginRegistry


class TestPluginRegistry:
    """Tests for PluginRegistry."""

    @pytest.fixture
    def registry(self) -> PluginRegistry:
        """Create a fresh registry for each test."""
        return PluginRegistry()

    def test_register_tool(self, registry: PluginRegistry) -> None:
        """Test registering a tool."""
        tool = MagicMock()
        tool.name = "my-tool"

        name = registry.register_tool("my-plugin", tool)
        assert name == "my-plugin__my-tool"

    def test_get_tools(self, registry: PluginRegistry) -> None:
        """Test getting all tools."""
        tool1 = MagicMock()
        tool1.name = "tool1"
        tool2 = MagicMock()
        tool2.name = "tool2"

        registry.register_tool("plugin1", tool1)
        registry.register_tool("plugin2", tool2)

        tools = registry.get_tools()
        assert len(tools) == 2
        assert "plugin1__tool1" in tools
        assert "plugin2__tool2" in tools

    def test_get_tool(self, registry: PluginRegistry) -> None:
        """Test getting a specific tool."""
        tool = MagicMock()
        tool.name = "search"

        registry.register_tool("my-plugin", tool)

        result = registry.get_tool("my-plugin__search")
        assert result is tool

        result = registry.get_tool("nonexistent")
        assert result is None

    def test_register_command(self, registry: PluginRegistry) -> None:
        """Test registering a command."""
        command = MagicMock()
        command.name = "my-command"

        name = registry.register_command("my-plugin", command)
        assert name == "my-plugin:my-command"

    def test_get_commands(self, registry: PluginRegistry) -> None:
        """Test getting all commands."""
        cmd1 = MagicMock()
        cmd1.name = "cmd1"
        cmd2 = MagicMock()
        cmd2.name = "cmd2"

        registry.register_command("plugin1", cmd1)
        registry.register_command("plugin2", cmd2)

        commands = registry.get_commands()
        assert len(commands) == 2
        assert "plugin1:cmd1" in commands
        assert "plugin2:cmd2" in commands

    def test_get_command(self, registry: PluginRegistry) -> None:
        """Test getting a specific command."""
        command = MagicMock()
        command.name = "run"

        registry.register_command("my-plugin", command)

        result = registry.get_command("my-plugin:run")
        assert result is command

        result = registry.get_command("nonexistent")
        assert result is None

    def test_register_hook(self, registry: PluginRegistry) -> None:
        """Test registering a hook."""
        handler = MagicMock()

        registry.register_hook("my-plugin", "before_execute", handler)

        hooks = registry.get_hooks("before_execute")
        assert handler in hooks

    def test_hooks_sorted_by_priority(self, registry: PluginRegistry) -> None:
        """Test hooks are sorted by priority."""
        handler_low = MagicMock()
        handler_high = MagicMock()
        handler_default = MagicMock()

        registry.register_hook("plugin", "event", handler_high, priority=50)
        registry.register_hook("plugin", "event", handler_default)  # default 100
        registry.register_hook("plugin", "event", handler_low, priority=200)

        hooks = registry.get_hooks("event")
        assert hooks[0] is handler_high
        assert hooks[1] is handler_default
        assert hooks[2] is handler_low

    def test_get_hooks_empty(self, registry: PluginRegistry) -> None:
        """Test getting hooks for non-existent event."""
        hooks = registry.get_hooks("nonexistent_event")
        assert hooks == []

    def test_register_subagent(self, registry: PluginRegistry) -> None:
        """Test registering a subagent."""
        subagent_class = MagicMock()

        name = registry.register_subagent("my-plugin", "analyzer", subagent_class)
        assert name == "my-plugin:analyzer"

    def test_get_subagents(self, registry: PluginRegistry) -> None:
        """Test getting all subagents."""
        agent1 = MagicMock()
        agent2 = MagicMock()

        registry.register_subagent("plugin1", "agent1", agent1)
        registry.register_subagent("plugin2", "agent2", agent2)

        subagents = registry.get_subagents()
        assert len(subagents) == 2
        assert "plugin1:agent1" in subagents
        assert "plugin2:agent2" in subagents

    def test_register_skill(self, registry: PluginRegistry) -> None:
        """Test registering a skill."""
        skill = MagicMock()
        skill.name = "my-skill"

        name = registry.register_skill("my-plugin", skill)
        assert name == "my-plugin:my-skill"

    def test_get_skills(self, registry: PluginRegistry) -> None:
        """Test getting all skills."""
        skill1 = MagicMock()
        skill1.name = "skill1"
        skill2 = MagicMock()
        skill2.name = "skill2"

        registry.register_skill("plugin1", skill1)
        registry.register_skill("plugin2", skill2)

        skills = registry.get_skills()
        assert len(skills) == 2
        assert "plugin1:skill1" in skills
        assert "plugin2:skill2" in skills

    def test_unregister_plugin(self, registry: PluginRegistry) -> None:
        """Test unregistering all plugin contributions."""
        tool = MagicMock()
        tool.name = "tool"
        command = MagicMock()
        command.name = "cmd"
        handler = MagicMock()
        subagent = MagicMock()
        skill = MagicMock()
        skill.name = "skill"

        registry.register_tool("my-plugin", tool)
        registry.register_command("my-plugin", command)
        registry.register_hook("my-plugin", "event", handler)
        registry.register_subagent("my-plugin", "agent", subagent)
        registry.register_skill("my-plugin", skill)

        # Verify registered
        assert len(registry.get_tools()) == 1
        assert len(registry.get_commands()) == 1
        assert len(registry.get_hooks("event")) == 1
        assert len(registry.get_subagents()) == 1
        assert len(registry.get_skills()) == 1

        # Unregister
        registry.unregister_plugin("my-plugin")

        # Verify all removed
        assert len(registry.get_tools()) == 0
        assert len(registry.get_commands()) == 0
        assert len(registry.get_hooks("event")) == 0
        assert len(registry.get_subagents()) == 0
        assert len(registry.get_skills()) == 0

    def test_unregister_plugin_preserves_others(self, registry: PluginRegistry) -> None:
        """Test unregistering preserves other plugins."""
        tool1 = MagicMock()
        tool1.name = "tool1"
        tool2 = MagicMock()
        tool2.name = "tool2"

        registry.register_tool("plugin1", tool1)
        registry.register_tool("plugin2", tool2)

        registry.unregister_plugin("plugin1")

        tools = registry.get_tools()
        assert len(tools) == 1
        assert "plugin2__tool2" in tools

    def test_list_plugins_contributions(self, registry: PluginRegistry) -> None:
        """Test listing plugin contributions."""
        tool1 = MagicMock()
        tool1.name = "tool1"
        tool2 = MagicMock()
        tool2.name = "tool2"
        command = MagicMock()
        command.name = "cmd"
        handler = MagicMock()

        registry.register_tool("my-plugin", tool1)
        registry.register_tool("my-plugin", tool2)
        registry.register_command("my-plugin", command)
        registry.register_hook("my-plugin", "event1", handler)
        registry.register_hook("my-plugin", "event2", handler)

        contributions = registry.list_plugins_contributions("my-plugin")

        assert len(contributions["tools"]) == 2
        assert "my-plugin__tool1" in contributions["tools"]
        assert "my-plugin__tool2" in contributions["tools"]
        assert len(contributions["commands"]) == 1
        assert contributions["hooks"]["event1"] == 1
        assert contributions["hooks"]["event2"] == 1

    def test_list_contributions_empty(self, registry: PluginRegistry) -> None:
        """Test listing contributions for non-existent plugin."""
        contributions = registry.list_plugins_contributions("nonexistent")
        assert contributions["tools"] == []
        assert contributions["commands"] == []
        assert contributions["subagents"] == []
        assert contributions["skills"] == []

    def test_multiple_hooks_same_event(self, registry: PluginRegistry) -> None:
        """Test multiple plugins can register hooks for same event."""
        handler1 = MagicMock()
        handler2 = MagicMock()

        registry.register_hook("plugin1", "event", handler1)
        registry.register_hook("plugin2", "event", handler2)

        hooks = registry.get_hooks("event")
        assert len(hooks) == 2
        assert handler1 in hooks
        assert handler2 in hooks
