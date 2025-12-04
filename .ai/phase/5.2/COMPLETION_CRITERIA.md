# Phase 5.2: Context Management - Completion Criteria

**Phase:** 5.2
**Name:** Context Management
**Dependencies:** Phase 5.1 (Session Management), Phase 3.2 (LangChain Integration)

---

## Definition of Done

All of the following criteria must be met before Phase 5.2 is considered complete.

---

## Checklist

### Token Counting (src/opencode/context/tokens.py)
- [ ] TokenCounter abstract base class defined
- [ ] TokenCounter.count() abstract method
- [ ] TokenCounter.count_messages() abstract method
- [ ] TokenCounter.count_message() convenience method
- [ ] TiktokenCounter class implemented
- [ ] TiktokenCounter falls back to ApproximateCounter
- [ ] TiktokenCounter counts message overhead
- [ ] TiktokenCounter counts tool call tokens
- [ ] ApproximateCounter class implemented
- [ ] ApproximateCounter uses tokens_per_word
- [ ] CachingCounter class implemented
- [ ] CachingCounter wraps other counters
- [ ] CachingCounter has LRU-style eviction
- [ ] get_counter() factory function
- [ ] MODEL_ENCODINGS mapping defined

### Context Limits (src/opencode/context/limits.py)
- [ ] ContextBudget dataclass defined
- [ ] ContextBudget.available property
- [ ] ContextBudget.conversation_budget property
- [ ] ContextBudget update methods
- [ ] MODEL_LIMITS dictionary with known models
- [ ] ContextLimits dataclass defined
- [ ] ContextLimits.for_model() class method
- [ ] ContextLimits.effective_limit property
- [ ] ContextTracker class implemented
- [ ] ContextTracker.for_model() class method
- [ ] ContextTracker.set_system_prompt()
- [ ] ContextTracker.set_tool_definitions()
- [ ] ContextTracker.update()
- [ ] ContextTracker.add_message()
- [ ] ContextTracker.current_tokens()
- [ ] ContextTracker.exceeds_limit()
- [ ] ContextTracker.overflow_amount()
- [ ] ContextTracker.available_tokens()
- [ ] ContextTracker.usage_percentage()
- [ ] ContextTracker.reset()

### Truncation Strategies (src/opencode/context/strategies.py)
- [ ] TruncationStrategy abstract base class
- [ ] TruncationStrategy.truncate() abstract method
- [ ] SlidingWindowStrategy implemented
- [ ] SlidingWindowStrategy.window_size configurable
- [ ] SlidingWindowStrategy preserves system messages
- [ ] TokenBudgetStrategy implemented
- [ ] TokenBudgetStrategy removes oldest first
- [ ] TokenBudgetStrategy preserves system messages
- [ ] SmartTruncationStrategy implemented
- [ ] SmartTruncationStrategy.preserve_first configurable
- [ ] SmartTruncationStrategy.preserve_last configurable
- [ ] SmartTruncationStrategy adds truncation marker
- [ ] SelectiveTruncationStrategy implemented
- [ ] SelectiveTruncationStrategy.preserve_roles works
- [ ] SelectiveTruncationStrategy.preserve_marked works
- [ ] CompositeStrategy implemented
- [ ] CompositeStrategy chains strategies

### Context Compaction (src/opencode/context/compaction.py)
- [ ] ContextCompactor class implemented
- [ ] ContextCompactor.compact() async method
- [ ] ContextCompactor.summarize_messages() async method
- [ ] ContextCompactor respects min_messages_to_summarize
- [ ] ContextCompactor preserves recent messages
- [ ] ContextCompactor handles LLM failures gracefully
- [ ] ToolResultCompactor class implemented
- [ ] ToolResultCompactor.compact_result()
- [ ] ToolResultCompactor.compact_message()
- [ ] ToolResultCompactor adds truncation message

