# Phase 8.1: MCP Protocol Support - Completion Criteria

**Phase:** 8.1
**Name:** MCP Protocol Support
**Dependencies:** Phase 2.1 (Tool System), Phase 3.2 (LangChain Integration)

---

## Completion Checklist

### 1. Protocol Types (protocol.py)

- [ ] `MCPError` dataclass implemented
  - [ ] `code: int`
  - [ ] `message: str`
  - [ ] `data: Any | None`
  - [ ] `to_dict()` method
  - [ ] `from_dict()` class method
  - [ ] Standard error code constants

- [ ] `MCPRequest` dataclass implemented
  - [ ] `id: str | int | None`
  - [ ] `method: str`
  - [ ] `params: dict | None`
  - [ ] `to_dict()` method
  - [ ] `to_json()` method

- [ ] `MCPResponse` dataclass implemented
  - [ ] `id: str | int`
  - [ ] `result: Any | None`
  - [ ] `error: MCPError | None`
  - [ ] `is_error` property
  - [ ] `to_dict()` method
  - [ ] `from_dict()` class method

- [ ] `MCPNotification` dataclass implemented
  - [ ] `method: str`
  - [ ] `params: dict | None`
  - [ ] `to_dict()` method
  - [ ] `to_json()` method

- [ ] `MCPTool` dataclass implemented
  - [ ] `name: str`
  - [ ] `description: str`
  - [ ] `input_schema: dict`
  - [ ] `from_dict()` class method

- [ ] `MCPResource` dataclass implemented
  - [ ] `uri: str`
  - [ ] `name: str`
  - [ ] `description: str | None`
  - [ ] `mime_type: str | None`
  - [ ] `from_dict()` class method

- [ ] `MCPPrompt` dataclass implemented
  - [ ] `name: str`
  - [ ] `description: str | None`
  - [ ] `arguments: list | None`
  - [ ] `from_dict()` class method

- [ ] `MCPCapabilities` dataclass implemented
  - [ ] `tools: bool`
  - [ ] `resources: bool`
  - [ ] `prompts: bool`
  - [ ] `from_dict()` class method

- [ ] `MCPServerInfo` dataclass implemented
  - [ ] `name: str`
  - [ ] `version: str`
  - [ ] `capabilities: MCPCapabilities`
  - [ ] `from_dict()` class method

- [ ] `parse_message()` function
  - [ ] Parses requests, responses, notifications
  - [ ] Handles invalid messages

### 2. Transport Layer (transport/)

- [ ] `MCPTransport` abstract base class
  - [ ] `connect()` async method
  - [ ] `disconnect()` async method
  - [ ] `send(message)` async method
  - [ ] `receive()` async method
  - [ ] `is_connected` property

- [ ] `StdioTransport` class implemented
  - [ ] `command: str`
  - [ ] `args: list[str]`
  - [ ] `env: dict[str, str]`
  - [ ] `cwd: str | None`
  - [ ] Subprocess management
  - [ ] JSON line protocol
  - [ ] Proper cleanup on disconnect

- [ ] `HTTPTransport` class implemented
  - [ ] `url: str`
  - [ ] `headers: dict`
  - [ ] `timeout: int`
  - [ ] HTTP POST for requests
  - [ ] SSE for notifications
  - [ ] Proper session management

### 3. MCP Client (client.py)

- [ ] `MCPClient` class implemented
  - [ ] `transport: MCPTransport`
  - [ ] `client_name: str`
  - [ ] `client_version: str`
  - [ ] `_server_info: MCPServerInfo | None`
  - [ ] `_pending_requests: dict`

- [ ] Connection lifecycle
  - [ ] `connect()` sends initialize and initialized
  - [ ] `disconnect()` cleans up properly
  - [ ] `is_connected` property
  - [ ] `capabilities` property

- [ ] Tool methods
  - [ ] `list_tools()` returns list[MCPTool]
  - [ ] `call_tool(name, arguments)` executes tool

- [ ] Resource methods
  - [ ] `list_resources()` returns list[MCPResource]
  - [ ] `list_resource_templates()` returns list
  - [ ] `read_resource(uri)` returns contents

- [ ] Prompt methods
  - [ ] `list_prompts()` returns list[MCPPrompt]
  - [ ] `get_prompt(name, arguments)` returns messages

- [ ] Internal methods
  - [ ] `_request()` sends request and waits
  - [ ] `_notify()` sends notification
  - [ ] `_receive_loop()` processes messages
  - [ ] `_handle_message()` dispatches messages

- [ ] Error handling
  - [ ] Request timeout
  - [ ] Server errors
  - [ ] Connection errors

### 4. Tool Integration (tools.py)

