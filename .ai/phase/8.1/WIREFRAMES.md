# Phase 8.1: MCP Protocol Support - Wireframes & Usage Examples

**Phase:** 8.1
**Name:** MCP Protocol Support
**Dependencies:** Phase 2.1 (Tool System), Phase 3.2 (LangChain Integration)

---

## 1. MCP Status Display

### Show MCP Status

```
You: /mcp

MCP Status
═══════════════════════════════════════════════════

Configured Servers: 3
Connected Servers:  2

Connections:
  ✓ filesystem     Connected (5 tools, 0 resources)
                   Connected 10 minutes ago

  ✓ database       Connected (8 tools, 2 resources)
                   Connected 10 minutes ago

  ✗ remote-api     Disconnected (disabled)

Total MCP Tools: 13
Total Resources: 2
Total Prompts:   0
```

### Detailed Status

```
You: /mcp status --verbose

MCP Detailed Status
═══════════════════════════════════════════════════

Server: filesystem
  Transport: stdio
  Command:   npx -y @anthropic/mcp-filesystem /home/user
  Status:    Connected
  PID:       12345
  Uptime:    10m 23s

  Capabilities:
    ✓ Tools
    ✗ Resources
    ✗ Prompts

  Tools (5):
    • mcp__filesystem__read_file
    • mcp__filesystem__write_file
    • mcp__filesystem__list_directory
    • mcp__filesystem__create_directory
    • mcp__filesystem__delete_file

───────────────────────────────────────────────────

Server: database
  Transport: stdio
  Command:   python -m mcp_postgres
  Status:    Connected
  PID:       12346
  Uptime:    10m 22s

  Capabilities:
    ✓ Tools
    ✓ Resources
    ✗ Prompts

  Tools (8):
    • mcp__database__query
    • mcp__database__execute
    • mcp__database__list_tables
    • mcp__database__describe_table
    • mcp__database__list_schemas
    • mcp__database__get_indexes
    • mcp__database__explain_query
    • mcp__database__get_stats

  Resources (2):
    • postgres://localhost/mydb/schema
    • postgres://localhost/mydb/tables
```

---

## 2. Server Management

### List Configured Servers

```
You: /mcp servers

MCP Servers
═══════════════════════════════════════════════════

Name          Transport  Status       Auto-Connect
──────────────────────────────────────────────────
filesystem    stdio      Connected    Yes
database      stdio      Connected    Yes
remote-api    http       Disabled     No

Use /mcp connect <name> to connect
Use /mcp disconnect <name> to disconnect
```

### Connect to Server

```
You: /mcp connect remote-api

Connecting to remote-api...

Initializing connection to https://api.example.com/mcp
  ✓ Transport established
  ✓ Protocol initialized
  ✓ Capabilities negotiated

Server: remote-api (v2.1.0)
Capabilities: Tools, Prompts

Discovered:
  • 4 tools
  • 0 resources
  • 3 prompts

Connection successful!
```

### Disconnect from Server

```
You: /mcp disconnect database

Disconnecting from database...

  ✓ Unregistered 8 tools
  ✓ Transport closed

Server database disconnected.
```

---

## 3. MCP Tools

### List MCP Tools

```
You: /mcp tools

MCP Tools (13 total)
═══════════════════════════════════════════════════

filesystem (5 tools):
  mcp__filesystem__read_file
    Read contents of a file
    Parameters: path (string, required)

  mcp__filesystem__write_file
    Write contents to a file
    Parameters: path (string), content (string)

  mcp__filesystem__list_directory
    List files in a directory
    Parameters: path (string)

  mcp__filesystem__create_directory
    Create a new directory
    Parameters: path (string)

  mcp__filesystem__delete_file
    Delete a file
    Parameters: path (string)

database (8 tools):
  mcp__database__query
    Execute a SELECT query
    Parameters: sql (string), params (array)

  mcp__database__execute
    Execute an INSERT/UPDATE/DELETE
    Parameters: sql (string), params (array)

  ... (6 more)
```

### Tool Details

