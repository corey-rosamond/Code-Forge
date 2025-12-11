# Phase 3.2: LangChain Integration - Completion Criteria

**Phase:** 3.2
**Name:** LangChain Integration
**Dependencies:** Phase 2.1 (Tool System Foundation), Phase 3.1 (OpenRouter Client)

---

## Definition of Done

All of the following criteria must be met before Phase 3.2 is considered complete.

---

## Checklist

### Message Conversion (src/forge/langchain/messages.py)
- [ ] langchain_to_forge() converts SystemMessage
- [ ] langchain_to_forge() converts HumanMessage
- [ ] langchain_to_forge() converts AIMessage
- [ ] langchain_to_forge() converts AIMessage with tool_calls
- [ ] langchain_to_forge() converts ToolMessage
- [ ] forge_to_langchain() converts SYSTEM role
- [ ] forge_to_langchain() converts USER role
- [ ] forge_to_langchain() converts ASSISTANT role
- [ ] forge_to_langchain() converts ASSISTANT with tool_calls
- [ ] forge_to_langchain() converts TOOL role
- [ ] langchain_messages_to_forge() batch conversion
- [ ] forge_messages_to_langchain() batch conversion

### OpenRouterLLM (src/forge/langchain/llm.py)
- [ ] OpenRouterLLM extends BaseChatModel
- [ ] Constructor accepts client, model, temperature, max_tokens
- [ ] _llm_type property returns "openrouter"
- [ ] _generate() synchronous generation
- [ ] _agenerate() async generation
- [ ] _stream() synchronous streaming
- [ ] _astream() async streaming
- [ ] bind_tools() returns new instance with tools
- [ ] bind_tools() converts Code-Forge ToolDefinition
- [ ] bind_tools() converts LangChain tools
- [ ] with_structured_output() for function calling
- [ ] _build_request() creates CompletionRequest correctly
- [ ] Parameters pass through (temperature, max_tokens, etc.)
- [ ] Stop sequences merged correctly

### Tool Adapters (src/forge/langchain/tools.py)
- [ ] LangChainToolAdapter wraps Code-Forge BaseTool
- [ ] LangChainToolAdapter.name property
- [ ] LangChainToolAdapter.description property
- [ ] LangChainToolAdapter.args_schema generates Pydantic model
- [ ] LangChainToolAdapter._run() synchronous execution
- [ ] LangChainToolAdapter._arun() async execution
- [ ] Code-ForgeToolAdapter wraps LangChain tool
- [ ] Code-ForgeToolAdapter.name property
- [ ] Code-ForgeToolAdapter.description property
- [ ] Code-ForgeToolAdapter.parameters extracted from schema
- [ ] Code-ForgeToolAdapter.execute() async execution
- [ ] Code-ForgeToolAdapter.to_openai_schema() conversion
- [ ] adapt_tools_for_langchain() batch conversion
- [ ] adapt_tools_for_forge() batch conversion

### Conversation Memory (src/forge/langchain/memory.py)
- [ ] ConversationMemory class implemented
- [ ] add_message() adds to history
- [ ] add_messages() batch add
- [ ] add_langchain_message() with conversion
- [ ] get_messages() returns all with system first
- [ ] get_history() returns only conversation
- [ ] set_system_message() sets/updates system
- [ ] clear() removes all messages
- [ ] clear_history() keeps system message
- [ ] max_messages limit enforced
- [ ] trim() by token count
- [ ] to_langchain_messages() conversion
- [ ] from_langchain_messages() import
- [ ] SlidingWindowMemory implemented
- [ ] SlidingWindowMemory window_size works
- [ ] SummaryMemory implemented
- [ ] SummaryMemory maybe_summarize() works

### Callback Handlers (src/forge/langchain/callbacks.py)
- [ ] Code-ForgeCallbackHandler base class
- [ ] TokenTrackingCallback.on_llm_end() tracks usage
- [ ] TokenTrackingCallback.get_usage() returns TokenUsage
- [ ] TokenTrackingCallback.reset() clears counters
- [ ] LoggingCallback logs LLM events
- [ ] LoggingCallback logs tool events
- [ ] LoggingCallback includes timing
- [ ] StreamingCallback.on_llm_new_token() accumulates
- [ ] StreamingCallback.get_buffer() returns content
- [ ] StreamingCallback custom handlers work
- [ ] CompositeCallback dispatches to all

