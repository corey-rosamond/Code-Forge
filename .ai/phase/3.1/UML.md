# Phase 3.1: OpenRouter Client - UML Diagrams

**Phase:** 3.1
**Name:** OpenRouter Client
**Dependencies:** Phase 1.1 (Project Foundation), Phase 1.2 (Configuration)

---

## 1. Class Diagram - LLM Package Overview

```mermaid
classDiagram
    class OpenRouterClient {
        +BASE_URL: str
        -api_key: str
        -base_url: str
        -app_name: str
        -app_url: str
        -timeout: float
        -max_retries: int
        -retry_delay: float
        -_client: AsyncClient?
        -_total_prompt_tokens: int
        -_total_completion_tokens: int
        +complete(request) CompletionResponse
        +stream(request) AsyncIterator~StreamChunk~
        +list_models() List~Dict~
        +get_usage() TokenUsage
        +reset_usage() void
        +close() void
        -_get_client() AsyncClient
        -_get_headers() Dict
        -_make_request(client, method, path, payload) Dict
        -_check_response(response) void
    }

    class Message {
        +role: MessageRole
        +content: str | List~ContentPart~
        +name: str?
        +tool_call_id: str?
        +tool_calls: List~ToolCall~?
        +to_dict() Dict
        +from_dict(data)$ Message
        +system(content)$ Message
        +user(content)$ Message
        +assistant(content, tool_calls)$ Message
        +tool_result(id, content)$ Message
    }

    class MessageRole {
        <<enumeration>>
        SYSTEM
        USER
        ASSISTANT
        TOOL
    }

    class ToolCall {
        +id: str
        +type: str
        +function: Dict
        +to_dict() Dict
        +from_dict(data)$ ToolCall
    }

    class ToolDefinition {
        +name: str
        +description: str
        +parameters: Dict
        +type: str
        +to_dict() Dict
    }

    class CompletionRequest {
        +model: str
        +messages: List~Message~
        +tools: List~ToolDefinition~?
        +tool_choice: str | Dict?
        +temperature: float
        +max_tokens: int?
        +top_p: float
        +frequency_penalty: float
        +presence_penalty: float
        +stop: List~str~?
        +stream: bool
        +transforms: List~str~?
        +route: str?
        +to_dict() Dict
    }

    class CompletionResponse {
        +id: str
        +model: str
        +choices: List~CompletionChoice~
        +usage: TokenUsage
        +created: int
        +provider: str?
        +from_dict(data)$ CompletionResponse
    }

    class CompletionChoice {
        +index: int
        +message: Message
        +finish_reason: str?
        +from_dict(data)$ CompletionChoice
    }

    class TokenUsage {
        +prompt_tokens: int
        +completion_tokens: int
        +total_tokens: int
        +from_dict(data)$ TokenUsage
    }

    class StreamChunk {
        +id: str
        +model: str
        +delta: StreamDelta
        +index: int
        +finish_reason: str?
        +usage: TokenUsage?
        +from_dict(data)$ StreamChunk
    }

    class StreamDelta {
        +role: str?
        +content: str?
        +tool_calls: List~Dict~?
        +from_dict(data)$ StreamDelta
    }

    OpenRouterClient --> CompletionRequest : accepts
    OpenRouterClient --> CompletionResponse : returns
    OpenRouterClient --> StreamChunk : yields
    CompletionRequest --> Message : contains
    CompletionRequest --> ToolDefinition : contains
    CompletionResponse --> CompletionChoice : contains
    CompletionResponse --> TokenUsage : contains
    CompletionChoice --> Message : contains
    Message --> MessageRole : has
    Message --> ToolCall : has
    StreamChunk --> StreamDelta : contains
    StreamChunk --> TokenUsage : contains
```

---

## 2. Class Diagram - Error Hierarchy

```mermaid
classDiagram
    class OpenCodeError {
        <<abstract>>
        +message: str
    }

    class LLMError {
        +message: str
    }

    class AuthenticationError {
        Invalid or missing API key
    }

    class RateLimitError {
        +retry_after: float?
    }

    class ModelNotFoundError {
        +model_id: str
    }

    class ContextLengthError {
        +max_tokens: int?
        +requested_tokens: int?
    }

    class ContentPolicyError {
        Content violates policy
    }

    class ProviderError {
        +provider: str?
    }

    OpenCodeError <|-- LLMError
    LLMError <|-- AuthenticationError
    LLMError <|-- RateLimitError
    LLMError <|-- ModelNotFoundError
    LLMError <|-- ContextLengthError
    LLMError <|-- ContentPolicyError
    LLMError <|-- ProviderError
```

---

## 3. Class Diagram - Routing

```mermaid
classDiagram
    class RouteVariant {
        <<enumeration>>
        DEFAULT = ""
        NITRO = ":nitro"
        FLOOR = ":floor"
        ONLINE = ":online"
        THINKING = ":thinking"
    }

    class RoutingFunctions {
        <<module>>
        +apply_variant(model_id, variant) str
        +parse_model_id(model_id) tuple
        +resolve_model_alias(model_id) str
    }

    class MODEL_ALIASES {
        <<dict>>
        claude-3-opus → anthropic/claude-3-opus
        gpt-4 → openai/gpt-4
        ...
    }

    RoutingFunctions --> RouteVariant : uses
    RoutingFunctions --> MODEL_ALIASES : uses
```