### Context Manager (src/opencode/context/manager.py)
- [ ] TruncationMode enum defined
- [ ] get_strategy() function for mode selection
- [ ] ContextManager class implemented
- [ ] ContextManager.set_system_prompt()
- [ ] ContextManager.set_tool_definitions()
- [ ] ContextManager.add_message()
- [ ] ContextManager.add_messages()
- [ ] ContextManager auto-compacts tool results
- [ ] ContextManager auto-truncates when enabled
- [ ] ContextManager.get_messages()
- [ ] ContextManager.get_context_for_request()
- [ ] ContextManager.compact_if_needed() async
- [ ] ContextManager.token_usage property
- [ ] ContextManager.available_tokens property
- [ ] ContextManager.usage_percentage property
- [ ] ContextManager.is_near_limit property
- [ ] ContextManager.reset()
- [ ] ContextManager.get_stats()

### Package Structure
- [ ] src/opencode/context/__init__.py exports all public classes
- [ ] All imports work correctly
- [ ] No circular dependencies

### Testing
- [ ] Unit tests for TiktokenCounter
- [ ] Unit tests for ApproximateCounter
- [ ] Unit tests for CachingCounter
- [ ] Unit tests for ContextBudget
- [ ] Unit tests for ContextLimits
- [ ] Unit tests for ContextTracker
- [ ] Unit tests for SlidingWindowStrategy
- [ ] Unit tests for TokenBudgetStrategy
- [ ] Unit tests for SmartTruncationStrategy
- [ ] Unit tests for SelectiveTruncationStrategy
- [ ] Unit tests for CompositeStrategy
- [ ] Unit tests for ContextCompactor (mock LLM)
- [ ] Unit tests for ToolResultCompactor
- [ ] Unit tests for ContextManager
- [ ] Integration tests with session
- [ ] Test coverage ≥ 90%

---

## Verification Commands

