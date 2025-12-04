# Phase 5.2: Context Management - Gherkin Specifications

**Phase:** 5.2
**Name:** Context Management
**Dependencies:** Phase 5.1 (Session Management), Phase 3.2 (LangChain Integration)

---

## Feature: Token Counting

### Scenario: Count tokens in simple text
```gherkin
Given a TiktokenCounter
When I call count("Hello, world!")
Then I should get a positive integer
And the count should be accurate within 5%
```

### Scenario: Count tokens with tiktoken unavailable
```gherkin
Given tiktoken is not installed
When I create a TiktokenCounter
Then it should fall back to ApproximateCounter
And count() should still work
```

### Scenario: Approximate token counting
```gherkin
Given an ApproximateCounter with tokens_per_word=1.3
When I count "one two three four five"
Then the count should be approximately 6-7 tokens
```

### Scenario: Count tokens in messages
```gherkin
Given a TokenCounter
And messages:
  | role      | content         |
  | user      | Hello           |
  | assistant | Hi there!       |
When I call count_messages(messages)
Then I should get total tokens including overhead
And the count should include message structure tokens
```

### Scenario: Count tokens with tool calls
```gherkin
Given a message with tool_calls
When I count the message
Then the count should include:
  - Tool call structure overhead
  - Function name tokens
  - Arguments tokens
```

### Scenario: Caching counter
```gherkin
Given a CachingCounter wrapping TiktokenCounter
When I count the same text twice
Then the second call should use cached result
And performance should be faster
```

### Scenario: Get counter for model
```gherkin
Given I need a counter for "claude-3-opus"
When I call get_counter("claude-3-opus")
Then I should get a CachingCounter
And it should use TiktokenCounter internally
```

---

## Feature: Context Limits

### Scenario: Get limits for known model
```gherkin
Given the model "claude-3-opus"
When I call ContextLimits.for_model("claude-3-opus")
Then max_tokens should be 200000
And max_output_tokens should be 4096
```

### Scenario: Get limits for unknown model
```gherkin
Given an unknown model "custom-model"
When I call ContextLimits.for_model("custom-model")
Then it should return default limits
And a warning should be logged
```

### Scenario: Effective limit calculation
```gherkin
Given ContextLimits with:
  - max_tokens: 100000
  - max_output_tokens: 4096
  - reserved_tokens: 1000
When I access effective_limit
Then it should be 94904
```

### Scenario: Context budget allocation
```gherkin
Given a ContextBudget with total=100000
When I update allocations:
  - system_prompt: 2000
  - tools: 5000
  - response_reserve: 4000
Then available should be 89000
And conversation_budget should be 89000
```

---

## Feature: Context Tracker

### Scenario: Create tracker for model
```gherkin
Given I need to track context for "gpt-4"
When I call ContextTracker.for_model("gpt-4")
Then I should get a tracker with correct limits
And it should have appropriate counter
```

### Scenario: Set system prompt
```gherkin
Given a ContextTracker
When I call set_system_prompt("You are a helpful assistant.")
Then the token count should be returned
And budget.system_prompt should be updated
```

### Scenario: Update with messages
```gherkin
Given a ContextTracker
And 10 messages totaling 5000 tokens
When I call update(messages)
Then current_tokens() should reflect the total
And budget.conversation should be updated
```

### Scenario: Detect context overflow
```gherkin
Given a ContextTracker with effective_limit=10000
And current usage of 12000 tokens
When I check exceeds_limit()
Then it should return True
And overflow_amount() should return 2000
```

### Scenario: Calculate usage percentage
```gherkin
Given a ContextTracker with effective_limit=100000
And current usage of 75000 tokens
When I check usage_percentage()
Then it should return 75.0
```

---

## Feature: Sliding Window Strategy

### Scenario: Truncate with sliding window
```gherkin
Given a SlidingWindowStrategy with window_size=10
And 25 messages
When I call truncate(messages, target_tokens, counter)
Then I should get the last 10 messages
And system messages should be preserved
```

### Scenario: Preserve system messages
```gherkin
Given messages with 2 system messages and 20 other messages
And a SlidingWindowStrategy with window_size=5, preserve_system=True
When I truncate
Then both system messages should be in result
And 5 most recent other messages should be kept
```

### Scenario: No truncation needed
```gherkin
Given 5 messages and window_size=10
When I truncate
Then all messages should be returned unchanged
```

---

## Feature: Token Budget Strategy

### Scenario: Truncate to fit budget
```gherkin
Given messages totaling 10000 tokens
And target_tokens=5000
When I apply TokenBudgetStrategy
Then result should fit within 5000 tokens
And oldest messages should be removed first
```

### Scenario: Preserve system messages in budget
```gherkin
Given a system message of 500 tokens
And other messages of 10000 tokens
And target_tokens=2000
When I apply TokenBudgetStrategy
Then system message should be preserved
And remaining budget should go to recent messages
```

### Scenario: System messages exceed budget
```gherkin
Given system messages totaling 3000 tokens
And target_tokens=2000
When I apply TokenBudgetStrategy
Then only system messages should be returned
And a warning should be logged
```

---

## Feature: Smart Truncation Strategy

