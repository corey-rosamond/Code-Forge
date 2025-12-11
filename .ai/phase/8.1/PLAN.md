# Phase 8.1: MCP Protocol Support - Implementation Plan

**Phase:** 8.1
**Name:** MCP Protocol Support
**Dependencies:** Phase 2.1 (Tool System), Phase 3.2 (LangChain Integration)

---

## Implementation Order

1. Protocol types and messages
2. Transport abstraction and implementations
3. MCP client
4. Tool adapter
5. Resource and prompt handling
6. Configuration system
7. Connection manager
8. Commands integration

---

## Step 1: Protocol Types (protocol.py)

### Message Types

```python
# src/forge/mcp/protocol.py
"""MCP protocol types and message handling."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import json
import uuid


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

    # Standard error codes
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "MCPError":
        """Create from dictionary."""
        return cls(
            code=data["code"],
            message=data["message"],
            data=data.get("data")
        )


@dataclass
class MCPRequest:
    """MCP JSON-RPC request."""
    method: str
    params: dict[str, Any] | None = None
    id: str | int | None = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        """Convert to JSON-RPC message."""
        msg = {
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

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        msg = {"jsonrpc": "2.0", "id": self.id}
        if self.error is not None:
            msg["error"] = self.error.to_dict()
        else:
            msg["result"] = self.result
        return msg

    @classmethod
    def from_dict(cls, data: dict) -> "MCPResponse":
        """Create from dictionary."""
        error = None
        if "error" in data:
            error = MCPError.from_dict(data["error"])
        return cls(
            id=data["id"],
            result=data.get("result"),
            error=error
        )


@dataclass
class MCPNotification:
    """MCP notification (no response expected)."""
    method: str
    params: dict[str, Any] | None = None

    def to_dict(self) -> dict:
        """Convert to JSON-RPC message."""
        msg = {
            "jsonrpc": "2.0",
            "method": self.method,
        }
        if self.params is not None:
            msg["params"] = self.params
        return msg

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


# MCP-specific types

@dataclass
class MCPTool:
    """Tool provided by MCP server."""
    name: str
    description: str
    input_schema: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict) -> "MCPTool":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            input_schema=data.get("inputSchema", {})
        )


@dataclass
class MCPResource:
    """Resource provided by MCP server."""
    uri: str
    name: str
    description: str | None = None
    mime_type: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "MCPResource":
        """Create from dictionary."""
        return cls(
            uri=data["uri"],
            name=data["name"],
            description=data.get("description"),
            mime_type=data.get("mimeType")
        )


@dataclass
class MCPResourceTemplate:
    """Resource template with URI pattern."""
    uri_template: str
    name: str
    description: str | None = None
    mime_type: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "MCPResourceTemplate":
        """Create from dictionary."""
        return cls(
            uri_template=data["uriTemplate"],
            name=data["name"],
            description=data.get("description"),
            mime_type=data.get("mimeType")
        )


@dataclass
class MCPPromptArgument:
    """Argument for an MCP prompt."""
    name: str
    description: str | None = None
    required: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "MCPPromptArgument":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description"),
            required=data.get("required", False)
        )


@dataclass
class MCPPrompt:
    """Prompt provided by MCP server."""
    name: str
    description: str | None = None
    arguments: list[MCPPromptArgument] | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "MCPPrompt":
        """Create from dictionary."""
        args = None
        if "arguments" in data:
            args = [MCPPromptArgument.from_dict(a) for a in data["arguments"]]
        return cls(
            name=data["name"],
            description=data.get("description"),
            arguments=args
        )


@dataclass
class MCPPromptMessage:
    """Message in a prompt response."""
    role: str
    content: str | dict

    @classmethod
    def from_dict(cls, data: dict) -> "MCPPromptMessage":
        """Create from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"]
        )


@dataclass
class MCPCapabilities:
    """Server capabilities from initialize."""
    tools: bool = False
    resources: bool = False
    prompts: bool = False
    logging: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "MCPCapabilities":
        """Create from capabilities dict."""
        caps = data.get("capabilities", {})
        return cls(
            tools="tools" in caps,
            resources="resources" in caps,
            prompts="prompts" in caps,
            logging="logging" in caps
        )


@dataclass
class MCPServerInfo:
    """Server information from initialize."""
    name: str
    version: str
    capabilities: MCPCapabilities

    @classmethod
    def from_dict(cls, data: dict) -> "MCPServerInfo":
        """Create from initialize result."""
        return cls(
            name=data.get("serverInfo", {}).get("name", "unknown"),
            version=data.get("serverInfo", {}).get("version", "0.0.0"),
            capabilities=MCPCapabilities.from_dict(data)
        )


def parse_message(data: dict) -> MCPRequest | MCPResponse | MCPNotification:
    """Parse a JSON-RPC message."""
    if "method" in data:
        if "id" in data:
            return MCPRequest(
                method=data["method"],
                params=data.get("params"),
                id=data["id"]
            )
        else:
            return MCPNotification(
                method=data["method"],
                params=data.get("params")
            )
    elif "id" in data:
        return MCPResponse.from_dict(data)
    else:
        raise ValueError("Invalid JSON-RPC message")
```

