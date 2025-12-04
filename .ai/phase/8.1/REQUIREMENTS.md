# Phase 8.1: MCP Protocol Support - Requirements

**Phase:** 8.1
**Name:** MCP Protocol Support
**Dependencies:** Phase 2.1 (Tool System), Phase 3.2 (LangChain Integration)

---

## Overview

Phase 8.1 implements Model Context Protocol (MCP) support for OpenCode, enabling integration with external MCP servers that provide additional tools, resources, and capabilities. MCP is an open protocol for connecting AI assistants to external data sources and services.

---

## Goals

1. Implement MCP client protocol
2. Connect to MCP servers (stdio and HTTP/SSE)
3. Discover and register MCP-provided tools
4. Access MCP resources and prompts
5. Support MCP server configuration
6. Enable hot-reload of MCP connections

---

## Non-Goals (This Phase)

- Running as an MCP server
- MCP tool approval UI (uses existing permission system)
- Custom MCP transport protocols
- MCP server marketplace
- MCP capability negotiation beyond basics

---

## Functional Requirements

### FR-1: MCP Client Protocol

**FR-1.1:** Protocol implementation
- JSON-RPC 2.0 message format
- Request/response handling
- Notification support
- Error handling per spec

**FR-1.2:** Connection lifecycle
- Initialize connection
- Negotiate capabilities
- Maintain connection
- Graceful shutdown

**FR-1.3:** Message types
- Initialize request/response
- Tool calls (tools/call)
- Resource reads (resources/read)
- Prompt retrieval (prompts/get)
- List operations (tools/list, resources/list, prompts/list)

### FR-2: Transport Support

**FR-2.1:** Stdio transport
- Launch MCP server as subprocess
- Communicate via stdin/stdout
- Handle process lifecycle
- Support command arguments

**FR-2.2:** HTTP/SSE transport
- Connect to HTTP endpoint
- Server-Sent Events for notifications
- HTTP POST for requests
- Connection timeout handling

**FR-2.3:** Transport abstraction
- Common interface for transports
- Transport-agnostic client code
- Easy transport switching

### FR-3: Tool Integration

**FR-3.1:** Tool discovery
- List tools from MCP server
- Parse tool schemas
- Handle tool metadata

**FR-3.2:** Tool registration
- Register MCP tools in ToolRegistry
- Namespace tools (mcp__{server}__{tool})
- Handle name conflicts

**FR-3.3:** Tool execution
- Route tool calls to MCP server
- Handle tool arguments
- Process tool results
- Handle tool errors

### FR-4: Resource Access

**FR-4.1:** Resource discovery
- List available resources
- Resource URIs and types
- Resource metadata

**FR-4.2:** Resource reading
- Read resource contents
- Handle text and binary
- Resource caching (optional)

**FR-4.3:** Resource templates
- URI templates support
- Parameter substitution
- Template validation

### FR-5: Prompt Support

**FR-5.1:** Prompt discovery
- List available prompts
- Prompt metadata
- Prompt arguments

**FR-5.2:** Prompt retrieval
- Get prompt by name
- Argument substitution
- Multi-message prompts

### FR-6: Server Configuration

**FR-6.1:** Configuration format
- Server name
- Transport type (stdio/http)
- Command or URL
- Arguments/headers
- Environment variables

**FR-6.2:** Configuration sources
- Global config (~/.src/opencode/mcp.yaml)
- Project config (.src/opencode/mcp.yaml)
- Environment variables
- CLI arguments

**FR-6.3:** Server management
- Enable/disable servers
- Auto-connect on startup
- Manual connection control

### FR-7: Connection Management

**FR-7.1:** Connection pool
- Multiple server connections
- Connection state tracking
- Reconnection logic

**FR-7.2:** Health monitoring
- Server health checks
- Connection timeouts
- Error recovery

**FR-7.3:** Hot reload
- Reload configuration
- Reconnect changed servers
- Preserve healthy connections

---

## Non-Functional Requirements

### NFR-1: Performance
- Connection establish < 5s
- Tool call latency < 500ms (plus server time)
- Minimal memory per connection

### NFR-2: Reliability
- Graceful handling of server crashes
- Automatic reconnection (configurable)
- No data loss on disconnect

### NFR-3: Security
- Validate server commands
- Sanitize tool inputs
- No arbitrary code execution

---

## Technical Specifications

### Package Structure

