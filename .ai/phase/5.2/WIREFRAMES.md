# Phase 5.2: Context Management - Wireframes & Usage Examples

**Phase:** 5.2
**Name:** Context Management
**Dependencies:** Phase 5.1 (Session Management), Phase 3.2 (LangChain Integration)

---

## 1. Basic Context Management

### Creating a Context Manager

```python
from opencode.context import ContextManager, TruncationMode

# Create manager for a model
manager = ContextManager(
    model="anthropic/claude-3-opus",
    mode=TruncationMode.SMART,
    auto_truncate=True,
)

# Set system prompt
tokens = manager.set_system_prompt(
    "You are a helpful coding assistant."
)
print(f"System prompt: {tokens} tokens")
```

### Adding Messages

```python
# Add user message
manager.add_message({
    "role": "user",
    "content": "Help me refactor this function",
})

# Add assistant response
manager.add_message({
    "role": "assistant",
    "content": "I'll help you refactor. Let me analyze the code first.",
})

# Add tool result
manager.add_message({
    "role": "tool",
    "content": "def complex_function():\n    # 500 lines of code...",
    "tool_call_id": "call_abc123",
    "name": "read",
})

# Check usage
print(f"Usage: {manager.usage_percentage:.1f}%")
print(f"Available: {manager.available_tokens} tokens")
```

---

## 2. Token Counting

### Direct Token Counting

```python
from opencode.context import get_counter, TiktokenCounter, ApproximateCounter

# Get counter for model
counter = get_counter("claude-3-opus")

# Count text
tokens = counter.count("Hello, how can I help you today?")
print(f"Text tokens: {tokens}")

# Count messages
messages = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there! How can I assist you?"},
]
total = counter.count_messages(messages)
print(f"Message tokens: {total}")
```

### Using Specific Counters

```python
# Use tiktoken directly
tiktoken_counter = TiktokenCounter(model="gpt-4")
tokens = tiktoken_counter.count("Some text to count")

# Use approximate counter
approx_counter = ApproximateCounter(tokens_per_word=1.3)
tokens = approx_counter.count("Approximate counting for unknown models")
```

---

## 3. Context Limits and Tracking

### Working with Limits

```python
from opencode.context import ContextLimits, ContextTracker

# Get limits for a model
limits = ContextLimits.for_model("claude-3-opus")
print(f"Max tokens: {limits.max_tokens}")
print(f"Max output: {limits.max_output_tokens}")
print(f"Effective limit: {limits.effective_limit}")

# Create tracker
tracker = ContextTracker.for_model("claude-3-opus")

# Set system prompt
tracker.set_system_prompt("You are helpful.")

# Add messages
tracker.add_message({"role": "user", "content": "Hello"})

# Check status
print(f"Current tokens: {tracker.current_tokens()}")
print(f"Exceeds limit: {tracker.exceeds_limit()}")
print(f"Usage: {tracker.usage_percentage():.1f}%")
```

### Budget Allocation

```python
from opencode.context import ContextBudget

budget = ContextBudget(
    total=200_000,
    system_prompt=2_000,
    tools=5_000,
    response_reserve=4_096,
)

print(f"Conversation budget: {budget.conversation_budget}")
print(f"Available: {budget.available}")

# Update allocations
budget.update_conversation(50_000)
print(f"After conversation: {budget.available}")
```

---

## 4. Truncation Strategies

### Sliding Window Strategy

```python
from opencode.context import SlidingWindowStrategy, get_counter

counter = get_counter("claude-3-opus")
strategy = SlidingWindowStrategy(
    window_size=20,
    preserve_system=True,
)

# Truncate messages
messages = [...]  # 100 messages
truncated = strategy.truncate(
    messages,
    target_tokens=50_000,
    counter=counter,
)

print(f"Before: {len(messages)}, After: {len(truncated)}")
```

### Token Budget Strategy

```python
from opencode.context import TokenBudgetStrategy

strategy = TokenBudgetStrategy(preserve_system=True)

# Truncate to fit budget
truncated = strategy.truncate(
    messages,
    target_tokens=30_000,
    counter=counter,
)
```

### Smart Truncation

```python
from opencode.context import SmartTruncationStrategy

strategy = SmartTruncationStrategy(
    preserve_first=2,   # Keep first 2 messages
    preserve_last=10,   # Keep last 10 messages
    preserve_system=True,
)

truncated = strategy.truncate(messages, target_tokens, counter)

# Result includes truncation marker:
# [system message]
# [first user message]
# [first assistant message]
# [42 messages omitted]
# [last 10 messages...]
```

### Composite Strategy

```python
from opencode.context import CompositeStrategy, SmartTruncationStrategy, TokenBudgetStrategy

# Chain strategies
strategy = CompositeStrategy([
    SmartTruncationStrategy(),
    TokenBudgetStrategy(),
])

# Applies each until within budget
truncated = strategy.truncate(messages, target_tokens, counter)
```

---

## 5. Context Compaction

### Summarization-based Compaction

```python
from opencode.context import ContextCompactor
from opencode.langchain import OpenRouterLLM

llm = OpenRouterLLM(model="anthropic/claude-3-haiku")  # Use fast model

compactor = ContextCompactor(
    llm=llm,
    max_summary_tokens=500,
    min_messages_to_summarize=5,
)

# Compact old messages
compacted = await compactor.compact(
    messages=messages,
    target_tokens=50_000,
    counter=counter,
    preserve_last=10,
)

# Result:
# [system message]
# [summary: "The user discussed refactoring the API client..."]
# [last 10 messages preserved]
```

### Tool Result Compaction