---

## Step 2: Transport Layer (transport/)

### Base Transport

```python
# src/forge/mcp/transport/base.py
"""Base transport interface for MCP."""

from abc import ABC, abstractmethod
from typing import Any


class MCPTransport(ABC):
    """Abstract base class for MCP transports."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to MCP server."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to MCP server."""
        ...

    @abstractmethod
    async def send(self, message: dict[str, Any]) -> None:
        """Send a message to the server."""
        ...

    @abstractmethod
    async def receive(self) -> dict[str, Any]:
        """Receive a message from the server."""
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        ...
```

### Stdio Transport

```python
# src/forge/mcp/transport/stdio.py
"""Stdio transport for subprocess-based MCP servers."""

import asyncio
import json
import logging
import os
from typing import Any

from .base import MCPTransport

logger = logging.getLogger(__name__)


class StdioTransport(MCPTransport):
    """Transport using stdio for subprocess communication."""

    def __init__(
        self,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        cwd: str | None = None
    ):
        """Initialize stdio transport.

        Args:
            command: Command to run
            args: Command arguments
            env: Environment variables (merged with current env)
            cwd: Working directory
        """
        self.command = command
        self.args = args or []
        self.env = env
        self.cwd = cwd
        self._process: asyncio.subprocess.Process | None = None
        self._read_lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()

    async def connect(self) -> None:
        """Start subprocess and establish connection.

        Raises:
            ConnectionError: If subprocess fails to start.
        """
        # Build environment
        process_env = os.environ.copy()
        if self.env:
            # Expand environment variables
            for key, value in self.env.items():
                expanded = os.path.expandvars(value)
                process_env[key] = expanded

        # Start process with proper cleanup on failure
        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                self.command,
                *self.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=process_env,
                cwd=self.cwd
            )

            # Verify process started successfully
            if process.returncode is not None:
                raise ConnectionError(f"MCP server exited immediately with code {process.returncode}")

            self._process = process
            logger.info(f"Started MCP server: {self.command} (PID: {self._process.pid})")

        except Exception:
            # Clean up process if startup failed
            if process is not None and process.returncode is None:
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass  # Best effort cleanup
            raise

    async def disconnect(self) -> None:
        """Terminate subprocess."""
        if self._process is not None:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()
                await self._process.wait()
            finally:
                self._process = None
        logger.info("MCP server disconnected")

    async def send(self, message: dict[str, Any]) -> None:
        """Send JSON-RPC message to subprocess stdin."""
        if self._process is None or self._process.stdin is None:
            raise ConnectionError("Not connected")

        async with self._write_lock:
            data = json.dumps(message)
            line = data + "\n"
            self._process.stdin.write(line.encode())
            await self._process.stdin.drain()
            logger.debug(f"Sent: {data}")

    async def receive(self) -> dict[str, Any]:
        """Receive JSON-RPC message from subprocess stdout."""
        if self._process is None or self._process.stdout is None:
            raise ConnectionError("Not connected")

        async with self._read_lock:
            line = await self._process.stdout.readline()
            if not line:
                raise ConnectionError("Server closed connection")

            data = line.decode().strip()
            logger.debug(f"Received: {data}")
            return json.loads(data)

    @property
    def is_connected(self) -> bool:
        """Check if subprocess is running."""
        return (
            self._process is not None
            and self._process.returncode is None
        )
```

### HTTP/SSE Transport

