# Phase 3.2: LangChain Integration - UML Diagrams

**Phase:** 3.2
**Name:** LangChain Integration
**Dependencies:** Phase 2.1 (Tool System Foundation), Phase 3.1 (OpenRouter Client)

---

## 1. Class Diagram - LangChain Package Overview

```mermaid
classDiagram
    class OpenRouterLLM {
        +client: OpenRouterClient
        +model: str
        +temperature: float
        +max_tokens: int?
        +top_p: float
        -_bound_tools: list
        +_generate(messages, stop, run_manager) ChatResult
        +_agenerate(messages, stop, run_manager) ChatResult
        +_stream(messages, stop, run_manager) Iterator
        +_astream(messages, stop, run_manager) AsyncIterator
        +bind_tools(tools, tool_choice) OpenRouterLLM
        +with_structured_output(schema, method) OpenRouterLLM
        -_build_request(messages, stop, stream) CompletionRequest
    }

    class BaseChatModel {
        <<langchain_core>>
        +invoke(messages) BaseMessage
        +ainvoke(messages) BaseMessage
        +stream(messages) Iterator
        +astream(messages) AsyncIterator
    }

    class OpenRouterClient {
        <<from Phase 3.1>>
        +complete(request) CompletionResponse
        +stream(request) AsyncIterator
    }

    class LangChainToolAdapter {
        +opencode_tool: BaseTool
        +executor: ToolExecutor?
        +context: ExecutionContext?
        +name: str
        +description: str
        +args_schema: type
        +_run(**kwargs) str
        +_arun(**kwargs) str
    }

    class OpenCodeToolAdapter {
        +langchain_tool: LangChainBaseTool
        +name: str
        +description: str
        +category: ToolCategory
        +parameters: list
        +execute(params, context) ToolResult
        +to_openai_schema() dict
    }

    class ConversationMemory {
        +messages: list~Message~
        +system_message: Message?
        +max_messages: int?
        +max_tokens: int?
        +add_message(message) void
        +add_messages(messages) void
        +get_messages() list~Message~
        +set_system_message(message) void
        +clear() void
        +trim(max_tokens) void
        +to_langchain_messages() list~BaseMessage~
    }

    class OpenCodeAgent {
        +llm: OpenRouterLLM
        +tools: list
        +memory: ConversationMemory
        +max_iterations: int
        +timeout: float
        -_tool_map: dict
        -_bound_llm: OpenRouterLLM
        +run(input, callbacks) AgentResult
        +stream(input, callbacks) AsyncIterator~AgentEvent~
        +reset() void
    }

    BaseChatModel <|-- OpenRouterLLM
    OpenRouterLLM --> OpenRouterClient : uses
    OpenRouterLLM --> LangChainToolAdapter : binds
    OpenCodeAgent --> OpenRouterLLM : uses
    OpenCodeAgent --> ConversationMemory : manages
    OpenCodeAgent --> LangChainToolAdapter : executes
```

---

## 2. Class Diagram - Memory Hierarchy

```mermaid
classDiagram
    class ConversationMemory {
        +messages: list~Message~
        +system_message: Message?
        +max_messages: int?
        +max_tokens: int?
        -_token_counter: callable?
        +add_message(message) void
        +add_messages(messages) void
        +add_langchain_message(message) void
        +get_messages() list~Message~
        +get_history() list~Message~
        +set_system_message(message) void
        +clear() void
        +clear_history() void
        +trim(max_tokens) void
        +to_langchain_messages() list~BaseMessage~
        +from_langchain_messages(messages) void
    }

    class SlidingWindowMemory {
        +window_size: int
        +add_message(message) void
        -_enforce_window() void
    }

    class SummaryMemory {
        +summary_threshold: int
        +summary: str?
        +summarizer: LLM?
        +get_messages() list~Message~
        +maybe_summarize() void
    }

    ConversationMemory <|-- SlidingWindowMemory
    ConversationMemory <|-- SummaryMemory
```

---

## 3. Class Diagram - Callback Hierarchy