```bash
# 1. Verify module structure
ls -la src/opencode/context/
# Expected: __init__.py, tokens.py, limits.py, strategies.py, compaction.py, manager.py

# 2. Test imports
python -c "
from opencode.context import (
    TokenCounter,
    TiktokenCounter,
    ApproximateCounter,
    CachingCounter,
    get_counter,
    ContextBudget,
    ContextLimits,
    ContextTracker,
    TruncationStrategy,
    SlidingWindowStrategy,
    TokenBudgetStrategy,
    SmartTruncationStrategy,
    SelectiveTruncationStrategy,
    CompositeStrategy,
    ContextCompactor,
    ToolResultCompactor,
    TruncationMode,
    ContextManager,
)
print('All context imports successful')
"

# 3. Test token counting
python -c "
from opencode.context import get_counter, ApproximateCounter

# Get counter
counter = get_counter('claude-3-opus')
assert counter is not None

# Count text
text = 'Hello, how are you doing today?'
tokens = counter.count(text)
assert tokens > 0
print(f'Text tokens: {tokens}')

# Count messages
messages = [
    {'role': 'user', 'content': 'Hello'},
    {'role': 'assistant', 'content': 'Hi there!'},
]
total = counter.count_messages(messages)
assert total > tokens
print(f'Message tokens: {total}')

# Approximate counter
approx = ApproximateCounter(tokens_per_word=1.3)
approx_tokens = approx.count('one two three four five')
assert 5 <= approx_tokens <= 10

print('Token counting: OK')
"

# 4. Test context limits
python -c "
from opencode.context import ContextLimits, ContextBudget

# Known model
limits = ContextLimits.for_model('claude-3-opus')
assert limits.max_tokens == 200000
assert limits.max_output_tokens == 4096
print(f'Claude limits: {limits.effective_limit}')

# Unknown model
limits2 = ContextLimits.for_model('unknown-model')
assert limits2 is not None  # Should use defaults

# Budget
budget = ContextBudget(total=100000, response_reserve=4000)
budget.update_system_prompt(2000)
budget.update_tools(5000)
assert budget.conversation_budget == 89000

print('Context limits: OK')
"

# 5. Test context tracker
python -c "
from opencode.context import ContextTracker

tracker = ContextTracker.for_model('claude-3-opus')

# Set system prompt
tokens = tracker.set_system_prompt('You are helpful.')
assert tokens > 0

# Add messages
tracker.add_message({'role': 'user', 'content': 'Hello'})
assert tracker.current_tokens() > tokens

# Check limits
assert not tracker.exceeds_limit()
assert tracker.available_tokens() > 0
assert 0 < tracker.usage_percentage() < 100

print('Context tracker: OK')
"

# 6. Test sliding window strategy
python -c "
from opencode.context import SlidingWindowStrategy, get_counter

counter = get_counter('claude-3-opus')
strategy = SlidingWindowStrategy(window_size=5, preserve_system=True)

messages = [
    {'role': 'system', 'content': 'You are helpful'},
] + [
    {'role': 'user', 'content': f'Message {i}'} for i in range(20)
]

truncated = strategy.truncate(messages, 100000, counter)
assert len(truncated) == 6  # 1 system + 5 recent

print('Sliding window strategy: OK')
"

# 7. Test smart truncation strategy
python -c "
from opencode.context import SmartTruncationStrategy, get_counter

counter = get_counter('claude-3-opus')
strategy = SmartTruncationStrategy(
    preserve_first=2,
    preserve_last=3,
    preserve_system=True,
)

messages = [
    {'role': 'system', 'content': 'System'},
    {'role': 'user', 'content': 'First user'},
    {'role': 'assistant', 'content': 'First assistant'},
] + [
    {'role': 'user', 'content': f'Message {i}'} for i in range(20)
]

truncated = strategy.truncate(messages, 100000, counter)
# Should have: system + 2 first + marker + 3 last = 7
assert len(truncated) >= 6

# Check for truncation marker
has_marker = any('omitted' in str(m.get('content', '')) for m in truncated)
assert has_marker

print('Smart truncation strategy: OK')
"

# 8. Test token budget strategy
python -c "
from opencode.context import TokenBudgetStrategy, get_counter

counter = get_counter('claude-3-opus')
strategy = TokenBudgetStrategy(preserve_system=True)

# Create messages with known size
messages = [{'role': 'system', 'content': 'System'}]
for i in range(50):
    messages.append({'role': 'user', 'content': 'x' * 100})

# Truncate to small budget
truncated = strategy.truncate(messages, 500, counter)
assert counter.count_messages(truncated) <= 500

print('Token budget strategy: OK')
"

# 9. Test composite strategy
python -c "
from opencode.context import CompositeStrategy, SmartTruncationStrategy, TokenBudgetStrategy, get_counter

counter = get_counter('claude-3-opus')
strategy = CompositeStrategy([
    SmartTruncationStrategy(),
    TokenBudgetStrategy(),
])

messages = [{'role': 'user', 'content': 'x' * 100} for _ in range(100)]
truncated = strategy.truncate(messages, 1000, counter)
assert counter.count_messages(truncated) <= 1000

print('Composite strategy: OK')
"

# 10. Test tool result compactor
python -c "
from opencode.context import ToolResultCompactor, get_counter

counter = get_counter('claude-3-opus')
compactor = ToolResultCompactor(max_result_tokens=100)

# Large result
large_result = 'x' * 10000
compacted = compactor.compact_result(large_result, counter)
assert counter.count(compacted) <= 150  # Some overhead allowed
assert 'truncated' in compacted.lower()

# Small result unchanged
small_result = 'Hello'
unchanged = compactor.compact_result(small_result, counter)
assert unchanged == small_result

print('Tool result compactor: OK')
"

# 11. Test context manager
python -c "
from opencode.context import ContextManager, TruncationMode

manager = ContextManager(
    model='claude-3-opus',
    mode=TruncationMode.SMART,
    auto_truncate=True,
)

# Set system prompt
tokens = manager.set_system_prompt('You are helpful.')
assert tokens > 0

# Add messages
manager.add_message({'role': 'user', 'content': 'Hello'})
manager.add_message({'role': 'assistant', 'content': 'Hi!'})

# Check state
assert len(manager.get_messages()) == 2
assert manager.token_usage > 0
assert manager.available_tokens > 0
assert not manager.is_near_limit

# Get context for request
context = manager.get_context_for_request()
assert context[0]['role'] == 'system'
assert len(context) == 3

# Get stats
stats = manager.get_stats()
assert 'model' in stats
assert 'token_usage' in stats
assert 'usage_percentage' in stats

# Reset
manager.reset()
assert len(manager.get_messages()) == 0

print('Context manager: OK')
"

# 12. Test auto-truncation
python -c "
from opencode.context import ContextManager, TruncationMode

# Create manager with small limit for testing
manager = ContextManager(
    model='gpt-4',  # Smaller context window
    mode=TruncationMode.TOKEN_BUDGET,
    auto_truncate=True,
)

# Add many messages
for i in range(100):
    manager.add_message({'role': 'user', 'content': 'x' * 500})

# Should have auto-truncated
assert manager.token_usage <= manager.tracker.limits.effective_limit

print('Auto-truncation: OK')
"

# 13. Test usage percentage
python -c "
from opencode.context import ContextManager

manager = ContextManager(model='claude-3-opus')
manager.set_system_prompt('System')

for i in range(10):
    manager.add_message({'role': 'user', 'content': 'Hello'})

usage = manager.usage_percentage
assert 0 < usage < 1  # Should be very low

print(f'Usage: {usage:.4f}%')
print('Usage percentage: OK')
"

# 14. Run all unit tests
pytest tests/unit/context/ -v --cov=opencode.context --cov-report=term-missing

# Expected: All tests pass, coverage ≥ 90%

# 15. Type checking
mypy src/opencode/context/ --strict
# Expected: No errors

# 16. Linting
ruff check src/opencode/context/
# Expected: No errors
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
| `src/opencode/context/__init__.py` | Package exports |
| `src/opencode/context/tokens.py` | Token counting |
| `src/opencode/context/limits.py` | Context limits |
| `src/opencode/context/strategies.py` | Truncation strategies |
| `src/opencode/context/compaction.py` | Context compaction |
| `src/opencode/context/manager.py` | Context manager |
| `tests/unit/context/__init__.py` | Test package |
| `tests/unit/context/test_tokens.py` | Token tests |
| `tests/unit/context/test_limits.py` | Limits tests |
| `tests/unit/context/test_strategies.py` | Strategy tests |
| `tests/unit/context/test_compaction.py` | Compaction tests |
| `tests/unit/context/test_manager.py` | Manager tests |

---

## Dependencies to Verify

```
tiktoken >= 0.5.0  # Optional, for accurate token counting
```

---

## Performance Requirements

| Operation | Target |
|-----------|--------|
| Token counting | < 10ms for typical message |
| Truncation | < 50ms for 100 messages |
| Summarization | Async (non-blocking) |
| Get context | < 5ms |

---

## Accuracy Requirements

| Metric | Target |
|--------|--------|
| Token count accuracy | Within 5% of actual |
| No context overflow | 100% |
| System prompt preserved | 100% |

---

## Manual Testing Checklist

- [ ] Token counting works with tiktoken
- [ ] Token counting falls back gracefully
- [ ] Context limits correct for known models
- [ ] Context limits use defaults for unknown
- [ ] Sliding window keeps recent messages
- [ ] Token budget stays within limit
- [ ] Smart truncation preserves ends
- [ ] Composite strategy chains correctly
- [ ] Tool results are compacted
- [ ] Auto-truncation triggers correctly
- [ ] Context manager provides correct stats
- [ ] Reset clears all state
- [ ] Near-limit detection works
- [ ] Summarization produces useful output

---

## Integration Points

Phase 5.2 provides context management for:

| Consumer | What It Uses |
|----------|--------------|
| Phase 5.1 (Sessions) | Session syncs with ContextManager |
| Phase 3.2 (LangChain) | Agent uses context for requests |
| Phase 3.1 (OpenRouter) | Token counting for usage |
| Phase 6.2 (Modes) | Context status in prompts |

---

## Sign-Off

Phase 5.2 is complete when:

1. [ ] All checklist items above are checked
2. [ ] All verification commands pass
3. [ ] All quality gates are met
4. [ ] Performance requirements met
5. [ ] Accuracy requirements met
6. [ ] Manual testing completed
7. [ ] Code has been reviewed (if applicable)
8. [ ] No TODO comments remain in Phase 5.2 code

---

## Next Phase

After completing Phase 5.2, proceed to:
- **Phase 6.1: Slash Commands**

Phase 6.1 will implement:
- Command parsing and dispatch
- Built-in commands (/help, /clear, /session, etc.)
- Custom command registration
- Command argument handling
- Command output formatting