```python
# src/forge/mcp/transport/http.py
"""HTTP/SSE transport for remote MCP servers."""

import asyncio
import json
import logging
from typing import Any

import aiohttp

from .base import MCPTransport

logger = logging.getLogger(__name__)


class HTTPTransport(MCPTransport):
    """Transport using HTTP for remote MCP servers."""

    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: int = 30
    ):
        """Initialize HTTP transport.

        Args:
            url: Base URL of MCP server
            headers: HTTP headers to include
            timeout: Request timeout in seconds
        """
        self.url = url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout
        self._session: aiohttp.ClientSession | None = None
        self._sse_task: asyncio.Task | None = None
        self._message_queue: asyncio.Queue[dict] = asyncio.Queue()
        self._connected = False

    async def connect(self) -> None:
        """Establish HTTP connection and start SSE listener."""
        self._session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )

        # Start SSE listener for notifications
        self._sse_task = asyncio.create_task(self._listen_sse())
        self._connected = True
        logger.info(f"Connected to MCP server: {self.url}")

    async def disconnect(self) -> None:
        """Close HTTP connection."""
        self._connected = False
        if self._sse_task:
            self._sse_task.cancel()
            try:
                await self._sse_task
            except asyncio.CancelledError:
                pass
            self._sse_task = None

        if self._session:
            await self._session.close()
            self._session = None
        logger.info("Disconnected from MCP server")

    async def send(self, message: dict[str, Any]) -> None:
        """Send JSON-RPC message via HTTP POST."""
        if self._session is None:
            raise ConnectionError("Not connected")

        async with self._session.post(
            f"{self.url}/message",
            json=message
        ) as response:
            response.raise_for_status()
            result = await response.json()
            # Queue the response for receive()
            await self._message_queue.put(result)
            logger.debug(f"Sent: {json.dumps(message)}")

    async def receive(self) -> dict[str, Any]:
        """Receive message from queue."""
        message = await self._message_queue.get()
        logger.debug(f"Received: {json.dumps(message)}")
        return message

    async def _listen_sse(self) -> None:
        """Listen for Server-Sent Events."""
        if self._session is None:
            return

        try:
            async with self._session.get(
                f"{self.url}/sse",
                headers={"Accept": "text/event-stream"}
            ) as response:
                async for line in response.content:
                    if line.startswith(b"data: "):
                        data = line[6:].decode().strip()
                        if data:
                            message = json.loads(data)
                            await self._message_queue.put(message)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"SSE error: {e}")

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected and self._session is not None
```

---

## Step 3: MCP Client (client.py)

