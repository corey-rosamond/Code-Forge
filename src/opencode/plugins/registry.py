"""Registry of plugin contributions."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from opencode.commands.base import Command
    from opencode.tools.base import BaseTool


class PluginRegistry:
    """Registry of plugin contributions.

    Tracks all tools, commands, hooks, subagents, and skills
    contributed by plugins. Provides namespaced access to
    plugin contributions.

    Thread-safe: All operations are atomic dictionary operations.
    """

    def __init__(self) -> None:
        """Initialize plugin registry."""
        # Maps tool name to (plugin_id, tool)
        self._tools: dict[str, tuple[str, Any]] = {}

        # Maps command name to (plugin_id, command)
        self._commands: dict[str, tuple[str, Any]] = {}

        # Maps event to list of (plugin_id, priority, handler)
        self._hooks: dict[str, list[tuple[str, int, Callable[..., Any]]]] = (
            defaultdict(list)
        )

        # Maps subagent type to (plugin_id, subagent_class)
        self._subagents: dict[str, tuple[str, type]] = {}

        # Maps skill name to (plugin_id, skill)
        self._skills: dict[str, tuple[str, Any]] = {}

    def register_tool(
        self,
        plugin_id: str,
        tool: BaseTool,
    ) -> str:
        """Register a plugin tool.

        Tools are namespaced with the plugin ID prefix.

        Args:
            plugin_id: Plugin identifier.
            tool: Tool instance.

        Returns:
            Prefixed tool name (plugin_id__tool_name).
        """
        # Prefix tool name with plugin namespace
        prefixed_name = f"{plugin_id}__{tool.name}"
        self._tools[prefixed_name] = (plugin_id, tool)
        return prefixed_name

    def register_command(
        self,
        plugin_id: str,
        command: Command,
    ) -> str:
        """Register a plugin command.

        Commands are namespaced with the plugin ID prefix.

        Args:
            plugin_id: Plugin identifier.
            command: Command instance.

        Returns:
            Prefixed command name (plugin_id:command_name).
        """
        prefixed_name = f"{plugin_id}:{command.name}"
        self._commands[prefixed_name] = (plugin_id, command)
        return prefixed_name

    def register_hook(
        self,
        plugin_id: str,
        event: str,
        handler: Callable[..., Any],
        priority: int = 100,
    ) -> None:
        """Register a plugin hook handler.

        Handlers are sorted by priority (lower = earlier execution).

        Args:
            plugin_id: Plugin identifier.
            event: Event name.
            handler: Handler function.
            priority: Handler priority (lower = earlier).
        """
        self._hooks[event].append((plugin_id, priority, handler))
        # Sort by priority
        self._hooks[event].sort(key=lambda x: x[1])

    def register_subagent(
        self,
        plugin_id: str,
        subagent_type: str,
        subagent_class: type,
    ) -> str:
        """Register a plugin subagent type.

        Args:
            plugin_id: Plugin identifier.
            subagent_type: Subagent type name.
            subagent_class: Subagent class.

        Returns:
            Prefixed subagent type (plugin_id:subagent_type).
        """
        prefixed_type = f"{plugin_id}:{subagent_type}"
        self._subagents[prefixed_type] = (plugin_id, subagent_class)
        return prefixed_type

    def register_skill(
        self,
        plugin_id: str,
        skill: Any,
    ) -> str:
        """Register a plugin skill.

        Args:
            plugin_id: Plugin identifier.
            skill: Skill instance.

        Returns:
            Prefixed skill name (plugin_id:skill_name).
        """
        prefixed_name = f"{plugin_id}:{skill.name}"
        self._skills[prefixed_name] = (plugin_id, skill)
        return prefixed_name

    def unregister_plugin(self, plugin_id: str) -> None:
        """Unregister all contributions from a plugin.

        Removes all tools, commands, hooks, subagents, and skills
        registered by the specified plugin.

        Args:
            plugin_id: Plugin identifier.
        """
        # Remove tools
        self._tools = {k: v for k, v in self._tools.items() if v[0] != plugin_id}

        # Remove commands
        self._commands = {k: v for k, v in self._commands.items() if v[0] != plugin_id}

        # Remove hooks
        for event in self._hooks:
            self._hooks[event] = [h for h in self._hooks[event] if h[0] != plugin_id]

        # Remove subagents
        self._subagents = {
            k: v for k, v in self._subagents.items() if v[0] != plugin_id
        }

        # Remove skills
        self._skills = {k: v for k, v in self._skills.items() if v[0] != plugin_id}

    def get_tools(self) -> dict[str, Any]:
        """Get all registered tools.

        Returns:
            Dictionary mapping prefixed names to tool instances.
        """
        return {name: tool for name, (_, tool) in self._tools.items()}

    def get_tool(self, name: str) -> Any | None:
        """Get a specific tool.

        Args:
            name: Prefixed tool name.

        Returns:
            Tool instance or None if not found.
        """
        entry = self._tools.get(name)
        return entry[1] if entry else None

    def get_commands(self) -> dict[str, Any]:
        """Get all registered commands.

        Returns:
            Dictionary mapping prefixed names to command instances.
        """
        return {name: cmd for name, (_, cmd) in self._commands.items()}

    def get_command(self, name: str) -> Any | None:
        """Get a specific command.

        Args:
            name: Prefixed command name.

        Returns:
            Command instance or None if not found.
        """
        entry = self._commands.get(name)
        return entry[1] if entry else None

    def get_hooks(self, event: str) -> list[Callable[..., Any]]:
        """Get all handlers for an event.

        Handlers are returned in priority order (lowest first).

        Args:
            event: Event name.

        Returns:
            List of handler functions.
        """
        return [handler for _, _, handler in self._hooks.get(event, [])]

    def get_subagents(self) -> dict[str, type]:
        """Get all registered subagent types.

        Returns:
            Dictionary mapping prefixed types to subagent classes.
        """
        return {name: cls for name, (_, cls) in self._subagents.items()}

    def get_skills(self) -> dict[str, Any]:
        """Get all registered skills.

        Returns:
            Dictionary mapping prefixed names to skill instances.
        """
        return {name: skill for name, (_, skill) in self._skills.items()}

    def list_plugins_contributions(self, plugin_id: str) -> dict[str, Any]:
        """List all contributions from a plugin.

        Args:
            plugin_id: Plugin identifier.

        Returns:
            Dictionary with lists of tool names, command names,
            hook counts, subagent types, and skill names.
        """
        return {
            "tools": [name for name, (pid, _) in self._tools.items() if pid == plugin_id],
            "commands": [
                name for name, (pid, _) in self._commands.items() if pid == plugin_id
            ],
            "hooks": {
                event: len([h for h in handlers if h[0] == plugin_id])
                for event, handlers in self._hooks.items()
            },
            "subagents": [
                name for name, (pid, _) in self._subagents.items() if pid == plugin_id
            ],
            "skills": [
                name for name, (pid, _) in self._skills.items() if pid == plugin_id
            ],
        }
