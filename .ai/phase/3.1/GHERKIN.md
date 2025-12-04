# Phase 3.1: OpenRouter Client - Gherkin Specifications

**Phase:** 3.1
**Name:** OpenRouter Client
**Dependencies:** Phase 1.1 (Project Foundation), Phase 1.2 (Configuration)

---

## Feature: Message Creation

### Scenario: Create system message
```gherkin
Given I need to create a system message
When I call Message.system("You are a helpful assistant.")
Then the message role should be "system"
And the message content should be "You are a helpful assistant."
And to_dict() should return {"role": "system", "content": "You are a helpful assistant."}
```

### Scenario: Create user message
```gherkin
Given I need to create a user message
When I call Message.user("Hello!")
Then the message role should be "user"
And the message content should be "Hello!"
```

### Scenario: Create assistant message with content
```gherkin
Given I need to create an assistant response
When I call Message.assistant("Hello! How can I help?")
Then the message role should be "assistant"
And the message content should be "Hello! How can I help?"
And tool_calls should be None
```

### Scenario: Create assistant message with tool calls
```gherkin
Given I need to create an assistant message with tool calls
When I call Message.assistant(content=None, tool_calls=[tool_call])
Then the message role should be "assistant"
And the message content should be None
And tool_calls should contain the provided tool calls
```

### Scenario: Create tool result message
```gherkin
Given I need to return a tool result
When I call Message.tool_result("call_abc123", "File contents here")
Then the message role should be "tool"
And the message tool_call_id should be "call_abc123"
And the message content should be "File contents here"
```

### Scenario: Create multimodal user message
```gherkin
Given I need to send text and an image
When I create a Message with content as List[ContentPart]
And the content includes text and image_url parts
Then to_dict() should format content as an array
And each part should have the correct type
```

---

## Feature: Tool Definitions

### Scenario: Create tool definition
```gherkin
Given I need to define a tool for function calling
When I create a ToolDefinition with:
  | name        | read_file                    |
  | description | Read contents of a file      |
  | parameters  | {"type": "object", ...}      |
Then to_dict() should return the OpenAI function format
And the type should be "function"
And function.name should be "read_file"
```

### Scenario: Tool definition from BaseTool schema
```gherkin
Given a BaseTool with to_openai_schema()
When I extract the function definition
Then I should be able to create a ToolDefinition
And it should be compatible with CompletionRequest
```

---

## Feature: Completion Request

### Scenario: Create basic completion request
```gherkin
Given messages: [system, user]
When I create CompletionRequest with model="anthropic/claude-3-opus"
Then to_dict() should include model and messages
And stream should default to false
And temperature should default to 1.0
```

### Scenario: Create completion request with tools
```gherkin
Given messages and tool definitions
When I create CompletionRequest with tools=[tool1, tool2]
Then to_dict() should include tools array
And tool_choice can be "auto", "none", or specific
```

### Scenario: Create completion request with optional parameters
```gherkin
Given a basic request
When I set:
  | temperature       | 0.7    |
  | max_tokens        | 1000   |
  | top_p             | 0.9    |
  | frequency_penalty | 0.5    |
Then to_dict() should include all non-default parameters
And default-valued parameters may be omitted
```

---

## Feature: Completion Response Parsing

### Scenario: Parse successful response
```gherkin
Given an API response JSON:
  """json
  {
    "id": "gen-abc123",
    "model": "anthropic/claude-3-opus",
    "choices": [{
      "index": 0,
      "message": {"role": "assistant", "content": "Hello!"},
      "finish_reason": "stop"
    }],
    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    "created": 1705312345
  }
  """
When I call CompletionResponse.from_dict(data)
Then response.id should be "gen-abc123"
And response.model should be "anthropic/claude-3-opus"
And response.choices should have 1 item
And response.choices[0].message.content should be "Hello!"
And response.usage.total_tokens should be 15
```

### Scenario: Parse response with tool calls
```gherkin
Given an API response with tool_calls in message
When I parse the response
Then the message should have tool_calls list
And each tool_call should have id, type, and function
And function should have name and arguments (JSON string)
```

---

## Feature: OpenRouter Client - Basic Operations