```python
# src/forge/mcp/client.py
"""MCP client implementation."""

import asyncio
import logging
from typing import Any

from .protocol import (
    MCPCapabilities,
    MCPError,
    MCPPrompt,
    MCPPromptMessage,
    MCPRequest,
    MCPResource,
    MCPResourceTemplate,
    MCPResponse,
    MCPServerInfo,
    MCPTool,
    parse_message,
)
from .transport.base import MCPTransport

logger = logging.getLogger(__name__)


class MCPClientError(Exception):
    """MCP client error."""

    def __init__(self, message: str, code: int | None = None):
        super().__init__(message)
        self.code = code


class MCPClient:
    """Client for communicating with MCP servers."""

    PROTOCOL_VERSION = "2024-11-05"

    def __init__(
        self,
        transport: MCPTransport,
        client_name: str = "forge",
        client_version: str = "1.0.0"
    ):
        """Initialize MCP client.

        Args:
            transport: Transport to use for communication
            client_name: Client name for initialization
            client_version: Client version
        """
        self.transport = transport
        self.client_name = client_name
        self.client_version = client_version
        self._server_info: MCPServerInfo | None = None
        self._pending_requests: dict[str | int, asyncio.Future] = {}
        self._receive_task: asyncio.Task | None = None

    async def connect(self) -> MCPServerInfo:
        """Connect to server and initialize."""
        await self.transport.connect()

        # Start message receiver
        self._receive_task = asyncio.create_task(self._receive_loop())

        # Send initialize request
        result = await self._request("initialize", {
            "protocolVersion": self.PROTOCOL_VERSION,
            "clientInfo": {
                "name": self.client_name,
                "version": self.client_version
            },
            "capabilities": {}
        })

        self._server_info = MCPServerInfo.from_dict(result)

        # Send initialized notification
        await self._notify("notifications/initialized", {})

        logger.info(
            f"Connected to {self._server_info.name} "
            f"v{self._server_info.version}"
        )
        return self._server_info

    async def disconnect(self) -> None:
        """Disconnect from server."""
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        await self.transport.disconnect()
        self._server_info = None

    @property
    def capabilities(self) -> MCPCapabilities | None:
        """Get server capabilities."""
        if self._server_info:
            return self._server_info.capabilities
        return None

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self.transport.is_connected

    # Tool methods

    async def list_tools(self) -> list[MCPTool]:
        """List available tools."""
        if not self.capabilities or not self.capabilities.tools:
            return []

        result = await self._request("tools/list", {})
        tools = result.get("tools", [])
        return [MCPTool.from_dict(t) for t in tools]

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None
    ) -> Any:
        """Call a tool.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result
        """
        result = await self._request("tools/call", {
            "name": name,
            "arguments": arguments or {}
        })
        return result.get("content", [])

    # Resource methods

    async def list_resources(self) -> list[MCPResource]:
        """List available resources."""
        if not self.capabilities or not self.capabilities.resources:
            return []

        result = await self._request("resources/list", {})
        resources = result.get("resources", [])
        return [MCPResource.from_dict(r) for r in resources]

    async def list_resource_templates(self) -> list[MCPResourceTemplate]:
        """List resource templates."""
        if not self.capabilities or not self.capabilities.resources:
            return []

        result = await self._request("resources/templates/list", {})
        templates = result.get("resourceTemplates", [])
        return [MCPResourceTemplate.from_dict(t) for t in templates]

    async def read_resource(self, uri: str) -> list[dict]:
        """Read a resource.

        Args:
            uri: Resource URI

        Returns:
            Resource contents
        """
        result = await self._request("resources/read", {"uri": uri})
        return result.get("contents", [])

    # Prompt methods

    async def list_prompts(self) -> list[MCPPrompt]:
        """List available prompts."""
        if not self.capabilities or not self.capabilities.prompts:
            return []

        result = await self._request("prompts/list", {})
        prompts = result.get("prompts", [])
        return [MCPPrompt.from_dict(p) for p in prompts]

    async def get_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None = None
    ) -> list[MCPPromptMessage]:
        """Get a prompt.

        Args:
            name: Prompt name
            arguments: Prompt arguments

        Returns:
            Prompt messages
        """
        result = await self._request("prompts/get", {
            "name": name,
            "arguments": arguments or {}
        })
        messages = result.get("messages", [])
        return [MCPPromptMessage.from_dict(m) for m in messages]

    # Internal methods

    async def _request(
        self,
        method: str,
        params: dict[str, Any]
    ) -> dict[str, Any]:
        """Send request and wait for response."""
        request = MCPRequest(method=method, params=params)
        future: asyncio.Future[dict] = asyncio.get_event_loop().create_future()
        self._pending_requests[request.id] = future

        try:
            await self.transport.send(request.to_dict())
            result = await asyncio.wait_for(future, timeout=30.0)
            return result
        except asyncio.TimeoutError:
            raise MCPClientError(f"Request timeout: {method}")
        finally:
            self._pending_requests.pop(request.id, None)

    async def _notify(self, method: str, params: dict[str, Any]) -> None:
        """Send notification (no response expected)."""
        from .protocol import MCPNotification
        notification = MCPNotification(method=method, params=params)
        await self.transport.send(notification.to_dict())

    async def _receive_loop(self) -> None:
        """Receive and dispatch messages."""
        try:
            while self.transport.is_connected:
                message = await self.transport.receive()
                await self._handle_message(message)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Receive error: {e}")
            # Cancel all pending requests
            for future in self._pending_requests.values():
                if not future.done():
                    future.set_exception(
                        MCPClientError(f"Connection error: {e}")
                    )

    async def _handle_message(self, data: dict) -> None:
        """Handle incoming message."""
        message = parse_message(data)

        if isinstance(message, MCPResponse):
            # Match to pending request
            future = self._pending_requests.get(message.id)
            if future and not future.done():
                if message.error:
                    future.set_exception(
                        MCPClientError(
                            message.error.message,
                            message.error.code
                        )
                    )
                else:
                    future.set_result(message.result or {})
        else:
            # Handle notification or request from server
            logger.debug(f"Received: {message}")
```

---

## Step 4: Tool Adapter (tools.py)