```
You: /mcp tools mcp__database__query

Tool: mcp__database__query
═══════════════════════════════════════════════════

Server:      database
Description: Execute a SELECT query and return results

Parameters:
  sql (string, required)
    The SQL query to execute

  params (array, optional)
    Query parameters for prepared statement

  limit (integer, optional, default: 100)
    Maximum rows to return

Returns:
  Object with columns and rows

Example:
  {
    "sql": "SELECT * FROM users WHERE id = $1",
    "params": [123],
    "limit": 10
  }
```

---

## 4. MCP Resources

### List Resources

```
You: /mcp resources

MCP Resources (2 total)
═══════════════════════════════════════════════════

database:
  postgres://localhost/mydb/schema
    Type: application/json
    Description: Database schema information

  postgres://localhost/mydb/tables
    Type: application/json
    Description: List of all tables

Use: /mcp read <uri> to read a resource
```

### Read Resource

```
You: /mcp read postgres://localhost/mydb/schema

Reading resource: postgres://localhost/mydb/schema

{
  "database": "mydb",
  "schemas": [
    {
      "name": "public",
      "tables": [
        {
          "name": "users",
          "columns": [
            {"name": "id", "type": "integer", "primary": true},
            {"name": "email", "type": "varchar(255)"},
            {"name": "created_at", "type": "timestamp"}
          ]
        },
        {
          "name": "orders",
          "columns": [...]
        }
      ]
    }
  ]
}
```

---

## 5. MCP Prompts

### List Prompts

```
You: /mcp prompts

MCP Prompts (3 total)
═══════════════════════════════════════════════════

remote-api:
  summarize
    Summarize content with specified length
    Arguments: content (required), length (optional)

  translate
    Translate text to another language
    Arguments: text (required), target_language (required)

  code_review
    Review code for issues
    Arguments: code (required), language (optional)

Use: /mcp prompt <name> to get a prompt
```

### Get Prompt

```
You: /mcp prompt code_review --code "def foo(): pass" --language python

Getting prompt: code_review

Messages:
  [system]
  You are a code reviewer. Analyze the following Python code
  for potential issues, style problems, and improvements.

  [user]
  ```python
  def foo(): pass
  ```

  Please review this code and provide feedback on:
  1. Code quality
  2. Potential bugs
  3. Style improvements
  4. Best practices
```

---

## 6. MCP in Action

### Using MCP Tools with LLM

```
You: Read the contents of /tmp/example.txt using the filesystem MCP

I'll use the MCP filesystem tool to read that file.

[Calling mcp__filesystem__read_file with path="/tmp/example.txt"]

The file contains:

```
Hello, this is example content.
Line 2 of the file.
Line 3 with some data.
```

Would you like me to do anything with this content?
```

### Database Query via MCP

```
You: Show me the top 5 users by order count

I'll query the database using the MCP database tool.

[Calling mcp__database__query]

Here are the top 5 users by order count:

| User ID | Email               | Order Count |
|---------|---------------------|-------------|
| 42      | power@user.com      | 156         |
| 17      | frequent@buyer.com  | 143         |
| 89      | loyal@customer.com  | 128         |
| 23      | regular@shopper.com | 115         |
| 56      | active@member.com   | 98          |

Would you like more details about any of these users?
```

---

## 7. Configuration Examples

### Basic Configuration File

```yaml
# ~/.src/forge/mcp.yaml

servers:
  # Local filesystem access
  filesystem:
    transport: stdio
    command: npx
    args:
      - -y
      - "@anthropic/mcp-filesystem"
      - /home/user/projects

  # PostgreSQL database
  database:
    transport: stdio
    command: python
    args:
      - -m
      - mcp_postgres
    env:
      DATABASE_URL: "${DATABASE_URL}"

settings:
  auto_connect: true
  timeout: 30
```

### Advanced Configuration

