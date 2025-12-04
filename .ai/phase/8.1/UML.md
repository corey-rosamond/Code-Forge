# Phase 8.1: MCP Protocol Support - UML Diagrams

**Phase:** 8.1
**Name:** MCP Protocol Support
**Dependencies:** Phase 2.1 (Tool System), Phase 3.2 (LangChain Integration)

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MCP PROTOCOL TYPES                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐     ┌─────────────────────────┐
│      MCPRequest         │     │      MCPResponse        │
├─────────────────────────┤     ├─────────────────────────┤
│ + id: str | int         │     │ + id: str | int         │
│ + method: str           │     │ + result: Any | None    │
│ + params: dict | None   │     │ + error: MCPError | None│
├─────────────────────────┤     ├─────────────────────────┤
│ + to_dict(): dict       │     │ + is_error: bool        │
│ + to_json(): str        │     │ + to_dict(): dict       │
└─────────────────────────┘     │ + from_dict(): cls      │
                                └─────────────────────────┘

┌─────────────────────────┐     ┌─────────────────────────┐
│    MCPNotification      │     │       MCPError          │
├─────────────────────────┤     ├─────────────────────────┤
│ + method: str           │     │ + code: int             │
│ + params: dict | None   │     │ + message: str          │
├─────────────────────────┤     │ + data: Any | None      │
│ + to_dict(): dict       │     ├─────────────────────────┤
│ + to_json(): str        │     │ + to_dict(): dict       │
└─────────────────────────┘     │ + from_dict(): cls      │
                                └─────────────────────────┘

┌─────────────────────────┐     ┌─────────────────────────┐
│        MCPTool          │     │      MCPResource        │
├─────────────────────────┤     ├─────────────────────────┤
│ + name: str             │     │ + uri: str              │
│ + description: str      │     │ + name: str             │
│ + input_schema: dict    │     │ + description: str|None │
├─────────────────────────┤     │ + mime_type: str | None │
│ + from_dict(): cls      │     ├─────────────────────────┤
└─────────────────────────┘     │ + from_dict(): cls      │
                                └─────────────────────────┘

┌─────────────────────────┐     ┌─────────────────────────┐
│       MCPPrompt         │     │   MCPCapabilities       │
├─────────────────────────┤     ├─────────────────────────┤
│ + name: str             │     │ + tools: bool           │
│ + description: str|None │     │ + resources: bool       │
│ + arguments: list|None  │     │ + prompts: bool         │
├─────────────────────────┤     │ + logging: bool         │
│ + from_dict(): cls      │     ├─────────────────────────┤
└─────────────────────────┘     │ + from_dict(): cls      │
                                └─────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                              TRANSPORT LAYER                                 │