```mermaid
classDiagram
    class BaseCallbackHandler {
        <<langchain_core>>
        +on_llm_start()
        +on_llm_end()
        +on_llm_error()
        +on_llm_new_token()
        +on_tool_start()
        +on_tool_end()
        +on_tool_error()
    }

    class OpenCodeCallbackHandler {
        +name: str
        +raise_error: bool
        -_safe_call(func, args) void
    }

    class TokenTrackingCallback {
        +total_prompt_tokens: int
        +total_completion_tokens: int
        +call_count: int
        +on_llm_end(response) void
        +get_usage() TokenUsage
        +reset() void
    }

    class LoggingCallback {
        +logger: Logger
        +log_level: int
        -_start_times: dict
        +on_llm_start() void
        +on_llm_end() void
        +on_llm_error() void
        +on_tool_start() void
        +on_tool_end() void
        +on_tool_error() void
    }

    class StreamingCallback {
        +on_token: callable?
        +on_complete: callable?
        -_buffer: str
        +on_llm_new_token(token) void
        +on_llm_end(response) void
        +get_buffer() str
        +clear_buffer() void
    }

    class CompositeCallback {
        +callbacks: list~BaseCallbackHandler~
        +on_llm_start() void
        +on_llm_end() void
        +on_tool_start() void
        +on_tool_end() void
    }

    BaseCallbackHandler <|-- OpenCodeCallbackHandler
    OpenCodeCallbackHandler <|-- TokenTrackingCallback
    OpenCodeCallbackHandler <|-- LoggingCallback
    OpenCodeCallbackHandler <|-- StreamingCallback
    OpenCodeCallbackHandler <|-- CompositeCallback
    CompositeCallback o-- BaseCallbackHandler : contains
```

---

## 4. Class Diagram - Agent Result Types

```mermaid
classDiagram
    class AgentEventType {
        <<enumeration>>
        LLM_START
        LLM_CHUNK
        LLM_END
        TOOL_START
        TOOL_END
        AGENT_END
        ERROR
    }

    class AgentEvent {
        +type: AgentEventType
        +data: dict
        +timestamp: float
    }

    class ToolCallRecord {
        +id: str
        +name: str
        +arguments: dict
        +result: str
        +success: bool
        +duration: float
    }

    class AgentResult {
        +output: str
        +messages: list~Message~
        +tool_calls: list~ToolCallRecord~
        +usage: TokenUsage
        +iterations: int
        +duration: float
        +stopped_reason: str
    }

    AgentEvent --> AgentEventType : has
    AgentResult --> ToolCallRecord : contains
```

---

## 5. Sequence Diagram - LLM Invocation

```mermaid
sequenceDiagram
    participant App as Application
    participant LLM as OpenRouterLLM
    participant Conv as Message Converter
    participant Client as OpenRouterClient
    participant API as OpenRouter API

    App->>LLM: invoke([HumanMessage("Hello")])
    LLM->>LLM: _agenerate()

    LLM->>Conv: langchain_messages_to_opencode()
    Conv-->>LLM: [Message]

    LLM->>LLM: _build_request()
    LLM->>Client: complete(request)
    Client->>API: POST /chat/completions
    API-->>Client: Response JSON
    Client-->>LLM: CompletionResponse

    LLM->>Conv: opencode_to_langchain(message)
    Conv-->>LLM: AIMessage

    LLM->>LLM: Create ChatResult
    LLM-->>App: ChatResult
```

---

## 6. Sequence Diagram - Streaming Response

```mermaid
sequenceDiagram
    participant App as Application
    participant LLM as OpenRouterLLM
    participant Client as OpenRouterClient
    participant Callback as StreamingCallback
    participant API as OpenRouter API

    App->>LLM: astream(messages, callbacks=[streamer])

    LLM->>Client: stream(request)
    Client->>API: POST /chat/completions (stream=true)

    loop For each SSE event
        API-->>Client: data: {...}
        Client-->>LLM: StreamChunk

        LLM->>LLM: Create AIMessageChunk
        LLM->>Callback: on_llm_new_token(content)
        Callback->>Callback: _buffer += content
        Callback->>App: on_token(content) [optional]

        LLM-->>App: yield ChatGenerationChunk
    end

    API-->>Client: data: [DONE]
    Client-->>LLM: stream ends

    LLM->>Callback: on_llm_end(response)
    Callback->>App: on_complete(buffer) [optional]
```

---

## 7. Sequence Diagram - Agent Tool Execution

```mermaid
sequenceDiagram
    participant App as Application
    participant Agent as OpenCodeAgent
    participant Memory as ConversationMemory
    participant LLM as OpenRouterLLM
    participant Tool as LangChainToolAdapter

    App->>Agent: run("Read /tmp/file.txt")

    Agent->>Memory: add_message(user_msg)

    loop Until done or max_iterations
        Agent->>Memory: to_langchain_messages()
        Memory-->>Agent: [BaseMessage]

        Agent->>LLM: ainvoke(messages)
        LLM-->>Agent: AIMessage

        alt Has tool_calls
            Agent->>Memory: add_message(assistant_msg)

            loop For each tool_call
                Agent->>Agent: lookup tool
                Agent->>Tool: _arun(**args)
                Tool->>Tool: Execute via ToolExecutor
                Tool-->>Agent: result string

                Agent->>Agent: Create ToolCallRecord
                Agent->>Memory: add_message(tool_result)
            end
        else No tool_calls (done)
            Agent->>Memory: add_message(assistant_msg)
            Note right of Agent: Exit loop
        end
    end

    Agent->>Agent: Build AgentResult
    Agent-->>App: AgentResult
```