### Agent Executor (src/forge/langchain/agent.py)
- [ ] AgentEventType enum defined
- [ ] AgentEvent dataclass defined
- [ ] ToolCallRecord dataclass defined
- [ ] AgentResult dataclass defined
- [ ] Code-ForgeAgent class implemented
- [ ] Code-ForgeAgent.run() executes to completion
- [ ] Code-ForgeAgent.run() handles tool calls
- [ ] Code-ForgeAgent.run() tracks iterations
- [ ] Code-ForgeAgent.run() respects max_iterations
- [ ] Code-ForgeAgent.run() respects timeout
- [ ] Code-ForgeAgent.stream() yields events
- [ ] Code-ForgeAgent.stream() LLM_START event
- [ ] Code-ForgeAgent.stream() LLM_CHUNK events
- [ ] Code-ForgeAgent.stream() LLM_END event
- [ ] Code-ForgeAgent.stream() TOOL_START events
- [ ] Code-ForgeAgent.stream() TOOL_END events
- [ ] Code-ForgeAgent.stream() AGENT_END event
- [ ] Code-ForgeAgent.reset() clears history
- [ ] Multiple tool calls handled in parallel
- [ ] Error handling for tool failures
- [ ] Error handling for unknown tools

### Package Structure
- [ ] src/forge/langchain/__init__.py exports all public classes
- [ ] src/forge/langchain/messages.py exists
- [ ] src/forge/langchain/llm.py exists
- [ ] src/forge/langchain/tools.py exists
- [ ] src/forge/langchain/memory.py exists
- [ ] src/forge/langchain/callbacks.py exists
- [ ] src/forge/langchain/agent.py exists
- [ ] All imports work correctly
- [ ] No circular dependencies

### Testing
- [ ] Unit tests for message conversion (both directions)
- [ ] Unit tests for OpenRouterLLM (mocked client)
- [ ] Unit tests for LangChainToolAdapter
- [ ] Unit tests for Code-ForgeToolAdapter
- [ ] Unit tests for ConversationMemory
- [ ] Unit tests for SlidingWindowMemory
- [ ] Unit tests for callback handlers
- [ ] Unit tests for agent loop logic
- [ ] Test streaming behavior
- [ ] Test parallel tool execution
- [ ] Test max iterations handling
- [ ] Test timeout handling
- [ ] Test coverage ≥ 90%

---

## Verification Commands