```
src/opencode/mcp/
├── __init__.py           # Package exports
├── protocol.py           # MCP protocol types
├── client.py             # MCP client implementation
├── transport/
│   ├── __init__.py
│   ├── base.py           # Transport interface
│   ├── stdio.py          # Stdio transport
│   └── http.py           # HTTP/SSE transport
├── tools.py              # MCP tool adapter
├── resources.py          # Resource handling
├── prompts.py            # Prompt handling
├── config.py             # Server configuration
└── manager.py            # Connection manager
```

### Configuration Format

```yaml
# ~/.src/opencode/mcp.yaml or .src/opencode/mcp.yaml
servers:
  filesystem:
    transport: stdio
    command: npx
    args:
      - -y
      - "@anthropic/mcp-filesystem"
      - /path/to/allowed/directory
    env:
      DEBUG: "true"

  database:
    transport: stdio
    command: python
    args:
      - -m
      - mcp_postgres
    env:
      DATABASE_URL: "${DATABASE_URL}"

  remote-api:
    transport: http
    url: https://mcp.example.com/api
    headers:
      Authorization: "Bearer ${MCP_API_KEY}"

# Global settings
settings:
  auto_connect: true
  reconnect_attempts: 3
  reconnect_delay: 5
  timeout: 30
```

### Class Signatures

```python
# protocol.py
from dataclasses import dataclass
from enum import Enum
from typing import Any


class MCPMessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


@dataclass
class MCPRequest:
    """MCP JSON-RPC request."""
    id: str | int
    method: str
    params: dict[str, Any] | None = None


@dataclass
class MCPResponse:
    """MCP JSON-RPC response."""
    id: str | int
    result: Any | None = None
    error: "MCPError | None" = None


@dataclass
class MCPError:
    """MCP error object."""
    code: int
    message: str
    data: Any | None = None


@dataclass
class MCPNotification:
    """MCP notification (no response expected)."""
    method: str
    params: dict[str, Any] | None = None


@dataclass
class MCPTool:
    """Tool provided by MCP server."""
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass
class MCPResource:
    """Resource provided by MCP server."""
    uri: str
    name: str
    description: str | None = None
    mime_type: str | None = None


@dataclass
class MCPPrompt:
    """Prompt provided by MCP server."""
    name: str
    description: str | None = None
    arguments: list[dict[str, Any]] | None = None


@dataclass
class MCPCapabilities:
    """Server capabilities from initialize."""
    tools: bool = False
    resources: bool = False
    prompts: bool = False


# transport/base.py
from abc import ABC, abstractmethod


class MCPTransport(ABC):
    """Abstract base for MCP transports."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection."""
        ...

    @abstractmethod
    async def send(self, message: dict) -> None:
        """Send message to server."""
        ...

    @abstractmethod
    async def receive(self) -> dict:
        """Receive message from server."""
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected."""
        ...


# transport/stdio.py
class StdioTransport(MCPTransport):
    """Stdio transport for subprocess-based MCP servers."""

    def __init__(
        self,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        cwd: str | None = None
    ):
        ...


# transport/http.py
class HTTPTransport(MCPTransport):
    """HTTP/SSE transport for remote MCP servers."""

    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: int = 30
    ):
        ...


# client.py
class MCPClient:
    """MCP client for communicating with servers."""

    def __init__(self, transport: MCPTransport, name: str = "opencode"):
        self.transport = transport
        self.name = name
        self._request_id = 0
        self._capabilities: MCPCapabilities | None = None

    async def connect(self) -> MCPCapabilities:
        """Connect and initialize."""
        ...

    async def disconnect(self) -> None:
        """Disconnect from server."""
        ...

    async def list_tools(self) -> list[MCPTool]:
        """List available tools."""
        ...

    async def call_tool(self, name: str, arguments: dict) -> Any:
        """Call a tool."""
        ...

    async def list_resources(self) -> list[MCPResource]:
        """List available resources."""
        ...

    async def read_resource(self, uri: str) -> str | bytes:
        """Read a resource."""
        ...

    async def list_prompts(self) -> list[MCPPrompt]:
        """List available prompts."""
        ...

    async def get_prompt(self, name: str, arguments: dict | None = None) -> list[dict]:
        """Get a prompt."""
        ...

    @property
    def capabilities(self) -> MCPCapabilities | None:
        """Get negotiated capabilities."""
        ...


# tools.py
class MCPToolAdapter:
    """Adapts MCP tools to OpenCode tool interface."""

    def __init__(self, client: MCPClient, server_name: str):
        ...

    def create_tool(self, mcp_tool: MCPTool) -> "Tool":
        """Create OpenCode Tool from MCP tool."""
        ...

    async def execute(self, tool_name: str, arguments: dict) -> Any:
        """Execute MCP tool."""
        ...


# config.py
@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    transport: str  # "stdio" or "http"
    command: str | None = None  # for stdio
    args: list[str] | None = None
    url: str | None = None  # for http
    headers: dict[str, str] | None = None
    env: dict[str, str] | None = None
    enabled: bool = True
    auto_connect: bool = True


@dataclass
class MCPConfig:
    """Overall MCP configuration."""
    servers: dict[str, MCPServerConfig]
    auto_connect: bool = True
    reconnect_attempts: int = 3
    reconnect_delay: int = 5
    timeout: int = 30


class MCPConfigLoader:
    """Loads MCP configuration."""

    def load(self) -> MCPConfig:
        """Load configuration from files."""
        ...

    def load_from_file(self, path: Path) -> MCPConfig:
        """Load from specific file."""
        ...

    def merge_configs(self, *configs: MCPConfig) -> MCPConfig:
        """Merge multiple configs."""
        ...


# manager.py
@dataclass
class MCPConnection:
    """Represents a connection to an MCP server."""
    name: str
    client: MCPClient
    config: MCPServerConfig
    tools: list[MCPTool]
    resources: list[MCPResource]
    prompts: list[MCPPrompt]
    connected_at: datetime


class MCPManager:
    """Manages MCP server connections."""

    _instance: "MCPManager | None" = None

    def __init__(self, config: MCPConfig):
        self._config = config
        self._connections: dict[str, MCPConnection] = {}
        self._tool_registry: ToolRegistry | None = None

    @classmethod
    def get_instance(cls) -> "MCPManager":
        """Get singleton instance."""
        ...

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)."""
        ...

    def set_tool_registry(self, registry: "ToolRegistry") -> None:
        """Set tool registry for tool registration."""
        ...

    async def connect(self, server_name: str) -> MCPConnection:
        """Connect to a specific server."""
        ...

    async def connect_all(self) -> list[MCPConnection]:
        """Connect to all enabled servers."""
        ...

    async def disconnect(self, server_name: str) -> None:
        """Disconnect from a server."""
        ...

    async def disconnect_all(self) -> None:
        """Disconnect from all servers."""
        ...

    async def reconnect(self, server_name: str) -> MCPConnection:
        """Reconnect to a server."""
        ...

    def get_connection(self, name: str) -> MCPConnection | None:
        """Get connection by name."""
        ...

    def list_connections(self) -> list[MCPConnection]:
        """List all connections."""
        ...

    async def reload_config(self) -> None:
        """Reload configuration and reconnect."""
        ...

    def get_all_tools(self) -> list[MCPTool]:
        """Get tools from all connections."""
        ...

    def get_all_resources(self) -> list[MCPResource]:
        """Get resources from all connections."""
        ...

    def get_all_prompts(self) -> list[MCPPrompt]:
        """Get prompts from all connections."""
        ...
```

