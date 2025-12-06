"""
Slash commands for skill management.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from opencode.commands.base import (
    Command,
    CommandCategory,
    CommandResult,
    SubcommandHandler,
)

from .registry import SkillRegistry

if TYPE_CHECKING:
    from opencode.commands.executor import CommandContext
    from opencode.commands.parser import ParsedCommand


class SkillListCommand(Command):
    """List available skills."""

    name: ClassVar[str] = "list"
    description: ClassVar[str] = "List available skills"
    usage: ClassVar[str] = "/skill list [--tag <tag>]"

    def __init__(self) -> None:
        """Initialize command."""
        self._registry = SkillRegistry.get_instance()

    async def execute(
        self,
        parsed: ParsedCommand,
        _context: CommandContext,
    ) -> CommandResult:
        """Execute list command."""
        tag = parsed.get_kwarg("tag")
        skills = self._registry.list_skills(tag)

        if not skills:
            if tag:
                return CommandResult.ok(f"No skills found with tag: {tag}")
            return CommandResult.ok("No skills available.")

        lines = ["Available Skills:", ""]

        active = self._registry.active_skill
        for skill in skills:
            marker = " (active)" if active and active.name == skill.name else ""
            builtin = " [builtin]" if skill.is_builtin else ""
            tags = f" [{', '.join(skill.tags)}]" if skill.tags else ""

            lines.append(f"  {skill.name}{marker}{builtin}")
            lines.append(f"    {skill.description}{tags}")
            lines.append("")

        return CommandResult.ok("\n".join(lines))


class SkillInfoCommand(Command):
    """Show skill details."""

    name: ClassVar[str] = "info"
    description: ClassVar[str] = "Show skill details"
    usage: ClassVar[str] = "/skill info <name>"

    def __init__(self) -> None:
        """Initialize command."""
        self._registry = SkillRegistry.get_instance()

    async def execute(
        self,
        parsed: ParsedCommand,
        _context: CommandContext,
    ) -> CommandResult:
        """Execute info command."""
        name = parsed.get_arg(0)
        if not name:
            return CommandResult.fail("Usage: /skill info <name>")

        skill = self._registry.get(name)
        if not skill:
            return CommandResult.fail(f"Skill not found: {name}")

        return CommandResult.ok(skill.get_help())


class SkillSearchCommand(Command):
    """Search for skills."""

    name: ClassVar[str] = "search"
    description: ClassVar[str] = "Search for skills"
    usage: ClassVar[str] = "/skill search <query>"

    def __init__(self) -> None:
        """Initialize command."""
        self._registry = SkillRegistry.get_instance()

    async def execute(
        self,
        parsed: ParsedCommand,
        _context: CommandContext,
    ) -> CommandResult:
        """Execute search command."""
        query = " ".join(parsed.args) if parsed.args else ""
        if not query:
            return CommandResult.fail("Usage: /skill search <query>")

        skills = self._registry.search(query)

        if not skills:
            return CommandResult.ok(f"No skills matching: {query}")

        lines = [f"Skills matching '{query}':", ""]
        for skill in skills:
            lines.append(f"  {skill.name}")
            lines.append(f"    {skill.description}")
            lines.append("")

        return CommandResult.ok("\n".join(lines))


class SkillReloadCommand(Command):
    """Reload skills."""

    name: ClassVar[str] = "reload"
    description: ClassVar[str] = "Reload all skills from disk"
    usage: ClassVar[str] = "/skill reload"

    def __init__(self) -> None:
        """Initialize command."""
        self._registry = SkillRegistry.get_instance()

    async def execute(
        self,
        _parsed: ParsedCommand,
        _context: CommandContext,
    ) -> CommandResult:
        """Execute reload command."""
        count = self._registry.reload_all()
        return CommandResult.ok(f"Reloaded {count} skills.")


class SkillCommand(SubcommandHandler):
    """Skill management command."""

    name: ClassVar[str] = "skill"
    aliases: ClassVar[list[str]] = ["sk"]
    description: ClassVar[str] = "Manage skills"
    usage: ClassVar[str] = "/skill [subcommand] [args]"
    category: ClassVar[CommandCategory] = CommandCategory.GENERAL

    subcommands: ClassVar[dict[str, Command]] = {}

    def __init__(self) -> None:
        """Initialize command with subcommands."""
        self._registry = SkillRegistry.get_instance()

        # Initialize subcommands
        SkillCommand.subcommands = {
            "list": SkillListCommand(),
            "info": SkillInfoCommand(),
            "search": SkillSearchCommand(),
            "reload": SkillReloadCommand(),
        }

    async def execute_default(
        self,
        parsed: ParsedCommand,
        _context: CommandContext,
    ) -> CommandResult:
        """Show active skill or activate by name."""
        if parsed.args:
            # Activate skill by name
            name = parsed.args[0]
            return await self._activate(name)

        # Show active skill
        active = self._registry.active_skill
        if active:
            return CommandResult.ok(
                f"Active skill: {active.name}\n\n"
                f"{active.description}\n\n"
                "Use /skill off to deactivate."
            )
        else:
            return CommandResult.ok(
                "No skill active.\n\n"
                "Use /skill <name> to activate a skill.\n"
                "Use /skill list to see available skills."
            )

    async def _activate(self, name: str) -> CommandResult:
        """Activate a skill."""
        if name == "off":
            skill = self._registry.deactivate()
            if skill:
                return CommandResult.ok(f"Deactivated skill: {skill.name}")
            return CommandResult.ok("No skill was active.")

        skill, errors = self._registry.activate(name)
        if errors:
            return CommandResult.fail("\n".join(errors))

        if skill is None:
            return CommandResult.fail(f"Failed to activate skill: {name}")

        return CommandResult.ok(
            f"Activated skill: {skill.name}\n\n" f"{skill.description}"
        )

    def get_help(self) -> str:
        """Get help including subcommands."""
        lines = [
            f"/{self.name} - {self.description}",
            "",
            "Usage:",
            "  /skill              Show active skill",
            "  /skill <name>       Activate a skill",
            "  /skill off          Deactivate current skill",
            "",
            "Subcommands:",
        ]

        for cmd_name, cmd in sorted(self.subcommands.items()):
            lines.append(f"  /skill {cmd_name} - {cmd.description}")

        lines.append("")
        lines.append("Type /help skill <subcommand> for more details.")

        return "\n".join(lines)


def get_skill_command() -> SkillCommand:
    """Get the skill command instance.

    Returns:
        Configured SkillCommand instance.
    """
    return SkillCommand()


__all__ = [
    "SkillCommand",
    "SkillInfoCommand",
    "SkillListCommand",
    "SkillReloadCommand",
    "SkillSearchCommand",
    "get_skill_command",
]