└─────────────────────────────────────────────────────────────────────────────┘

              ┌─────────────────────────────────────┐
              │      MCPTransport <<abstract>>      │
              ├─────────────────────────────────────┤
              │                                     │
              ├─────────────────────────────────────┤
              │ + connect(): None <<async>>         │
              │ + disconnect(): None <<async>>      │
              │ + send(message): None <<async>>     │
              │ + receive(): dict <<async>>         │
              │ + is_connected: bool <<property>>   │
              └─────────────────┬───────────────────┘
                                │
                                │ implements
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│     StdioTransport        │   │      HTTPTransport        │
├───────────────────────────┤   ├───────────────────────────┤
│ + command: str            │   │ + url: str                │
│ + args: list[str]         │   │ + headers: dict           │
│ + env: dict[str, str]     │   │ + timeout: int            │
│ + cwd: str | None         │   │ - _session: ClientSession │
│ - _process: Process       │   │ - _sse_task: Task         │
│ - _read_lock: Lock        │   │ - _message_queue: Queue   │
│ - _write_lock: Lock       │   ├───────────────────────────┤
├───────────────────────────┤   │ + connect()               │
│ + connect()               │   │ + disconnect()            │
│ + disconnect()            │   │ + send(message)           │
│ + send(message)           │   │ + receive()               │
│ + receive()               │   │ - _listen_sse()           │
└───────────────────────────┘   └───────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                              MCP CLIENT                                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        MCPClient                                 │
├─────────────────────────────────────────────────────────────────┤
│ + transport: MCPTransport                                        │
│ + client_name: str                                               │
│ + client_version: str                                            │
│ - _server_info: MCPServerInfo | None                            │
│ - _pending_requests: dict[str|int, Future]                      │
│ - _receive_task: Task | None                                    │
├─────────────────────────────────────────────────────────────────┤
│ + connect(): MCPServerInfo <<async>>                            │
│ + disconnect(): None <<async>>                                  │
│ + capabilities: MCPCapabilities <<property>>                    │
│ + is_connected: bool <<property>>                               │
│                                                                  │
│ # Tool methods                                                   │
│ + list_tools(): list[MCPTool] <<async>>                         │
│ + call_tool(name, arguments): Any <<async>>                     │
│                                                                  │
│ # Resource methods                                               │
│ + list_resources(): list[MCPResource] <<async>>                 │
│ + list_resource_templates(): list[Template] <<async>>           │
│ + read_resource(uri): list[dict] <<async>>                      │
│                                                                  │
│ # Prompt methods                                                 │
│ + list_prompts(): list[MCPPrompt] <<async>>                     │
│ + get_prompt(name, args): list[Message] <<async>>               │
│                                                                  │
│ # Internal                                                       │
│ - _request(method, params): dict <<async>>                      │
│ - _notify(method, params): None <<async>>                       │
│ - _receive_loop(): None <<async>>                               │
│ - _handle_message(data): None <<async>>                         │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                              TOOL INTEGRATION                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────┐
│        MCPToolAdapter               │
├─────────────────────────────────────┤
│ + client: MCPClient                 │
│ + server_name: str                  │
├─────────────────────────────────────┤
│ + get_tool_name(tool): str          │
│ + create_tool_definition(tool): dict│
│ + execute(name, args): Any <<async>>│
└─────────────────────────────────────┘
         │
         │ uses
         ▼
┌─────────────────────────────────────┐
│       MCPToolRegistry               │
├─────────────────────────────────────┤
│ - _tools: dict[str, dict]           │
│ - _adapters: dict[str, Adapter]     │
├─────────────────────────────────────┤
│ + register_server_tools(): list[str]│
│ + unregister_server_tools(): list   │
│ + get_tool(name): dict | None       │
│ + get_adapter(name): Adapter | None │
│ + list_tools(): list[dict]          │
│ + execute(name, args): Any <<async>>│
└─────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                              CONFIGURATION                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐     ┌─────────────────────────┐
│    MCPServerConfig      │     │      MCPSettings        │
├─────────────────────────┤     ├─────────────────────────┤
│ + name: str             │     │ + auto_connect: bool    │
│ + transport: str        │     │ + reconnect_attempts: int│
│ + command: str | None   │     │ + reconnect_delay: int  │
│ + args: list[str]       │     │ + timeout: int          │
│ + url: str | None       │     └─────────────────────────┘
│ + headers: dict         │
│ + env: dict             │     ┌─────────────────────────┐
│ + cwd: str | None       │     │       MCPConfig         │
│ + enabled: bool         │     ├─────────────────────────┤
│ + auto_connect: bool    │     │ + servers: dict[Config] │
├─────────────────────────┤     │ + settings: MCPSettings │
│ + from_dict(): cls      │     ├─────────────────────────┤
└─────────────────────────┘     │ + from_dict(): cls      │
                                └─────────────────────────┘

┌─────────────────────────────────────┐
│        MCPConfigLoader              │
├─────────────────────────────────────┤
│ + user_path: Path                   │
│ + project_path: Path                │
├─────────────────────────────────────┤
│ + load(): MCPConfig                 │
│ + load_from_file(path): MCPConfig   │
│ + merge_configs(*configs): MCPConfig│
│ - _expand_env_vars(data): Any       │
└─────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONNECTION MANAGER                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────┐
│        MCPConnection                │
├─────────────────────────────────────┤
│ + name: str                         │
│ + client: MCPClient                 │
│ + config: MCPServerConfig           │
│ + adapter: MCPToolAdapter           │
│ + tools: list[MCPTool]              │
│ + resources: list[MCPResource]      │
│ + prompts: list[MCPPrompt]          │
│ + connected_at: datetime            │
└─────────────────────────────────────┘
         │
         │ managed by
         ▼
