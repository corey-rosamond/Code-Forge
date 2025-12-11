"""Plugin management commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from code_forge.commands.base import (
    Command,
    CommandCategory,
    CommandResult,
    SubcommandHandler,
)

if TYPE_CHECKING:
    from code_forge.commands.executor import CommandContext
    from code_forge.commands.parser import ParsedCommand


class PluginListCommand(Command):
    """List all plugins."""

    name: ClassVar[str] = "list"
    description: ClassVar[str] = "List all plugins"
    usage: ClassVar[str] = "/plugins list"
    category: ClassVar[CommandCategory] = CommandCategory.GENERAL

    async def execute(
        self,
        _parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """List plugins."""
        if context.plugin_manager is None:
            return CommandResult.fail("Plugin manager not available")

        plugins = context.plugin_manager.list_plugins()

        if not plugins:
            return CommandResult.ok("No plugins loaded.")

        lines = [f"Plugins ({len(plugins)}):", ""]

        for plugin in sorted(plugins, key=lambda p: p.id):
            if plugin.active:
                status = "active"
            elif not plugin.enabled:
                status = "disabled"
            else:
                status = "inactive"
            lines.append(f"  {plugin.id} v{plugin.manifest.version}")
            lines.append(f"    Status: {status} | Source: {plugin.source}")
            lines.append(f"    {plugin.manifest.description}")
            lines.append("")

        # Show load errors if any
        errors = context.plugin_manager.get_load_errors()
        if errors:
            lines.append("Failed to load:")
            for plugin_id, error in errors.items():
                lines.append(f"  {plugin_id}: {error}")
            lines.append("")

        return CommandResult.ok("\n".join(lines))


class PluginInfoCommand(Command):
    """Show plugin details."""

    name: ClassVar[str] = "info"
    description: ClassVar[str] = "Show plugin details"
    usage: ClassVar[str] = "/plugins info <name>"
    category: ClassVar[CommandCategory] = CommandCategory.GENERAL

    def _format_metadata(self, meta: Any) -> list[str]:
        """Format metadata section."""
        lines = [
            f"Plugin: {meta.name}",
            f"Version: {meta.version}",
            f"Description: {meta.description}",
            "",
        ]
        optional = [
            ("Author", meta.author),
            ("Email", meta.email),
            ("License", meta.license),
            ("Homepage", meta.homepage),
            ("Repository", meta.repository),
        ]
        for label, value in optional:
            if value:
                lines.append(f"{label}: {value}")
        if meta.keywords:
            lines.append(f"Keywords: {', '.join(meta.keywords)}")
        return lines

    def _format_capabilities(self, caps: Any) -> list[str]:
        """Format capabilities section."""
        cap_names = ["tools", "commands", "hooks", "subagents", "skills", "system_access"]
        cap_list = [name for name in cap_names if getattr(caps, name, False)]
        return ["", "Capabilities:", f"  {', '.join(cap_list) if cap_list else 'none'}"]

    def _format_contributions(self, contributions: dict[str, Any]) -> list[str]:
        """Format contributions section."""
        lines = ["", "Contributions:"]
        if contributions["tools"]:
            lines.append(f"  Tools: {', '.join(contributions['tools'])}")
        if contributions["commands"]:
            lines.append(f"  Commands: {', '.join(contributions['commands'])}")
        hook_count = sum(contributions["hooks"].values())
        if hook_count:
            lines.append(f"  Hooks: {hook_count} handlers")
        if contributions["subagents"]:
            lines.append(f"  Subagents: {', '.join(contributions['subagents'])}")
        if contributions["skills"]:
            lines.append(f"  Skills: {', '.join(contributions['skills'])}")
        return lines

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Show plugin info."""
        if context.plugin_manager is None:
            return CommandResult.fail("Plugin manager not available")

        plugin_id = parsed.get_arg(0)
        if not plugin_id:
            return CommandResult.fail("Plugin name required. Usage: /plugins info <name>")

        plugin = context.plugin_manager.get_plugin(plugin_id)
        if plugin is None:
            return CommandResult.fail(f"Plugin not found: {plugin_id}")

        meta = plugin.manifest.metadata
        contributions = context.plugin_manager.registry.list_plugins_contributions(plugin_id)

        lines = self._format_metadata(meta)
        lines.extend([
            "",
            f"Status: {'active' if plugin.active else 'inactive'}",
            f"Enabled: {plugin.enabled}",
            f"Source: {plugin.source}",
        ])
        lines.extend(self._format_capabilities(plugin.manifest.capabilities))
        lines.extend(self._format_contributions(contributions))

        return CommandResult.ok("\n".join(lines))