```python
# src/forge/mcp/tools.py
"""Adapter for MCP tools to Code-Forge tool interface."""

import json
import logging
from typing import Any

from .client import MCPClient
from .protocol import MCPTool

logger = logging.getLogger(__name__)


class MCPToolAdapter:
    """Adapts MCP tools to Code-Forge Tool interface."""

    def __init__(self, client: MCPClient, server_name: str):
        """Initialize adapter.

        Args:
            client: MCP client
            server_name: Server name for namespacing
        """
        self.client = client
        self.server_name = server_name

    def get_tool_name(self, mcp_tool: MCPTool) -> str:
        """Get namespaced tool name.

        Format: mcp__{server}__{tool}
        """
        # Sanitize names for valid identifiers
        server = self.server_name.replace("-", "_").replace(".", "_")
        tool = mcp_tool.name.replace("-", "_").replace(".", "_")
        return f"mcp__{server}__{tool}"

    def create_tool_definition(self, mcp_tool: MCPTool) -> dict:
        """Create tool definition for LangChain.

        Args:
            mcp_tool: MCP tool definition

        Returns:
            Tool definition dict
        """
        return {
            "name": self.get_tool_name(mcp_tool),
            "description": mcp_tool.description,
            "parameters": mcp_tool.input_schema,
            "mcp_server": self.server_name,
            "mcp_tool": mcp_tool.name
        }

    async def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any]
    ) -> Any:
        """Execute MCP tool.

        Args:
            tool_name: Namespaced tool name
            arguments: Tool arguments

        Returns:
            Tool result
        """
        # Extract original tool name
        parts = tool_name.split("__")
        if len(parts) != 3 or parts[0] != "mcp":
            raise ValueError(f"Invalid MCP tool name: {tool_name}")

        original_name = parts[2].replace("_", "-")

        logger.info(f"Executing MCP tool: {original_name}")
        result = await self.client.call_tool(original_name, arguments)

        # Process result content
        if isinstance(result, list):
            # Combine text content
            texts = []
            for item in result:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        texts.append(item.get("text", ""))
                    elif item.get("type") == "image":
                        texts.append(f"[Image: {item.get('mimeType', 'image')}]")
                else:
                    texts.append(str(item))
            return "\n".join(texts)

        return result


class MCPToolRegistry:
    """Registry for MCP tools from all connected servers."""

    def __init__(self):
        self._tools: dict[str, dict] = {}
        self._adapters: dict[str, MCPToolAdapter] = {}

    def register_server_tools(
        self,
        adapter: MCPToolAdapter,
        tools: list[MCPTool]
    ) -> list[str]:
        """Register tools from a server.

        Args:
            adapter: Tool adapter for the server
            tools: List of MCP tools

        Returns:
            List of registered tool names
        """
        registered = []
        for tool in tools:
            name = adapter.get_tool_name(tool)
            self._tools[name] = adapter.create_tool_definition(tool)
            self._adapters[name] = adapter
            registered.append(name)
            logger.info(f"Registered MCP tool: {name}")
        return registered

    def unregister_server_tools(self, server_name: str) -> list[str]:
        """Unregister all tools from a server.

        Args:
            server_name: Server name

        Returns:
            List of unregistered tool names
        """
        prefix = f"mcp__{server_name.replace('-', '_').replace('.', '_')}__"
        unregistered = []

        for name in list(self._tools.keys()):
            if name.startswith(prefix):
                del self._tools[name]
                del self._adapters[name]
                unregistered.append(name)
                logger.info(f"Unregistered MCP tool: {name}")

        return unregistered

    def get_tool(self, name: str) -> dict | None:
        """Get tool definition by name."""
        return self._tools.get(name)

    def get_adapter(self, name: str) -> MCPToolAdapter | None:
        """Get adapter for tool."""
        return self._adapters.get(name)

    def list_tools(self) -> list[dict]:
        """List all registered tools."""
        return list(self._tools.values())

    async def execute(self, name: str, arguments: dict) -> Any:
        """Execute a tool.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result
        """
        adapter = self._adapters.get(name)
        if adapter is None:
            raise ValueError(f"Unknown MCP tool: {name}")

        return await adapter.execute(name, arguments)
```

---

## Step 5: Configuration (config.py)

