# Phase 2.1: Tool System Foundation - Gherkin Specifications

**Phase:** 2.1
**Name:** Tool System Foundation
**Dependencies:** Phase 1.1 (Project Foundation), Phase 1.2 (Configuration), Phase 1.3 (REPL)

---

## Feature: Tool Parameter Definition

### Scenario: Define simple string parameter
```gherkin
Given I am creating a tool parameter
When I define a parameter with:
  | name        | file_path                          |
  | type        | string                             |
  | description | Absolute path to the file to read  |
  | required    | true                               |
Then the parameter should be valid
And to_json_schema() should return:
  """json
  {
    "type": "string",
    "description": "Absolute path to the file to read"
  }
  """
```

### Scenario: Define parameter with enum constraint
```gherkin
Given I am creating a tool parameter
When I define a parameter with:
  | name        | format                    |
  | type        | string                    |
  | description | Output format             |
  | required    | false                     |
  | default     | openai                    |
  | enum        | ["openai", "anthropic"]   |
Then the parameter should be valid
And to_json_schema() should return:
  """json
  {
    "type": "string",
    "description": "Output format",
    "default": "openai",
    "enum": ["openai", "anthropic"]
  }
  """
```

### Scenario: Define parameter with numeric constraints
```gherkin
Given I am creating a tool parameter
When I define a parameter with:
  | name        | timeout                          |
  | type        | integer                          |
  | description | Execution timeout in seconds     |
  | required    | false                            |
  | default     | 120                              |
  | minimum     | 1                                |
  | maximum     | 600                              |
Then the parameter should be valid
And to_json_schema() should return:
  """json
  {
    "type": "integer",
    "description": "Execution timeout in seconds",
    "default": 120,
    "minimum": 1,
    "maximum": 600
  }
  """
```

### Scenario: Define parameter with string length constraints
```gherkin
Given I am creating a tool parameter
When I define a parameter with:
  | name        | content                          |
  | type        | string                           |
  | description | File content to write            |
  | required    | true                             |
  | min_length  | 1                                |
  | max_length  | 1000000                          |
Then the parameter should be valid
And to_json_schema() should include minLength and maxLength
```

---

## Feature: Tool Result Creation

### Scenario: Create successful result
```gherkin
Given I need to return a tool result
When I call ToolResult.ok("file content here")
Then result.success should be true
And result.output should be "file content here"
And result.error should be None
```

### Scenario: Create successful result with metadata
```gherkin
Given I need to return a tool result with metrics
When I call ToolResult.ok("output", lines=100, bytes=5000)
Then result.success should be true
And result.output should be "output"
And result.metadata should contain {"lines": 100, "bytes": 5000}
```

### Scenario: Create failed result
```gherkin
Given a tool execution has failed
When I call ToolResult.fail("File not found: /foo/bar")
Then result.success should be false
And result.error should be "File not found: /foo/bar"
And result.output should be None
```

### Scenario: Create failed result with metadata
```gherkin
Given a tool execution has failed with context
When I call ToolResult.fail("Permission denied", path="/etc/shadow", errno=13)
Then result.success should be false
And result.error should be "Permission denied"
And result.metadata should contain {"path": "/etc/shadow", "errno": 13}
```

### Scenario: Convert result to display string
```gherkin
Given a successful tool result with output "Hello World"
When I call result.to_display()
Then the return value should be "Hello World"

Given a failed tool result with error "Something went wrong"
When I call result.to_display()
Then the return value should be "Error: Something went wrong"
```

---

## Feature: Execution Context

### Scenario: Create default execution context
```gherkin
Given I need an execution context
When I create ExecutionContext(working_dir="/home/user/project")
Then context.working_dir should be "/home/user/project"
And context.session_id should be None
And context.agent_id should be None
And context.dry_run should be false
And context.timeout should be 120
And context.max_output_size should be 100000
And context.metadata should be an empty dict
```

### Scenario: Create execution context with all options
```gherkin
Given I need a fully configured execution context
When I create ExecutionContext with:
  | working_dir     | /home/user/project  |
  | session_id      | sess_abc123         |
  | agent_id        | agent_001           |
  | dry_run         | true                |
  | timeout         | 60                  |
  | max_output_size | 50000               |
Then all properties should match the provided values
```