class PluginEnableCommand(Command):
    """Enable a plugin."""

    name: ClassVar[str] = "enable"
    description: ClassVar[str] = "Enable a plugin"
    usage: ClassVar[str] = "/plugins enable <name>"
    category: ClassVar[CommandCategory] = CommandCategory.GENERAL

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Enable plugin."""
        if context.plugin_manager is None:
            return CommandResult.fail("Plugin manager not available")

        plugin_id = parsed.get_arg(0)
        if not plugin_id:
            return CommandResult.fail("Plugin name required. Usage: /plugins enable <name>")

        try:
            context.plugin_manager.enable(plugin_id)
            return CommandResult.ok(f"Enabled plugin: {plugin_id}")
        except Exception as e:
            return CommandResult.fail(f"Failed to enable plugin: {e}")


class PluginDisableCommand(Command):
    """Disable a plugin."""

    name: ClassVar[str] = "disable"
    description: ClassVar[str] = "Disable a plugin"
    usage: ClassVar[str] = "/plugins disable <name>"
    category: ClassVar[CommandCategory] = CommandCategory.GENERAL

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Disable plugin."""
        if context.plugin_manager is None:
            return CommandResult.fail("Plugin manager not available")

        plugin_id = parsed.get_arg(0)
        if not plugin_id:
            return CommandResult.fail("Plugin name required. Usage: /plugins disable <name>")

        try:
            context.plugin_manager.disable(plugin_id)
            return CommandResult.ok(f"Disabled plugin: {plugin_id}")
        except Exception as e:
            return CommandResult.fail(f"Failed to disable plugin: {e}")


class PluginReloadCommand(Command):
    """Reload a plugin."""

    name: ClassVar[str] = "reload"
    description: ClassVar[str] = "Reload a plugin"
    usage: ClassVar[str] = "/plugins reload <name>"
    category: ClassVar[CommandCategory] = CommandCategory.GENERAL

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Reload plugin."""
        if context.plugin_manager is None:
            return CommandResult.fail("Plugin manager not available")

        plugin_id = parsed.get_arg(0)
        if not plugin_id:
            return CommandResult.fail("Plugin name required. Usage: /plugins reload <name>")

        try:
            context.plugin_manager.reload(plugin_id)
            return CommandResult.ok(f"Reloaded plugin: {plugin_id}")
        except Exception as e:
            return CommandResult.fail(f"Failed to reload plugin: {e}")


class PluginsCommand(SubcommandHandler):
    """Plugin management commands."""

    name: ClassVar[str] = "plugins"
    aliases: ClassVar[list[str]] = ["plugin"]
    description: ClassVar[str] = "Plugin management"
    usage: ClassVar[str] = "/plugins [list|info|enable|disable|reload]"
    category: ClassVar[CommandCategory] = CommandCategory.GENERAL

    subcommands: ClassVar[dict[str, Command]] = {
        "list": PluginListCommand(),
        "info": PluginInfoCommand(),
        "enable": PluginEnableCommand(),
        "disable": PluginDisableCommand(),
        "reload": PluginReloadCommand(),
    }

    async def execute_default(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Default: list plugins."""
        return await PluginListCommand().execute(parsed, context)


def get_commands() -> list[Command]:
    """Get all plugin commands.

    Returns:
        List of command instances.
    """
    return [PluginsCommand()]