```python
# src/forge/mcp/config.py
"""MCP server configuration."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


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
    cwd: str | None = None
    enabled: bool = True
    auto_connect: bool = True

    def __post_init__(self):
        """Validate configuration."""
        if self.transport == "stdio" and not self.command:
            raise ValueError(f"Server {self.name}: stdio transport requires command")
        if self.transport == "http" and not self.url:
            raise ValueError(f"Server {self.name}: http transport requires url")

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "MCPServerConfig":
        """Create from dictionary."""
        return cls(
            name=name,
            transport=data.get("transport", "stdio"),
            command=data.get("command"),
            args=data.get("args"),
            url=data.get("url"),
            headers=data.get("headers"),
            env=data.get("env"),
            cwd=data.get("cwd"),
            enabled=data.get("enabled", True),
            auto_connect=data.get("auto_connect", True)
        )


@dataclass
class MCPSettings:
    """Global MCP settings."""
    auto_connect: bool = True
    reconnect_attempts: int = 3
    reconnect_delay: int = 5
    timeout: int = 30


@dataclass
class MCPConfig:
    """Complete MCP configuration."""
    servers: dict[str, MCPServerConfig] = field(default_factory=dict)
    settings: MCPSettings = field(default_factory=MCPSettings)

    @classmethod
    def from_dict(cls, data: dict) -> "MCPConfig":
        """Create from dictionary."""
        servers = {}
        for name, server_data in data.get("servers", {}).items():
            servers[name] = MCPServerConfig.from_dict(name, server_data)

        settings_data = data.get("settings", {})
        settings = MCPSettings(
            auto_connect=settings_data.get("auto_connect", True),
            reconnect_attempts=settings_data.get("reconnect_attempts", 3),
            reconnect_delay=settings_data.get("reconnect_delay", 5),
            timeout=settings_data.get("timeout", 30)
        )

        return cls(servers=servers, settings=settings)


class MCPConfigLoader:
    """Loads MCP configuration from files."""

    DEFAULT_USER_PATH = Path.home() / ".forge" / "mcp.yaml"
    DEFAULT_PROJECT_PATH = Path(".forge") / "mcp.yaml"

    def __init__(
        self,
        user_path: Path | None = None,
        project_path: Path | None = None
    ):
        """Initialize loader.

        Args:
            user_path: Path to user config (default: ~/.src/forge/mcp.yaml)
            project_path: Path to project config (default: .src/forge/mcp.yaml)
        """
        self.user_path = user_path or self.DEFAULT_USER_PATH
        self.project_path = project_path or self.DEFAULT_PROJECT_PATH

    def load(self) -> MCPConfig:
        """Load and merge all configurations."""
        configs = []

        # Load user config
        if self.user_path.exists():
            configs.append(self.load_from_file(self.user_path))

        # Load project config (overrides user)
        if self.project_path.exists():
            configs.append(self.load_from_file(self.project_path))

        if not configs:
            return MCPConfig()

        return self.merge_configs(*configs)

    def load_from_file(self, path: Path) -> MCPConfig:
        """Load configuration from a file.

        Args:
            path: Path to config file

        Returns:
            Loaded configuration
        """
        with open(path) as f:
            data = yaml.safe_load(f) or {}

        # Expand environment variables in values
        data = self._expand_env_vars(data)

        return MCPConfig.from_dict(data)

    def merge_configs(self, *configs: MCPConfig) -> MCPConfig:
        """Merge multiple configurations.

        Later configs override earlier ones. Settings are merged field by field,
        not replaced wholesale.
        """
        merged_servers: dict[str, MCPServerConfig] = {}
        # Start with default settings
        merged_settings = MCPSettings()

        for config in configs:
            merged_servers.update(config.servers)
            # Merge settings field by field (not replace entirely)
            # Only override if the value differs from default
            if config.settings.auto_connect != MCPSettings().auto_connect:
                merged_settings.auto_connect = config.settings.auto_connect
            if config.settings.reconnect_attempts != MCPSettings().reconnect_attempts:
                merged_settings.reconnect_attempts = config.settings.reconnect_attempts
            if config.settings.reconnect_delay != MCPSettings().reconnect_delay:
                merged_settings.reconnect_delay = config.settings.reconnect_delay
            if config.settings.timeout != MCPSettings().timeout:
                merged_settings.timeout = config.settings.timeout

        return MCPConfig(servers=merged_servers, settings=merged_settings)

    def _expand_env_vars(self, data: Any) -> Any:
        """Recursively expand environment variables."""
        if isinstance(data, str):
            return os.path.expandvars(data)
        elif isinstance(data, dict):
            return {k: self._expand_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._expand_env_vars(item) for item in data]
        return data
```

