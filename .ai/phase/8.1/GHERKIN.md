# Phase 8.1: MCP Protocol Support - Gherkin Specifications

**Phase:** 8.1
**Name:** MCP Protocol Support
**Dependencies:** Phase 2.1 (Tool System), Phase 3.2 (LangChain Integration)

---

## Feature: MCP Protocol Messages

### Scenario: Create JSON-RPC request
```gherkin
Given a method "tools/list" with params {}
When I create an MCPRequest
Then request.method should be "tools/list"
And request.id should be generated
And to_dict() should return valid JSON-RPC 2.0 format
```

### Scenario: Parse JSON-RPC response
```gherkin
Given a JSON-RPC response dict with result
When I call MCPResponse.from_dict(data)
Then response.id should match the dict
And response.result should contain the data
And response.is_error should be False
```

### Scenario: Parse error response
```gherkin
Given a JSON-RPC response dict with error
When I call MCPResponse.from_dict(data)
Then response.error should be an MCPError
And response.error.code should match
And response.error.message should match
And response.is_error should be True
```

### Scenario: Create notification
```gherkin
Given a method "notifications/initialized"
When I create an MCPNotification
Then notification.id should be None
And to_dict() should not contain "id" field
```

---

## Feature: MCP Transport

### Scenario: Stdio transport connection
```gherkin
Given a StdioTransport with command "python" and args ["-m", "mcp_server"]
When I call connect()
Then subprocess should be started
And is_connected should be True
```

### Scenario: Stdio transport send/receive
```gherkin
Given a connected StdioTransport
When I send a JSON message
Then message should be written to subprocess stdin
When subprocess writes to stdout
Then receive() should return parsed JSON
```

### Scenario: Stdio transport disconnect
```gherkin
Given a connected StdioTransport
When I call disconnect()
Then subprocess should be terminated
And is_connected should be False
```

### Scenario: HTTP transport connection
```gherkin
Given an HTTPTransport with url "https://mcp.example.com"
When I call connect()
Then HTTP session should be created
And is_connected should be True
```

### Scenario: HTTP transport send
```gherkin
Given a connected HTTPTransport
When I send a JSON message
Then HTTP POST should be made to /message endpoint
And response should be queued
```

### Scenario: Transport with environment variables
```gherkin
Given environment variable DATABASE_URL="postgres://..."
And StdioTransport with env {"DB": "${DATABASE_URL}"}
When transport is created
Then env["DB"] should be expanded to "postgres://..."
```

---

## Feature: MCP Client

### Scenario: Client initialization
```gherkin
Given an MCPClient with transport
When I call connect()
Then initialize request should be sent
And initialized notification should be sent
And server_info should be populated
And capabilities should be available
```

### Scenario: List tools
```gherkin
Given a connected MCPClient
And server has tools capability
When I call list_tools()
Then tools/list request should be sent
And result should be list of MCPTool
```

### Scenario: Call tool
```gherkin
Given a connected MCPClient
And tool "read_file" exists
When I call call_tool("read_file", {"path": "/tmp/test"})
Then tools/call request should be sent
And result should be tool output
```

### Scenario: List resources
```gherkin
Given a connected MCPClient
And server has resources capability
When I call list_resources()
Then resources/list request should be sent
And result should be list of MCPResource
```

### Scenario: Read resource
```gherkin
Given a connected MCPClient
And resource "file:///tmp/test.txt" exists
When I call read_resource("file:///tmp/test.txt")
Then resources/read request should be sent
And result should be resource contents
```

### Scenario: List prompts
```gherkin
Given a connected MCPClient
And server has prompts capability
When I call list_prompts()
Then prompts/list request should be sent
And result should be list of MCPPrompt
```

### Scenario: Get prompt
```gherkin
Given a connected MCPClient
And prompt "summarize" exists
When I call get_prompt("summarize", {"length": "short"})
Then prompts/get request should be sent
And result should be list of prompt messages
```

### Scenario: Client disconnection
```gherkin
Given a connected MCPClient
When I call disconnect()
Then receive loop should be stopped
And transport should be disconnected
And is_connected should be False
```

### Scenario: Request timeout
```gherkin
Given a connected MCPClient
And server does not respond
When I call a method
And 30 seconds pass
Then MCPClientError should be raised
And error message should mention timeout
```

---

## Feature: MCP Tool Integration

### Scenario: Tool name namespacing
```gherkin
Given MCPToolAdapter for server "filesystem"
And MCP tool named "read_file"
When I call get_tool_name()
Then result should be "mcp__filesystem__read_file"
```