┌─────────────────────────────────────────────────────────────────┐
│               MCPManager <<singleton>>                          │
├─────────────────────────────────────────────────────────────────┤
│ - _instance: MCPManager | None                                  │
│ - _config: MCPConfig                                            │
│ - _connections: dict[str, MCPConnection]                        │
│ - _tool_registry: MCPToolRegistry                               │
│ - _lock: asyncio.Lock                                           │
├─────────────────────────────────────────────────────────────────┤
│ + get_instance(): MCPManager <<classmethod>>                    │
│ + reset_instance(): None <<classmethod>>                        │
│ + tool_registry: MCPToolRegistry <<property>>                   │
│                                                                  │
│ # Connection management                                          │
│ + connect(server_name): MCPConnection <<async>>                 │
│ + connect_all(): list[MCPConnection] <<async>>                  │
│ + disconnect(server_name): None <<async>>                       │
│ + disconnect_all(): None <<async>>                              │
│ + reconnect(server_name): MCPConnection <<async>>               │
│                                                                  │
│ # Queries                                                        │
│ + get_connection(name): MCPConnection | None                    │
│ + list_connections(): list[MCPConnection]                       │
│ + is_connected(server_name): bool                               │
│                                                                  │
│ # Aggregation                                                    │
│ + get_all_tools(): list[MCPTool]                                │
│ + get_all_resources(): list[MCPResource]                        │
│ + get_all_prompts(): list[MCPPrompt]                            │
│                                                                  │
│ # Management                                                     │
│ + reload_config(): None <<async>>                               │
│ + get_status(): dict                                            │
│                                                                  │
│ # Internal                                                       │
│ - _create_transport(config): MCPTransport                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MCP SYSTEM                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        Configuration Layer                            │  │
│  │                                                                       │  │
│  │  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐         │  │
│  │  │ ~/.src/opencode/ │     │ .src/opencode/   │     │ Environment  │         │  │
│  │  │ mcp.yaml     │     │ mcp.yaml     │     │ Variables    │         │  │
│  │  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘         │  │
│  │         │                    │                    │                  │  │
│  │         └────────────────────┼────────────────────┘                  │  │
│  │                              ▼                                       │  │
│  │                    ┌──────────────────┐                              │  │
│  │                    │  MCPConfigLoader │                              │  │
│  │                    └────────┬─────────┘                              │  │
│  └─────────────────────────────┼────────────────────────────────────────┘  │
│                                │                                           │
│                                ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        Connection Manager                             │  │
│  │                                                                       │  │
│  │                    ┌──────────────────┐                              │  │
│  │                    │    MCPManager    │                              │  │
│  │                    │   (singleton)    │                              │  │
│  │                    └────────┬─────────┘                              │  │
│  │                             │                                        │  │
│  │         ┌───────────────────┼───────────────────┐                   │  │
│  │         │                   │                   │                    │  │
│  │         ▼                   ▼                   ▼                    │  │
│  │  ┌────────────┐     ┌────────────┐     ┌────────────┐               │  │
│  │  │ Connection │     │ Connection │     │ Connection │               │  │
│  │  │  (server1) │     │  (server2) │     │  (server3) │               │  │
│  │  └─────┬──────┘     └─────┬──────┘     └─────┬──────┘               │  │
│  └────────┼──────────────────┼──────────────────┼───────────────────────┘  │
│           │                  │                  │                          │
│           ▼                  ▼                  ▼                          │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Client Layer                                  │  │
│  │                                                                       │  │
│  │   ┌──────────┐        ┌──────────┐        ┌──────────┐              │  │
│  │   │MCPClient │        │MCPClient │        │MCPClient │              │  │
│  │   └────┬─────┘        └────┬─────┘        └────┬─────┘              │  │
│  │        │                   │                   │                     │  │
│  └────────┼───────────────────┼───────────────────┼─────────────────────┘  │
│           │                   │                   │                        │
│           ▼                   ▼                   ▼                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        Transport Layer                                │  │
│  │                                                                       │  │
│  │   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐           │  │
│  │   │   Stdio     │     │   Stdio     │     │    HTTP     │           │  │
│  │   │ Transport   │     │ Transport   │     │  Transport  │           │  │
│  │   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘           │  │
│  │          │                   │                   │                   │  │
│  └──────────┼───────────────────┼───────────────────┼───────────────────┘  │
│             │                   │                   │                      │
│             ▼                   ▼                   ▼                      │
│      ┌────────────┐      ┌────────────┐      ┌────────────┐               │
│      │ MCP Server │      │ MCP Server │      │ MCP Server │               │
│      │ (subprocess)│      │ (subprocess)│      │  (remote)  │               │
│      └────────────┘      └────────────┘      └────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Sequence Diagram: MCP Server Connection