- [ ] `MCPToolAdapter` class implemented
  - [ ] `client: MCPClient`
  - [ ] `server_name: str`
  - [ ] `get_tool_name()` returns namespaced name
  - [ ] `create_tool_definition()` returns dict
  - [ ] `execute()` calls MCP tool

- [ ] `MCPToolRegistry` class implemented
  - [ ] `_tools: dict[str, dict]`
  - [ ] `_adapters: dict[str, MCPToolAdapter]`
  - [ ] `register_server_tools()` registers tools
  - [ ] `unregister_server_tools()` removes tools
  - [ ] `get_tool()` returns definition
  - [ ] `get_adapter()` returns adapter
  - [ ] `list_tools()` returns all tools
  - [ ] `execute()` routes to adapter

### 5. Configuration (config.py)

- [ ] `MCPServerConfig` dataclass implemented
  - [ ] `name: str`
  - [ ] `transport: str`
  - [ ] `command: str | None`
  - [ ] `args: list[str] | None`
  - [ ] `url: str | None`
  - [ ] `headers: dict | None`
  - [ ] `env: dict | None`
  - [ ] `cwd: str | None`
  - [ ] `enabled: bool`
  - [ ] `auto_connect: bool`
  - [ ] Validation in `__post_init__`
  - [ ] `from_dict()` class method

- [ ] `MCPSettings` dataclass implemented
  - [ ] `auto_connect: bool`
  - [ ] `reconnect_attempts: int`
  - [ ] `reconnect_delay: int`
  - [ ] `timeout: int`

- [ ] `MCPConfig` dataclass implemented
  - [ ] `servers: dict[str, MCPServerConfig]`
  - [ ] `settings: MCPSettings`
  - [ ] `from_dict()` class method

- [ ] `MCPConfigLoader` class implemented
  - [ ] `user_path: Path`
  - [ ] `project_path: Path`
  - [ ] `load()` loads and merges configs
  - [ ] `load_from_file()` loads single file
  - [ ] `merge_configs()` merges configs
  - [ ] `_expand_env_vars()` expands variables

### 6. Connection Manager (manager.py)

- [ ] `MCPConnection` dataclass implemented
  - [ ] `name: str`
  - [ ] `client: MCPClient`
  - [ ] `config: MCPServerConfig`
  - [ ] `adapter: MCPToolAdapter`
  - [ ] `tools: list[MCPTool]`
  - [ ] `resources: list[MCPResource]`
  - [ ] `prompts: list[MCPPrompt]`
  - [ ] `connected_at: datetime`

- [ ] `MCPManager` singleton implemented
  - [ ] `_instance` class variable
  - [ ] `_config: MCPConfig`
  - [ ] `_connections: dict`
  - [ ] `_tool_registry: MCPToolRegistry`
  - [ ] `get_instance()` class method
  - [ ] `reset_instance()` class method

- [ ] Connection management
  - [ ] `connect(server_name)` connects to server
  - [ ] `connect_all()` connects all enabled
  - [ ] `disconnect(server_name)` disconnects
  - [ ] `disconnect_all()` disconnects all
  - [ ] `reconnect(server_name)` reconnects

- [ ] Queries
  - [ ] `get_connection(name)` returns connection
  - [ ] `list_connections()` returns list
  - [ ] `is_connected(server_name)` checks status

- [ ] Aggregation
  - [ ] `get_all_tools()` from all connections
  - [ ] `get_all_resources()` from all connections
  - [ ] `get_all_prompts()` from all connections

- [ ] Management
  - [ ] `reload_config()` reloads and reconnects
  - [ ] `get_status()` returns status dict
  - [ ] `_create_transport()` creates transport

### 7. Package Exports (__init__.py)

- [ ] All protocol types exported
- [ ] Transport classes exported
- [ ] MCPClient exported
- [ ] Tool classes exported
- [ ] Config classes exported
- [ ] Manager classes exported
- [ ] `__all__` list complete

### 8. Integration Points

- [ ] Tool system integration
  - [ ] MCP tools registered in ToolRegistry
  - [ ] Namespaced properly
  - [ ] Tool calls routed to MCP

- [ ] LangChain integration
  - [ ] MCP tools available to agents
  - [ ] Tool schemas correct

- [ ] Permission system integration
  - [ ] MCP tools respect permissions
  - [ ] Permission checks applied

- [ ] Session integration
  - [ ] Connection state saved
  - [ ] Connections restored on resume

### 9. Testing

- [ ] Unit tests for protocol types
- [ ] Unit tests for StdioTransport (with mock)
- [ ] Unit tests for HTTPTransport (with mock)
- [ ] Unit tests for MCPClient (with mock transport)
- [ ] Unit tests for MCPToolAdapter
- [ ] Unit tests for MCPToolRegistry
- [ ] Unit tests for MCPConfigLoader
- [ ] Unit tests for MCPManager
- [ ] Integration tests with mock server
- [ ] Test coverage ≥ 90%