```yaml
# .src/forge/mcp.yaml (project-specific)

servers:
  # Project database (overrides user config)
  database:
    transport: stdio
    command: python
    args:
      - -m
      - mcp_postgres
    env:
      DATABASE_URL: "postgres://localhost/project_db"
    auto_connect: true

  # Remote API service
  api-service:
    transport: http
    url: https://mcp.internal.company.com/api
    headers:
      Authorization: "Bearer ${API_TOKEN}"
      X-Project-ID: "project-123"
    timeout: 60
    enabled: true
    auto_connect: false

  # Development tools
  dev-tools:
    transport: stdio
    command: node
    args:
      - ./scripts/mcp-dev-server.js
    cwd: /home/user/projects/current
    enabled: "${DEV_MODE:-false}"

settings:
  auto_connect: true
  reconnect_attempts: 3
  reconnect_delay: 5
  timeout: 30
```

---

## 8. Error Handling

### Connection Failure

```
You: /mcp connect broken-server

Connecting to broken-server...

Error: Failed to connect to broken-server

Details:
  Command: /invalid/path/to/server
  Error: spawn /invalid/path/to/server ENOENT

The server command could not be found. Please check:
  1. The command path is correct
  2. Required dependencies are installed
  3. The command has execute permissions

Use /mcp servers to see configuration.
```

### Server Crash

```
[MCP] Warning: Server 'database' disconnected unexpectedly

Connection lost to database server.
Reason: Process exited with code 1

Attempting reconnection (1/3)...
  ✗ Failed: Connection refused

Attempting reconnection (2/3)...
  ✗ Failed: Connection refused

Attempting reconnection (3/3)...
  ✓ Reconnected successfully

Server database is back online.
```

### Tool Execution Error

```
You: Delete all files in /important-data using filesystem MCP

[Calling mcp__filesystem__delete_file]

Error from MCP server:

  Server: filesystem
  Tool:   delete_file
  Error:  Access denied: /important-data is outside allowed directory

The filesystem MCP server only allows access to:
  /home/user/projects

Would you like to try a different path?
```

---

## 9. Reload Configuration

### Reload Success

```
You: /mcp reload

Reloading MCP configuration...

Changes detected:
  • Server 'new-server' added
  • Server 'database' configuration changed
  • Server 'old-server' removed

Applying changes:
  ✓ Disconnected from old-server
  ✓ Reconnected to database
  ✓ Connected to new-server

Configuration reloaded successfully.

Current status:
  3 servers configured
  3 servers connected
```

### No Changes

```
You: /mcp reload

Reloading MCP configuration...

No configuration changes detected.
All connections remain active.
```

---

## 10. Integration with Tool System

### MCP Tools in Tool List

```
You: /tools

Available Tools (25 total)
═══════════════════════════════════════════════════

Built-in Tools:
  read          Read file contents
  write         Write file contents
  edit          Edit file contents
  glob          Find files by pattern
  grep          Search file contents
  bash          Execute shell commands
  ...

MCP Tools (13):
  mcp__filesystem__read_file      [filesystem]
  mcp__filesystem__write_file     [filesystem]
  mcp__filesystem__list_directory [filesystem]
  mcp__database__query            [database]
  mcp__database__execute          [database]
  ...

Use /tools <name> for details.
```

---

## 11. Session Integration

### Startup with MCP

```
$ forge

Code-Forge v1.0.0

Loading configuration...
  ✓ Settings loaded
  ✓ Tools registered

Connecting MCP servers...
  ✓ filesystem (5 tools)
  ✓ database (8 tools)
  ✗ remote-api (connection timeout)

Ready. Type /help for commands.

forge>
```

### Session Resume with MCP

```
$ forge --resume

Resuming session: abc123...

Restoring state...
  ✓ Conversation history loaded
  ✓ Context restored

Reconnecting MCP servers...
  ✓ filesystem (5 tools)
  ✓ database (8 tools)

Session resumed. 15 messages in history.

forge>
```

---

## Notes

- MCP tools are prefixed with `mcp__<server>__` for namespacing
- All MCP operations are async and non-blocking
- Configuration supports environment variable expansion
- Auto-reconnection handles transient failures
- Permissions system applies to MCP tools
- Session saves connection state for resume