---

## Feature: Tool Category

### Scenario Outline: Tool categories are defined
```gherkin
Given the ToolCategory enum exists
Then it should have value "<category>"
And the value should be "<string_value>"

Examples:
  | category   | string_value |
  | FILE       | file         |
  | EXECUTION  | execution    |
  | WEB        | web          |
  | TASK       | task         |
  | NOTEBOOK   | notebook     |
  | MCP        | mcp          |
  | OTHER      | other        |
```

---

## Feature: Base Tool Implementation

### Scenario: Create concrete tool from BaseTool
```gherkin
Given I create a TestTool class extending BaseTool
And the tool has:
  | name        | test_tool                    |
  | description | A test tool for verification |
  | category    | OTHER                        |
And the tool has parameters:
  | name    | type   | required | description      |
  | message | string | true     | Message to echo  |
When I instantiate TestTool
Then tool.name should be "test_tool"
And tool.description should be "A test tool for verification"
And tool.category should be ToolCategory.OTHER
And tool.parameters should have 1 item
```

### Scenario: Tool validates required parameter present
```gherkin
Given a tool with required parameter "file_path"
When I call validate_params(file_path="/some/path")
Then the result should be (True, None)
```

### Scenario: Tool validates required parameter missing
```gherkin
Given a tool with required parameter "file_path"
When I call validate_params() with no arguments
Then the result should be (False, "Missing required parameter: file_path")
```

### Scenario: Tool validates parameter type - string
```gherkin
Given a tool with parameter "name" of type "string"
When I call validate_params(name="hello")
Then the result should be (True, None)

When I call validate_params(name=123)
Then the result should be (False, "Invalid type for name: expected string")
```

### Scenario: Tool validates parameter type - integer
```gherkin
Given a tool with parameter "count" of type "integer"
When I call validate_params(count=42)
Then the result should be (True, None)

When I call validate_params(count="42")
Then the result should be (False, "Invalid type for count: expected integer")

When I call validate_params(count=3.14)
Then the result should be (False, "Invalid type for count: expected integer")
```

### Scenario: Tool validates parameter type - number
```gherkin
Given a tool with parameter "value" of type "number"
When I call validate_params(value=42)
Then the result should be (True, None)

When I call validate_params(value=3.14)
Then the result should be (True, None)

When I call validate_params(value="3.14")
Then the result should be (False, "Invalid type for value: expected number")
```

### Scenario: Tool validates parameter type - boolean
```gherkin
Given a tool with parameter "enabled" of type "boolean"
When I call validate_params(enabled=True)
Then the result should be (True, None)

When I call validate_params(enabled=False)
Then the result should be (True, None)

When I call validate_params(enabled="true")
Then the result should be (False, "Invalid type for enabled: expected boolean")
```

### Scenario: Tool validates parameter type - array
```gherkin
Given a tool with parameter "items" of type "array"
When I call validate_params(items=[1, 2, 3])
Then the result should be (True, None)

When I call validate_params(items="[1, 2, 3]")
Then the result should be (False, "Invalid type for items: expected array")
```

### Scenario: Tool validates parameter type - object
```gherkin
Given a tool with parameter "config" of type "object"
When I call validate_params(config={"key": "value"})
Then the result should be (True, None)

When I call validate_params(config="{'key': 'value'}")
Then the result should be (False, "Invalid type for config: expected object")
```

### Scenario: Tool validates enum constraint
```gherkin
Given a tool with parameter "format" with enum ["json", "yaml", "toml"]
When I call validate_params(format="json")
Then the result should be (True, None)

When I call validate_params(format="xml")
Then the result should be (False, "Invalid value for format: must be one of ['json', 'yaml', 'toml']")
```

### Scenario: Tool validates numeric minimum
```gherkin
Given a tool with parameter "timeout" with minimum 1
When I call validate_params(timeout=1)
Then the result should be (True, None)

When I call validate_params(timeout=0)
Then the result should be (False, "Value for timeout is below minimum: 1")
```

### Scenario: Tool validates numeric maximum
```gherkin
Given a tool with parameter "limit" with maximum 1000
When I call validate_params(limit=1000)
Then the result should be (True, None)

When I call validate_params(limit=1001)
Then the result should be (False, "Value for limit exceeds maximum: 1000")
```

