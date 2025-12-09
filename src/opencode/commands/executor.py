"""Command execution engine."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .base import CommandResult
from .parser import CommandParser
from .registry import CommandRegistry

if TYPE_CHECKING:
    from opencode.config.models import OpenCodeConfig
    from opencode.context.manager import ContextManager
    from opencode.plugins.manager import PluginManager
    from opencode.sessions.manager import SessionManager

logger = logging.getLogger(__name__)


@dataclass
class CommandContext:
    """Context provided to command execution.

    Contains references to system components that commands
    may need to access or modify.

    Attributes:
        session_manager: Session management instance.
        context_manager: Context management instance.
        config: Application configuration.
        llm: LLM client instance.
        repl: REPL instance.
        plugin_manager: Plugin management instance.
        output: Function for writing output to user.
    """

    session_manager: SessionManager | None = None
    context_manager: ContextManager | None = None
    config: OpenCodeConfig | None = None
    llm: Any = None  # OpenRouterLLM
    repl: Any = None  # REPL instance
    plugin_manager: PluginManager | None = None
    output: Callable[[str], None] = field(default_factory=lambda: print)

    def print(self, text: str) -> None:
        """Output text to user.

        Args:
            text: Text to output.
        """
        self.output(text)


class CommandExecutor:
    """Executes parsed commands.

    Coordinates command lookup, validation, and execution.

    Attributes:
        registry: Command registry for lookup.
        parser: Parser for command text.
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
        self.registry = registry if registry is not None else CommandRegistry.get_instance()
        self.parser = parser if parser is not None else CommandParser()

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
        config_commands,
        context_commands,
        control_commands,
        debug_commands,
        help_commands,
        session_commands,
    )
    from opencode.plugins import commands as plugin_commands

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
        plugin_commands,
    ]:
        for command in module.get_commands():
            try:
                registry.register(command)
            except ValueError as e:
                logger.warning(f"Failed to register command: {e}")

    logger.info(f"Registered {len(registry)} built-in commands")
