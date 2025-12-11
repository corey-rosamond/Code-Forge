"""MCP protocol types and message handling.

This module implements the Model Context Protocol (MCP) message types
following the JSON-RPC 2.0 specification.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MCPMessageType(Enum):
    """Types of MCP messages."""

    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"


@dataclass
class MCPError:
    """MCP error object per JSON-RPC 2.0."""

    code: int
    message: str
    data: Any | None = None

    # Standard JSON-RPC error codes
    PARSE_ERROR: int = -32700
    INVALID_REQUEST: int = -32600
    METHOD_NOT_FOUND: int = -32601
    INVALID_PARAMS: int = -32602
    INTERNAL_ERROR: int = -32603

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MCPError:
        """Create from dictionary."""
        return cls(
            code=data["code"],
            message=data["message"],
            data=data.get("data"),
        )

    @classmethod
    def parse_error(cls, message: str = "Parse error") -> MCPError:
        """Create a parse error."""
        return cls(code=cls.PARSE_ERROR, message=message)

    @classmethod
    def invalid_request(cls, message: str = "Invalid request") -> MCPError:
        """Create an invalid request error."""
        return cls(code=cls.INVALID_REQUEST, message=message)

    @classmethod
    def method_not_found(cls, message: str = "Method not found") -> MCPError:
        """Create a method not found error."""
        return cls(code=cls.METHOD_NOT_FOUND, message=message)

    @classmethod
    def invalid_params(cls, message: str = "Invalid params") -> MCPError:
        """Create an invalid params error."""
        return cls(code=cls.INVALID_PARAMS, message=message)

    @classmethod
    def internal_error(cls, message: str = "Internal error") -> MCPError:
        """Create an internal error."""
        return cls(code=cls.INTERNAL_ERROR, message=message)


@dataclass
class MCPRequest:
    """MCP JSON-RPC request."""

    method: str
    params: dict[str, Any] | None = None
    id: str | int | None = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-RPC message."""
        msg: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": self.method,
        }
        if self.id is not None:
            msg["id"] = self.id
        if self.params is not None:
            msg["params"] = self.params
        return msg

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MCPRequest:
        """Create from dictionary."""
        return cls(
            method=data["method"],
            params=data.get("params"),
            id=data.get("id"),
        )


@dataclass
class MCPResponse:
    """MCP JSON-RPC response."""

    id: str | int
    result: Any | None = None
    error: MCPError | None = None

    @property
    def is_error(self) -> bool:
        """Check if response is an error."""
        return self.error is not None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        msg: dict[str, Any] = {"jsonrpc": "2.0", "id": self.id}
        if self.error is not None:
            msg["error"] = self.error.to_dict()
        else:
            msg["result"] = self.result
        return msg

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MCPResponse:
        """Create from dictionary."""
        error = None
        if "error" in data:
            error = MCPError.from_dict(data["error"])
        return cls(
            id=data["id"],
            result=data.get("result"),
            error=error,
        )

    @classmethod
    def success(cls, id: str | int, result: Any) -> MCPResponse:
        """Create a success response."""
        return cls(id=id, result=result)

    @classmethod
    def failure(cls, id: str | int, error: MCPError) -> MCPResponse:
        """Create an error response."""
        return cls(id=id, error=error)