---

## 4. Class Diagram - Stream Collector

```mermaid
classDiagram
    class StreamCollector {
        +content: str
        +tool_calls: List~dict~
        +usage: TokenUsage?
        +model: str
        +finish_reason: str?
        -_tool_call_index: int
        +add_chunk(chunk) str?
        +get_message() Message
        +is_complete: bool
    }

    class StreamChunk {
        +id: str
        +model: str
        +delta: StreamDelta
        +finish_reason: str?
        +usage: TokenUsage?
    }

    class Message {
        +role: MessageRole
        +content: str?
        +tool_calls: List~ToolCall~?
    }

    StreamCollector --> StreamChunk : processes
    StreamCollector --> Message : produces
```

---

## 5. Sequence Diagram - Chat Completion

```mermaid
sequenceDiagram
    participant App as Application
    participant Client as OpenRouterClient
    participant HTTP as httpx.AsyncClient
    participant API as OpenRouter API

    App->>Client: complete(request)

    Client->>Client: resolve_model_alias()
    Client->>Client: request.to_dict()

    Client->>HTTP: POST /chat/completions
    HTTP->>API: HTTP Request

    alt Success
        API-->>HTTP: 200 OK + JSON
        HTTP-->>Client: Response
        Client->>Client: CompletionResponse.from_dict()
        Client->>Client: Track usage
        Client-->>App: CompletionResponse
    else Rate Limited
        API-->>HTTP: 429 + Retry-After
        HTTP-->>Client: Response
        Client->>Client: Wait (exponential backoff)
        Client->>HTTP: Retry request
    else Auth Error
        API-->>HTTP: 401 Unauthorized
        HTTP-->>Client: Response
        Client-->>App: raise AuthenticationError
    else Other Error
        API-->>HTTP: 4xx/5xx
        HTTP-->>Client: Response
        Client->>Client: Parse error
        Client-->>App: raise LLMError
    end
```

---

## 6. Sequence Diagram - Streaming Response

```mermaid
sequenceDiagram
    participant App as Application
    participant Client as OpenRouterClient
    participant Collector as StreamCollector
    participant HTTP as httpx.AsyncClient
    participant API as OpenRouter API

    App->>Client: stream(request)
    App->>Collector: Create StreamCollector()

    Client->>Client: set request.stream = True
    Client->>HTTP: POST /chat/completions (streaming)
    HTTP->>API: HTTP Request

    API-->>HTTP: SSE Stream Begin

    loop For each SSE event
        API-->>HTTP: data: {...}
        HTTP-->>Client: line

        Client->>Client: Parse JSON
        Client->>Client: StreamChunk.from_dict()

        Client-->>App: yield StreamChunk
        App->>Collector: add_chunk(chunk)

        alt Has content
            Collector-->>App: new_content
            App->>App: Display content
        end
    end

    API-->>HTTP: data: [DONE]
    HTTP-->>Client: stream ends

    App->>Collector: get_message()
    Collector-->>App: Complete Message
```

---

## 7. Sequence Diagram - Tool Calling

```mermaid
sequenceDiagram
    participant App as Application
    participant Client as OpenRouterClient
    participant API as OpenRouter API
    participant Tool as Tool Executor

    App->>Client: complete(request with tools)
    Client->>API: Request with tool definitions

    API-->>Client: Response with tool_calls

    Client-->>App: CompletionResponse

    App->>App: Extract tool_calls

    loop For each tool call
        App->>Tool: Execute tool
        Tool-->>App: Result
        App->>App: Create tool result message
    end

    App->>App: Add tool results to messages

    App->>Client: complete(continuation request)
    Client->>API: Request with tool results

    API-->>Client: Final response

    Client-->>App: CompletionResponse
```

---

## 8. State Diagram - Request Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Preparing: complete() called

    Preparing --> Resolving: Prepare request
    Resolving --> Building: Resolve model alias
    Building --> Sending: Build payload

    Sending --> WaitingResponse: HTTP POST

    WaitingResponse --> Parsing: 200 OK
    WaitingResponse --> RateLimited: 429
    WaitingResponse --> AuthFailed: 401
    WaitingResponse --> ModelNotFound: 404
    WaitingResponse --> OtherError: 4xx/5xx

    RateLimited --> Waiting: Get retry-after
    Waiting --> Sending: Retry (if attempts left)
    Waiting --> Failed: Max retries exceeded

    AuthFailed --> Failed: AuthenticationError
    ModelNotFound --> Failed: ModelNotFoundError
    OtherError --> Failed: LLMError

    Parsing --> TrackUsage: Parse response
    TrackUsage --> Success: Update counters

    Success --> [*]: Return response
    Failed --> [*]: Raise error