### Scenario: Tool validates string min_length
```gherkin
Given a tool with parameter "content" with min_length 1
When I call validate_params(content="hello")
Then the result should be (True, None)

When I call validate_params(content="")
Then the result should be (False, "Value for content is shorter than minimum length: 1")
```

### Scenario: Tool validates string max_length
```gherkin
Given a tool with parameter "name" with max_length 50
When I call validate_params(name="short")
Then the result should be (True, None)

When I call validate_params(name="x" * 51)
Then the result should be (False, "Value for name exceeds maximum length: 50")
```

### Scenario: Optional parameter uses default when not provided
```gherkin
Given a tool with optional parameter "timeout" default 120
When I call execute without providing timeout
Then the tool should use timeout=120
```

---

## Feature: Tool Execution

### Scenario: Execute tool successfully
```gherkin
Given a tool "EchoTool" that returns its input
And an execution context with working_dir="/home/user"
When I call tool.execute(context, message="Hello")
Then the result should be successful
And result.output should be "Hello"
```

### Scenario: Execute tool with validation failure
```gherkin
Given a tool requiring parameter "file_path"
And an execution context
When I call tool.execute(context) without file_path
Then the result should be failed
And result.error should be "Missing required parameter: file_path"
```

### Scenario: Execute tool with timeout
```gherkin
Given a tool "SlowTool" that takes 5 seconds to execute
And an execution context with timeout=1
When I call tool.execute(context)
Then the result should be failed
And result.error should contain "timed out"
```

### Scenario: Execute tool in dry run mode
```gherkin
Given a tool "WriteTool" that writes to files
And an execution context with dry_run=true
When I call tool.execute(context, file_path="/foo", content="bar")
Then the result should be successful
And result.output should contain "[Dry Run]"
And no file should actually be written
```

### Scenario: Execute tool with exception
```gherkin
Given a tool that raises an exception during execution
And an execution context
When I call tool.execute(context)
Then the result should be failed
And result.error should contain the exception message
And the exception should not propagate
```

---

## Feature: OpenAI Schema Generation

### Scenario: Generate OpenAI schema for simple tool
```gherkin
Given a tool "Read" with:
  | name        | Read                           |
  | description | Read contents of a file        |
And parameters:
  | name      | type    | required | description                  |
  | file_path | string  | true     | Absolute path to the file    |
  | offset    | integer | false    | Line number to start from    |
  | limit     | integer | false    | Maximum lines to read        |
When I call tool.to_openai_schema()
Then the result should be:
  """json
  {
    "type": "function",
    "function": {
      "name": "Read",
      "description": "Read contents of a file",
      "parameters": {
        "type": "object",
        "properties": {
          "file_path": {
            "type": "string",
            "description": "Absolute path to the file"
          },
          "offset": {
            "type": "integer",
            "description": "Line number to start from"
          },
          "limit": {
            "type": "integer",
            "description": "Maximum lines to read"
          }
        },
        "required": ["file_path"]
      }
    }
  }
  """
```

### Scenario: Generate OpenAI schema with enum parameter
```gherkin
Given a tool with parameter "format" with enum ["json", "yaml"]
When I call tool.to_openai_schema()
Then the schema properties for "format" should include:
  """json
  {
    "type": "string",
    "enum": ["json", "yaml"]
  }
  """
```

### Scenario: Generate OpenAI schema with numeric constraints
```gherkin
Given a tool with parameter "timeout" with minimum 1 and maximum 600
When I call tool.to_openai_schema()
Then the schema properties for "timeout" should include:
  """json
  {
    "type": "integer",
    "minimum": 1,
    "maximum": 600
  }
  """
```

---

## Feature: Anthropic Schema Generation

### Scenario: Generate Anthropic schema for simple tool
```gherkin
Given a tool "Read" with:
  | name        | Read                           |
  | description | Read contents of a file        |
And parameters:
  | name      | type    | required | description                  |
  | file_path | string  | true     | Absolute path to the file    |
When I call tool.to_anthropic_schema()
Then the result should be:
  """json
  {
    "name": "Read",
    "description": "Read contents of a file",
    "input_schema": {
      "type": "object",
      "properties": {
        "file_path": {
          "type": "string",
          "description": "Absolute path to the file"
        }
      },
      "required": ["file_path"]
    }
  }
  """
```

