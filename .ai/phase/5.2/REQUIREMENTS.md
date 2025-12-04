# Phase 5.2: Context Management - Requirements

**Phase:** 5.2
**Name:** Context Management
**Dependencies:** Phase 5.1 (Session Management), Phase 3.2 (LangChain Integration)

---

## Overview

Phase 5.2 implements context window management for OpenCode, providing token counting, context truncation, and message compaction strategies. This ensures conversations stay within model context limits while preserving important information.

---

## Goals

1. Accurate token counting for messages
2. Context window tracking and limits
3. Automatic message truncation when needed
4. Multiple truncation strategies
5. Context compaction via summarization
6. Token budget allocation for tools

---

## Non-Goals (This Phase)

- Custom tokenizers per model
- Semantic importance ranking
- Multi-model context switching
- Persistent context compression
- Context caching across sessions

---

## Functional Requirements

### FR-1: Token Counting

**FR-1.1:** Token counter interface
- Count tokens in text strings
- Count tokens in message objects
- Count tokens in conversation history
- Support multiple tokenizer backends

**FR-1.2:** Tokenizer implementations
- tiktoken for OpenAI-compatible counting
- Approximate counting for other models
- Configurable tokens-per-word fallback

**FR-1.3:** Message token estimation
- Account for message structure overhead
- Include tool call tokens
- Include function definitions

### FR-2: Context Window Management

**FR-2.1:** Context limits
- Track model context window size
- Track current context usage
- Reserve space for responses
- Reserve space for system prompt

**FR-2.2:** Context budget
- Configurable max context percentage
- Separate budgets for:
  - System prompt
  - Conversation history
  - Tool definitions
  - Expected response

**FR-2.3:** Context overflow detection
- Detect when context exceeds limit
- Calculate overflow amount
- Trigger truncation or compaction

### FR-3: Truncation Strategies

**FR-3.1:** Strategy interface
- Common interface for strategies
- Configurable per-session
- Chainable strategies

**FR-3.2:** Sliding window strategy
- Keep most recent N messages
- Preserve system prompt
- Configurable window size

**FR-3.3:** Token budget strategy
- Truncate to fit token limit
- Remove oldest messages first
- Preserve system and recent

**FR-3.4:** Selective truncation
- Preserve messages by role
- Preserve marked messages
- Skip tool results if needed

**FR-3.5:** Smart truncation
- Preserve first and last N messages
- Remove middle messages
- Keep important markers

### FR-4: Context Compaction

**FR-4.1:** Summarization strategy
- Summarize old conversation
- Replace with summary message
- Preserve recent context

**FR-4.2:** Tool result compaction
- Truncate large tool outputs
- Summarize file contents
- Preserve key information

**FR-4.3:** Progressive compaction
- Multiple compaction levels
- More aggressive as context grows
- Preserve essential context

### FR-5: Context Manager

**FR-5.1:** Central manager
- Coordinate all context operations
- Track current context state
- Apply strategies automatically

**FR-5.2:** Integration with session
- Sync with session messages
- Update on message add
- Persist context metadata

**FR-5.3:** Configuration
- Per-model context limits
- Default truncation strategy
- Compaction thresholds

---

## Non-Functional Requirements

### NFR-1: Performance
- Token counting < 10ms for typical message
- Truncation < 50ms for 100 messages
- Summarization async (non-blocking)

### NFR-2: Accuracy
- Token counts within 5% of actual
- Preserve conversation coherence
- No information loss without fallback

### NFR-3: Reliability
- Handle tokenizer failures gracefully
- Fallback to approximate counting
- Never exceed context limits

---

## Technical Specifications

### Package Structure

```
src/opencode/context/
├── __init__.py           # Package exports
├── tokens.py             # Token counting
├── limits.py             # Context limits
├── strategies.py         # Truncation strategies
├── compaction.py         # Compaction logic
└── manager.py            # Context manager
```

### Class Signatures