### Scenario: Preserve first and last messages
```gherkin
Given a SmartTruncationStrategy with:
  - preserve_first: 2
  - preserve_last: 5
And 50 messages
When I truncate
Then first 2 messages should be kept
And last 5 messages should be kept
And a truncation marker should be inserted
```

### Scenario: Small conversation not truncated
```gherkin
Given 5 messages and preserve_first=2, preserve_last=5
When I truncate
Then all messages should be kept
And no truncation marker should be added
```

### Scenario: Truncation marker content
```gherkin
Given 100 messages with preserve_first=2, preserve_last=5
When I truncate
Then the marker should contain "[93 messages omitted]"
```

---

## Feature: Selective Truncation Strategy

### Scenario: Preserve messages by role
```gherkin
Given messages with roles: system, user, assistant, tool
And preserve_roles={"system", "user"}
When I truncate
Then all system and user messages should be preserved
And assistant/tool messages may be removed
```

### Scenario: Preserve marked messages
```gherkin
Given messages where some have _preserve=True
And preserve_marked=True
When I truncate
Then marked messages should be kept
And unmarked messages may be removed
```

---

## Feature: Composite Strategy

### Scenario: Chain strategies
```gherkin
Given a CompositeStrategy with [SmartTruncation, TokenBudget]
And messages over budget
When I truncate
Then SmartTruncation should be applied first
And if still over budget, TokenBudget should be applied
```

### Scenario: Stop when within budget
```gherkin
Given a CompositeStrategy with [Strategy1, Strategy2]
And Strategy1 brings messages within budget
When I truncate
Then Strategy2 should not be applied
```

---

## Feature: Context Compaction

### Scenario: Compact via summarization
```gherkin
Given a ContextCompactor with LLM
And 50 messages exceeding budget
When I call compact(messages, target_tokens, counter, preserve_last=10)
Then old messages should be summarized
And last 10 messages should be preserved
And result should include summary message
```

### Scenario: Skip compaction for few messages
```gherkin
Given messages fewer than min_messages_to_summarize
When I call compact()
Then original messages should be returned
And no LLM call should be made
```

### Scenario: Summarization failure fallback
```gherkin
Given a ContextCompactor where LLM fails
When I call compact()
Then original messages should be returned
And error should be logged
```

---

## Feature: Tool Result Compaction

### Scenario: Compact large tool result
```gherkin
Given a ToolResultCompactor with max_result_tokens=1000
And a tool result of 5000 tokens
When I call compact_result(result, counter)
Then result should be truncated to ~1000 tokens
And truncation message should be appended
```

### Scenario: Small result unchanged
```gherkin
Given a tool result of 500 tokens
And max_result_tokens=1000
When I compact
Then result should be unchanged
```

### Scenario: Compact tool message
```gherkin
Given a tool message with large content
When I call compact_message(message, counter)
Then content should be compacted
And other message fields should be preserved
```

---

## Feature: Context Manager

### Scenario: Create context manager
```gherkin
Given I need context management for "claude-3-opus"
When I create ContextManager(model="claude-3-opus", mode=SMART)
Then it should have appropriate counter
And it should have SmartTruncationStrategy
```

### Scenario: Set system prompt
```gherkin
Given a ContextManager
When I call set_system_prompt("You are helpful")
Then system prompt should be stored
And token count should be tracked
```

### Scenario: Add message with auto-truncation
```gherkin
Given a ContextManager with auto_truncate=True
And context is at 95% capacity
When I add a large message
Then truncation should be triggered automatically
And context should fit within limits
```

### Scenario: Get context for request
```gherkin
Given a ContextManager with system prompt and messages
When I call get_context_for_request()
Then result should start with system message
And all conversation messages should follow
```

### Scenario: Compact when near limit
```gherkin
Given a ContextManager with compactor
And usage at 92%
When I call compact_if_needed(threshold=0.9)
Then compaction should be triggered
And usage should decrease
```

### Scenario: Check near limit status
```gherkin
Given a ContextManager at 85% usage
When I check is_near_limit
Then it should return True
```

### Scenario: Get context statistics
```gherkin
Given a ContextManager with messages
When I call get_stats()
Then I should get:
  - model
  - mode
  - message_count
  - token_usage
  - available_tokens
  - usage_percentage
```

### Scenario: Reset context
```gherkin
Given a ContextManager with messages and history
When I call reset()
Then all messages should be cleared
And tracker should be reset
```

---

## Feature: Integration with Session

### Scenario: Sync context with session
```gherkin
Given a Session with message history
When I load messages into ContextManager
Then token counts should be accurate
And truncation should work correctly
```

### Scenario: Update session after truncation
```gherkin
Given a ContextManager synced with session
When truncation occurs
Then session should be notified
And session state should be consistent
```

---

## Feature: Truncation Mode Selection

### Scenario: Select sliding window mode
```gherkin
Given TruncationMode.SLIDING_WINDOW
When I create ContextManager
Then it should use SlidingWindowStrategy
```

### Scenario: Select smart mode
```gherkin
Given TruncationMode.SMART
When I create ContextManager
Then it should use SmartTruncationStrategy
```

### Scenario: Select summarize mode
```gherkin
Given TruncationMode.SUMMARIZE
And an LLM is provided
When I create ContextManager
Then it should use CompositeStrategy
And compactor should be initialized
```
