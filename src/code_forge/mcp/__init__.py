"""MCP (Model Context Protocol) support for Code-Forge.

This package provides integration with MCP servers, allowing Code-Forge
to use tools, resources, and prompts from external MCP-compatible services.
"""

from code_forge.mcp.client import MCPClient, MCPClientError
from code_forge.mcp.config import MCPConfig, MCPConfigLoader, MCPServerConfig, MCPSettings
from code_forge.mcp.manager import MCPConnection, MCPManager
from code_forge.mcp.protocol import (
    MCPCapabilities,
    MCPError,
    MCPMessageType,
    MCPNotification,
    MCPPrompt,
    MCPPromptArgument,
    MCPPromptMessage,
    MCPRequest,
    MCPResource,
    MCPResourceTemplate,
    MCPResponse,
    MCPServerInfo,
    MCPTool,
    parse_json_message,
    parse_message,
)
from code_forge.mcp.tools import MCPToolAdapter, MCPToolRegistry
from code_forge.mcp.transport import HTTPTransport, MCPTransport, StdioTransport

__all__ = [
    # Protocol types
    "MCPMessageType",
    "MCPError",
    "MCPRequest",
    "MCPResponse",
    "MCPNotification",
    "MCPTool",
    "MCPResource",
    "MCPResourceTemplate",
    "MCPPrompt",
    "MCPPromptArgument",
    "MCPPromptMessage",
    "MCPCapabilities",
    "MCPServerInfo",
    "parse_message",
    "parse_json_message",
    # Transport
    "MCPTransport",
    "StdioTransport",
    "HTTPTransport",
    # Client
    "MCPClient",
    "MCPClientError",
    # Tools
    "MCPToolAdapter",
    "MCPToolRegistry",
    # Config
    "MCPServerConfig",
    "MCPSettings",
    "MCPConfig",
    "MCPConfigLoader",
    # Manager
    "MCPConnection",
    "MCPManager",
]
