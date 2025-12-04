# Phase 2.1: Tool System Foundation - UML Diagrams

**Phase:** 2.1
**Name:** Tool System Foundation
**Dependencies:** Phase 1.1, Phase 1.2, Phase 1.3

---

## 1. Class Diagram - Tool System Overview

```mermaid
classDiagram
    class BaseTool {
        <<abstract>>
        +name: str*
        +description: str*
        +category: ToolCategory*
        +parameters: List~ToolParameter~*
        +execute(context, **kwargs) ToolResult
        +validate_params(**kwargs) tuple
        +to_openai_schema() Dict
        +to_anthropic_schema() Dict
        +to_langchain_tool() Tool
        #_execute(context, **kwargs)* ToolResult
        -_check_type(value, expected) bool
    }

    class ToolRegistry {
        <<singleton>>
        -_instance: ToolRegistry
        -_tools: Dict~str,BaseTool~
        +register(tool) void
        +register_many(tools) void
        +deregister(name) bool
        +get(name) BaseTool?
        +get_or_raise(name) BaseTool
        +exists(name) bool
        +list_all() List~BaseTool~
        +list_names() List~str~
        +list_by_category(category) List~BaseTool~
        +count() int
        +clear() void
        +reset()$ void
    }

    class ToolExecutor {
        -_registry: ToolRegistry
        -_executions: List~ToolExecution~
        +execute(tool_name, context, **kwargs) ToolResult
        +get_all_schemas(format) List~Dict~
        +get_schemas_by_category(category, format) List~Dict~
        +get_executions() List~ToolExecution~
        +clear_executions() void
    }

    class ToolParameter {
        <<Value Object>>
        +name: str
        +type: str
        +description: str
        +required: bool
        +default: Any
        +enum: List~Any~?
        +min_length: int?
        +max_length: int?
        +minimum: float?
        +maximum: float?
        +to_json_schema() Dict
    }

    class ToolResult {
        <<Value Object>>
        +success: bool
        +output: Any
        +error: str?
        +duration_ms: float?
        +metadata: Dict
        +ok(output, **metadata)$ ToolResult
        +fail(error, **metadata)$ ToolResult
        +to_display() str
    }

    class ExecutionContext {
        <<Value Object>>
        +working_dir: str
        +session_id: str?
        +agent_id: str?
        +dry_run: bool
        +timeout: int
        +max_output_size: int
        +metadata: Dict
    }

    class ToolExecution {
        <<Entity>>
        +tool_name: str
        +parameters: Dict
        +context: ExecutionContext
        +result: ToolResult
        +started_at: datetime
        +completed_at: datetime
        +duration_ms: float
    }

    class ToolCategory {
        <<enumeration>>
        FILE
        EXECUTION
        WEB
        TASK
        NOTEBOOK
        MCP
        OTHER
    }

    BaseTool --> ToolParameter
    BaseTool --> ToolResult
    BaseTool --> ExecutionContext
    BaseTool --> ToolCategory
    ToolRegistry --> BaseTool
    ToolExecutor --> ToolRegistry
    ToolExecutor --> ToolExecution
    ToolExecution --> ExecutionContext
    ToolExecution --> ToolResult
```

---

## 2. Class Diagram - Concrete Tool Example

```mermaid
classDiagram
    class BaseTool {
        <<abstract>>
        +name: str*
        +description: str*
        +category: ToolCategory*
        +parameters: List~ToolParameter~*
        #_execute(context, **kwargs)* ToolResult
    }

    class ReadTool {
        +name = "Read"
        +description = "Read file contents"
        +category = FILE
        +parameters = [file_path, offset, limit]
        #_execute(context, **kwargs) ToolResult
    }

    class WriteTool {
        +name = "Write"
        +description = "Write file contents"
        +category = FILE
        +parameters = [file_path, content]
        #_execute(context, **kwargs) ToolResult
    }

    class BashTool {
        +name = "Bash"
        +description = "Execute bash command"
        +category = EXECUTION
        +parameters = [command, timeout, background]
        #_execute(context, **kwargs) ToolResult
    }

    BaseTool <|-- ReadTool
    BaseTool <|-- WriteTool
    BaseTool <|-- BashTool

    note for ReadTool "Implemented in Phase 2.2"
    note for WriteTool "Implemented in Phase 2.2"
    note for BashTool "Implemented in Phase 2.3"
```

