# Phase 6.1: Slash Commands - Implementation Plan

**Phase:** 6.1
**Name:** Slash Commands
**Dependencies:** Phase 1.3 (Basic REPL Shell), Phase 5.1 (Session Management)

---

## Overview

This plan details the implementation of the slash command system for OpenCode, providing built-in commands for session management, context control, and system configuration.

---

## Implementation Order

1. **parser.py** - Command parsing
2. **base.py** - Base command class
3. **registry.py** - Command registry
4. **executor.py** - Command execution
5. **builtin/** - Built-in command implementations

---

## File 1: src/opencode/commands/parser.py

```python
"""Command parsing utilities."""

import re
import shlex
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParsedCommand:
    """Parsed slash command structure.

    Represents a parsed command with its name, positional arguments,
    keyword arguments, and flags.
    """

    name: str
    args: list[str] = field(default_factory=list)
    kwargs: dict[str, str] = field(default_factory=dict)
    flags: set[str] = field(default_factory=set)
    raw: str = ""

    @property
    def has_args(self) -> bool:
        """Check if command has positional arguments."""
        return len(self.args) > 0

    def get_arg(self, index: int, default: str | None = None) -> str | None:
        """Get positional argument by index.

        Args:
            index: Argument index (0-based).
            default: Default value if not present.

        Returns:
            Argument value or default.
        """
        if 0 <= index < len(self.args):
            return self.args[index]
        return default

    def get_kwarg(self, name: str, default: str | None = None) -> str | None:
        """Get keyword argument by name.

        Args:
            name: Argument name.
            default: Default value if not present.

        Returns:
            Argument value or default.
        """
        return self.kwargs.get(name, default)

    def has_flag(self, name: str) -> bool:
        """Check if flag is set.

        Args:
            name: Flag name.

        Returns:
            True if flag is present.
        """
        return name in self.flags

    @property
    def subcommand(self) -> str | None:
        """Get first argument as subcommand."""
        return self.get_arg(0)

    @property
    def rest_args(self) -> list[str]:
        """Get arguments after the first (subcommand)."""
        return self.args[1:]


class CommandParser:
    """Parses slash command input.

    Handles command detection, name extraction, and argument parsing.
    Supports quoted strings, flags, and keyword arguments.
    """

    COMMAND_PREFIX = "/"
    KWARG_PATTERN = re.compile(r"^--([a-zA-Z][a-zA-Z0-9_-]*)$")
    FLAG_PATTERN = re.compile(r"^-([a-zA-Z])$")

    def is_command(self, text: str) -> bool:
        """Check if text is a slash command.

        Args:
            text: Input text to check.

        Returns:
            True if text starts with command prefix.
        """
        stripped = text.strip()
        if not stripped.startswith(self.COMMAND_PREFIX):
            return False

        # Must have content after prefix
        if len(stripped) <= len(self.COMMAND_PREFIX):
            return False

        # First char after prefix must be letter
        first_char = stripped[len(self.COMMAND_PREFIX)]
        return first_char.isalpha()

    def parse(self, text: str) -> ParsedCommand:
        """Parse command text into structured form.

        Args:
            text: Command text starting with /.

        Returns:
            ParsedCommand with parsed components.

        Raises:
            ValueError: If text is not a valid command.
        """
        stripped = text.strip()

        if not self.is_command(stripped):
            raise ValueError(f"Not a valid command: {text}")

        # Remove prefix
        content = stripped[len(self.COMMAND_PREFIX):]

        # Parse using shlex for proper quoting
        try:
            tokens = shlex.split(content)
        except ValueError:
            # Fallback to simple split if quotes are unbalanced
            tokens = content.split()

        if not tokens:
            raise ValueError("Empty command")

        # First token is command name
        name = tokens[0].lower()
        tokens = tokens[1:]

        # Parse remaining tokens
        args: list[str] = []
        kwargs: dict[str, str] = {}
        flags: set[str] = set()

        i = 0
        while i < len(tokens):
            token = tokens[i]

            # Check for --key=value or --key value
            if token.startswith("--"):
                if "=" in token:
                    key, value = token[2:].split("=", 1)
                    kwargs[key] = value
                else:
                    key = token[2:]
                    if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                        kwargs[key] = tokens[i + 1]
                        i += 1
                    else:
                        flags.add(key)

            # Check for -f flags
            elif token.startswith("-") and len(token) == 2:
                flags.add(token[1])

            # Positional argument
            else:
                args.append(token)

            i += 1

        return ParsedCommand(
            name=name,
            args=args,
            kwargs=kwargs,
            flags=flags,
            raw=text,
        )

    def suggest_command(self, text: str, available: list[str]) -> str | None:
        """Suggest a command if input is close to a known command.

        Args:
            text: Input text.
            available: List of available command names.

        Returns:
            Suggested command name or None.
        """
        if not self.is_command(text):
            return None

        try:
            parsed = self.parse(text)
            name = parsed.name
        except ValueError:
            return None

        # Exact match
        if name in available:
            return None

        # Find closest match
        best_match = None
        best_score = 0

        for cmd in available:
            score = self._similarity(name, cmd)
            if score > best_score and score > 0.6:
                best_score = score
                best_match = cmd

        return best_match

    def _similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity (simple Levenshtein-based).

        Args:
            s1: First string.
            s2: Second string.

        Returns:
            Similarity score 0-1.
        """
        if s1 == s2:
            return 1.0

        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0

        # Simple character overlap
        set1 = set(s1)
        set2 = set(s2)
        overlap = len(set1 & set2)
        total = len(set1 | set2)

        return overlap / total if total > 0 else 0.0
```

---

## File 2: src/opencode/commands/base.py

```python
"""Base command classes and types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .parser import ParsedCommand
    from .executor import CommandContext


class ArgumentType(str, Enum):
    """Argument type for validation."""

    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    CHOICE = "choice"
    PATH = "path"


@dataclass
class CommandArgument:
    """Command argument specification.

    Defines an expected argument with validation rules.
    """

    name: str
    description: str = ""
    required: bool = True
    default: Any = None
    type: ArgumentType = ArgumentType.STRING
    choices: list[str] = field(default_factory=list)

    def validate(self, value: str | None) -> tuple[bool, str | None]:
        """Validate an argument value.

        Args:
            value: Value to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if value is None:
            if self.required:
                return False, f"Missing required argument: {self.name}"
            return True, None

        if self.type == ArgumentType.INTEGER:
            try:
                int(value)
            except ValueError:
                return False, f"Argument {self.name} must be an integer"

        if self.type == ArgumentType.BOOLEAN:
            if value.lower() not in ("true", "false", "yes", "no", "1", "0"):
                return False, f"Argument {self.name} must be a boolean"

        if self.type == ArgumentType.CHOICE:
            if value not in self.choices:
                choices_str = ", ".join(self.choices)
                return False, f"Argument {self.name} must be one of: {choices_str}"

        return True, None


@dataclass
class CommandResult:
    """Result of command execution.

    Contains success status, output text, and optional data.
    """

    success: bool
    output: str = ""
    error: str | None = None
    data: Any = None

    @classmethod
    def ok(cls, output: str = "", data: Any = None) -> "CommandResult":
        """Create a success result.

        Args:
            output: Output text.
            data: Optional structured data.

        Returns:
            Success CommandResult.
        """
        return cls(success=True, output=output, data=data)

    @classmethod
    def fail(cls, error: str, output: str = "") -> "CommandResult":
        """Create a failure result.

        Args:
            error: Error message.
            output: Optional output text.

        Returns:
            Failure CommandResult.
        """
        return cls(success=False, output=output, error=error)


class CommandCategory(str, Enum):
    """Command category for organization."""

    GENERAL = "general"
    SESSION = "session"
    CONTEXT = "context"
    CONTROL = "control"
    CONFIG = "config"
    DEBUG = "debug"


class Command(ABC):
    """Base class for all commands.

    Subclasses implement specific command behavior.

    Attributes:
        name: Primary command name.
        aliases: Alternative names for the command.
        description: Short description.
        usage: Usage pattern.
        category: Command category.
        arguments: Expected arguments.
    """

    name: str = ""
    aliases: list[str] = []
    description: str = ""
    usage: str = ""
    category: CommandCategory = CommandCategory.GENERAL
    arguments: list[CommandArgument] = []

    @abstractmethod
    async def execute(
        self,
        parsed: "ParsedCommand",
        context: "CommandContext",
    ) -> CommandResult:
        """Execute the command.

        Args:
            parsed: Parsed command with arguments.
            context: Execution context.

        Returns:
            CommandResult with output or error.
        """
        ...

    def validate(self, parsed: "ParsedCommand") -> list[str]:
        """Validate command arguments.

        Args:
            parsed: Parsed command to validate.

        Returns:
            List of validation error messages.
        """
        errors = []

        for i, arg_spec in enumerate(self.arguments):
            if arg_spec.required:
                value = parsed.get_arg(i)
                if value is None:
                    errors.append(f"Missing required argument: <{arg_spec.name}>")

        return errors

    def get_help(self) -> str:
        """Get detailed help text for the command.

        Returns:
            Formatted help string.
        """
        lines = [
            f"/{self.name} - {self.description}",
            "",
        ]

        if self.usage:
            lines.append("Usage:")
            lines.append(f"  {self.usage}")
            lines.append("")

        if self.aliases:
            lines.append(f"Aliases: {', '.join(self.aliases)}")
            lines.append("")

        if self.arguments:
            lines.append("Arguments:")
            for arg in self.arguments:
                req = "" if arg.required else " (optional)"
                lines.append(f"  <{arg.name}>{req} - {arg.description}")
            lines.append("")

        return "\n".join(lines)


class SubcommandHandler(Command):
    """Base class for commands with subcommands.

    Provides structure for commands like /session that have
    multiple subcommands (/session list, /session new, etc.).
    """

    subcommands: dict[str, "Command"] = {}

    async def execute(
        self,
        parsed: "ParsedCommand",
        context: "CommandContext",
    ) -> CommandResult:
        """Execute the appropriate subcommand.

        Args:
            parsed: Parsed command.
            context: Execution context.

        Returns:
            CommandResult from subcommand or default.
        """
        subcommand = parsed.subcommand

        if subcommand is None:
            # Default behavior when no subcommand
            return await self.execute_default(parsed, context)

        if subcommand in self.subcommands:
            # Create new parsed with shifted args
            # Use lazy import to avoid circular dependency
            ParsedCommandCls = _get_parsed_command_class()
            sub_parsed = ParsedCommandCls(
                name=subcommand,
                args=parsed.rest_args,
                kwargs=parsed.kwargs,
                flags=parsed.flags,
                raw=parsed.raw,
            )
            return await self.subcommands[subcommand].execute(sub_parsed, context)

        return CommandResult.fail(
            f"Unknown subcommand: {subcommand}. "
            f"Available: {', '.join(self.subcommands.keys())}"
        )

    async def execute_default(
        self,
        parsed: "ParsedCommand",
        context: "CommandContext",
    ) -> CommandResult:
        """Execute default behavior when no subcommand given.

        Args:
            parsed: Parsed command.
            context: Execution context.

        Returns:
            CommandResult.
        """
        # Default: show help
        return CommandResult.ok(self.get_help())

    def get_help(self) -> str:
        """Get help including subcommands.

        Returns:
            Formatted help string.
        """
        lines = [
            f"/{self.name} - {self.description}",
            "",
            "Subcommands:",
        ]

        for name, cmd in self.subcommands.items():
            lines.append(f"  /{self.name} {name} - {cmd.description}")

        lines.append("")
        lines.append(f"Type /help {self.name} <subcommand> for more details.")

        return "\n".join(lines)


# Note: ParsedCommand is imported via TYPE_CHECKING block above.
# At runtime, type annotations are strings so no import is needed here.
# The SubcommandHandler.execute method creates ParsedCommand instances,
# so we need to import it there or use a factory. For now, defer import:
def _get_parsed_command_class():
    """Lazy import to avoid circular dependency."""
    from .parser import ParsedCommand
    return ParsedCommand
```

---

## File 3: src/opencode/commands/registry.py

```python
"""Command registry for managing available commands."""

import logging
from typing import Iterator

from .base import Command, CommandCategory

logger = logging.getLogger(__name__)


class CommandRegistry:
    """Registry of available commands.

    Manages registration, lookup, and discovery of commands.
    Supports aliases for convenient command access.
    """

    _instance: "CommandRegistry | None" = None

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._commands: dict[str, Command] = {}
        self._aliases: dict[str, str] = {}

    @classmethod
    def get_instance(cls) -> "CommandRegistry":
        """Get singleton registry instance.

        Returns:
            The CommandRegistry singleton.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing)."""
        cls._instance = None

    def register(self, command: Command) -> None:
        """Register a command.

        Args:
            command: Command to register.

        Raises:
            ValueError: If command name conflicts.
        """
        name = command.name.lower()

        if name in self._commands:
            raise ValueError(f"Command already registered: {name}")

        if name in self._aliases:
            raise ValueError(f"Command name conflicts with alias: {name}")

        self._commands[name] = command

        # Register aliases
        for alias in command.aliases:
            alias_lower = alias.lower()
            if alias_lower in self._commands or alias_lower in self._aliases:
                logger.warning(f"Alias conflicts, skipping: {alias}")
                continue
            self._aliases[alias_lower] = name

        logger.debug(f"Registered command: {name}")

    def unregister(self, name: str) -> bool:
        """Unregister a command.

        Args:
            name: Command name to unregister.

        Returns:
            True if command was unregistered.
        """
        name_lower = name.lower()

        if name_lower not in self._commands:
            return False

        command = self._commands[name_lower]

        # Remove aliases
        for alias in command.aliases:
            self._aliases.pop(alias.lower(), None)

        del self._commands[name_lower]
        logger.debug(f"Unregistered command: {name}")
        return True

    def get(self, name: str) -> Command | None:
        """Get command by exact name.

        Args:
            name: Command name.

        Returns:
            Command or None if not found.
        """
        return self._commands.get(name.lower())

    def resolve(self, name: str) -> Command | None:
        """Resolve command by name or alias.

        Args:
            name: Command name or alias.

        Returns:
            Command or None if not found.
        """
        name_lower = name.lower()

        # Try direct lookup
        if name_lower in self._commands:
            return self._commands[name_lower]

        # Try alias
        if name_lower in self._aliases:
            return self._commands[self._aliases[name_lower]]

        return None

    def list_commands(
        self,
        category: CommandCategory | None = None,
    ) -> list[Command]:
        """List all registered commands.

        Args:
            category: Optional category filter.

        Returns:
            List of commands.
        """
        commands = list(self._commands.values())

        if category is not None:
            commands = [c for c in commands if c.category == category]

        return sorted(commands, key=lambda c: c.name)

    def list_names(self) -> list[str]:
        """List all command names (including aliases).

        Returns:
            List of command names and aliases.
        """
        names = list(self._commands.keys())
        names.extend(self._aliases.keys())
        return sorted(set(names))

    def search(self, query: str) -> list[Command]:
        """Search commands by name or description.

        Args:
            query: Search query.

        Returns:
            List of matching commands.
        """
        query_lower = query.lower()
        results = []

        for command in self._commands.values():
            if (
                query_lower in command.name.lower() or
                query_lower in command.description.lower() or
                any(query_lower in alias.lower() for alias in command.aliases)
            ):
                results.append(command)

        return results

    def get_categories(self) -> dict[CommandCategory, list[Command]]:
        """Get commands grouped by category.

        Returns:
            Dictionary of category -> commands.
        """
        categories: dict[CommandCategory, list[Command]] = {}

        for command in self._commands.values():
            if command.category not in categories:
                categories[command.category] = []
            categories[command.category].append(command)

        # Sort commands within each category
        for cat in categories:
            categories[cat].sort(key=lambda c: c.name)

        return categories

    def __len__(self) -> int:
        """Number of registered commands."""
        return len(self._commands)

    def __contains__(self, name: str) -> bool:
        """Check if command is registered."""
        return self.resolve(name) is not None

    def __iter__(self) -> Iterator[Command]:
        """Iterate over registered commands."""
        return iter(self._commands.values())
```

---

## File 4: src/opencode/commands/executor.py

```python
"""Command execution engine."""

import logging
from dataclasses import dataclass
from typing import Any, Callable

from .base import Command, CommandResult
from .parser import CommandParser, ParsedCommand
from .registry import CommandRegistry

logger = logging.getLogger(__name__)


@dataclass
class CommandContext:
    """Context provided to command execution.

    Contains references to system components that commands
    may need to access or modify.
    """

    session_manager: Any = None  # SessionManager
    context_manager: Any = None  # ContextManager
    config: Any = None           # Configuration
    llm: Any = None              # OpenRouterLLM
    repl: Any = None             # REPL instance

    # Output function for writing to user
    output: Callable[[str], None] = print

    def print(self, text: str) -> None:
        """Output text to user.

        Args:
            text: Text to output.
        """
        self.output(text)


class CommandExecutor:
    """Executes parsed commands.

    Coordinates command lookup, validation, and execution.
    """

    def __init__(
        self,
        registry: CommandRegistry | None = None,
        parser: CommandParser | None = None,
    ) -> None:
        """Initialize executor.

        Args:
            registry: Command registry. Uses singleton if None.
            parser: Command parser. Creates default if None.
        """
        self.registry = registry or CommandRegistry.get_instance()
        self.parser = parser or CommandParser()

    async def execute(
        self,
        input_text: str,
        context: CommandContext,
    ) -> CommandResult:
        """Execute a command from input text.

        Args:
            input_text: Raw command input.
            context: Execution context.

        Returns:
            CommandResult with output or error.
        """
        # Parse command
        try:
            parsed = self.parser.parse(input_text)
        except ValueError as e:
            return CommandResult.fail(str(e))

        # Look up command
        command = self.registry.resolve(parsed.name)

        if command is None:
            # Try to suggest a similar command
            suggestion = self.parser.suggest_command(
                input_text,
                self.registry.list_names(),
            )

            error = f"Unknown command: /{parsed.name}"
            if suggestion:
                error += f". Did you mean /{suggestion}?"
            error += " Type /help for available commands."

            return CommandResult.fail(error)

        # Validate arguments
        errors = command.validate(parsed)
        if errors:
            return CommandResult.fail(
                "\n".join(errors) + f"\n\nUsage: {command.usage}"
            )

        # Execute command
        try:
            result = await command.execute(parsed, context)
            logger.debug(f"Command {parsed.name} executed: success={result.success}")
            return result

        except Exception as e:
            logger.exception(f"Command {parsed.name} failed")
            return CommandResult.fail(f"Command failed: {e}")

    def can_execute(self, name: str) -> bool:
        """Check if a command exists and can be executed.

        Args:
            name: Command name.

        Returns:
            True if command is available.
        """
        return self.registry.resolve(name) is not None

    def is_command(self, text: str) -> bool:
        """Check if text is a command.

        Args:
            text: Input text.

        Returns:
            True if text is a slash command.
        """
        return self.parser.is_command(text)


def register_builtin_commands(registry: CommandRegistry | None = None) -> None:
    """Register all built-in commands.

    Args:
        registry: Registry to use. Uses singleton if None.
    """
    from .builtin import (
        help_commands,
        session_commands,
        context_commands,
        control_commands,
        config_commands,
        debug_commands,
    )

    if registry is None:
        registry = CommandRegistry.get_instance()

    # Register all built-in commands
    for module in [
        help_commands,
        session_commands,
        context_commands,
        control_commands,
        config_commands,
        debug_commands,
    ]:
        for command in module.get_commands():
            registry.register(command)

    logger.info(f"Registered {len(registry)} built-in commands")
```

---

## File 5: src/opencode/commands/builtin/help.py

```python
"""Help and discovery commands."""

from ..base import Command, CommandResult, CommandCategory, CommandArgument, ArgumentType
from ..parser import ParsedCommand
from ..executor import CommandContext
from ..registry import CommandRegistry


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
            "OpenCode Commands",
            "=" * 40,
            "",
        ]

        categories = registry.get_categories()

        for category, commands in categories.items():
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
                return CommandResult.fail(f"Unknown category: {category_filter}")
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
```

---

## File 6: src/opencode/commands/builtin/session.py

```python
"""Session management commands."""

from ..base import Command, CommandResult, CommandCategory, SubcommandHandler
from ..parser import ParsedCommand
from ..executor import CommandContext


class SessionListCommand(Command):
    """List all sessions."""

    name = "list"
    description = "List all sessions"
    usage = "/session list [--limit N]"

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """List sessions."""
        if context.session_manager is None:
            return CommandResult.fail("Session manager not available")

        limit = int(parsed.get_kwarg("limit", "20"))
        sessions = context.session_manager.list_sessions(limit=limit)

        if not sessions:
            return CommandResult.ok("No sessions found.")

        lines = [f"Sessions ({len(sessions)}):", ""]

        for s in sessions:
            lines.append(f"  {s.id[:8]}... | {s.title or '(untitled)'}")
            lines.append(f"           {s.message_count} msgs | {s.total_tokens} tokens")
            lines.append(f"           Updated: {s.updated_at}")
            lines.append("")

        return CommandResult.ok("\n".join(lines))


class SessionNewCommand(Command):
    """Create new session."""

    name = "new"
    description = "Create a new session"
    usage = "/session new [--title <title>]"

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Create new session."""
        if context.session_manager is None:
            return CommandResult.fail("Session manager not available")

        title = parsed.get_kwarg("title", "")

        # Close current session if any
        if context.session_manager.has_current:
            context.session_manager.close()

        session = context.session_manager.create(title=title)

        return CommandResult.ok(f"Created new session: {session.id[:8]}...")


class SessionResumeCommand(Command):
    """Resume a session."""

    name = "resume"
    description = "Resume a session"
    usage = "/session resume [id]"

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Resume session."""
        if context.session_manager is None:
            return CommandResult.fail("Session manager not available")

        session_id = parsed.get_arg(0)

        if session_id:
            # Find matching session
            sessions = context.session_manager.list_sessions()
            for s in sessions:
                if s.id.startswith(session_id):
                    if context.session_manager.has_current:
                        context.session_manager.close()
                    session = context.session_manager.resume(s.id)
                    return CommandResult.ok(
                        f"Resumed session: {session.title or session.id[:8]}"
                    )
            return CommandResult.fail(f"Session not found: {session_id}")
        else:
            # Resume latest
            session = context.session_manager.resume_latest()
            if session:
                return CommandResult.ok(
                    f"Resumed session: {session.title or session.id[:8]}"
                )
            return CommandResult.fail("No sessions to resume")


class SessionDeleteCommand(Command):
    """Delete a session."""

    name = "delete"
    description = "Delete a session"
    usage = "/session delete <id>"

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Delete session."""
        if context.session_manager is None:
            return CommandResult.fail("Session manager not available")

        session_id = parsed.get_arg(0)
        if not session_id:
            return CommandResult.fail("Session ID required")

        # Find matching session
        sessions = context.session_manager.list_sessions()
        for s in sessions:
            if s.id.startswith(session_id):
                if context.session_manager.delete(s.id):
                    return CommandResult.ok(f"Deleted session: {s.id[:8]}...")
                return CommandResult.fail("Failed to delete session")

        return CommandResult.fail(f"Session not found: {session_id}")


class SessionTitleCommand(Command):
    """Set session title."""

    name = "title"
    description = "Set session title"
    usage = "/session title <text>"

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Set title."""
        if context.session_manager is None:
            return CommandResult.fail("Session manager not available")

        if not context.session_manager.has_current:
            return CommandResult.fail("No active session")

        title = " ".join(parsed.args)
        if not title:
            return CommandResult.fail("Title required")

        context.session_manager.set_title(title)
        return CommandResult.ok(f"Title set: {title}")


class SessionCommand(SubcommandHandler):
    """Session management."""

    name = "session"
    aliases = ["sess", "s"]
    description = "Session management"
    usage = "/session [subcommand]"
    category = CommandCategory.SESSION
    subcommands = {
        "list": SessionListCommand(),
        "new": SessionNewCommand(),
        "resume": SessionResumeCommand(),
        "delete": SessionDeleteCommand(),
        "title": SessionTitleCommand(),
    }

    async def execute_default(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Show current session info."""
        if context.session_manager is None:
            return CommandResult.fail("Session manager not available")

        if not context.session_manager.has_current:
            return CommandResult.ok("No active session. Use /session new to create one.")

        session = context.session_manager.current_session

        lines = [
            f"Session: {session.id}",
            f"Title: {session.title or '(untitled)'}",
            f"Messages: {session.message_count}",
            f"Tokens: {session.total_tokens}",
            f"Created: {session.created_at}",
            f"Updated: {session.updated_at}",
        ]

        if session.tags:
            lines.append(f"Tags: {', '.join(session.tags)}")

        return CommandResult.ok("\n".join(lines))


def get_commands() -> list[Command]:
    """Get all session commands."""
    return [SessionCommand()]
```

---

## File 7: src/opencode/commands/builtin/control.py

```python
"""Control commands for REPL operations."""

from ..base import Command, CommandResult, CommandCategory
from ..parser import ParsedCommand
from ..executor import CommandContext


class ClearCommand(Command):
    """Clear the screen."""

    name = "clear"
    aliases = ["cls"]
    description = "Clear the screen"
    usage = "/clear"
    category = CommandCategory.CONTROL

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Clear screen."""
        # ANSI escape code to clear screen
        context.print("\033[2J\033[H")
        return CommandResult.ok("")


class ExitCommand(Command):
    """Exit the application."""

    name = "exit"
    aliases = ["quit", "q"]
    description = "Exit the application"
    usage = "/exit"
    category = CommandCategory.CONTROL

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Exit application."""
        # Save session if active
        if context.session_manager and context.session_manager.has_current:
            context.session_manager.close()

        # Return special result to signal exit
        return CommandResult.ok("Goodbye!", data={"action": "exit"})


class ResetCommand(Command):
    """Reset to fresh state."""

    name = "reset"
    description = "Reset to fresh state"
    usage = "/reset"
    category = CommandCategory.CONTROL

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Reset state."""
        # Close current session
        if context.session_manager and context.session_manager.has_current:
            context.session_manager.close()

        # Reset context
        if context.context_manager:
            context.context_manager.reset()

        # Create new session
        if context.session_manager:
            context.session_manager.create()

        return CommandResult.ok("Reset complete. Started fresh session.")


class StopCommand(Command):
    """Stop current operation."""

    name = "stop"
    aliases = ["cancel", "abort"]
    description = "Stop current operation"
    usage = "/stop"
    category = CommandCategory.CONTROL

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Stop operation."""
        # Signal to stop any running operation
        return CommandResult.ok("Stopping...", data={"action": "stop"})


def get_commands() -> list[Command]:
    """Get all control commands."""
    return [
        ClearCommand(),
        ExitCommand(),
        ResetCommand(),
        StopCommand(),
    ]
```

---

## File 8: src/opencode/commands/__init__.py

```python
"""Slash command system.

This package provides the command parsing and execution system for OpenCode.
Commands are invoked with /command syntax in the REPL.

Example:
    from opencode.commands import CommandExecutor, CommandContext, register_builtin_commands

    # Register built-in commands
    register_builtin_commands()

    # Create executor
    executor = CommandExecutor()

    # Execute a command
    context = CommandContext(session_manager=session_mgr)
    result = await executor.execute("/help", context)
    print(result.output)
"""

from .parser import CommandParser, ParsedCommand
from .base import (
    Command,
    CommandArgument,
    CommandResult,
    CommandCategory,
    ArgumentType,
    SubcommandHandler,
)
from .registry import CommandRegistry
from .executor import CommandExecutor, CommandContext, register_builtin_commands

__all__ = [
    # Parser
    "CommandParser",
    "ParsedCommand",
    # Base
    "Command",
    "CommandArgument",
    "CommandResult",
    "CommandCategory",
    "ArgumentType",
    "SubcommandHandler",
    # Registry
    "CommandRegistry",
    # Executor
    "CommandExecutor",
    "CommandContext",
    "register_builtin_commands",
]
```

---

## Additional Built-in Commands (Summary)

### src/opencode/commands/builtin/context.py
- `/context` - Show context status
- `/context compact` - Compact context
- `/context reset` - Reset context
- `/context mode <mode>` - Set truncation mode

### src/opencode/commands/builtin/config.py
- `/config` - Show configuration
- `/config get <key>` - Get value
- `/config set <key> <value>` - Set value
- `/model` - Show/set model

### src/opencode/commands/builtin/debug.py
- `/debug` - Toggle debug mode
- `/tokens` - Show token usage
- `/history` - Show message history
- `/tools` - List tools

---

## Integration with REPL

```python
# In REPL main loop
from opencode.commands import CommandExecutor, CommandContext, register_builtin_commands

# Setup
register_builtin_commands()
executor = CommandExecutor()

# Create context
context = CommandContext(
    session_manager=session_manager,
    context_manager=context_manager,
    config=config,
    llm=llm,
    repl=self,
    output=self.print,
)

# In input loop
async def handle_input(self, text: str):
    if executor.is_command(text):
        result = await executor.execute(text, context)
        if result.output:
            self.print(result.output)
        if result.error:
            self.print(f"Error: {result.error}")
        if result.data and result.data.get("action") == "exit":
            return False  # Signal exit
        return True
    else:
        # Handle as normal input
        ...
```

---

## Next Steps

After implementing Phase 6.1:
1. Verify all tests pass
2. Run type checking with mypy
3. Proceed to Phase 6.2 (Operating Modes)