---

## Step 6: Connection Manager (manager.py)

```python
# src/forge/mcp/manager.py
"""MCP connection manager."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .client import MCPClient, MCPClientError
from .config import MCPConfig, MCPConfigLoader, MCPServerConfig
from .protocol import MCPPrompt, MCPResource, MCPTool
from .tools import MCPToolAdapter, MCPToolRegistry
from .transport.base import MCPTransport
from .transport.http import HTTPTransport
from .transport.stdio import StdioTransport

logger = logging.getLogger(__name__)


@dataclass
class MCPConnection:
    """Represents a connection to an MCP server."""
    name: str
    client: MCPClient
    config: MCPServerConfig
    adapter: MCPToolAdapter
    tools: list[MCPTool]
    resources: list[MCPResource]
    prompts: list[MCPPrompt]
    connected_at: datetime


class MCPManager:
    """Manages MCP server connections."""

    _instance: "MCPManager | None" = None

    def __init__(self, config: MCPConfig | None = None):
        """Initialize manager.

        Args:
            config: MCP configuration (loads default if None)
        """
        self._config = config or MCPConfigLoader().load()
        self._connections: dict[str, MCPConnection] = {}
        self._tool_registry = MCPToolRegistry()
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "MCPManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance."""
        if cls._instance is not None:
            # Disconnect all
            asyncio.create_task(cls._instance.disconnect_all())
        cls._instance = None

    @property
    def tool_registry(self) -> MCPToolRegistry:
        """Get MCP tool registry."""
        return self._tool_registry

    def _create_transport(self, config: MCPServerConfig) -> MCPTransport:
        """Create transport for server config."""
        if config.transport == "stdio":
            return StdioTransport(
                command=config.command,
                args=config.args,
                env=config.env,
                cwd=config.cwd
            )
        elif config.transport == "http":
            return HTTPTransport(
                url=config.url,
                headers=config.headers,
                timeout=self._config.settings.timeout
            )
        else:
            raise ValueError(f"Unknown transport: {config.transport}")

    async def connect(self, server_name: str) -> MCPConnection:
        """Connect to a specific server.

        Args:
            server_name: Name of server to connect

        Returns:
            Connection object
        """
        async with self._lock:
            # Check if already connected
            if server_name in self._connections:
                return self._connections[server_name]

            # Get config
            config = self._config.servers.get(server_name)
            if config is None:
                raise ValueError(f"Unknown server: {server_name}")

            if not config.enabled:
                raise ValueError(f"Server {server_name} is disabled")

            # Create transport and client
            transport = self._create_transport(config)
            client = MCPClient(transport)

            try:
                # Connect
                server_info = await client.connect()
                logger.info(f"Connected to MCP server: {server_name}")

                # Create adapter
                adapter = MCPToolAdapter(client, server_name)

                # Discover capabilities
                tools = await client.list_tools()
                resources = await client.list_resources()
                prompts = await client.list_prompts()

                # Register tools
                self._tool_registry.register_server_tools(adapter, tools)

                # Create connection
                connection = MCPConnection(
                    name=server_name,
                    client=client,
                    config=config,
                    adapter=adapter,
                    tools=tools,
                    resources=resources,
                    prompts=prompts,
                    connected_at=datetime.now()
                )

                self._connections[server_name] = connection
                return connection

            except Exception as e:
                await client.disconnect()
                raise MCPClientError(f"Failed to connect to {server_name}: {e}")

    async def connect_all(self) -> list[MCPConnection]:
        """Connect to all enabled servers with auto_connect=True.

        Returns:
            List of successful connections
        """
        connections = []
        for name, config in self._config.servers.items():
            if config.enabled and config.auto_connect:
                try:
                    conn = await self.connect(name)
                    connections.append(conn)
                except Exception as e:
                    logger.error(f"Failed to connect to {name}: {e}")
        return connections

    async def disconnect(self, server_name: str) -> None:
        """Disconnect from a server.

        Args:
            server_name: Server to disconnect
        """
        async with self._lock:
            connection = self._connections.pop(server_name, None)
            if connection:
                # Unregister tools
                self._tool_registry.unregister_server_tools(server_name)
                # Disconnect client
                await connection.client.disconnect()
                logger.info(f"Disconnected from {server_name}")

    async def disconnect_all(self) -> None:
        """Disconnect from all servers."""
        for name in list(self._connections.keys()):
            await self.disconnect(name)

    async def reconnect(self, server_name: str) -> MCPConnection:
        """Reconnect to a server.

        Args:
            server_name: Server to reconnect

        Returns:
            New connection
        """
        await self.disconnect(server_name)
        return await self.connect(server_name)

    def get_connection(self, name: str) -> MCPConnection | None:
        """Get connection by name."""
        return self._connections.get(name)

    def list_connections(self) -> list[MCPConnection]:
        """List all connections."""
        return list(self._connections.values())

    def is_connected(self, server_name: str) -> bool:
        """Check if connected to a server."""
        conn = self._connections.get(server_name)
        return conn is not None and conn.client.is_connected

    async def reload_config(self) -> None:
        """Reload configuration and reconnect changed servers."""
        new_config = MCPConfigLoader().load()

        # Find servers to disconnect (removed or changed)
        for name in list(self._connections.keys()):
            if name not in new_config.servers:
                await self.disconnect(name)
            elif new_config.servers[name] != self._config.servers.get(name):
                await self.disconnect(name)

        # Update config
        self._config = new_config

        # Connect new/changed servers
        await self.connect_all()

    def get_all_tools(self) -> list[MCPTool]:
        """Get tools from all connections."""
        tools = []
        for conn in self._connections.values():
            tools.extend(conn.tools)
        return tools

    def get_all_resources(self) -> list[MCPResource]:
        """Get resources from all connections."""
        resources = []
        for conn in self._connections.values():
            resources.extend(conn.resources)
        return resources

    def get_all_prompts(self) -> list[MCPPrompt]:
        """Get prompts from all connections."""
        prompts = []
        for conn in self._connections.values():
            prompts.extend(conn.prompts)
        return prompts

    def get_status(self) -> dict[str, Any]:
        """Get manager status."""
        return {
            "configured_servers": len(self._config.servers),
            "connected_servers": len(self._connections),
            "total_tools": len(self._tool_registry.list_tools()),
            "total_resources": len(self.get_all_resources()),
            "total_prompts": len(self.get_all_prompts()),
            "connections": {
                name: {
                    "connected": conn.client.is_connected,
                    "tools": len(conn.tools),
                    "resources": len(conn.resources),
                    "prompts": len(conn.prompts),
                    "connected_at": conn.connected_at.isoformat()
                }
                for name, conn in self._connections.items()
            }
        }
```