### Scenario: Initialize client
```gherkin
Given an API key "sk-or-xxx"
When I create OpenRouterClient(api_key="sk-or-xxx")
Then the client should be configured with:
  | base_url   | https://openrouter.ai/api/v1 |
  | timeout    | 120.0                        |
  | max_retries| 3                            |
And headers should include Authorization Bearer token
And headers should include HTTP-Referer and X-Title
```

### Scenario: Initialize client with custom settings
```gherkin
Given custom configuration
When I create OpenRouterClient with:
  | api_key     | sk-or-xxx                |
  | base_url    | https://custom.api       |
  | app_name    | MyApp                    |
  | app_url     | https://myapp.com        |
  | timeout     | 60.0                     |
  | max_retries | 5                        |
Then all settings should be applied
```

---

## Feature: Chat Completion

### Scenario: Successful completion request
```gherkin
Given an OpenRouterClient with valid API key
And a CompletionRequest with model and messages
When I call client.complete(request)
Then I should receive a CompletionResponse
And response should have choices with assistant message
And response should have usage statistics
And client usage counters should be updated
```

### Scenario: Completion with model alias
```gherkin
Given a request with model="claude-3-opus" (alias)
When I call client.complete(request)
Then the model should be resolved to "anthropic/claude-3-opus"
And the request should succeed
```

### Scenario: Completion with tool calls
```gherkin
Given a request with tools defined
And the model decides to call a tool
When I call client.complete(request)
Then response message should have tool_calls
And finish_reason should be "tool_calls"
And I can extract the tool call details
```

---

## Feature: Streaming Response

### Scenario: Stream completion response
```gherkin
Given an OpenRouterClient with valid API key
And a CompletionRequest
When I call async for chunk in client.stream(request)
Then I should receive StreamChunk objects
And each chunk should have delta with content
And the final chunk should have finish_reason
```

### Scenario: Collect streamed content
```gherkin
Given a streaming response
And a StreamCollector
When I add_chunk(chunk) for each chunk
Then collector.content should accumulate text
And collector.get_message() should return complete Message
```

### Scenario: Stream with tool calls
```gherkin
Given a streaming response with tool calls
When I collect all chunks
Then tool call information should be assembled
And get_message() should include complete tool_calls
And tool call arguments should be complete JSON
```

### Scenario: Stream interrupted
```gherkin
Given a streaming response in progress
When the connection is interrupted
Then an appropriate error should be raised
And partial content should be available
```

---

## Feature: Error Handling

### Scenario: Authentication error (401)
```gherkin
Given an OpenRouterClient with invalid API key
When I call client.complete(request)
Then AuthenticationError should be raised
And the error message should indicate invalid key
```

### Scenario: Rate limit error (429)
```gherkin
Given an OpenRouterClient hitting rate limits
When I call client.complete(request)
And the API returns 429 with Retry-After: 30
Then the client should wait and retry
And if retries exhausted, RateLimitError should be raised
And error.retry_after should be 30
```

### Scenario: Model not found (404)
```gherkin
Given a request for non-existent model "fake/model"
When I call client.complete(request)
Then ModelNotFoundError should be raised
And error.model_id should be "fake/model"
```

### Scenario: Context length exceeded
```gherkin
Given a request with too many tokens
When the API returns context length error
Then ContextLengthError should be raised
And error should contain max_tokens if available
```

### Scenario: Content policy violation
```gherkin
Given a request with policy-violating content
When the API returns content policy error
Then ContentPolicyError should be raised
```

### Scenario: Timeout handling
```gherkin
Given a request that takes too long
When the timeout is exceeded
Then the client should retry with backoff
And if retries exhausted, LLMError should be raised
```

---

## Feature: Retry Logic

### Scenario: Retry on rate limit
```gherkin
Given max_retries=3 and retry_delay=1.0
When the API returns 429 on first attempt
And succeeds on second attempt
Then the final result should be successful
And only 2 requests should have been made
```

### Scenario: Exponential backoff
```gherkin
Given max_retries=3 and retry_delay=1.0
When multiple retries are needed
Then wait times should be: 1s, 2s, 4s (exponential)
```

### Scenario: Max retries exceeded
```gherkin
Given max_retries=3
When all 3 attempts fail
Then the last error should be raised
And no more retries should occur
```

