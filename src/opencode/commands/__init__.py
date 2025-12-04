"""Slash command system.

This package provides the command parsing and execution system for OpenCode.
Commands are invoked with /command syntax in the REPL.

Example:
    from opencode.commands import (
        CommandExecutor,
        CommandContext,
        register_builtin_commands,
    )

    # Register built-in commands
    register_builtin_commands()

    # Create executor
    executor = CommandExecutor()

    # Execute a command
    context = CommandContext(session_manager=session_mgr)
    result = await executor.execute("/help", context)
    print(result.output)
"""

from .base import (
    ArgumentType,
    Command,
    CommandArgument,
    CommandCategory,
    CommandResult,
    SubcommandHandler,
)
from .executor import CommandContext, CommandExecutor, register_builtin_commands
from .parser import CommandParser, ParsedCommand
from .registry import CommandRegistry

__all__ = [
    "ArgumentType",
    # Base
    "Command",
    "CommandArgument",
    "CommandCategory",
    "CommandContext",
    # Executor
    "CommandExecutor",
    # Parser
    "CommandParser",
    # Registry
    "CommandRegistry",
    "CommandResult",
    "ParsedCommand",
    "SubcommandHandler",
    "register_builtin_commands",
]
