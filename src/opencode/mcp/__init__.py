"""MCP (Model Context Protocol) support for OpenCode.

This package provides integration with MCP servers, allowing OpenCode
to use tools, resources, and prompts from external MCP-compatible services.
"""

from opencode.mcp.client import MCPClient, MCPClientError
from opencode.mcp.config import MCPConfig, MCPConfigLoader, MCPServerConfig, MCPSettings
from opencode.mcp.manager import MCPConnection, MCPManager
from opencode.mcp.protocol import (
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
from opencode.mcp.tools import MCPToolAdapter, MCPToolRegistry
from opencode.mcp.transport import HTTPTransport, MCPTransport, StdioTransport

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