```

---

## 9. State Diagram - Streaming Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Starting: stream() called

    Starting --> Connected: HTTP stream connected
    Connected --> Receiving: Stream active

    Receiving --> ProcessingChunk: data: {...}
    ProcessingChunk --> YieldingChunk: Parse successful
    ProcessingChunk --> Receiving: Parse failed (skip)

    YieldingChunk --> Receiving: Yield and continue
    YieldingChunk --> CheckDone: Has finish_reason

    CheckDone --> Receiving: Not done
    CheckDone --> Completing: Done

    Receiving --> Done: data: [DONE]
    Completing --> Done: Stream complete

    Done --> [*]: Return

    Connected --> Error: Connection failed
    Receiving --> Error: Stream error
    Error --> [*]: Raise error
```

---

## 10. Component Diagram - LLM Package

```mermaid
flowchart TB
    subgraph LLMPackage["src/opencode/llm/"]
        INIT["__init__.py"]
        CLIENT["client.py"]
        MODELS["models.py"]
        ERRORS["errors.py"]
        ROUTING["routing.py"]
        STREAMING["streaming.py"]
    end

    subgraph Core["src/opencode/core/"]
        CORE_ERRORS["errors.py"]
        LOGGING["logging.py"]
    end

    subgraph External["External"]
        HTTPX[httpx]
        OPENROUTER[OpenRouter API]
    end

    CLIENT --> MODELS
    CLIENT --> ERRORS
    CLIENT --> ROUTING
    CLIENT --> STREAMING
    CLIENT --> LOGGING
    CLIENT --> HTTPX

    ERRORS --> CORE_ERRORS

    HTTPX --> OPENROUTER

    INIT --> CLIENT
    INIT --> MODELS
    INIT --> ERRORS
    INIT --> ROUTING
```

---

## 11. Activity Diagram - Retry Logic

```mermaid
flowchart TD
    START([make_request]) --> INIT[attempt = 0]
    INIT --> CHECK{attempt < max_retries?}

    CHECK -->|Yes| SEND[Send HTTP request]
    CHECK -->|No| FAIL[Raise last_error]

    SEND --> RESPONSE{Response status?}

    RESPONSE -->|200 OK| SUCCESS[Return response.json]
    RESPONSE -->|429| RATE_LIMIT[Get retry_after]
    RESPONSE -->|Timeout| TIMEOUT[Calculate backoff]
    RESPONSE -->|Other error| ERROR[Parse error]

    RATE_LIMIT --> WAIT[Wait retry_after or backoff]
    TIMEOUT --> WAIT

    WAIT --> INCREMENT[attempt += 1]
    INCREMENT --> CHECK

    ERROR --> CHECK_RETRY{Retryable?}
    CHECK_RETRY -->|Yes| INCREMENT
    CHECK_RETRY -->|No| FAIL

    SUCCESS --> END([Return data])
    FAIL --> END
```

---

## 12. Package Structure Diagram

```mermaid
flowchart TD
    subgraph opencode_llm["src/opencode/llm/"]
        INIT["__init__.py"]
        CLIENT["client.py<br/>OpenRouterClient"]
        MODELS["models.py<br/>Message, Request, Response"]
        ERRORS["errors.py<br/>LLMError hierarchy"]
        ROUTING["routing.py<br/>RouteVariant, aliases"]
        STREAMING["streaming.py<br/>StreamCollector"]
    end

    subgraph tests_llm["tests/unit/llm/"]
        TEST_CLIENT["test_client.py"]
        TEST_MODELS["test_models.py"]
        TEST_ERRORS["test_errors.py"]
        TEST_ROUTING["test_routing.py"]
        TEST_STREAMING["test_streaming.py"]
    end

    INIT --> CLIENT
    INIT --> MODELS
    INIT --> ERRORS
    INIT --> ROUTING
    INIT --> STREAMING

    TEST_CLIENT --> CLIENT
    TEST_MODELS --> MODELS
    TEST_ERRORS --> ERRORS
    TEST_ROUTING --> ROUTING
    TEST_STREAMING --> STREAMING
```

---

## 13. Data Flow Diagram - Message Formats

### Request Message Format
```json
{
  "model": "anthropic/claude-3-opus",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Hello!"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "read_file",
        "description": "Read a file",
        "parameters": {
          "type": "object",
          "properties": {
            "path": {"type": "string"}
          },
          "required": ["path"]
        }
      }
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false
}
```

### Response Format
```json
{
  "id": "gen-abc123",
  "model": "anthropic/claude-3-opus",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_xyz",
            "type": "function",
            "function": {
              "name": "read_file",
              "arguments": "{\"path\": \"/home/user/file.txt\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 25,
    "total_tokens": 175
  },
  "created": 1705312345
}
```

### Streaming Chunk Format
```json
{
  "id": "gen-abc123",
  "model": "anthropic/claude-3-opus",
  "choices": [
    {
      "index": 0,
      "delta": {
        "content": "Hello"
      },
      "finish_reason": null
    }
  ]
}
```

---

## Notes

- OpenRouterClient uses httpx for async HTTP requests
- Streaming uses Server-Sent Events (SSE) format
- Tool calls are accumulated across multiple streaming chunks
- Retry logic uses exponential backoff
- All models are accessed through unified OpenRouter API
- Route variants modify model selection behavior