---

## Feature: LangChain Tool Conversion

### Scenario: Convert to LangChain tool
```gherkin
Given a tool "Read" extending BaseTool
When I call tool.to_langchain_tool()
Then the result should be a LangChain Tool instance
And the tool name should be "Read"
And the tool description should match
And the tool should be callable
```

---

## Feature: Tool Registry

### Scenario: Register a tool
```gherkin
Given an empty ToolRegistry
And a tool "ReadTool" with name "Read"
When I call registry.register(ReadTool())
Then registry.exists("Read") should be true
And registry.count() should be 1
```

### Scenario: Register multiple tools
```gherkin
Given an empty ToolRegistry
And tools: ReadTool, WriteTool, BashTool
When I call registry.register_many([ReadTool(), WriteTool(), BashTool()])
Then registry.count() should be 3
And registry.list_names() should be ["Read", "Write", "Bash"]
```

### Scenario: Prevent duplicate registration
```gherkin
Given a ToolRegistry with "Read" already registered
When I try to register another tool with name "Read"
Then a ToolError should be raised
And the error message should contain "already registered"
```

### Scenario: Get tool by name - exists
```gherkin
Given a ToolRegistry with "Read" registered
When I call registry.get("Read")
Then the result should be the ReadTool instance
```

### Scenario: Get tool by name - not found
```gherkin
Given a ToolRegistry with no "Unknown" tool
When I call registry.get("Unknown")
Then the result should be None
```

### Scenario: Get tool or raise - exists
```gherkin
Given a ToolRegistry with "Read" registered
When I call registry.get_or_raise("Read")
Then the result should be the ReadTool instance
```

### Scenario: Get tool or raise - not found
```gherkin
Given a ToolRegistry with no "Unknown" tool
When I call registry.get_or_raise("Unknown")
Then a ToolError should be raised
And the error message should contain "not found"
```

### Scenario: Deregister a tool
```gherkin
Given a ToolRegistry with "Read" registered
When I call registry.deregister("Read")
Then the result should be true
And registry.exists("Read") should be false
```

### Scenario: Deregister non-existent tool
```gherkin
Given a ToolRegistry with no "Unknown" tool
When I call registry.deregister("Unknown")
Then the result should be false
```

### Scenario: List all tools
```gherkin
Given a ToolRegistry with ReadTool, WriteTool, BashTool
When I call registry.list_all()
Then the result should contain all three tools
```

### Scenario: List tool names
```gherkin
Given a ToolRegistry with ReadTool, WriteTool, BashTool
When I call registry.list_names()
Then the result should be ["Read", "Write", "Bash"] (sorted alphabetically)
```

### Scenario: List tools by category
```gherkin
Given a ToolRegistry with:
  | tool      | category   |
  | ReadTool  | FILE       |
  | WriteTool | FILE       |
  | BashTool  | EXECUTION  |
When I call registry.list_by_category(ToolCategory.FILE)
Then the result should contain ReadTool and WriteTool
And the result should not contain BashTool
```

### Scenario: Clear registry
```gherkin
Given a ToolRegistry with multiple tools registered
When I call registry.clear()
Then registry.count() should be 0
And registry.list_all() should be empty
```

### Scenario: Registry is singleton
```gherkin
Given I create ToolRegistry instance A
And I create ToolRegistry instance B
Then A and B should be the same instance
```

### Scenario: Reset singleton for testing
```gherkin
Given a ToolRegistry singleton with tools registered
When I call ToolRegistry.reset()
And I create a new ToolRegistry instance
Then the registry should be empty
```

---

## Feature: Tool Executor

### Scenario: Execute tool by name
```gherkin
Given a ToolExecutor with a registry containing "Echo" tool
And an execution context
When I call executor.execute("Echo", context, message="Hello")
Then the result should be from the Echo tool
And the result should be successful
```

### Scenario: Execute unknown tool
```gherkin
Given a ToolExecutor with an empty registry
And an execution context
When I call executor.execute("Unknown", context)
Then the result should be failed
And result.error should be "Unknown tool: Unknown"
```