```bash
# 1. Verify module structure
ls -la src/forge/langchain/
# Expected: __init__.py, messages.py, llm.py, tools.py, memory.py, callbacks.py, agent.py

# 2. Test imports
python -c "
from forge.langchain import (
    OpenRouterLLM,
    LangChainToolAdapter,
    Code-ForgeToolAdapter,
    adapt_tools_for_langchain,
    adapt_tools_for_forge,
    ConversationMemory,
    SlidingWindowMemory,
    SummaryMemory,
    Code-ForgeAgent,
    AgentEvent,
    AgentEventType,
    AgentResult,
    ToolCallRecord,
    TokenTrackingCallback,
    LoggingCallback,
    StreamingCallback,
    CompositeCallback,
    langchain_to_forge,
    forge_to_langchain,
)
print('All LangChain imports successful')
"

# 3. Test message conversion
python -c "
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from forge.langchain import langchain_to_forge, forge_to_langchain
from forge.llm import Message, MessageRole

# LangChain to Code-Forge
sys_msg = langchain_to_forge(SystemMessage(content='Be helpful'))
assert sys_msg.role == MessageRole.SYSTEM
assert sys_msg.content == 'Be helpful'

human_msg = langchain_to_forge(HumanMessage(content='Hello'))
assert human_msg.role == MessageRole.USER

ai_msg = langchain_to_forge(AIMessage(content='Hi there'))
assert ai_msg.role == MessageRole.ASSISTANT

tool_msg = langchain_to_forge(ToolMessage(content='result', tool_call_id='call_123'))
assert tool_msg.role == MessageRole.TOOL
assert tool_msg.tool_call_id == 'call_123'

# Code-Forge to LangChain
lc_sys = forge_to_langchain(Message.system('Be helpful'))
assert isinstance(lc_sys, SystemMessage)

lc_human = forge_to_langchain(Message.user('Hello'))
assert isinstance(lc_human, HumanMessage)

lc_ai = forge_to_langchain(Message.assistant('Hi'))
assert isinstance(lc_ai, AIMessage)

lc_tool = forge_to_langchain(Message.tool_result('call_123', 'result'))
assert isinstance(lc_tool, ToolMessage)

print('Message conversion: OK')
"

# 4. Test OpenRouterLLM initialization
python -c "
from forge.llm import OpenRouterClient
from forge.langchain import OpenRouterLLM

client = OpenRouterClient(api_key='test-key')
llm = OpenRouterLLM(
    client=client,
    model='anthropic/claude-3-opus',
    temperature=0.7,
    max_tokens=1000,
)

assert llm.model == 'anthropic/claude-3-opus'
assert llm.temperature == 0.7
assert llm.max_tokens == 1000
assert llm._llm_type == 'openrouter'

print('OpenRouterLLM initialization: OK')
"

# 5. Test tool adapter
python -c "
from forge.tools import ReadTool
from forge.langchain import LangChainToolAdapter

read_tool = ReadTool()
adapter = LangChainToolAdapter(forge_tool=read_tool)

assert adapter.name == read_tool.name
assert adapter.description == read_tool.description
assert adapter.args_schema is not None

schema = adapter.args_schema.model_json_schema()
assert 'properties' in schema
assert 'file_path' in schema['properties']

print('Tool adapter: OK')
"

# 6. Test ConversationMemory
python -c "
from forge.langchain import ConversationMemory
from forge.llm import Message

memory = ConversationMemory(max_messages=5)

# Set system message
memory.set_system_message(Message.system('Be helpful'))

# Add messages
memory.add_message(Message.user('Hello'))
memory.add_message(Message.assistant('Hi!'))

# Check messages
messages = memory.get_messages()
assert len(messages) == 3  # system + 2 conversation
assert messages[0].role.value == 'system'

# Check history (no system)
history = memory.get_history()
assert len(history) == 2

# Test max_messages
for i in range(10):
    memory.add_message(Message.user(f'Msg {i}'))

assert len(memory.get_history()) == 5  # Limited to max

# Test clear
memory.clear()
assert len(memory.get_messages()) == 0

print('ConversationMemory: OK')
"

# 7. Test SlidingWindowMemory
python -c "
from forge.langchain import SlidingWindowMemory
from forge.llm import Message

memory = SlidingWindowMemory(window_size=2)

# Add 5 exchanges
for i in range(5):
    memory.add_message(Message.user(f'Q{i}'))
    memory.add_message(Message.assistant(f'A{i}'))

# Should only have last 2 exchanges (4 messages)
history = memory.get_history()
assert len(history) <= 4

print('SlidingWindowMemory: OK')
"

# 8. Test TokenTrackingCallback
python -c "
from forge.langchain import TokenTrackingCallback
from langchain_core.outputs import LLMResult, Generation
from uuid import uuid4

tracker = TokenTrackingCallback()

# Simulate LLM response
response = LLMResult(
    generations=[[Generation(text='Hello')]],
    llm_output={'usage': {'prompt_tokens': 100, 'completion_tokens': 50}}
)

tracker.on_llm_end(response, run_id=uuid4())

usage = tracker.get_usage()
assert usage.prompt_tokens == 100
assert usage.completion_tokens == 50
assert usage.total_tokens == 150
assert tracker.call_count == 1

# Reset
tracker.reset()
assert tracker.get_usage().total_tokens == 0

print('TokenTrackingCallback: OK')
"

# 9. Test AgentResult structure
python -c "
from forge.langchain import AgentResult, ToolCallRecord, AgentEvent, AgentEventType
from forge.llm import Message
from forge.llm.models import TokenUsage

# Create tool call record
record = ToolCallRecord(
    id='call_123',
    name='read',
    arguments={'path': '/tmp/test'},
    result='file contents',
    success=True,
    duration=0.5,
)

# Create agent result
result = AgentResult(
    output='Done',
    messages=[Message.user('Hello')],
    tool_calls=[record],
    usage=TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
    iterations=2,
    duration=1.5,
    stopped_reason='complete',
)

assert result.output == 'Done'
assert len(result.tool_calls) == 1
assert result.iterations == 2

# Create agent event
event = AgentEvent(type=AgentEventType.LLM_START, data={'iteration': 1})
assert event.type == AgentEventType.LLM_START

print('Agent structures: OK')
"

# 10. Test LangChain message conversion
python -c "
from forge.langchain import ConversationMemory
from forge.llm import Message
from langchain_core.messages import SystemMessage, HumanMessage

memory = ConversationMemory()
memory.set_system_message(Message.system('Be helpful'))
memory.add_message(Message.user('Hello'))
memory.add_message(Message.assistant('Hi!'))

# Convert to LangChain
lc_messages = memory.to_langchain_messages()
assert len(lc_messages) == 3
assert isinstance(lc_messages[0], SystemMessage)
assert isinstance(lc_messages[1], HumanMessage)

print('LangChain conversion: OK')
"

# 11. Run all unit tests
pytest tests/unit/langchain/ -v --cov=forge.langchain --cov-report=term-missing

# Expected: All tests pass, coverage ≥ 90%

# 12. Type checking
mypy src/forge/langchain/ --strict
# Expected: No errors

# 13. Linting
ruff check src/forge/langchain/
# Expected: No errors

# 14. Integration test with mock
python -c "
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import HumanMessage, AIMessage

async def test_llm_integration():
    from forge.langchain import OpenRouterLLM
    from forge.llm.models import CompletionResponse, CompletionChoice, TokenUsage, Message

    # Mock client
    mock_client = MagicMock()
    mock_response = CompletionResponse(
        id='gen-test',
        model='test/model',
        choices=[CompletionChoice(
            index=0,
            message=Message.assistant('Hello from mock!'),
            finish_reason='stop',
        )],
        usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        created=1234567890,
    )
    mock_client.complete = AsyncMock(return_value=mock_response)

    # Create LLM
    llm = OpenRouterLLM(client=mock_client, model='test/model')

    # Invoke
    response = await llm.ainvoke([HumanMessage(content='Hello')])

    assert isinstance(response, AIMessage)
    assert response.content == 'Hello from mock!'
    mock_client.complete.assert_called_once()

    print('Integration test: OK')

asyncio.run(test_llm_integration())
"

# 15. Test bind_tools
python -c "
from forge.langchain import OpenRouterLLM
from forge.llm import OpenRouterClient
from forge.llm.models import ToolDefinition

client = OpenRouterClient(api_key='test')
llm = OpenRouterLLM(client=client, model='test')

# Create tool definition
tool = ToolDefinition(
    name='test_tool',
    description='A test tool',
    parameters={'type': 'object', 'properties': {'arg': {'type': 'string'}}}
)

# Bind tools
llm_with_tools = llm.bind_tools([tool])

assert llm_with_tools is not llm  # New instance
assert len(llm_with_tools._bound_tools) == 1

print('bind_tools: OK')
"
```