```
┌──────┐    ┌───────────┐    ┌─────────┐    ┌───────────┐    ┌───────────┐
│ App  │    │MCPManager │    │MCPClient│    │ Transport │    │MCP Server │
└──┬───┘    └─────┬─────┘    └────┬────┘    └─────┬─────┘    └─────┬─────┘
   │              │               │               │                │
   │ connect()    │               │               │                │
   │─────────────>│               │               │                │
   │              │               │               │                │
   │              │ create        │               │                │
   │              │ transport     │               │                │
   │              │───────────────────────────────>│                │
   │              │               │               │                │
   │              │ create client │               │                │
   │              │──────────────>│               │                │
   │              │               │               │                │
   │              │               │ connect()     │                │
   │              │               │──────────────>│                │
   │              │               │               │                │
   │              │               │               │ start process  │
   │              │               │               │───────────────>│
   │              │               │               │                │
   │              │               │ send initialize               │
   │              │               │──────────────>│───────────────>│
   │              │               │               │                │
   │              │               │               │    response    │
   │              │               │<──────────────│<───────────────│
   │              │               │               │                │
   │              │               │ send initialized notification  │
   │              │               │──────────────>│───────────────>│
   │              │               │               │                │
   │              │ list_tools()  │               │                │
   │              │──────────────>│               │                │
   │              │               │               │                │
   │              │               │ tools/list    │                │
   │              │               │──────────────>│───────────────>│
   │              │               │               │                │
   │              │               │    tools[]    │                │
   │              │               │<──────────────│<───────────────│
   │              │               │               │                │
   │              │ register tools│               │                │
   │              │───────────────│─────────┐     │                │
   │              │               │         │     │                │
   │              │               │<────────┘     │                │
   │              │               │               │                │
   │  connection  │               │               │                │
   │<─────────────│               │               │                │
   │              │               │               │                │
```

---

## Sequence Diagram: MCP Tool Call

```
┌──────┐    ┌──────────┐    ┌───────────────┐    ┌─────────┐    ┌───────────┐
│ LLM  │    │ToolReg   │    │MCPToolRegistry│    │MCPClient│    │MCP Server │
└──┬───┘    └────┬─────┘    └───────┬───────┘    └────┬────┘    └─────┬─────┘
   │             │                  │                 │                │
   │ call tool   │                  │                 │                │
   │ mcp__fs__   │                  │                 │                │
   │ read_file   │                  │                 │                │
   │────────────>│                  │                 │                │
   │             │                  │                 │                │
   │             │ is MCP tool?     │                 │                │
   │             │─────────┐        │                 │                │
   │             │         │        │                 │                │
   │             │<────────┘        │                 │                │
   │             │                  │                 │                │
   │             │ execute()        │                 │                │
   │             │─────────────────>│                 │                │
   │             │                  │                 │                │
   │             │                  │ get adapter     │                │
   │             │                  │─────────┐       │                │
   │             │                  │         │       │                │
   │             │                  │<────────┘       │                │
   │             │                  │                 │                │
   │             │                  │ adapter.execute │                │
   │             │                  │────────────────>│                │
   │             │                  │                 │                │
   │             │                  │                 │ tools/call     │
   │             │                  │                 │───────────────>│
   │             │                  │                 │                │
   │             │                  │                 │   result       │
   │             │                  │                 │<───────────────│
   │             │                  │                 │                │
   │             │                  │    result       │                │
   │             │                  │<────────────────│                │
   │             │                  │                 │                │
   │             │     result       │                 │                │
   │             │<─────────────────│                 │                │
   │             │                  │                 │                │
   │   result    │                  │                 │                │
   │<────────────│                  │                 │                │
   │             │                  │                 │                │
```