---

## MCP Commands

| Command | Description |
|---------|-------------|
| `/mcp` | Show MCP status |
| `/mcp servers` | List configured servers |
| `/mcp connect <name>` | Connect to server |
| `/mcp disconnect <name>` | Disconnect from server |
| `/mcp tools` | List MCP tools |
| `/mcp resources` | List MCP resources |
| `/mcp prompts` | List MCP prompts |
| `/mcp reload` | Reload configuration |

---

## Integration Points

### With Tool System (Phase 2.1)
- MCP tools registered in ToolRegistry
- Namespaced as `mcp__{server}__{tool}`
- Standard tool interface

### With LangChain (Phase 3.2)
- MCP tools available to agents
- Tool calls routed through MCP client

### With Permission System (Phase 4.1)
- MCP tool permissions
- Server connection permissions

### With Configuration (Phase 1.2)
- MCP config files
- Environment variable expansion

---

## Testing Requirements

1. Unit tests for protocol types
2. Unit tests for transports (with mocks)
3. Unit tests for MCPClient
4. Unit tests for MCPManager
5. Unit tests for config loading
6. Integration tests with mock server
7. Test coverage ≥ 90%

---

## Acceptance Criteria

1. Can connect to stdio MCP servers
2. Can connect to HTTP MCP servers
3. MCP tools appear in tool list
4. MCP tool calls work correctly
5. Resources can be read
6. Prompts can be retrieved
7. Configuration loads correctly
8. Multiple servers supported
9. Graceful error handling
10. Reconnection works
11. Hot reload functions