---

## 8. Sequence Diagram - Tool Adaptation

```mermaid
sequenceDiagram
    participant App as Application
    participant Adapter as LangChainToolAdapter
    participant Executor as ToolExecutor
    participant OCTool as OpenCode BaseTool

    App->>Adapter: invoke({"path": "/tmp/file"})

    Adapter->>Adapter: Validate against args_schema

    Adapter->>Executor: execute(tool, params, context)
    Executor->>OCTool: execute(params, context)

    alt Success
        OCTool-->>Executor: ToolResult(success=True, output=...)
        Executor-->>Adapter: ToolResult
        Adapter->>Adapter: Format output as string
        Adapter-->>App: "File contents..."
    else Error
        OCTool-->>Executor: ToolResult(success=False, error=...)
        Executor-->>Adapter: ToolResult
        Adapter-->>App: "Error: ..."
    end
```

---

## 9. State Diagram - Agent Execution

```mermaid
stateDiagram-v2
    [*] --> Initialized: run() called

    Initialized --> AddingUserMessage: Add user input
    AddingUserMessage --> PreparingMessages: Get memory

    PreparingMessages --> InvokingLLM: Send to LLM

    InvokingLLM --> ParsingResponse: Response received
    InvokingLLM --> TimedOut: Timeout exceeded
    InvokingLLM --> Error: LLM error

    ParsingResponse --> ExecutingTools: Has tool_calls
    ParsingResponse --> Complete: No tool_calls

    ExecutingTools --> ToolExecution: For each tool
    ToolExecution --> AddingToolResult: Tool complete
    AddingToolResult --> ExecutingTools: More tools
    AddingToolResult --> CheckIteration: All tools done

    CheckIteration --> PreparingMessages: iterations < max
    CheckIteration --> MaxIterations: iterations >= max

    Complete --> BuildResult: Build AgentResult
    MaxIterations --> BuildResult
    TimedOut --> BuildResult
    Error --> BuildResult

    BuildResult --> [*]: Return result
```

---

## 10. State Diagram - Memory Management

```mermaid
stateDiagram-v2
    [*] --> Empty: Created

    Empty --> HasSystem: set_system_message()
    Empty --> HasMessages: add_message()

    HasSystem --> HasBoth: add_message()
    HasMessages --> HasBoth: set_system_message()

    HasBoth --> HasBoth: add_message()
    HasBoth --> Trimmed: max_messages exceeded

    Trimmed --> HasBoth: Continue adding

    HasBoth --> TokenTrimmed: trim(max_tokens)
    TokenTrimmed --> HasBoth: Continue adding

    HasBoth --> Empty: clear()
    HasSystem --> Empty: clear()
    HasMessages --> Empty: clear()

    HasBoth --> HasSystem: clear_history()
```

---

## 11. Component Diagram - LangChain Package

```mermaid
flowchart TB
    subgraph LangChainPkg["src/opencode/langchain/"]
        INIT["__init__.py"]
        LLM["llm.py<br/>OpenRouterLLM"]
        TOOLS["tools.py<br/>Tool Adapters"]
        MEMORY["memory.py<br/>ConversationMemory"]
        AGENT["agent.py<br/>OpenCodeAgent"]
        CALLBACKS["callbacks.py<br/>Callback Handlers"]
        MESSAGES["messages.py<br/>Message Conversion"]
    end

    subgraph LLMPkg["src/opencode/llm/"]
        CLIENT["client.py"]
        MODELS["models.py"]
    end

    subgraph ToolsPkg["src/opencode/tools/"]
        BASE["base.py"]
        EXECUTOR["executor.py"]
    end

    subgraph LangChain["langchain_core"]
        LC_LLM["language_models"]
        LC_TOOLS["tools"]
        LC_MSG["messages"]
        LC_CB["callbacks"]
    end

    LLM --> CLIENT
    LLM --> MODELS
    LLM --> MESSAGES
    LLM --> LC_LLM

    TOOLS --> BASE
    TOOLS --> EXECUTOR
    TOOLS --> LC_TOOLS

    MEMORY --> MODELS
    MEMORY --> MESSAGES
    MEMORY --> LC_MSG

    AGENT --> LLM
    AGENT --> TOOLS
    AGENT --> MEMORY
    AGENT --> CALLBACKS

    CALLBACKS --> LC_CB

    MESSAGES --> MODELS
    MESSAGES --> LC_MSG

    INIT --> LLM
    INIT --> TOOLS
    INIT --> MEMORY
    INIT --> AGENT
    INIT --> CALLBACKS
    INIT --> MESSAGES
```

