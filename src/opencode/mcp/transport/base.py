"""Base transport interface for MCP."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MCPTransport(ABC):
    """Abstract base class for MCP transports.

    This class defines the interface that all MCP transports must implement.
    Transports handle the low-level communication with MCP servers.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to MCP server.

        Raises:
            ConnectionError: If connection fails.
        """
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to MCP server."""
        ...

    @abstractmethod
    async def send(self, message: dict[str, Any]) -> None:
        """Send a message to the server.

        Args:
            message: The JSON-RPC message as a dictionary.

        Raises:
            ConnectionError: If not connected or send fails.
        """
        ...

    @abstractmethod
    async def receive(self) -> dict[str, Any]:
        """Receive a message from the server.

        Returns:
            The received JSON-RPC message as a dictionary.

        Raises:
            ConnectionError: If not connected or receive fails.
        """
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if transport is connected.

        Returns:
            True if connected, False otherwise.
        """
        ...