---

## Quality Gates

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Test Coverage | ≥ 90% | `pytest --cov` |
| Type Hints | 100% public APIs | `mypy --strict` |
| Lint Errors | 0 | `ruff check` |
| McCabe Complexity | ≤ 10 | `ruff check --select=C901` |

---

## Files to Create

| File | Purpose |
|------|---------|
| `src/forge/langchain/__init__.py` | Package exports |
| `src/forge/langchain/messages.py` | Message conversion utilities |
| `src/forge/langchain/llm.py` | OpenRouterLLM wrapper |
| `src/forge/langchain/tools.py` | Tool adapters |
| `src/forge/langchain/memory.py` | Conversation memory classes |
| `src/forge/langchain/callbacks.py` | Callback handlers |
| `src/forge/langchain/agent.py` | Agent executor |
| `tests/unit/langchain/__init__.py` | Test package |
| `tests/unit/langchain/test_messages.py` | Message conversion tests |
| `tests/unit/langchain/test_llm.py` | LLM wrapper tests |
| `tests/unit/langchain/test_tools.py` | Tool adapter tests |
| `tests/unit/langchain/test_memory.py` | Memory tests |
| `tests/unit/langchain/test_callbacks.py` | Callback tests |
| `tests/unit/langchain/test_agent.py` | Agent tests |

---

## Dependencies to Verify

Ensure these are in `pyproject.toml`:
```toml
[tool.poetry.dependencies]
langchain = "^0.3"
langchain-core = "^0.3"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-asyncio = "^0.23"
pytest-cov = "^4.1"
```

---

## Manual Testing Checklist

(Requires valid OPENROUTER_API_KEY)

- [ ] Create OpenRouterLLM with real client
- [ ] Send simple message and receive response
- [ ] Test streaming response
- [ ] Bind tools and verify tool calls work
- [ ] Create agent with tools
- [ ] Run agent with tool-using task
- [ ] Verify token tracking across multiple calls
- [ ] Test memory windowing with long conversation
- [ ] Verify agent timeout behavior

---

## Integration Points

Phase 3.2 provides the LangChain layer for:

| Consumer | What It Uses |
|----------|--------------|
| Phase 5.1 (Sessions) | ConversationMemory for persistence |
| Phase 5.2 (Context) | Memory trimming for token management |
| Phase 6.2 (Modes) | Agent streaming for real-time output |
| Phase 7.1 (Subagents) | Agent executor for sub-tasks |

---

## Sign-Off

Phase 3.2 is complete when:

1. [ ] All checklist items above are checked
2. [ ] All verification commands pass
3. [ ] All quality gates are met
4. [ ] Manual testing completed (if API key available)
5. [ ] Code has been reviewed (if applicable)
6. [ ] No TODO comments remain in Phase 3.2 code

---

## Next Phase

After completing Phase 3.2, proceed to:
- **Phase 4.1: Permission System**

Phase 4.1 will implement:
- Permission levels (ALLOW, ASK, DENY)
- Permission rules and matching
- User confirmation flow
- Permission persistence