### Scenario: Get all schemas - OpenAI format
```gherkin
Given a ToolExecutor with registry containing Read, Write, Bash tools
When I call executor.get_all_schemas("openai")
Then the result should be a list of 3 OpenAI-format schemas
And each schema should have "type": "function"
```

### Scenario: Get all schemas - Anthropic format
```gherkin
Given a ToolExecutor with registry containing Read, Write, Bash tools
When I call executor.get_all_schemas("anthropic")
Then the result should be a list of 3 Anthropic-format schemas
And each schema should have "input_schema"
```

### Scenario: Get schemas by category
```gherkin
Given a ToolExecutor with registry containing:
  | tool  | category  |
  | Read  | FILE      |
  | Write | FILE      |
  | Bash  | EXECUTION |
When I call executor.get_schemas_by_category(ToolCategory.FILE, "openai")
Then the result should contain 2 schemas
And the schemas should be for Read and Write tools
```

### Scenario: Track execution history
```gherkin
Given a ToolExecutor
And I execute "Read" tool with file_path="/foo"
And I execute "Write" tool with file_path="/bar", content="test"
When I call executor.get_executions()
Then the result should contain 2 ToolExecution records
And the first should be for "Read" tool
And the second should be for "Write" tool
```

### Scenario: Clear execution history
```gherkin
Given a ToolExecutor with execution history
When I call executor.clear_executions()
Then executor.get_executions() should be empty
```

### Scenario: Execution record contains timing
```gherkin
Given a ToolExecutor
When I execute a tool
Then the ToolExecution record should contain:
  | field        | description                    |
  | started_at   | datetime when execution began  |
  | completed_at | datetime when execution ended  |
  | duration_ms  | execution time in milliseconds |
```

---

## Feature: Tool Execution Logging

### Scenario: Log tool execution start
```gherkin
Given a ToolExecutor with logging enabled
When I execute "Read" tool
Then an info log should be written: "Executing tool: Read"
```

### Scenario: Log tool execution parameters
```gherkin
Given a ToolExecutor with debug logging
When I execute "Read" tool with file_path="/home/user/test.txt"
Then a debug log should contain the parameters
```

### Scenario: Log successful execution
```gherkin
Given a ToolExecutor with logging enabled
When I execute a tool successfully
Then an info log should be written: "Tool <name> succeeded"
```

### Scenario: Log failed execution
```gherkin
Given a ToolExecutor with logging enabled
When I execute a tool that fails
Then a warning log should be written containing the error message
```

---

## Feature: Error Handling

### Scenario: ToolError contains tool name
```gherkin
Given I raise ToolError("Read", "File not found")
Then error.tool_name should be "Read"
And error.message should be "File not found"
And str(error) should be "Tool 'Read' error: File not found"
```

### Scenario: Tool execution catches all exceptions
```gherkin
Given a tool that raises RuntimeError("Unexpected error")
When I execute the tool
Then no exception should propagate
And the result should be failed
And result.error should contain "Unexpected error"
```

---

## Feature: Thread Safety

### Scenario: Concurrent tool registration
```gherkin
Given an empty ToolRegistry
When 10 threads try to register different tools simultaneously
Then all tools should be registered
And no race conditions should occur
```

### Scenario: Concurrent tool execution
```gherkin
Given a ToolExecutor with tools registered
When 10 threads execute tools simultaneously
Then all executions should complete
And no state corruption should occur
```

---

## Feature: Integration Tests

### Scenario: Full tool lifecycle
```gherkin
Given a new ToolRegistry
And a custom tool implementation
When I:
  1. Create the tool
  2. Register it with the registry
  3. Create a ToolExecutor with the registry
  4. Generate schemas for the tool
  5. Execute the tool with valid parameters
  6. Execute the tool with invalid parameters
  7. Deregister the tool
Then each step should complete successfully
And the tool should no longer be available after deregistration
```

### Scenario: Tool system initialization
```gherkin
Given the Code-Forge application starts
When the tool system initializes
Then the ToolRegistry should be available
And the ToolExecutor should be available
And schemas should be generatable for LLM integration
```
