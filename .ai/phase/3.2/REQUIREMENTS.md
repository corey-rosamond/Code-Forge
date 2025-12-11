# Phase 3.2: LangChain Integration - Requirements

**Phase:** 3.2
**Name:** LangChain Integration
**Dependencies:** Phase 2.1 (Tool System Foundation), Phase 3.1 (OpenRouter Client)

---

## Overview

Phase 3.2 integrates LangChain 1.0 as the middleware layer for agent orchestration. This provides a standardized abstraction over LLM interactions, enabling tool binding, conversation memory, and sophisticated agent patterns while leveraging the OpenRouter client from Phase 3.1.

---

## Goals

1. Create a LangChain-compatible LLM wrapper around OpenRouterClient
2. Implement tool adapters that bridge BaseTool to LangChain tools
3. Build an agent executor with configurable strategies
4. Provide conversation memory management
5. Support LangChain's callback system for observability

---

## Non-Goals (This Phase)

- Advanced RAG (Retrieval Augmented Generation) pipelines
- Vector store integration
- Multi-agent orchestration (Phase 7.1)
- Custom prompt templates beyond basics

---

## Functional Requirements

### FR-1: LangChain LLM Wrapper

**FR-1.1:** Create `OpenRouterLLM` class extending LangChain's `BaseChatModel`
- Must implement `_generate()` for synchronous calls
- Must implement `_agenerate()` for async calls
- Must implement `_stream()` for sync streaming
- Must implement `_astream()` for async streaming

**FR-1.2:** Support all LangChain message types
- `SystemMessage` → Code-Forge `Message.system()`
- `HumanMessage` → Code-Forge `Message.user()`
- `AIMessage` → Code-Forge `Message.assistant()`
- `ToolMessage` → Code-Forge `Message.tool_result()`

**FR-1.3:** Handle tool calls in LangChain format
- Parse `AIMessage.tool_calls` from responses
- Convert Code-Forge `ToolCall` to LangChain format
- Support `tool_choice` parameter

**FR-1.4:** Pass through model parameters
- temperature, max_tokens, top_p
- frequency_penalty, presence_penalty
- stop sequences

**FR-1.5:** Support model binding
- `llm.bind_tools([tools])` returns new LLM with tools bound
- `llm.with_structured_output(schema)` for structured responses

### FR-2: Tool Adapters

**FR-2.1:** Create `LangChainToolAdapter` to wrap Code-Forge `BaseTool`
- Convert Code-Forge tool parameters to LangChain tool schema
- Execute tool through Code-Forge's `ToolExecutor`
- Return results in LangChain expected format

**FR-2.2:** Support both sync and async execution
- `_run()` for synchronous tool execution
- `_arun()` for asynchronous tool execution

**FR-2.3:** Handle tool errors gracefully
- Catch `ToolError` and convert to LangChain error format
- Preserve error details for debugging

**FR-2.4:** Provide reverse adapter for LangChain tools
- `Code-ForgeToolAdapter` wraps LangChain tools as Code-Forge `BaseTool`
- Enable use of existing LangChain tools in Code-Forge

### FR-3: Agent Executor

**FR-3.1:** Create `Code-ForgeAgent` class for tool-calling agents
- Support ReAct-style reasoning loop
- Configurable maximum iterations
- Timeout handling per iteration and overall

**FR-3.2:** Implement agent loop
- Send messages to LLM with tools
- Parse tool calls from response
- Execute tools
- Add tool results to conversation
- Continue until stop condition

**FR-3.3:** Support multiple stop conditions
- `finish_reason == "stop"` (model done)
- `finish_reason == "end_turn"` (Anthropic models)
- Max iterations reached
- Timeout exceeded
- Explicit stop tool called

**FR-3.4:** Provide streaming agent execution
- Stream LLM responses as they arrive
- Yield intermediate tool call/result events
- Support partial content display

**FR-3.5:** Handle parallel tool calls
- Some models return multiple tool calls
- Execute in parallel when possible
- Collect all results before continuing

### FR-4: Conversation Memory

**FR-4.1:** Create `ConversationMemory` class
- Store message history
- Support message windowing (last N messages)
- Support token-based truncation

**FR-4.2:** Implement memory backends
- In-memory storage (default)
- Interface for persistent storage (Phase 5.1)

**FR-4.3:** Support memory operations
- `add_message(message)` - add to history
- `get_messages()` - retrieve history
- `clear()` - reset history
- `trim(max_tokens)` - truncate to token budget