@dataclass
class MCPNotification:
    """MCP notification (no response expected)."""

    method: str
    params: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-RPC message."""
        msg: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": self.method,
        }
        if self.params is not None:
            msg["params"] = self.params
        return msg

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MCPNotification:
        """Create from dictionary."""
        return cls(
            method=data["method"],
            params=data.get("params"),
        )


# MCP-specific types


@dataclass
class MCPTool:
    """Tool provided by MCP server."""

    name: str
    description: str
    input_schema: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MCPTool:
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            input_schema=data.get("inputSchema", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


@dataclass
class MCPResource:
    """Resource provided by MCP server."""

    uri: str
    name: str
    description: str | None = None
    mime_type: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MCPResource:
        """Create from dictionary."""
        return cls(
            uri=data["uri"],
            name=data["name"],
            description=data.get("description"),
            mime_type=data.get("mimeType"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {
            "uri": self.uri,
            "name": self.name,
        }
        if self.description is not None:
            result["description"] = self.description
        if self.mime_type is not None:
            result["mimeType"] = self.mime_type
        return result


@dataclass
class MCPResourceTemplate:
    """Resource template with URI pattern."""

    uri_template: str
    name: str
    description: str | None = None
    mime_type: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MCPResourceTemplate:
        """Create from dictionary."""
        return cls(
            uri_template=data["uriTemplate"],
            name=data["name"],
            description=data.get("description"),
            mime_type=data.get("mimeType"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {
            "uriTemplate": self.uri_template,
            "name": self.name,
        }
        if self.description is not None:
            result["description"] = self.description
        if self.mime_type is not None:
            result["mimeType"] = self.mime_type
        return result


@dataclass
class MCPPromptArgument:
    """Argument for an MCP prompt."""

    name: str
    description: str | None = None
    required: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MCPPromptArgument:
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description"),
            required=data.get("required", False),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {"name": self.name}
        if self.description is not None:
            result["description"] = self.description
        if self.required:
            result["required"] = self.required
        return result


@dataclass
class MCPPrompt:
    """Prompt provided by MCP server."""

    name: str
    description: str | None = None
    arguments: list[MCPPromptArgument] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MCPPrompt:
        """Create from dictionary."""
        args = None
        if "arguments" in data:
            args = [MCPPromptArgument.from_dict(a) for a in data["arguments"]]
        return cls(
            name=data["name"],
            description=data.get("description"),
            arguments=args,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {"name": self.name}
        if self.description is not None:
            result["description"] = self.description
        if self.arguments is not None:
            result["arguments"] = [a.to_dict() for a in self.arguments]
        return result


@dataclass
class MCPPromptMessage:
    """Message in a prompt response."""

    role: str
    content: str | dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MCPPromptMessage:
        """Create from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
        }


@dataclass
class MCPCapabilities:
    """Server capabilities from initialize."""

    tools: bool = False
    resources: bool = False
    prompts: bool = False
    logging: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MCPCapabilities:
        """Create from capabilities dict."""
        caps = data.get("capabilities", {})
        return cls(
            tools="tools" in caps,
            resources="resources" in caps,
            prompts="prompts" in caps,
            logging="logging" in caps,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        caps: dict[str, dict[str, Any]] = {}
        if self.tools:
            caps["tools"] = {}
        if self.resources:
            caps["resources"] = {}
        if self.prompts:
            caps["prompts"] = {}
        if self.logging:
            caps["logging"] = {}
        return {"capabilities": caps}


@dataclass
class MCPServerInfo:
    """Server information from initialize."""

    name: str
    version: str
    capabilities: MCPCapabilities

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MCPServerInfo:
        """Create from initialize result."""
        server_info = data.get("serverInfo", {})
        return cls(
            name=server_info.get("name", "unknown"),
            version=server_info.get("version", "0.0.0"),
            capabilities=MCPCapabilities.from_dict(data),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "serverInfo": {
                "name": self.name,
                "version": self.version,
            },
        }
        result.update(self.capabilities.to_dict())
        return result


def parse_message(data: dict[str, Any]) -> MCPRequest | MCPResponse | MCPNotification:
    """Parse a JSON-RPC message.

    Args:
        data: The JSON-RPC message as a dictionary.

    Returns:
        The parsed message object.

    Raises:
        ValueError: If the message is invalid.
    """
    if "method" in data:
        if "id" in data:
            return MCPRequest.from_dict(data)
        else:
            return MCPNotification.from_dict(data)
    elif "id" in data:
        return MCPResponse.from_dict(data)
    else:
        raise ValueError("Invalid JSON-RPC message: missing 'method' or 'id'")


def parse_json_message(json_str: str) -> MCPRequest | MCPResponse | MCPNotification:
    """Parse a JSON-RPC message from a JSON string.

    Args:
        json_str: The JSON string.

    Returns:
        The parsed message object.

    Raises:
        ValueError: If the JSON is invalid or the message is invalid.
    """
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e
    return parse_message(data)