---

## Sequence Diagram: Resource Read

```
┌──────┐    ┌───────────┐    ┌─────────┐    ┌───────────┐
│ User │    │MCPManager │    │MCPClient│    │MCP Server │
└──┬───┘    └─────┬─────┘    └────┬────┘    └─────┬─────┘
   │              │               │               │
   │ /mcp resource│               │               │
   │ file:///path │               │               │
   │─────────────>│               │               │
   │              │               │               │
   │              │ get_connection│               │
   │              │───────┐       │               │
   │              │       │       │               │
   │              │<──────┘       │               │
   │              │               │               │
   │              │ read_resource │               │
   │              │──────────────>│               │
   │              │               │               │
   │              │               │ resources/read│
   │              │               │──────────────>│
   │              │               │               │
   │              │               │   contents[]  │
   │              │               │<──────────────│
   │              │               │               │
   │              │   contents    │               │
   │              │<──────────────│               │
   │              │               │               │
   │   contents   │               │               │
   │<─────────────│               │               │
   │              │               │               │
```

---

## State Diagram: MCP Connection Lifecycle

```
                    ┌─────────────────┐
                    │                 │
                    │  DISCONNECTED   │
                    │                 │
                    └────────┬────────┘
                             │
                             │ connect()
                             ▼
                    ┌─────────────────┐
                    │                 │
                    │  CONNECTING     │
                    │                 │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              │ success      │ failure      │
              ▼              │              ▼
    ┌─────────────────┐      │    ┌─────────────────┐
    │                 │      │    │                 │
    │  INITIALIZING   │      │    │     FAILED      │
    │                 │      │    │                 │
    └────────┬────────┘      │    └────────┬────────┘
             │               │             │
             │ initialized   │             │ retry
             ▼               │             │
    ┌─────────────────┐      │             │
    │                 │      │             │
    │   CONNECTED     │◄─────┴─────────────┘
    │                 │
    └────────┬────────┘
             │
    ┌────────┼────────┬──────────────┐
    │        │        │              │
    │ error  │ close  │ reconnect    │
    ▼        ▼        │              │
┌────────┐ ┌────────┐ │              │
│        │ │        │ │              │
│ ERROR  │ │CLOSING │ │              │
│        │ │        │ │              │
└───┬────┘ └───┬────┘ │              │
    │          │      │              │
    │ recover  │      │              │
    │          ▼      │              │
    │  ┌─────────────────┐           │
    │  │                 │           │
    └─>│  DISCONNECTED   │<──────────┘
       │                 │
       └─────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MCP DATA FLOW                                      │
└─────────────────────────────────────────────────────────────────────────────┘

                         ┌─────────────────┐
                         │   Config Files  │
                         │ ~/.src/opencode/    │
                         │ .src/opencode/      │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ MCPConfigLoader │
                         │                 │
                         │ - Parse YAML    │
                         │ - Expand vars   │
                         │ - Merge configs │
                         └────────┬────────┘
                                  │
                                  │ MCPConfig
                                  ▼
                         ┌─────────────────┐
                         │   MCPManager    │
                         │                 │
                         │ - Create conns  │
                         │ - Track state   │
                         └────────┬────────┘
                                  │
           ┌──────────────────────┼──────────────────────┐
           │                      │                      │
           ▼                      ▼                      ▼
   ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
   │  MCPClient 1  │      │  MCPClient 2  │      │  MCPClient 3  │
   └───────┬───────┘      └───────┬───────┘      └───────┬───────┘
           │                      │                      │
           ▼                      ▼                      ▼
   ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
   │StdioTransport │      │StdioTransport │      │ HTTPTransport │
   └───────┬───────┘      └───────┬───────┘      └───────┬───────┘
           │                      │                      │
           │ JSON-RPC             │ JSON-RPC             │ HTTP/SSE
           ▼                      ▼                      ▼
   ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
   │  MCP Server   │      │  MCP Server   │      │  MCP Server   │
   │ (filesystem)  │      │  (database)   │      │   (remote)    │
   └───────────────┘      └───────────────┘      └───────────────┘
           │                      │                      │
           │ Tools                │ Tools                │ Tools
           │ Resources            │ Resources            │ Resources
           │ Prompts              │ Prompts              │ Prompts
           │                      │                      │
           └──────────────────────┼──────────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │MCPToolRegistry  │
                         │                 │
                         │ Namespace tools │
                         │ Route calls     │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │  Tool System    │
                         │  (Phase 2.1)    │
                         │                 │
                         │ MCP tools       │
                         │ available to    │
                         │ LLM agents      │
                         └─────────────────┘
```