**FR-4.4:** Handle system message specially
- System message always at start
- Never truncated by windowing
- Can be updated independently

### FR-5: Callback System

**FR-5.1:** Integrate with LangChain callbacks
- Support `on_llm_start`, `on_llm_end`
- Support `on_tool_start`, `on_tool_end`
- Support `on_chain_start`, `on_chain_end`

**FR-5.2:** Create Code-Forge-specific callbacks
- `Code-ForgeCallbackHandler` base class
- Token usage tracking callback
- Logging callback for debugging

**FR-5.3:** Support callback chaining
- Multiple callbacks can be registered
- Callbacks execute in registration order

---

## Non-Functional Requirements

### NFR-1: Performance
- Agent loop iteration < 100ms overhead (excluding LLM/tool time)
- Memory operations O(1) for add, O(n) for retrieval
- Streaming latency < 50ms additional overhead

### NFR-2: Compatibility
- LangChain 0.3.x compatibility
- Support LCEL (LangChain Expression Language) chains
- Work with standard LangChain tools

### NFR-3: Observability
- All LLM calls logged with timing
- Tool executions traced
- Token usage aggregated across agent run

### NFR-4: Error Handling
- Graceful degradation on tool errors
- Retry logic delegated to OpenRouterClient
- Clear error messages with context

---

## Technical Specifications

### Package Structure

```
src/forge/langchain/
├── __init__.py           # Package exports
├── llm.py                # OpenRouterLLM wrapper
├── tools.py              # Tool adapters
├── agent.py              # Code-ForgeAgent
├── memory.py             # ConversationMemory
└── callbacks.py          # Callback handlers
```

### Dependencies

```toml
[tool.poetry.dependencies]
langchain = "^0.3"
langchain-core = "^0.3"
```

### Class Signatures

```python
# llm.py
class OpenRouterLLM(BaseChatModel):
    """LangChain wrapper for OpenRouter client."""

    client: OpenRouterClient
    model: str
    temperature: float = 1.0
    max_tokens: int | None = None

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs,
    ) -> ChatResult: ...

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs,
    ) -> ChatResult: ...

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs,
    ) -> Iterator[ChatGenerationChunk]: ...

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs,
    ) -> AsyncIterator[ChatGenerationChunk]: ...

    def bind_tools(
        self,
        tools: Sequence[BaseTool | ToolDefinition],
        **kwargs,
    ) -> "OpenRouterLLM": ...


# tools.py
class LangChainToolAdapter(BaseTool):
    """Adapts Code-Forge BaseTool to LangChain tool."""

    forge_tool: "forge.tools.BaseTool"

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def args_schema(self) -> type[BaseModel]: ...

    def _run(self, **kwargs) -> str: ...

    async def _arun(self, **kwargs) -> str: ...


class Code-ForgeToolAdapter(BaseTool):
    """Adapts LangChain tool to Code-Forge BaseTool."""

    langchain_tool: "langchain.tools.BaseTool"

    # BaseTool interface implementation


# agent.py
class Code-ForgeAgent:
    """Agent executor for tool-calling workflows."""

    llm: OpenRouterLLM
    tools: list[BaseTool]
    memory: ConversationMemory
    max_iterations: int = 10
    timeout: float = 300.0

    async def run(
        self,
        input: str,
        *,
        callbacks: list[BaseCallbackHandler] | None = None,
    ) -> AgentResult: ...

    async def stream(
        self,
        input: str,
        *,
        callbacks: list[BaseCallbackHandler] | None = None,
    ) -> AsyncIterator[AgentEvent]: ...


@dataclass
class AgentResult:
    """Result of agent execution."""
    output: str
    messages: list[Message]
    tool_calls: list[ToolCallRecord]
    usage: TokenUsage
    iterations: int


@dataclass
class AgentEvent:
    """Event during agent execution."""
    type: Literal["llm_start", "llm_chunk", "llm_end",
                  "tool_start", "tool_end", "agent_end"]
    data: dict


# memory.py
class ConversationMemory:
    """Manages conversation history."""

    messages: list[Message]
    system_message: Message | None
    max_messages: int | None = None
    max_tokens: int | None = None

    def add_message(self, message: Message) -> None: ...
    def add_messages(self, messages: list[Message]) -> None: ...
    def get_messages(self) -> list[Message]: ...
    def set_system_message(self, message: Message) -> None: ...
    def clear(self) -> None: ...
    def trim(self, max_tokens: int) -> None: ...
    def to_langchain_messages(self) -> list[BaseMessage]: ...


# callbacks.py
class Code-ForgeCallbackHandler(BaseCallbackHandler):
    """Base callback handler for Code-Forge."""
    pass


class TokenTrackingCallback(Code-ForgeCallbackHandler):
    """Tracks token usage across calls."""

    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0

    def on_llm_end(self, response: LLMResult, **kwargs) -> None: ...
    def get_usage(self) -> TokenUsage: ...
    def reset(self) -> None: ...


class LoggingCallback(Code-ForgeCallbackHandler):
    """Logs all LLM and tool events."""

    logger: Logger

    def on_llm_start(self, ...) -> None: ...
    def on_llm_end(self, ...) -> None: ...
    def on_tool_start(self, ...) -> None: ...
    def on_tool_end(self, ...) -> None: ...
```