### Scenario: Tool registration
```gherkin
Given MCPToolRegistry
And MCPToolAdapter with 3 tools
When I call register_server_tools()
Then 3 tools should be registered
And all should be prefixed with "mcp__server__"
```

### Scenario: Tool execution routing
```gherkin
Given registered MCP tool "mcp__fs__read_file"
When I call execute("mcp__fs__read_file", {"path": "/tmp"})
Then call should be routed to correct adapter
And adapter should call MCP client
```

### Scenario: Tool unregistration
```gherkin
Given registered tools from server "filesystem"
When I call unregister_server_tools("filesystem")
Then all tools from that server should be removed
And other server tools should remain
```

---

## Feature: MCP Configuration

### Scenario: Load stdio server config
```gherkin
Given YAML config:
  """
  servers:
    filesystem:
      transport: stdio
      command: npx
      args: ["-y", "@anthropic/mcp-filesystem"]
  """
When I load the config
Then server "filesystem" should exist
And transport should be "stdio"
And command should be "npx"
```

### Scenario: Load HTTP server config
```gherkin
Given YAML config:
  """
  servers:
    remote:
      transport: http
      url: https://mcp.example.com
      headers:
        Authorization: "Bearer token"
  """
When I load the config
Then server "remote" should exist
And transport should be "http"
And url should be set
And headers should contain Authorization
```

### Scenario: Expand environment variables
```gherkin
Given YAML config with env: {"API_KEY": "${MCP_API_KEY}"}
And environment variable MCP_API_KEY="secret123"
When I load the config
Then env["API_KEY"] should be "secret123"
```

### Scenario: Merge user and project configs
```gherkin
Given user config with server "A"
And project config with server "B"
When I load merged config
Then both servers "A" and "B" should exist
```

### Scenario: Project config overrides user
```gherkin
Given user config with server "shared" using command "old"
And project config with server "shared" using command "new"
When I load merged config
Then server "shared" should use command "new"
```

### Scenario: Invalid config - missing command
```gherkin
Given config with stdio transport but no command
When I try to create MCPServerConfig
Then ValueError should be raised
And error should mention "command"
```

### Scenario: Invalid config - missing url
```gherkin
Given config with http transport but no url
When I try to create MCPServerConfig
Then ValueError should be raised
And error should mention "url"
```

---

## Feature: MCP Connection Manager

### Scenario: Get singleton instance
```gherkin
When I call MCPManager.get_instance() twice
Then I should get the same instance
```

### Scenario: Connect to server
```gherkin
Given MCPManager with config for "filesystem"
When I call connect("filesystem")
Then MCPConnection should be returned
And tools should be discovered
And connection should be tracked
```

### Scenario: Connect to all servers
```gherkin
Given MCPManager with 3 enabled servers
When I call connect_all()
Then all 3 servers should be connected
And connections should be returned
```

### Scenario: Disabled server not connected
```gherkin
Given MCPManager with server enabled=False
When I call connect_all()
Then that server should not be connected
```

### Scenario: Auto-connect disabled
```gherkin
Given MCPManager with server auto_connect=False
When I call connect_all()
Then that server should not be connected
```

### Scenario: Disconnect from server
```gherkin
Given connected server "filesystem"
When I call disconnect("filesystem")
Then client should be disconnected
And tools should be unregistered
And connection should be removed
```

### Scenario: Disconnect all servers
```gherkin
Given 3 connected servers
When I call disconnect_all()
Then all servers should be disconnected
And all tools should be unregistered
```

### Scenario: Reconnect to server
```gherkin
Given connected server "filesystem"
When I call reconnect("filesystem")
Then old connection should be closed
And new connection should be established
```

### Scenario: List connections
```gherkin
Given 2 connected servers
When I call list_connections()
Then result should have 2 MCPConnection objects
```

### Scenario: Get connection by name
```gherkin
Given connected server "filesystem"
When I call get_connection("filesystem")
Then MCPConnection should be returned
```

### Scenario: Get unknown connection
```gherkin
Given no connection to "unknown"
When I call get_connection("unknown")
Then result should be None
```

### Scenario: Check is_connected
```gherkin
Given connected server "filesystem"
When I call is_connected("filesystem")
Then result should be True

Given disconnected server "other"
When I call is_connected("other")
Then result should be False
```

### Scenario: Get all tools from connections
```gherkin
Given server A with 3 tools
And server B with 2 tools
When I call get_all_tools()
Then result should have 5 tools
```

