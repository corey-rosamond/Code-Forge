# Phase 3.1: OpenRouter Client - Completion Criteria

**Phase:** 3.1
**Name:** OpenRouter Client
**Dependencies:** Phase 1.1 (Project Foundation), Phase 1.2 (Configuration)

---

## Definition of Done

All of the following criteria must be met before Phase 3.1 is considered complete.

---

## Checklist

### Message Models (src/forge/llm/models.py)
- [ ] MessageRole enum defined (SYSTEM, USER, ASSISTANT, TOOL)
- [ ] ContentPart dataclass for multimodal content
- [ ] ToolCall dataclass with id, type, function
- [ ] Message dataclass with role, content, name, tool_call_id, tool_calls
- [ ] Message.to_dict() serializes correctly
- [ ] Message.from_dict() deserializes correctly
- [ ] Message.system() factory method
- [ ] Message.user() factory method
- [ ] Message.assistant() factory method
- [ ] Message.tool_result() factory method

### Tool Definition Models (src/forge/llm/models.py)
- [ ] ToolDefinition dataclass with name, description, parameters
- [ ] ToolDefinition.to_dict() returns OpenAI function format

### Request Models (src/forge/llm/models.py)
- [ ] CompletionRequest dataclass with all parameters
- [ ] CompletionRequest.to_dict() serializes correctly
- [ ] Supports: model, messages, tools, tool_choice
- [ ] Supports: temperature, max_tokens, top_p
- [ ] Supports: frequency_penalty, presence_penalty, stop
- [ ] Supports: stream, transforms, route (OpenRouter-specific)

### Response Models (src/forge/llm/models.py)
- [ ] TokenUsage dataclass with prompt/completion/total tokens
- [ ] CompletionChoice dataclass with index, message, finish_reason
- [ ] CompletionResponse dataclass with id, model, choices, usage
- [ ] CompletionResponse.from_dict() parses API response
- [ ] StreamDelta dataclass with role, content, tool_calls
- [ ] StreamChunk dataclass with id, model, delta, finish_reason, usage
- [ ] StreamChunk.from_dict() parses streaming chunks

### Error Classes (src/forge/llm/errors.py)
- [ ] LLMError base class extends Code-ForgeError
- [ ] AuthenticationError for 401 responses
- [ ] RateLimitError with retry_after attribute
- [ ] ModelNotFoundError with model_id attribute
- [ ] ContextLengthError with max/requested tokens
- [ ] ContentPolicyError for content violations
- [ ] ProviderError for upstream provider errors

### Routing (src/forge/llm/routing.py)
- [ ] RouteVariant enum (DEFAULT, NITRO, FLOOR, ONLINE, THINKING)
- [ ] apply_variant() adds suffix to model ID
- [ ] parse_model_id() extracts base model and variant
- [ ] resolve_model_alias() resolves common aliases
- [ ] MODEL_ALIASES dict with common shortcuts

### OpenRouter Client (src/forge/llm/client.py)
- [ ] OpenRouterClient class with constructor
- [ ] Constructor accepts: api_key, base_url, app_name, app_url, timeout, max_retries
- [ ] _get_headers() returns proper auth and app headers
- [ ] _get_client() creates/reuses httpx.AsyncClient
- [ ] complete() sends non-streaming request
- [ ] complete() resolves model aliases
- [ ] complete() returns CompletionResponse
- [ ] complete() tracks token usage
- [ ] stream() sends streaming request
- [ ] stream() yields StreamChunk objects
- [ ] stream() handles SSE format correctly
- [ ] stream() tracks final usage from last chunk
- [ ] list_models() retrieves available models
- [ ] get_usage() returns cumulative TokenUsage
- [ ] reset_usage() clears counters
- [ ] close() closes HTTP client
- [ ] Supports async context manager (async with)

### Error Handling
- [ ] _check_response() maps 401 to AuthenticationError
- [ ] _check_response() maps 429 to RateLimitError
- [ ] _check_response() maps 404 to ModelNotFoundError
- [ ] _check_response() detects context length errors
- [ ] _check_response() detects content policy errors
- [ ] _make_request() implements retry logic
- [ ] Retry uses exponential backoff
- [ ] Retry respects Retry-After header

### Streaming (src/forge/llm/streaming.py)
- [ ] StreamCollector class implemented
- [ ] add_chunk() accumulates content
- [ ] add_chunk() returns new content (or None)
- [ ] add_chunk() assembles tool calls across chunks
- [ ] get_message() returns complete Message
- [ ] is_complete property checks finish_reason
- [ ] Handles partial tool call arguments

### Package Structure
- [ ] src/forge/llm/__init__.py exports all public classes
- [ ] All imports work correctly
- [ ] No circular dependencies