---

## 3. Sequence Diagram - Tool Execution Flow

```mermaid
sequenceDiagram
    participant Agent
    participant Executor as ToolExecutor
    participant Registry as ToolRegistry
    participant Tool as BaseTool
    participant Logger

    Agent->>Executor: execute("Read", context, file_path="/foo")

    Executor->>Registry: get("Read")
    Registry-->>Executor: ReadTool instance

    Executor->>Logger: info("Executing tool: Read")

    Executor->>Tool: execute(context, file_path="/foo")

    Tool->>Tool: validate_params(file_path="/foo")
    alt Validation failed
        Tool-->>Executor: ToolResult.fail("Missing required param")
    else Validation passed
        Tool->>Tool: check dry_run

        alt Dry run
            Tool-->>Executor: ToolResult.ok("[Dry Run]...")
        else Normal execution
            Tool->>Tool: _execute(context, **kwargs)

            alt Timeout
                Tool-->>Executor: ToolResult.fail("Timed out")
            else Success
                Tool-->>Executor: ToolResult.ok(file_content)
            else Error
                Tool-->>Executor: ToolResult.fail(error_msg)
            end
        end
    end

    Executor->>Executor: Track execution
    Executor->>Logger: info/warning(result)
    Executor-->>Agent: ToolResult
```

---

## 4. Sequence Diagram - Schema Generation

```mermaid
sequenceDiagram
    participant LLM as LLM Client
    participant Executor as ToolExecutor
    participant Registry as ToolRegistry
    participant Tool1 as ReadTool
    participant Tool2 as WriteTool

    LLM->>Executor: get_all_schemas("openai")

    Executor->>Registry: list_all()
    Registry-->>Executor: [ReadTool, WriteTool, ...]

    loop For each tool
        Executor->>Tool1: to_openai_schema()
        Tool1-->>Executor: {"type": "function", ...}
    end

    Executor-->>LLM: [schema1, schema2, ...]

    Note over LLM: Uses schemas in<br/>tool/function calling
```

---

## 5. State Diagram - Tool Execution States

```mermaid
stateDiagram-v2
    [*] --> Received: Tool call requested

    Received --> Validating: Look up tool

    Validating --> Validated: Parameters valid
    Validating --> Failed: Validation error

    Validated --> DryRun: dry_run=true
    Validated --> Executing: dry_run=false

    DryRun --> Completed: Return dry run result

    Executing --> Completed: Execution success
    Executing --> Failed: Execution error
    Executing --> TimedOut: Timeout exceeded
    Executing --> Cancelled: Cancellation requested

    Completed --> [*]: Return success result
    Failed --> [*]: Return error result
    TimedOut --> [*]: Return timeout error
    Cancelled --> [*]: Return cancelled error
```

---

## 6. Component Diagram

```mermaid
flowchart TB
    subgraph Tools["Tool System (Phase 2.1)"]
        BASE[base.py<br/>BaseTool, Models]
        REGISTRY[registry.py<br/>ToolRegistry]
        EXECUTOR[executor.py<br/>ToolExecutor]
    end

    subgraph FutureTools["Future Tool Implementations"]
        FILE_TOOLS[Phase 2.2<br/>File Tools]
        EXEC_TOOLS[Phase 2.3<br/>Execution Tools]
        WEB_TOOLS[Phase 8.2<br/>Web Tools]
        MCP_TOOLS[Phase 8.1<br/>MCP Tools]
    end

    subgraph Consumers["Tool Consumers"]
        AGENT[Agent<br/>Phase 3.2]
        PERMS[Permissions<br/>Phase 4.1]
        HOOKS[Hooks<br/>Phase 4.2]
    end

    BASE --> REGISTRY
    BASE --> EXECUTOR
    REGISTRY --> EXECUTOR

    FILE_TOOLS --> BASE
    EXEC_TOOLS --> BASE
    WEB_TOOLS --> BASE
    MCP_TOOLS --> BASE

    EXECUTOR --> AGENT
    REGISTRY --> PERMS
    EXECUTOR --> HOOKS
```

---

## 7. Activity Diagram - Parameter Validation