---

## Step 7: Package Exports (__init__.py)

```python
# src/forge/mcp/__init__.py
"""MCP (Model Context Protocol) support for Code-Forge."""

from .client import MCPClient, MCPClientError
from .config import MCPConfig, MCPConfigLoader, MCPServerConfig, MCPSettings
from .manager import MCPConnection, MCPManager
from .protocol import (
    MCPCapabilities,
    MCPError,
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
)
from .tools import MCPToolAdapter, MCPToolRegistry
from .transport.base import MCPTransport
from .transport.http import HTTPTransport
from .transport.stdio import StdioTransport

__all__ = [
    # Protocol
    "MCPRequest",
    "MCPResponse",
    "MCPNotification",
    "MCPError",
    "MCPTool",
    "MCPResource",
    "MCPResourceTemplate",
    "MCPPrompt",
    "MCPPromptArgument",
    "MCPPromptMessage",
    "MCPCapabilities",
    "MCPServerInfo",
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
```

---

## Testing Strategy

1. **Protocol tests**: Message serialization/deserialization
2. **Transport tests**: Mock subprocess and HTTP
3. **Client tests**: Mock transport, test protocol flow
4. **Tool adapter tests**: Test namespacing and execution
5. **Config tests**: YAML parsing, environment expansion
6. **Manager tests**: Connection lifecycle, reconnection
7. **Integration tests**: Mock MCP server

---

## Notes

- MCP tools are namespaced to avoid conflicts
- All connections are async for non-blocking operation
- Configuration supports environment variable expansion
- Reconnection logic handles transient failures
- Tool registry integrates with main ToolRegistry