### 10. Code Quality

- [ ] McCabe complexity ≤ 10 for all functions
- [ ] Type hints on all public methods
- [ ] Docstrings on all public classes/methods
- [ ] No circular imports
- [ ] Follows project code style

---

## Verification Commands

```bash
# Run unit tests
pytest tests/mcp/ -v

# Run with coverage
pytest tests/mcp/ --cov=src/opencode/mcp --cov-report=term-missing

# Check coverage threshold
pytest tests/mcp/ --cov=src/opencode/mcp --cov-fail-under=90

# Type checking
mypy src/opencode/mcp/

# Complexity check
flake8 src/opencode/mcp/ --max-complexity=10
```

---

## Test Scenarios

### Protocol Tests

```python
def test_mcp_request_serialization():
    request = MCPRequest(method="tools/list", params={})
    data = request.to_dict()
    assert data["jsonrpc"] == "2.0"
    assert data["method"] == "tools/list"
    assert "id" in data

def test_mcp_response_parsing():
    data = {"jsonrpc": "2.0", "id": "123", "result": {"tools": []}}
    response = MCPResponse.from_dict(data)
    assert response.id == "123"
    assert response.result == {"tools": []}
    assert not response.is_error
```

### Transport Tests

```python
async def test_stdio_transport_connect():
    transport = StdioTransport(
        command="echo",
        args=["test"]
    )
    await transport.connect()
    assert transport.is_connected
    await transport.disconnect()
    assert not transport.is_connected

async def test_stdio_transport_send_receive(mock_process):
    transport = StdioTransport(command="mock")
    await transport.connect()

    await transport.send({"method": "test"})
    mock_process.stdin.write.assert_called()

    mock_process.stdout.readline.return_value = b'{"result": "ok"}\n'
    response = await transport.receive()
    assert response == {"result": "ok"}
```

### Client Tests

```python
async def test_client_connect(mock_transport):
    client = MCPClient(mock_transport)

    # Mock initialize response
    mock_transport.receive.return_value = {
        "jsonrpc": "2.0",
        "id": "1",
        "result": {
            "serverInfo": {"name": "test", "version": "1.0"},
            "capabilities": {"tools": {}}
        }
    }

    server_info = await client.connect()
    assert server_info.name == "test"
    assert client.capabilities.tools

async def test_client_list_tools(connected_client):
    connected_client.transport.receive.return_value = {
        "id": "2",
        "result": {"tools": [{"name": "test_tool", "description": "Test"}]}
    }

    tools = await connected_client.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "test_tool"
```

### Manager Tests

```python
async def test_manager_connect(mock_config):
    manager = MCPManager(mock_config)
    connection = await manager.connect("test-server")

    assert connection.name == "test-server"
    assert "test-server" in manager._connections

async def test_manager_disconnect(connected_manager):
    await connected_manager.disconnect("test-server")

    assert "test-server" not in connected_manager._connections
    assert connected_manager.tool_registry.get_tool("mcp__test__tool") is None

async def test_manager_reload_config(manager, tmp_path):
    # Modify config file
    new_config = tmp_path / "mcp.yaml"
    new_config.write_text("servers:\n  new-server:\n    ...")

    await manager.reload_config()
    # Assert new server connected
```

---

## Definition of Done

Phase 8.1 is complete when:

1. All checklist items are checked off
2. All unit tests pass
3. Test coverage is ≥ 90%
4. Code complexity is ≤ 10
5. Type checking passes with no errors
6. Stdio transport works with subprocess MCP servers
7. HTTP transport works with remote MCP servers
8. MCP tools are registered and callable
9. Resources can be read
10. Prompts can be retrieved
11. Configuration loads and merges correctly
12. Environment variables expand properly
13. Connection manager handles multiple servers
14. Reconnection logic works
15. Hot reload functions correctly
16. Documentation is complete
17. Code review approved

---

## Dependencies Verification

Before starting Phase 8.1, verify:

- [ ] Phase 2.1 (Tool System) is complete
  - [ ] ToolRegistry available
  - [ ] Tool interface defined
  - [ ] Tools can be registered dynamically

- [ ] Phase 3.2 (LangChain Integration) is complete
  - [ ] LLM can call tools
  - [ ] Tool binding works

- [ ] Phase 1.2 (Configuration) is complete
  - [ ] YAML config loading works
  - [ ] Environment variable expansion works

---

## Notes

- MCP is Model Context Protocol - open standard for AI tool integration
- JSON-RPC 2.0 is the message format
- Stdio transport runs MCP servers as subprocesses
- HTTP transport connects to remote MCP servers
- Tools are namespaced to avoid conflicts
- All operations are async for non-blocking behavior
- Configuration supports multiple sources and merging
- Reconnection handles transient failures gracefully