---

## Package Structure Diagram

```
src/opencode/mcp/
├── __init__.py
│   ├── MCPClient
│   ├── MCPManager
│   ├── MCPConfig
│   └── Protocol types...
│
├── protocol.py
│   ├── MCPRequest
│   ├── MCPResponse
│   ├── MCPNotification
│   ├── MCPError
│   ├── MCPTool
│   ├── MCPResource
│   ├── MCPPrompt
│   ├── MCPCapabilities
│   └── MCPServerInfo
│
├── client.py
│   ├── MCPClient
│   └── MCPClientError
│
├── transport/
│   ├── __init__.py
│   ├── base.py
│   │   └── MCPTransport (abstract)
│   ├── stdio.py
│   │   └── StdioTransport
│   └── http.py
│       └── HTTPTransport
│
├── tools.py
│   ├── MCPToolAdapter
│   └── MCPToolRegistry
│
├── resources.py
│   └── Resource handling utilities
│
├── prompts.py
│   └── Prompt handling utilities
│
├── config.py
│   ├── MCPServerConfig
│   ├── MCPSettings
│   ├── MCPConfig
│   └── MCPConfigLoader
│
└── manager.py
    ├── MCPConnection
    └── MCPManager
```

---

## Integration Points Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MCP INTEGRATION POINTS                                │
└─────────────────────────────────────────────────────────────────────────────┘

                         ┌────────────────┐
                         │   MCP System   │
                         │  (Phase 8.1)   │
                         └───────┬────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐        ┌───────────────┐        ┌───────────────┐
│ Tool System   │        │  LangChain    │        │ Configuration │
│ (Phase 2.1)   │        │ (Phase 3.2)   │        │ (Phase 1.2)   │
├───────────────┤        ├───────────────┤        ├───────────────┤
│               │        │               │        │               │
│ MCP tools     │        │ MCP tools     │        │ MCP config    │
│ registered in │        │ available to  │        │ files loaded  │
│ ToolRegistry  │        │ agents        │        │ and merged    │
│               │        │               │        │               │
│ Namespaced:   │        │ Tool binding  │        │ Env vars      │
│ mcp__srv__    │        │ with schemas  │        │ expanded      │
│ tool_name     │        │               │        │               │
└───────────────┘        └───────────────┘        └───────────────┘

        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐        ┌───────────────┐        ┌───────────────┐
│  Permission   │        │    Session    │        │ Slash Commands│
│ (Phase 4.1)   │        │ (Phase 5.1)   │        │ (Phase 6.1)   │
├───────────────┤        ├───────────────┤        ├───────────────┤
│               │        │               │        │               │
│ MCP tools use │        │ Connection    │        │ /mcp command  │
│ permission    │        │ state saved   │        │ for status    │
│ system        │        │ in session    │        │ and control   │
│               │        │               │        │               │
└───────────────┘        └───────────────┘        └───────────────┘
```

---

## Notes

- MCP uses JSON-RPC 2.0 protocol over various transports
- Tools are namespaced to prevent conflicts between servers
- Both stdio (subprocess) and HTTP/SSE transports supported
- Configuration supports environment variable expansion
- Connection manager handles reconnection automatically
- All operations are async for non-blocking behavior
