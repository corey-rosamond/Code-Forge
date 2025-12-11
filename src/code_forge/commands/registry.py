"""Command registry for managing available commands."""

from __future__ import annotations

import logging
import threading
from collections.abc import Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Command, CommandCategory

logger = logging.getLogger(__name__)


class CommandRegistry:
    """Registry of available commands.

    Manages registration, lookup, and discovery of commands.
    Supports aliases for convenient command access.

    This is a thread-safe singleton that maintains all registered commands.

    Attributes:
        _instance: Singleton instance.
        _instance_lock: Lock for singleton creation.
    """

    _instance: CommandRegistry | None = None
    _instance_lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._commands: dict[str, Command] = {}
        self._aliases: dict[str, str] = {}
        self._lock = threading.RLock()

    @classmethod
    def get_instance(cls) -> CommandRegistry:
        """Get singleton registry instance.

        Returns:
            The CommandRegistry singleton.
        """
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing)."""
        with cls._instance_lock:
            cls._instance = None

    def register(self, command: Command) -> None:
        """Register a command.

        Args:
            command: Command to register.

        Raises:
            ValueError: If command name conflicts with existing command or alias.
        """
        name = command.name.lower()

        with self._lock:
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

        with self._lock:
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
        with self._lock:
            return self._commands.get(name.lower())

    def resolve(self, name: str) -> Command | None:
        """Resolve command by name or alias.

        Args:
            name: Command name or alias.

        Returns:
            Command or None if not found.
        """
        name_lower = name.lower()

        with self._lock:
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
            List of commands, sorted by name.
        """
        with self._lock:
            commands = list(self._commands.values())

        if category is not None:
            commands = [c for c in commands if c.category == category]

        return sorted(commands, key=lambda c: c.name)

    def list_names(self) -> list[str]:
        """List all command names (including aliases).

        Returns:
            Sorted list of command names and aliases.
        """
        with self._lock:
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

        with self._lock:
            for command in self._commands.values():
                if (
                    query_lower in command.name.lower()
                    or query_lower in command.description.lower()
                    or any(query_lower in alias.lower() for alias in command.aliases)
                ):
                    results.append(command)

        return results

    def get_categories(self) -> dict[CommandCategory, list[Command]]:
        """Get commands grouped by category.

        Returns:
            Dictionary of category -> commands.
        """
        categories: dict[CommandCategory, list[Command]] = {}

        with self._lock:
            for command in self._commands.values():
                if command.category not in categories:
                    categories[command.category] = []
                categories[command.category].append(command)

        # Sort commands within each category
        for cmd_list in categories.values():
            cmd_list.sort(key=lambda c: c.name)

        return categories

    def __len__(self) -> int:
        """Number of registered commands."""
        with self._lock:
            return len(self._commands)

    def __contains__(self, name: str) -> bool:
        """Check if command is registered."""
        return self.resolve(name) is not None

    def __iter__(self) -> Iterator[Command]:
        """Iterate over registered commands."""
        with self._lock:
            # Return a copy to avoid modification during iteration
            return iter(list(self._commands.values()))