---

## 12. Activity Diagram - Agent Run Flow

```mermaid
flowchart TD
    START([run input]) --> ADD_USER[Add user message to memory]
    ADD_USER --> CHECK_ITER{iterations < max?}

    CHECK_ITER -->|Yes| CHECK_TIME{timeout exceeded?}
    CHECK_ITER -->|No| MAX_ITER[stopped_reason = max_iterations]

    CHECK_TIME -->|No| GET_MSGS[Get messages from memory]
    CHECK_TIME -->|Yes| TIMEOUT[stopped_reason = timeout]

    GET_MSGS --> INVOKE_LLM[Invoke LLM with tools]
    INVOKE_LLM --> CHECK_TOOLS{Has tool_calls?}

    CHECK_TOOLS -->|Yes| ADD_ASST[Add assistant message]
    CHECK_TOOLS -->|No| DONE[stopped_reason = complete]

    ADD_ASST --> EXEC_TOOLS[Execute each tool]
    EXEC_TOOLS --> RECORD[Record ToolCallRecord]
    RECORD --> ADD_RESULT[Add tool result to memory]
    ADD_RESULT --> INC_ITER[iterations += 1]
    INC_ITER --> CHECK_ITER

    DONE --> ADD_FINAL[Add final assistant message]
    MAX_ITER --> BUILD[Build AgentResult]
    TIMEOUT --> BUILD
    ADD_FINAL --> BUILD

    BUILD --> RETURN([Return AgentResult])
```

---

## 13. Data Flow Diagram - Message Conversion

```mermaid
flowchart LR
    subgraph LangChain["LangChain Messages"]
        SYS_LC[SystemMessage]
        HUM_LC[HumanMessage]
        AI_LC[AIMessage]
        TOOL_LC[ToolMessage]
    end

    subgraph Convert["messages.py"]
        L2O[langchain_to_opencode]
        O2L[opencode_to_langchain]
    end

    subgraph OpenCode["OpenCode Messages"]
        SYS_OC[Message role=SYSTEM]
        USR_OC[Message role=USER]
        ASST_OC[Message role=ASSISTANT]
        TOOL_OC[Message role=TOOL]
    end

    SYS_LC --> L2O --> SYS_OC
    HUM_LC --> L2O --> USR_OC
    AI_LC --> L2O --> ASST_OC
    TOOL_LC --> L2O --> TOOL_OC

    SYS_OC --> O2L --> SYS_LC
    USR_OC --> O2L --> HUM_LC
    ASST_OC --> O2L --> AI_LC
    TOOL_OC --> O2L --> TOOL_LC
```

---

## 14. Integration Architecture

```mermaid
flowchart TB
    subgraph Application
        APP[Application Code]
    end

    subgraph LangChainLayer["LangChain Integration Layer"]
        AGENT[OpenCodeAgent]
        LLM[OpenRouterLLM]
        MEMORY[ConversationMemory]
        TOOLS_LC[LangChain Tools]
    end

    subgraph OpenCodeCore["OpenCode Core"]
        CLIENT[OpenRouterClient]
        TOOLS_OC[OpenCode Tools]
        EXECUTOR[ToolExecutor]
    end

    subgraph External["External Services"]
        OPENROUTER[OpenRouter API]
    end

    APP --> AGENT
    AGENT --> LLM
    AGENT --> MEMORY
    AGENT --> TOOLS_LC

    LLM --> CLIENT
    TOOLS_LC --> EXECUTOR
    EXECUTOR --> TOOLS_OC

    CLIENT --> OPENROUTER
```

---

## Notes

- OpenRouterLLM extends LangChain's BaseChatModel for compatibility
- Tool adapters work bidirectionally (OpenCode ↔ LangChain)
- Memory supports multiple strategies (basic, sliding window, summary)
- Agent implements ReAct-style tool-calling loop
- Callbacks integrate with LangChain's callback system
- Message conversion handles all standard message types including tool calls