```mermaid
flowchart TD
    START([validate_params]) --> LOOP{For each parameter}

    LOOP -->|Has param| CHECK_REQ{Required?}
    LOOP -->|Done| RETURN_OK[Return True, None]

    CHECK_REQ -->|Yes| CHECK_PRESENT{Provided?}
    CHECK_REQ -->|No| CHECK_IF_PROVIDED{Provided?}

    CHECK_PRESENT -->|No| RETURN_MISSING[Return False,<br/>"Missing required"]
    CHECK_PRESENT -->|Yes| VALIDATE

    CHECK_IF_PROVIDED -->|No| LOOP
    CHECK_IF_PROVIDED -->|Yes| VALIDATE

    VALIDATE --> CHECK_TYPE{Type matches?}
    CHECK_TYPE -->|No| RETURN_TYPE[Return False,<br/>"Invalid type"]
    CHECK_TYPE -->|Yes| CHECK_ENUM{Has enum?}

    CHECK_ENUM -->|No| CHECK_RANGE{Numeric range?}
    CHECK_ENUM -->|Yes| VALUE_IN_ENUM{Value in enum?}

    VALUE_IN_ENUM -->|No| RETURN_ENUM[Return False,<br/>"Invalid value"]
    VALUE_IN_ENUM -->|Yes| CHECK_RANGE

    CHECK_RANGE -->|Yes| RANGE_OK{In range?}
    CHECK_RANGE -->|No| LOOP

    RANGE_OK -->|No| RETURN_RANGE[Return False,<br/>"Out of range"]
    RANGE_OK -->|Yes| LOOP

    RETURN_OK --> END([End])
    RETURN_MISSING --> END
    RETURN_TYPE --> END
    RETURN_ENUM --> END
    RETURN_RANGE --> END
```

---

## 8. JSON Schema Output Examples

### OpenAI Format
```json
{
  "type": "function",
  "function": {
    "name": "Read",
    "description": "Read contents of a file from the filesystem",
    "parameters": {
      "type": "object",
      "properties": {
        "file_path": {
          "type": "string",
          "description": "Absolute path to the file to read"
        },
        "offset": {
          "type": "integer",
          "description": "Line number to start reading from",
          "minimum": 0
        },
        "limit": {
          "type": "integer",
          "description": "Maximum number of lines to read",
          "minimum": 1,
          "maximum": 10000
        }
      },
      "required": ["file_path"]
    }
  }
}
```

### Anthropic Format
```json
{
  "name": "Read",
  "description": "Read contents of a file from the filesystem",
  "input_schema": {
    "type": "object",
    "properties": {
      "file_path": {
        "type": "string",
        "description": "Absolute path to the file to read"
      },
      "offset": {
        "type": "integer",
        "description": "Line number to start reading from",
        "minimum": 0
      },
      "limit": {
        "type": "integer",
        "description": "Maximum number of lines to read",
        "minimum": 1,
        "maximum": 10000
      }
    },
    "required": ["file_path"]
  }
}
```

---

## 9. Package Dependency Diagram

```mermaid
flowchart TD
    subgraph phase2_1["Phase 2.1"]
        TOOLS_BASE[tools/base.py]
        TOOLS_REG[tools/registry.py]
        TOOLS_EXEC[tools/executor.py]
    end

    subgraph phase1["Earlier Phases"]
        ERRORS[core/errors.py]
        LOGGING[core/logging.py]
        INTERFACES[core/interfaces.py]
    end

    subgraph external["External"]
        PYDANTIC[pydantic]
        ASYNCIO[asyncio]
    end

    TOOLS_BASE --> ERRORS
    TOOLS_BASE --> LOGGING
    TOOLS_BASE --> INTERFACES
    TOOLS_BASE --> PYDANTIC
    TOOLS_BASE --> ASYNCIO

    TOOLS_REG --> TOOLS_BASE
    TOOLS_REG --> ERRORS
    TOOLS_REG --> LOGGING

    TOOLS_EXEC --> TOOLS_REG
    TOOLS_EXEC --> TOOLS_BASE
    TOOLS_EXEC --> LOGGING
```

---

## Notes

- All tools inherit from BaseTool
- ToolRegistry is a singleton for global tool access
- ToolExecutor wraps execution with tracking and logging
- Schema generation supports multiple LLM formats
- Parameter validation is type-safe and comprehensive