### Testing
- [ ] Unit tests for Message models
- [ ] Unit tests for ToolDefinition
- [ ] Unit tests for CompletionRequest
- [ ] Unit tests for CompletionResponse parsing
- [ ] Unit tests for StreamChunk parsing
- [ ] Unit tests for error classes
- [ ] Unit tests for routing functions
- [ ] Unit tests for StreamCollector
- [ ] Unit tests for OpenRouterClient (mocked HTTP)
- [ ] Test retry logic
- [ ] Test streaming
- [ ] Test coverage ≥ 90%

---

## Verification Commands

```bash
# 1. Verify module structure
ls -la src/forge/llm/
# Expected: __init__.py, client.py, models.py, errors.py, routing.py, streaming.py

# 2. Test imports
python -c "
from forge.llm import (
    OpenRouterClient,
    Message, MessageRole, ToolDefinition,
    CompletionRequest, CompletionResponse, CompletionChoice,
    TokenUsage, StreamChunk,
    LLMError, AuthenticationError, RateLimitError,
    ModelNotFoundError, ContextLengthError, ContentPolicyError,
    RouteVariant, apply_variant,
)
print('All LLM imports successful')
"

# 3. Test Message creation
python -c "
from forge.llm import Message, MessageRole

# System message
sys_msg = Message.system('You are helpful.')
assert sys_msg.role == MessageRole.SYSTEM
assert sys_msg.content == 'You are helpful.'

# User message
user_msg = Message.user('Hello!')
assert user_msg.role == MessageRole.USER

# Assistant message
asst_msg = Message.assistant('Hi there!')
assert asst_msg.role == MessageRole.ASSISTANT

# Tool result
tool_msg = Message.tool_result('call_123', 'result')
assert tool_msg.role == MessageRole.TOOL
assert tool_msg.tool_call_id == 'call_123'

print('Message creation: OK')
"

# 4. Test Message serialization
python -c "
from forge.llm import Message, MessageRole

msg = Message.user('Hello!')
d = msg.to_dict()
assert d == {'role': 'user', 'content': 'Hello!'}

msg2 = Message.from_dict(d)
assert msg2.role == MessageRole.USER
assert msg2.content == 'Hello!'

print('Message serialization: OK')
"

# 5. Test CompletionRequest
python -c "
from forge.llm import CompletionRequest, Message, ToolDefinition

req = CompletionRequest(
    model='anthropic/claude-3-opus',
    messages=[Message.user('Hello!')],
    temperature=0.7,
    max_tokens=1000,
)
d = req.to_dict()
assert d['model'] == 'anthropic/claude-3-opus'
assert len(d['messages']) == 1
assert d['temperature'] == 0.7
assert d['max_tokens'] == 1000

print('CompletionRequest: OK')
"

# 6. Test CompletionResponse parsing
python -c "
from forge.llm import CompletionResponse

data = {
    'id': 'gen-123',
    'model': 'anthropic/claude-3-opus',
    'choices': [{
        'index': 0,
        'message': {'role': 'assistant', 'content': 'Hello!'},
        'finish_reason': 'stop'
    }],
    'usage': {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15},
    'created': 1705312345
}

resp = CompletionResponse.from_dict(data)
assert resp.id == 'gen-123'
assert resp.choices[0].message.content == 'Hello!'
assert resp.usage.total_tokens == 15

print('CompletionResponse parsing: OK')
"

# 7. Test routing
python -c "
from forge.llm import RouteVariant, apply_variant
from forge.llm.routing import resolve_model_alias, parse_model_id

# Apply variant
result = apply_variant('anthropic/claude-3-opus', RouteVariant.NITRO)
assert result == 'anthropic/claude-3-opus:nitro'

# Parse model ID
base, variant = parse_model_id('anthropic/claude-3-opus:floor')
assert base == 'anthropic/claude-3-opus'
assert variant == RouteVariant.FLOOR

# Resolve alias
full = resolve_model_alias('claude-3-opus')
assert full == 'anthropic/claude-3-opus'

print('Routing: OK')
"

# 8. Test StreamCollector
python -c "
from forge.llm.streaming import StreamCollector
from forge.llm import StreamChunk, MessageRole

collector = StreamCollector()

# Simulate chunks
chunks = [
    {'id': 'gen-1', 'model': 'test', 'choices': [{'index': 0, 'delta': {'role': 'assistant'}, 'finish_reason': None}]},
    {'id': 'gen-1', 'model': 'test', 'choices': [{'index': 0, 'delta': {'content': 'Hello'}, 'finish_reason': None}]},
    {'id': 'gen-1', 'model': 'test', 'choices': [{'index': 0, 'delta': {'content': ' World'}, 'finish_reason': None}]},
    {'id': 'gen-1', 'model': 'test', 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]},
]

for chunk_data in chunks:
    chunk = StreamChunk.from_dict(chunk_data)
    collector.add_chunk(chunk)

assert collector.content == 'Hello World'
assert collector.is_complete

msg = collector.get_message()
assert msg.role == MessageRole.ASSISTANT
assert msg.content == 'Hello World'

print('StreamCollector: OK')
"

# 9. Test error classes
python -c "
from forge.llm import (
    LLMError, AuthenticationError, RateLimitError,
    ModelNotFoundError, ContextLengthError
)

# Auth error
try:
    raise AuthenticationError('Invalid key')
except LLMError as e:
    assert 'Invalid key' in str(e)

# Rate limit with retry_after
err = RateLimitError('Too many requests', retry_after=30)
assert err.retry_after == 30

# Model not found
err = ModelNotFoundError('fake/model')
assert err.model_id == 'fake/model'

print('Error classes: OK')
"

# 10. Test client initialization (no API call)
python -c "
from forge.llm import OpenRouterClient

client = OpenRouterClient(
    api_key='test-key',
    app_name='TestApp',
    timeout=60.0,
    max_retries=5,
)

assert client.api_key == 'test-key'
assert client.app_name == 'TestApp'
assert client.timeout == 60.0
assert client.max_retries == 5

headers = client._get_headers()
assert 'Authorization' in headers
assert 'Bearer test-key' in headers['Authorization']
assert headers['X-Title'] == 'TestApp'

print('Client initialization: OK')
"

# 11. Run all unit tests
pytest tests/unit/llm/ -v --cov=forge.llm --cov-report=term-missing

# Expected: All tests pass, coverage ≥ 90%

# 12. Type checking
mypy src/forge/llm/ --strict
# Expected: No errors

# 13. Linting
ruff check src/forge/llm/
# Expected: No errors

# 14. Integration test with mock (if available)
python -c "
import asyncio
from unittest.mock import AsyncMock, patch

from forge.llm import OpenRouterClient, CompletionRequest, Message

async def test_complete_mock():
    mock_response = {
        'id': 'gen-test',
        'model': 'test/model',
        'choices': [{
            'index': 0,
            'message': {'role': 'assistant', 'content': 'Test response'},
            'finish_reason': 'stop'
        }],
        'usage': {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15},
        'created': 1705312345
    }

    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=AsyncMock(
            is_success=True,
            json=lambda: mock_response
        ))
        mock_client_class.return_value = mock_client
        mock_client.is_closed = False

        client = OpenRouterClient(api_key='test')
        client._client = mock_client

        request = CompletionRequest(
            model='test/model',
            messages=[Message.user('Hello')]
        )

        response = await client.complete(request)
        assert response.choices[0].message.content == 'Test response'
        print('Mock integration: OK')

asyncio.run(test_complete_mock())
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
| `src/forge/llm/__init__.py` | Package exports |
| `src/forge/llm/models.py` | Message, Request, Response models |
| `src/forge/llm/client.py` | OpenRouterClient implementation |
| `src/forge/llm/errors.py` | LLM error classes |
| `src/forge/llm/routing.py` | Model routing and aliases |
| `src/forge/llm/streaming.py` | StreamCollector utility |
| `tests/unit/llm/__init__.py` | Test package |
| `tests/unit/llm/test_models.py` | Model tests |
| `tests/unit/llm/test_client.py` | Client tests |
| `tests/unit/llm/test_errors.py` | Error tests |
| `tests/unit/llm/test_routing.py` | Routing tests |
| `tests/unit/llm/test_streaming.py` | Streaming tests |

---

## Dependencies to Verify

Ensure these are in `pyproject.toml`:
```toml
[tool.poetry.dependencies]
httpx = "^0.27"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-asyncio = "^0.23"
pytest-cov = "^4.1"
respx = "^0.21"  # For mocking httpx
```

---

## Manual Testing Checklist

(Requires valid OPENROUTER_API_KEY)

- [ ] Create client with API key from environment
- [ ] Send simple completion request
- [ ] Verify response parsing
- [ ] Test streaming response
- [ ] Test model alias resolution
- [ ] Test invalid API key error
- [ ] Verify retry logic (may need to trigger rate limit)
- [ ] Check usage tracking across multiple requests

---

## Integration Points

Phase 3.1 provides the LLM client for:

| Consumer | What It Uses |
|----------|--------------|
| Phase 3.2 (LangChain) | OpenRouterClient as LLM backend |
| Phase 5.1 (Sessions) | Message models for history |
| Phase 5.2 (Context) | Token usage for context management |
| Phase 6.2 (Modes) | Streaming for real-time output |

---

## Sign-Off

Phase 3.1 is complete when:

1. [ ] All checklist items above are checked
2. [ ] All verification commands pass
3. [ ] All quality gates are met
4. [ ] Manual testing completed (if API key available)
5. [ ] Code has been reviewed (if applicable)
6. [ ] No TODO comments remain in Phase 3.1 code

---

## Next Phase

After completing Phase 3.1, proceed to:
- **Phase 3.2: LangChain Integration**

Phase 3.2 will implement:
- LangChain LLM wrapper
- Agent orchestration
- Tool integration with LangChain
- Conversation memory