---

## Message Conversion

### LangChain to Code-Forge

```python
def langchain_to_forge(message: BaseMessage) -> Message:
    """Convert LangChain message to Code-Forge message."""
    if isinstance(message, SystemMessage):
        return Message.system(message.content)
    elif isinstance(message, HumanMessage):
        return Message.user(message.content)
    elif isinstance(message, AIMessage):
        tool_calls = None
        if message.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc["id"],
                    type="function",
                    function={
                        "name": tc["name"],
                        "arguments": json.dumps(tc["args"])
                    }
                )
                for tc in message.tool_calls
            ]
        return Message.assistant(message.content, tool_calls=tool_calls)
    elif isinstance(message, ToolMessage):
        return Message.tool_result(message.tool_call_id, message.content)
    else:
        raise ValueError(f"Unknown message type: {type(message)}")
```

### Code-Forge to LangChain

```python
def forge_to_langchain(message: Message) -> BaseMessage:
    """Convert Code-Forge message to LangChain message."""
    if message.role == MessageRole.SYSTEM:
        return SystemMessage(content=message.content)
    elif message.role == MessageRole.USER:
        return HumanMessage(content=message.content)
    elif message.role == MessageRole.ASSISTANT:
        tool_calls = []
        if message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "name": tc.function["name"],
                    "args": json.loads(tc.function["arguments"])
                }
                for tc in message.tool_calls
            ]
        return AIMessage(content=message.content or "", tool_calls=tool_calls)
    elif message.role == MessageRole.TOOL:
        return ToolMessage(
            content=message.content,
            tool_call_id=message.tool_call_id
        )
```

---

## Agent Execution Flow

```
1. User input received
2. Add user message to memory
3. Get messages from memory
4. Send to LLM with tools
5. Parse response
6. If tool calls:
   a. Execute each tool
   b. Add tool results to memory
   c. Go to step 3 (if iterations < max)
7. If content only:
   a. Add assistant message to memory
   b. Return result
8. If max iterations reached:
   a. Return partial result with warning
```

---

## Integration Points

### With Phase 2.1 (Tool System)
- `LangChainToolAdapter` wraps `BaseTool`
- Uses `ToolExecutor` for execution
- Respects `ToolResult` format

### With Phase 3.1 (OpenRouter Client)
- `OpenRouterLLM` wraps `OpenRouterClient`
- Delegates all API calls to client
- Uses client's error handling and retry

### With Phase 4.1 (Permissions)
- Tool execution checks permissions
- Agent respects permission denials
- Callbacks report permission events

### With Phase 5.1 (Sessions)
- Memory can be persisted
- Agent state saved/restored
- Conversation continuity

---

## Error Scenarios

| Scenario | Handling |
|----------|----------|
| LLM API error | Propagate from OpenRouterClient |
| Tool execution error | Catch, format as tool result, continue |
| Max iterations | Return partial result + warning |
| Timeout | Interrupt, return partial result |
| Invalid tool call | Return error as tool result |
| Memory overflow | Trim oldest messages |

---

## Testing Requirements

1. Unit tests for message conversion (both directions)
2. Unit tests for LangChainToolAdapter
3. Unit tests for OpenRouterLLM (mocked client)
4. Unit tests for ConversationMemory
5. Unit tests for agent loop logic
6. Integration tests with mocked LLM responses
7. Test streaming behavior
8. Test parallel tool execution
9. Test callback invocation order
10. Test coverage ≥ 90%

---

## Acceptance Criteria

1. OpenRouterLLM works with standard LangChain chains
2. Tools can be bound and called through LangChain
3. Agent executes multi-turn tool-calling conversations
4. Memory correctly manages conversation history
5. Callbacks receive all expected events
6. Streaming works for both LLM and agent
7. All message types convert correctly
8. Error handling is graceful and informative
