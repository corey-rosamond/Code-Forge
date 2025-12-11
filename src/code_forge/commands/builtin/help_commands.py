"""Help and discovery commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..base import Command, CommandArgument, CommandCategory, CommandResult
from ..registry import CommandRegistry

if TYPE_CHECKING:
    from ..executor import CommandContext
    from ..parser import ParsedCommand


class HelpCommand(Command):
    """Show help for commands."""

    name = "help"
    aliases = ["?", "h"]
    description = "Show help for commands"
    usage = "/help [command]"
    category = CommandCategory.GENERAL
    arguments = [
        CommandArgument(
            name="command",
            description="Command to get help for",
            required=False,
        ),
    ]

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Show help."""
        registry = CommandRegistry.get_instance()
        command_name = parsed.get_arg(0)

        if command_name:
            # Help for specific command
            command = registry.resolve(command_name)
            if command is None:
                return CommandResult.fail(f"Unknown command: {command_name}")

            return CommandResult.ok(command.get_help())

        # General help
        lines = [
            "Code-Forge Commands",
            "=" * 40,
            "",
        ]

        categories = registry.get_categories()

        # Order categories for display
        category_order = [
            CommandCategory.GENERAL,
            CommandCategory.SESSION,
            CommandCategory.CONTEXT,
            CommandCategory.CONTROL,
            CommandCategory.CONFIG,
            CommandCategory.DEBUG,
        ]

        for category in category_order:
            if category not in categories:
                continue
            commands = categories[category]
            lines.append(f"{category.value.title()}:")
            for cmd in commands:
                lines.append(f"  /{cmd.name:<15} {cmd.description}")
            lines.append("")

        lines.append('Type "/help <command>" for detailed help.')

        return CommandResult.ok("\n".join(lines))


class CommandsCommand(Command):
    """List all available commands."""

    name = "commands"
    aliases = ["cmds"]
    description = "List all available commands"
    usage = "/commands [--category <cat>]"
    category = CommandCategory.GENERAL

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """List commands."""
        registry = CommandRegistry.get_instance()

        category_filter = parsed.get_kwarg("category")

        if category_filter:
            try:
                cat = CommandCategory(category_filter.lower())
                commands = registry.list_commands(category=cat)
            except ValueError:
                valid_cats = ", ".join(c.value for c in CommandCategory)
                return CommandResult.fail(
                    f"Unknown category: {category_filter}. Valid: {valid_cats}"
                )
        else:
            commands = registry.list_commands()

        if not commands:
            return CommandResult.ok("No commands available.")

        lines = [f"Available Commands ({len(commands)}):", ""]

        for cmd in commands:
            aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
            lines.append(f"  /{cmd.name}{aliases}")
            lines.append(f"    {cmd.description}")

        return CommandResult.ok("\n".join(lines))


def get_commands() -> list[Command]:
    """Get all help commands."""
    return [
        HelpCommand(),
        CommandsCommand(),
    ]