---

## Feature: Model Routing

### Scenario: Apply nitro variant
```gherkin
Given model_id="anthropic/claude-3-opus"
When I call apply_variant(model_id, RouteVariant.NITRO)
Then the result should be "anthropic/claude-3-opus:nitro"
```

### Scenario: Apply floor variant
```gherkin
Given model_id="openai/gpt-4"
When I call apply_variant(model_id, RouteVariant.FLOOR)
Then the result should be "openai/gpt-4:floor"
```

### Scenario: Apply default (no) variant
```gherkin
Given model_id="anthropic/claude-3-opus"
When I call apply_variant(model_id, RouteVariant.DEFAULT)
Then the result should be "anthropic/claude-3-opus" (unchanged)
```

### Scenario: Parse model with variant
```gherkin
Given model_id="anthropic/claude-3-opus:nitro"
When I call parse_model_id(model_id)
Then the result should be ("anthropic/claude-3-opus", RouteVariant.NITRO)
```

### Scenario: Resolve model alias
```gherkin
Given alias="claude-3-opus"
When I call resolve_model_alias(alias)
Then the result should be "anthropic/claude-3-opus"
```

### Scenario: Unknown alias passes through
```gherkin
Given model_id="custom/model"
When I call resolve_model_alias(model_id)
Then the result should be "custom/model" (unchanged)
```

---

## Feature: Token Usage Tracking

### Scenario: Track usage across requests
```gherkin
Given a new OpenRouterClient
When I make 3 completion requests with varying token counts
Then client.get_usage() should return cumulative totals
And prompt_tokens should be sum of all prompt tokens
And completion_tokens should be sum of all completion tokens
```

### Scenario: Reset usage
```gherkin
Given a client with accumulated usage
When I call client.reset_usage()
Then get_usage() should return all zeros
```

### Scenario: Track streaming usage
```gherkin
Given a streaming request
When the final chunk includes usage
Then the usage should be tracked
And get_usage() should reflect the streaming request
```

---

## Feature: List Models

### Scenario: List available models
```gherkin
Given a valid OpenRouterClient
When I call client.list_models()
Then I should receive a list of model info dicts
And each model should have id, name, context_length
And pricing information should be included
```

---

## Feature: Stream Collector

### Scenario: Collect text content
```gherkin
Given a StreamCollector
And chunks with delta.content: ["Hello", " ", "World"]
When I add_chunk for each chunk
Then collector.content should be "Hello World"
And add_chunk should return the new content each time
```

### Scenario: Collect tool calls
```gherkin
Given a StreamCollector
And chunks building a tool call:
  | chunk 1 | {"id": "call_1", "function": {"name": "read"}} |
  | chunk 2 | {"function": {"arguments": '{"path'}}          |
  | chunk 3 | {"function": {"arguments": '": "/tmp"}'}}      |
When I add_chunk for each
Then collector.tool_calls should have one complete tool call
And the arguments should be '{"path": "/tmp"}'
```

### Scenario: Check completion
```gherkin
Given a StreamCollector
When I add chunks without finish_reason
Then collector.is_complete should be False

When I add chunk with finish_reason="stop"
Then collector.is_complete should be True
```

---

## Feature: Client Lifecycle

### Scenario: Context manager usage
```gherkin
Given need for automatic cleanup
When I use:
  async with OpenRouterClient(api_key) as client:
      response = await client.complete(request)
Then the client should be properly closed after the block
```

### Scenario: Manual close
```gherkin
Given an OpenRouterClient
When I call client.close()
Then the HTTP client should be closed
And the client should be safe to close multiple times
```

---

## Feature: Integration Tests

### Scenario: Full conversation with tool use
```gherkin
Given an OpenRouterClient
And a system message and user message asking to read a file
And read_file tool is provided
When I:
  1. Send completion request
  2. Receive tool call response
  3. Execute the tool
  4. Send tool result
  5. Receive final response
Then each step should complete successfully
And the final response should reference the file contents
```

### Scenario: Streaming conversation
```gherkin
Given an OpenRouterClient
And messages asking for a long response
When I stream the response
And collect all chunks
Then I should have the complete response
And it should match what a non-streaming request would return
```