```python
from opencode.context import ToolResultCompactor

compactor = ToolResultCompactor(
    max_result_tokens=1000,
    truncation_message="\n[Output truncated - {removed} tokens removed]",
)

# Compact large result
large_result = "..." * 10000  # Very long output
compacted = compactor.compact_result(large_result, counter)

# Compact tool message
message = {"role": "tool", "content": large_result, "name": "read"}
compacted_message = compactor.compact_message(message, counter)
```

---

## 6. Full Context Manager Usage

### Complete Workflow

```python
from opencode.context import ContextManager, TruncationMode
from opencode.langchain import OpenRouterLLM

# Create with summarization support
llm = OpenRouterLLM(model="anthropic/claude-3-opus")

manager = ContextManager(
    model="anthropic/claude-3-opus",
    mode=TruncationMode.SUMMARIZE,
    llm=llm,
    auto_truncate=True,
)

# Configure
manager.set_system_prompt("You are a helpful coding assistant.")
manager.set_tool_definitions([
    {"name": "read", "description": "Read a file", ...},
    {"name": "bash", "description": "Run command", ...},
])

# Add conversation
for message in conversation_history:
    manager.add_message(message)

# Check status
stats = manager.get_stats()
print(f"Messages: {stats['message_count']}")
print(f"Tokens: {stats['token_usage']}")
print(f"Usage: {stats['usage_percentage']:.1f}%")

# Get context for LLM request
if manager.is_near_limit:
    # Try to compact if possible
    await manager.compact_if_needed(threshold=0.9)

messages = manager.get_context_for_request()

# Make LLM call
response = await llm.ainvoke(messages)
```

### Integration with Session

```python
from opencode.sessions import SessionManager
from opencode.context import ContextManager, TruncationMode

session_manager = SessionManager.get_instance()
session = session_manager.current_session

# Create context manager
ctx = ContextManager(
    model=session.model,
    mode=TruncationMode.SMART,
)

# Sync session messages
for msg in session.messages:
    ctx.add_message({
        "role": msg.role,
        "content": msg.content,
        "tool_calls": msg.tool_calls,
        "tool_call_id": msg.tool_call_id,
    })

# Now use context manager for LLM calls
messages = ctx.get_context_for_request()

# After getting response, add to both
new_message = {"role": "assistant", "content": response}
ctx.add_message(new_message)
session_manager.add_message("assistant", response)
```

---

## 7. Monitoring and Debugging

### Context Statistics

```python
manager = ContextManager(model="claude-3-opus")

# ... add messages ...

# Get detailed stats
stats = manager.get_stats()

print(f"""
Context Status:
  Model: {stats['model']}
  Mode: {stats['mode']}
  Messages: {stats['message_count']}
  Token Usage: {stats['token_usage']:,}
  Available: {stats['available_tokens']:,}
  Usage: {stats['usage_percentage']:.1f}%
  Max Tokens: {stats['max_tokens']:,}
  Effective Limit: {stats['effective_limit']:,}
""")
```

### Warning on Near Limit

```python
if manager.is_near_limit:
    print("⚠️  Context is near capacity!")
    print(f"   Usage: {manager.usage_percentage:.1f}%")
    print(f"   Available: {manager.available_tokens:,} tokens")

    if manager.compactor:
        compacted = await manager.compact_if_needed()
        if compacted:
            print("✓ Context compacted successfully")
```

---

## 8. CLI Integration Example

### Context Status Display

```
$ opencode

[claude-3-opus | 15 msgs | 12.5K tokens (6.3%)]
You: Can you help me understand this codebase?

[Reading files...]

[claude-3-opus | 45 msgs | 85.2K tokens (42.6%)]
You: Now refactor the main module

[claude-3-opus | 78 msgs | 156.3K tokens (78.2%)]
⚠️  Context usage high. Consider compacting.

You: /context status

Context Status:
  Model: claude-3-opus
  Messages: 78
  Tokens: 156,340 / 200,000 (78.2%)
  Mode: smart

You: /context compact

Compacting context...
Summarized 50 messages into 1 summary.
Context: 78 → 29 messages
Tokens: 156,340 → 45,230 (22.6%)
```

### Context Commands

```
/context status    - Show current context usage
/context compact   - Compact context via summarization
/context reset     - Clear all context
/context mode <m>  - Set truncation mode (sliding_window|token_budget|smart|summarize)
```

---

## 9. Configuration

### Default Settings

```python
# In opencode configuration

context:
  # Default truncation mode
  mode: smart

  # Auto-truncate when over limit
  auto_truncate: true

  # Summarization model (faster/cheaper than main model)
  summarization_model: anthropic/claude-3-haiku

  # Tokens reserved for response
  response_reserve: 4096

  # Max tokens per tool result
  max_tool_result_tokens: 2000

  # Compact threshold (percentage)
  compact_threshold: 0.9

  # Smart truncation settings
  smart:
    preserve_first: 2
    preserve_last: 10

  # Sliding window settings
  sliding_window:
    window_size: 50
```

---

## 10. Error Handling

### Handling Truncation Edge Cases

```python
from opencode.context import ContextManager

manager = ContextManager(model="claude-3-opus")

try:
    # Add very large message
    manager.add_message({
        "role": "tool",
        "content": "x" * 1_000_000,  # Huge result
    })
except Exception as e:
    # Tool result will be auto-compacted
    # If still too large, truncation will occur
    pass

# Check if context is usable
if manager.token_usage < manager.tracker.limits.effective_limit:
    messages = manager.get_context_for_request()
else:
    # Extreme case: need aggressive truncation
    manager.reset()
    manager.add_message({"role": "user", "content": "Start fresh"})
```

---

## Notes

- Token counting is approximate for non-OpenAI models
- Summarization requires an LLM and is async
- Auto-truncation happens on every add_message if enabled
- System prompts are always preserved during truncation
- Tool results are automatically compacted to prevent bloat
- Monitor usage_percentage to avoid context overflow