```python
# tokens.py
from abc import ABC, abstractmethod

class TokenCounter(ABC):
    """Abstract token counter."""

    @abstractmethod
    def count(self, text: str) -> int:
        """Count tokens in text."""
        ...

    @abstractmethod
    def count_messages(self, messages: list[dict]) -> int:
        """Count tokens in message list."""
        ...


class TiktokenCounter(TokenCounter):
    """Token counter using tiktoken library."""

    encoding_name: str = "cl100k_base"

    def __init__(self, model: str | None = None): ...
    def count(self, text: str) -> int: ...
    def count_messages(self, messages: list[dict]) -> int: ...


class ApproximateCounter(TokenCounter):
    """Approximate token counter for non-OpenAI models."""

    tokens_per_word: float = 1.3

    def count(self, text: str) -> int: ...
    def count_messages(self, messages: list[dict]) -> int: ...


def get_counter(model: str) -> TokenCounter:
    """Get appropriate counter for model."""
    ...


# limits.py
from dataclasses import dataclass

@dataclass
class ContextBudget:
    """Token budget allocation."""
    total: int
    system_prompt: int
    conversation: int
    tools: int
    response_reserve: int

    @property
    def available(self) -> int:
        """Available tokens for conversation."""
        ...


@dataclass
class ContextLimits:
    """Context window limits for a model."""
    model: str
    max_tokens: int
    max_output_tokens: int
    reserved_tokens: int = 1000

    @classmethod
    def for_model(cls, model: str) -> "ContextLimits": ...


class ContextTracker:
    """Tracks current context usage."""

    limits: ContextLimits
    counter: TokenCounter
    current_tokens: int = 0

    def __init__(self, model: str): ...
    def update(self, messages: list[dict]) -> None: ...
    def add_message(self, message: dict) -> int: ...
    def exceeds_limit(self) -> bool: ...
    def overflow_amount(self) -> int: ...
    def available_tokens(self) -> int: ...


# strategies.py
from abc import ABC, abstractmethod

class TruncationStrategy(ABC):
    """Abstract truncation strategy."""

    @abstractmethod
    def truncate(
        self,
        messages: list[dict],
        target_tokens: int,
        counter: TokenCounter,
    ) -> list[dict]:
        """Truncate messages to fit target tokens."""
        ...


class SlidingWindowStrategy(TruncationStrategy):
    """Keep most recent messages."""

    window_size: int = 20
    preserve_system: bool = True

    def truncate(self, messages, target_tokens, counter) -> list[dict]: ...


class TokenBudgetStrategy(TruncationStrategy):
    """Truncate to fit token budget."""

    def truncate(self, messages, target_tokens, counter) -> list[dict]: ...


class SmartTruncationStrategy(TruncationStrategy):
    """Preserve first and last messages, remove middle."""

    preserve_first: int = 2
    preserve_last: int = 10

    def truncate(self, messages, target_tokens, counter) -> list[dict]: ...


class CompositeStrategy(TruncationStrategy):
    """Chain multiple strategies."""

    strategies: list[TruncationStrategy]

    def truncate(self, messages, target_tokens, counter) -> list[dict]: ...


# compaction.py
class ContextCompactor:
    """Compacts context via summarization."""

    llm: Any  # OpenRouterLLM
    summary_prompt: str
    max_summary_tokens: int = 500

    def __init__(self, llm: Any): ...

    async def compact(
        self,
        messages: list[dict],
        target_tokens: int,
        counter: TokenCounter,
    ) -> list[dict]:
        """Compact messages via summarization."""
        ...

    async def summarize_messages(
        self,
        messages: list[dict],
    ) -> str:
        """Summarize a list of messages."""
        ...


class ToolResultCompactor:
    """Compacts large tool results."""

    max_result_tokens: int = 1000
    truncation_message: str = "[Output truncated...]"

    def compact_result(self, result: str, counter: TokenCounter) -> str: ...


# manager.py
from enum import Enum

class TruncationMode(str, Enum):
    """How to handle context overflow."""
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUDGET = "token_budget"
    SMART = "smart"
    SUMMARIZE = "summarize"


class ContextManager:
    """Central context management."""

    tracker: ContextTracker
    strategy: TruncationStrategy
    compactor: ContextCompactor | None

    def __init__(
        self,
        model: str,
        mode: TruncationMode = TruncationMode.SMART,
        llm: Any | None = None,
    ): ...

    def add_message(self, message: dict) -> None:
        """Add message and truncate if needed."""
        ...

    def get_messages(self) -> list[dict]:
        """Get current messages."""
        ...

    def set_system_prompt(self, prompt: str) -> None:
        """Set system prompt."""
        ...

    def get_context_for_request(self) -> list[dict]:
        """Get messages ready for LLM request."""
        ...

    async def compact_if_needed(self) -> bool:
        """Compact context if over threshold."""
        ...

    @property
    def token_usage(self) -> int:
        """Current token usage."""
        ...

    @property
    def available_tokens(self) -> int:
        """Available tokens."""
        ...

    def reset(self) -> None:
        """Clear all messages."""
        ...
```

---

## Model Context Limits

| Model Family | Context Window | Output Limit |
|--------------|----------------|--------------|
| claude-3-opus | 200K | 4K |
| claude-3-sonnet | 200K | 4K |
| claude-3-haiku | 200K | 4K |
| gpt-4-turbo | 128K | 4K |
| gpt-4 | 8K | 4K |
| gpt-3.5-turbo | 16K | 4K |
| llama-3-70b | 8K | 4K |
| mistral-large | 32K | 4K |

---

## Truncation Strategy Selection

```
Context Usage Flow:

1. Message Added
   ↓
2. Count Tokens
   ↓
3. Check Limit
   ↓
4. If Over Limit:
   ├─→ Sliding Window: Remove oldest
   ├─→ Token Budget: Remove until fits
   ├─→ Smart: Remove middle, keep ends
   └─→ Summarize: Compress old messages
```

---

## Integration Points

### With Session Management (Phase 5.1)
- ContextManager uses session messages
- Token counts stored in session
- Truncation updates session

### With LangChain Integration (Phase 3.2)
- Uses ConversationMemory
- Summarization via LLM
- Token counting for chain

### With OpenRouter Client (Phase 3.1)
- Model context limits
- Token usage from responses
- Streaming token counts

---

## Error Scenarios

| Scenario | Handling |
|----------|----------|
| Tokenizer not available | Fall back to approximate |
| Summarization fails | Fall back to truncation |
| Context still too large | Aggressive truncation |
| Invalid message format | Skip with warning |
| Unknown model | Use default limits |

---

## Testing Requirements

1. Unit tests for each TokenCounter
2. Unit tests for ContextLimits
3. Unit tests for ContextTracker
4. Unit tests for each TruncationStrategy
5. Unit tests for ContextCompactor
6. Unit tests for ContextManager
7. Integration tests with session
8. Test coverage ≥ 90%

---

## Acceptance Criteria

1. Token counting accurate within 5%
2. Context never exceeds model limit
3. System prompt always preserved
4. Recent messages prioritized
5. Truncation preserves coherence
6. Summarization produces useful summaries
7. All strategies work correctly
8. Configuration respected
9. Performance targets met
10. Integration with session works