### Scenario: Get all resources from connections
```gherkin
Given server A with 2 resources
And server B with 3 resources
When I call get_all_resources()
Then result should have 5 resources
```

### Scenario: Get manager status
```gherkin
Given 2 configured servers
And 1 connected server
When I call get_status()
Then status should show configured_servers=2
And status should show connected_servers=1
```

---

## Feature: MCP Reload

### Scenario: Reload configuration
```gherkin
Given running MCPManager
And config file is modified
When I call reload_config()
Then new config should be loaded
And changed servers should be reconnected
And unchanged servers should remain connected
```

### Scenario: Server removed from config
```gherkin
Given connected server "old"
And config file without "old"
When I call reload_config()
Then "old" should be disconnected
```

### Scenario: Server added to config
```gherkin
Given config without server "new"
And config file with server "new"
When I call reload_config()
Then "new" should be connected
```

---

## Feature: MCP Error Handling

### Scenario: Server launch failure
```gherkin
Given config with invalid command
When I try to connect
Then MCPClientError should be raised
And connection should not be stored
```

### Scenario: Server crashes during connection
```gherkin
Given server that crashes on initialize
When I try to connect
Then MCPClientError should be raised
And transport should be cleaned up
```

### Scenario: Server crashes during operation
```gherkin
Given connected server
When server crashes
Then pending requests should fail
And connection state should update
```

### Scenario: Network error on HTTP transport
```gherkin
Given HTTPTransport to unreachable server
When I try to send a message
Then connection error should be raised
```

### Scenario: Invalid JSON from server
```gherkin
Given server that sends invalid JSON
When receive() is called
Then JSON parse error should be logged
And client should handle gracefully
```

---

## Feature: MCP Commands

### Scenario: Show MCP status
```gherkin
Given 2 connected servers
When user runs "/mcp"
Then status should show connected servers
And should show tool counts
```

### Scenario: List configured servers
```gherkin
Given 3 configured servers
When user runs "/mcp servers"
Then all 3 servers should be listed
And connection status should be shown
```

### Scenario: Connect to server
```gherkin
Given disconnected server "database"
When user runs "/mcp connect database"
Then server should be connected
And success message should be shown
```

### Scenario: Disconnect from server
```gherkin
Given connected server "database"
When user runs "/mcp disconnect database"
Then server should be disconnected
And success message should be shown
```

### Scenario: List MCP tools
```gherkin
Given connected servers with tools
When user runs "/mcp tools"
Then all MCP tools should be listed
And grouped by server
```

### Scenario: List MCP resources
```gherkin
Given connected servers with resources
When user runs "/mcp resources"
Then all MCP resources should be listed
```

### Scenario: Reload MCP configuration
```gherkin
Given modified config file
When user runs "/mcp reload"
Then config should be reloaded
And affected connections should update
```

---

## Feature: MCP Tool Permissions

### Scenario: MCP tool requires permission
```gherkin
Given MCP tool "mcp__fs__write_file"
And permission mode is "ask"
When tool is called
Then permission should be requested
```

### Scenario: MCP tool allowed
```gherkin
Given MCP tool with allow rule
When tool is called
Then tool should execute without asking
```

### Scenario: MCP tool denied
```gherkin
Given MCP tool with deny rule
When tool is called
Then tool should be blocked
And error should be returned
```

---

## Feature: MCP Capabilities

### Scenario: Server without tools capability
```gherkin
Given server that doesn't support tools
When I call list_tools()
Then empty list should be returned
And no request should be sent
```

### Scenario: Server without resources capability
```gherkin
Given server that doesn't support resources
When I call list_resources()
Then empty list should be returned
And no request should be sent
```

### Scenario: Server without prompts capability
```gherkin
Given server that doesn't support prompts
When I call list_prompts()
Then empty list should be returned
And no request should be sent
```

---

## Feature: MCP Integration

### Scenario: MCP tools available to LLM
```gherkin
Given connected MCP server with tools
When LLM requests tool list
Then MCP tools should be included
And should have proper schemas
```

### Scenario: LLM calls MCP tool
```gherkin
Given LLM wants to call "mcp__fs__read_file"
When tool execution is requested
Then call should be routed to MCP server
And result should be returned to LLM
```

### Scenario: Session saves MCP state
```gherkin
Given active MCP connections
When session is saved
Then connection state should be persisted
```

### Scenario: Session restores MCP connections
```gherkin
Given saved session with MCP connections
When session is resumed
Then MCP servers should reconnect
```
