# Phase 5.2: Context Management - Implementation Plan

**Phase:** 5.2
**Name:** Context Management
**Dependencies:** Phase 5.1 (Session Management), Phase 3.2 (LangChain Integration)

---

## Overview

This plan details the implementation of context window management for Code-Forge, including token counting, truncation strategies, and context compaction.

---

## Implementation Order

1. **tokens.py** - Token counting implementations
2. **limits.py** - Context limits and tracking
3. **strategies.py** - Truncation strategies
4. **compaction.py** - Context compaction
5. **manager.py** - Central context manager

---

## File 1: src/forge/context/tokens.py

```python
"""Token counting implementations."""

import logging
import re
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class TokenCounter(ABC):
    """Abstract base class for token counting.

    Provides interface for counting tokens in text and messages.
    Different implementations support different tokenizer backends.
    """

    @abstractmethod
    def count(self, text: str) -> int:
        """Count tokens in a text string.

        Args:
            text: The text to count tokens in.

        Returns:
            Number of tokens.
        """
        ...

    @abstractmethod
    def count_messages(self, messages: list[dict[str, Any]]) -> int:
        """Count tokens in a list of messages.

        Args:
            messages: List of message dictionaries with role/content.

        Returns:
            Total tokens across all messages.
        """
        ...

    def count_message(self, message: dict[str, Any]) -> int:
        """Count tokens in a single message.

        Args:
            message: Message dictionary.

        Returns:
            Number of tokens.
        """
        return self.count_messages([message])


class TiktokenCounter(TokenCounter):
    """Token counter using OpenAI's tiktoken library.

    Provides accurate token counting for OpenAI and Claude models.
    Falls back to approximate counting if tiktoken not available.
    """

    # Message overhead tokens (varies by model)
    MESSAGE_OVERHEAD = 4  # <im_start>, role, \n, <im_end>
    REPLY_OVERHEAD = 3    # <im_start>assistant<im_sep>

    def __init__(self, model: str | None = None) -> None:
        """Initialize tiktoken counter.

        Args:
            model: Model name for encoding selection.
        """
        self.model = model
        self._encoding = None
        self._fallback = ApproximateCounter()

        # Try to load tiktoken
        try:
            import tiktoken
            self._tiktoken = tiktoken

            # Get encoding for model
            if model:
                try:
                    self._encoding = tiktoken.encoding_for_model(model)
                except KeyError:
                    # Unknown model, use default
                    self._encoding = tiktoken.get_encoding("cl100k_base")
            else:
                self._encoding = tiktoken.get_encoding("cl100k_base")

        except ImportError:
            logger.warning("tiktoken not available, using approximate counting")
            self._tiktoken = None

    def count(self, text: str) -> int:
        """Count tokens in text using tiktoken.

        Args:
            text: Text to count.

        Returns:
            Token count.
        """
        if not text:
            return 0

        if self._encoding:
            return len(self._encoding.encode(text))

        return self._fallback.count(text)

    def count_messages(self, messages: list[dict[str, Any]]) -> int:
        """Count tokens in messages including overhead.

        Args:
            messages: List of message dictionaries.

        Returns:
            Total token count.
        """
        if not messages:
            return 0

        total = 0

        for message in messages:
            # Base overhead per message
            total += self.MESSAGE_OVERHEAD

            # Role token
            role = message.get("role", "")
            total += self.count(role)

            # Content tokens
            content = message.get("content", "")
            if content:
                total += self.count(content)

            # Name tokens (if present)
            name = message.get("name")
            if name:
                total += self.count(name) + 1  # +1 for separator

            # Tool calls (if present)
            tool_calls = message.get("tool_calls")
            if tool_calls:
                for tc in tool_calls:
                    # Tool call structure overhead
                    total += 10

                    # Function name
                    func = tc.get("function", {})
                    total += self.count(func.get("name", ""))

                    # Arguments
                    args = func.get("arguments", "")
                    total += self.count(args)

            # Tool call ID (for tool results)
            tool_call_id = message.get("tool_call_id")
            if tool_call_id:
                total += self.count(tool_call_id)

        # Reply priming overhead
        total += self.REPLY_OVERHEAD

        return total


class ApproximateCounter(TokenCounter):
    """Approximate token counter for models without tiktoken.

    Uses a simple word-based approximation with configurable
    tokens-per-word ratio.
    """

    def __init__(
        self,
        tokens_per_word: float = 1.3,
        tokens_per_char: float = 0.25,
    ) -> None:
        """Initialize approximate counter.

        Args:
            tokens_per_word: Average tokens per word.
            tokens_per_char: Tokens per character for non-word text.
        """
        self.tokens_per_word = tokens_per_word
        self.tokens_per_char = tokens_per_char

        # Pattern for splitting into words
        self._word_pattern = re.compile(r'\w+')

    def count(self, text: str) -> int:
        """Count tokens approximately.

        Args:
            text: Text to count.

        Returns:
            Approximate token count.
        """
        if not text:
            return 0

        # Count words
        words = self._word_pattern.findall(text)
        word_tokens = int(len(words) * self.tokens_per_word)

        # Count non-word characters (punctuation, whitespace, etc.)
        non_word_chars = len(text) - sum(len(w) for w in words)
        char_tokens = int(non_word_chars * self.tokens_per_char)

        return word_tokens + char_tokens

    def count_messages(self, messages: list[dict[str, Any]]) -> int:
        """Count tokens in messages approximately.

        Args:
            messages: List of message dictionaries.

        Returns:
            Approximate token count.
        """
        if not messages:
            return 0

        total = 0
        message_overhead = 4  # Per-message overhead

        for message in messages:
            total += message_overhead

            # Content
            content = message.get("content", "")
            if content:
                total += self.count(content)

            # Role
            total += self.count(message.get("role", ""))

            # Tool calls
            tool_calls = message.get("tool_calls")
            if tool_calls:
                for tc in tool_calls:
                    total += 10  # Structure overhead
                    func = tc.get("function", {})
                    total += self.count(func.get("name", ""))
                    total += self.count(func.get("arguments", ""))

        return total


class CachingCounter(TokenCounter):
    """Token counter with LRU caching for repeated text.

    Wraps another counter and caches results for efficiency.
    Uses OrderedDict for true LRU eviction.
    Thread-safe: uses RLock for all cache operations.
    """

    def __init__(
        self,
        counter: TokenCounter,
        max_cache_size: int = 1000,
    ) -> None:
        """Initialize caching counter.

        Args:
            counter: Underlying token counter.
            max_cache_size: Maximum cache entries (must be > 0).

        Raises:
            ValueError: If max_cache_size is not positive.
        """
        from collections import OrderedDict
        import threading

        if max_cache_size <= 0:
            raise ValueError("max_cache_size must be positive")

        self._counter = counter
        self._cache: OrderedDict[str, int] = OrderedDict()
        self._max_size = max_cache_size
        self._lock = threading.RLock()  # Thread-safe cache access
        self._hits = 0
        self._misses = 0

    def count(self, text: str) -> int:
        """Count with LRU caching.

        Thread-safe: uses lock for cache access.

        Args:
            text: Text to count.

        Returns:
            Token count.
        """
        with self._lock:
            if text in self._cache:
                # Move to end (most recently used) for true LRU behavior
                self._cache.move_to_end(text)
                self._hits += 1
                return self._cache[text]

            self._misses += 1

        # Do the expensive count outside the lock
        count = self._counter.count(text)

        with self._lock:
            # Add to cache, evicting LRU (first) entry if needed
            if len(self._cache) >= self._max_size:
                # Remove least recently used (first) entry
                self._cache.popitem(last=False)

            self._cache[text] = count
        return count

    def count_messages(self, messages: list[dict[str, Any]]) -> int:
        """Count messages using underlying counter.

        Args:
            messages: Messages to count.

        Returns:
            Token count.
        """
        return self._counter.count_messages(messages)

    def clear_cache(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dict with hits, misses, size, and hit_rate.
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._cache),
                "hit_rate_percent": int(hit_rate),
            }


# Model-to-encoding mapping
MODEL_ENCODINGS: dict[str, str] = {
    # Claude models use cl100k_base approximation
    "claude": "cl100k_base",
    "anthropic": "cl100k_base",
    # GPT models
    "gpt-4": "cl100k_base",
    "gpt-3.5": "cl100k_base",
    # Others default to approximate
}


def get_counter(model: str) -> TokenCounter:
    """Get appropriate token counter for a model.

    Args:
        model: Model name or identifier.

    Returns:
        TokenCounter instance.
    """
    model_lower = model.lower()

    # Check for tiktoken-compatible models
    for prefix, encoding in MODEL_ENCODINGS.items():
        if prefix in model_lower:
            counter = TiktokenCounter(model)
            return CachingCounter(counter)

    # Fall back to approximate counter
    logger.debug(f"Using approximate counter for model: {model}")
    return CachingCounter(ApproximateCounter())
```

---

## File 2: src/forge/context/limits.py

```python
"""Context limits and tracking."""

import logging
from dataclasses import dataclass, field
from typing import Any

from .tokens import TokenCounter, get_counter

logger = logging.getLogger(__name__)


@dataclass
class ContextBudget:
    """Token budget allocation for different components.

    Defines how context window should be allocated between
    system prompt, conversation history, tools, and response.

    All token counts are validated to be non-negative and
    within total budget constraints.
    """

    total: int
    system_prompt: int = 0
    conversation: int = 0
    tools: int = 0
    response_reserve: int = 4096

    def __post_init__(self):
        """Validate budget constraints."""
        if self.total <= 0:
            raise ValueError("total must be positive")
        if self.response_reserve < 0:
            raise ValueError("response_reserve cannot be negative")
        if self.response_reserve >= self.total:
            raise ValueError("response_reserve must be less than total")

        # Ensure all allocations are non-negative
        self.system_prompt = max(0, self.system_prompt)
        self.conversation = max(0, self.conversation)
        self.tools = max(0, self.tools)

    @property
    def available(self) -> int:
        """Available tokens for new content.

        Returns:
            Tokens available after allocations (never negative).
        """
        used = self.system_prompt + self.conversation + self.tools
        return max(0, self.total - used - self.response_reserve)

    @property
    def conversation_budget(self) -> int:
        """Budget available for conversation.

        Returns:
            Maximum tokens for conversation history (never negative).
        """
        budget = self.total - self.system_prompt - self.tools - self.response_reserve
        return max(0, budget)

    @property
    def is_over_budget(self) -> bool:
        """Check if allocations exceed total budget.

        Returns:
            True if allocations exceed available space.
        """
        used = self.system_prompt + self.conversation + self.tools + self.response_reserve
        return used > self.total

    def update_system_prompt(self, tokens: int) -> None:
        """Update system prompt token count."""
        self.system_prompt = max(0, tokens)

    def update_tools(self, tokens: int) -> None:
        """Update tools token count."""
        self.tools = max(0, tokens)

    def update_conversation(self, tokens: int) -> None:
        """Update conversation token count."""
        self.conversation = max(0, tokens)


# Known model context limits
MODEL_LIMITS: dict[str, tuple[int, int]] = {
    # Claude models (context, max_output)
    "claude-3-opus": (200_000, 4096),
    "claude-3-sonnet": (200_000, 4096),
    "claude-3-haiku": (200_000, 4096),
    "claude-3.5-sonnet": (200_000, 8192),
    "claude-2": (100_000, 4096),

    # GPT models
    "gpt-4-turbo": (128_000, 4096),
    "gpt-4-32k": (32_768, 4096),
    "gpt-4": (8_192, 4096),
    "gpt-3.5-turbo-16k": (16_385, 4096),
    "gpt-3.5-turbo": (4_096, 4096),

    # Llama models
    "llama-3-70b": (8_192, 4096),
    "llama-3-8b": (8_192, 4096),
    "llama-2-70b": (4_096, 4096),

    # Mistral models
    "mistral-large": (32_768, 4096),
    "mistral-medium": (32_768, 4096),
    "mistral-small": (32_768, 4096),
    "mixtral-8x7b": (32_768, 4096),

    # Default for unknown models
    "default": (8_192, 4096),
}


@dataclass
class ContextLimits:
    """Context window limits for a model.

    Defines the maximum context and output sizes for a model.
    """

    model: str
    max_tokens: int
    max_output_tokens: int
    reserved_tokens: int = 1000  # Buffer for safety

    @classmethod
    def for_model(cls, model: str) -> "ContextLimits":
        """Get context limits for a model.

        Args:
            model: Model name or identifier.

        Returns:
            ContextLimits for the model.
        """
        model_lower = model.lower()

        # Try exact match
        if model_lower in MODEL_LIMITS:
            max_ctx, max_out = MODEL_LIMITS[model_lower]
            return cls(model=model, max_tokens=max_ctx, max_output_tokens=max_out)

        # Try prefix match
        for key, (max_ctx, max_out) in MODEL_LIMITS.items():
            if key in model_lower or model_lower.startswith(key):
                return cls(model=model, max_tokens=max_ctx, max_output_tokens=max_out)

        # Default limits
        logger.warning(f"Unknown model {model}, using default limits")
        max_ctx, max_out = MODEL_LIMITS["default"]
        return cls(model=model, max_tokens=max_ctx, max_output_tokens=max_out)

    @property
    def effective_limit(self) -> int:
        """Effective context limit after reserves.

        Returns:
            Usable context tokens.
        """
        return self.max_tokens - self.max_output_tokens - self.reserved_tokens


@dataclass
class ContextTracker:
    """Tracks current context usage.

    Monitors token usage across messages and detects overflow.
    """

    limits: ContextLimits
    counter: TokenCounter
    budget: ContextBudget = field(default_factory=lambda: ContextBudget(total=0))

    # Current state
    messages: list[dict[str, Any]] = field(default_factory=list)
    system_prompt: str = ""
    tool_definitions: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize budget with limits."""
        self.budget = ContextBudget(
            total=self.limits.effective_limit,
            response_reserve=self.limits.max_output_tokens,
        )

    @classmethod
    def for_model(cls, model: str) -> "ContextTracker":
        """Create tracker for a model.

        Args:
            model: Model name.

        Returns:
            ContextTracker instance.
        """
        limits = ContextLimits.for_model(model)
        counter = get_counter(model)
        return cls(limits=limits, counter=counter)

    def set_system_prompt(self, prompt: str) -> int:
        """Set system prompt and count tokens.

        Args:
            prompt: System prompt text.

        Returns:
            Token count for prompt.
        """
        self.system_prompt = prompt
        tokens = self.counter.count(prompt)
        self.budget.update_system_prompt(tokens)
        return tokens

    def set_tool_definitions(self, tools: list[dict[str, Any]]) -> int:
        """Set tool definitions and count tokens.

        Args:
            tools: Tool definition dictionaries.

        Returns:
            Token count for tools.
        """
        self.tool_definitions = tools
        # Estimate tool tokens
        import json
        tools_json = json.dumps(tools)
        tokens = self.counter.count(tools_json)
        self.budget.update_tools(tokens)
        return tokens

    def update(self, messages: list[dict[str, Any]]) -> int:
        """Update with new message list.

        Args:
            messages: Full message list.

        Returns:
            Token count for messages.
        """
        self.messages = list(messages)
        tokens = self.counter.count_messages(messages)
        self.budget.update_conversation(tokens)
        return tokens

    def add_message(self, message: dict[str, Any]) -> int:
        """Add a single message.

        Args:
            message: Message to add.

        Returns:
            Token count for message.
        """
        self.messages.append(message)
        tokens = self.counter.count_message(message)
        self.budget.conversation += tokens
        return tokens

    def current_tokens(self) -> int:
        """Get current total token usage.

        Returns:
            Total tokens in use.
        """
        return (
            self.budget.system_prompt +
            self.budget.conversation +
            self.budget.tools
        )

    def exceeds_limit(self) -> bool:
        """Check if context exceeds limit.

        Returns:
            True if over limit.
        """
        return self.current_tokens() > self.budget.conversation_budget

    def overflow_amount(self) -> int:
        """Calculate how many tokens over limit.

        Returns:
            Tokens over limit (0 if under).
        """
        diff = self.current_tokens() - self.budget.conversation_budget
        return max(0, diff)

    def available_tokens(self) -> int:
        """Get available tokens for new content.

        Returns:
            Available tokens.
        """
        return self.budget.available

    def usage_percentage(self) -> float:
        """Get context usage as percentage.

        Returns:
            Usage percentage (0-100).
        """
        if self.limits.effective_limit == 0:
            return 100.0
        return (self.current_tokens() / self.limits.effective_limit) * 100

    def reset(self) -> None:
        """Reset all messages."""
        self.messages = []
        self.budget.update_conversation(0)
```

---

## File 3: src/forge/context/strategies.py

```python
"""Context truncation strategies."""

import logging
from abc import ABC, abstractmethod
from typing import Any

from .tokens import TokenCounter

logger = logging.getLogger(__name__)


class TruncationStrategy(ABC):
    """Abstract base for truncation strategies.

    Truncation strategies reduce message history to fit
    within token limits while preserving important context.
    """

    @abstractmethod
    def truncate(
        self,
        messages: list[dict[str, Any]],
        target_tokens: int,
        counter: TokenCounter,
    ) -> list[dict[str, Any]]:
        """Truncate messages to fit target tokens.

        Args:
            messages: Messages to truncate.
            target_tokens: Target token count.
            counter: Token counter to use.

        Returns:
            Truncated message list.
        """
        ...

    def _count_messages(
        self,
        messages: list[dict[str, Any]],
        counter: TokenCounter,
    ) -> int:
        """Count tokens in messages."""
        return counter.count_messages(messages)


class SlidingWindowStrategy(TruncationStrategy):
    """Keep most recent messages within window.

    Simple strategy that keeps the N most recent messages.
    System prompt is always preserved.
    """

    def __init__(
        self,
        window_size: int = 20,
        preserve_system: bool = True,
    ) -> None:
        """Initialize sliding window strategy.

        Args:
            window_size: Maximum messages to keep.
            preserve_system: Whether to preserve system messages.
        """
        self.window_size = window_size
        self.preserve_system = preserve_system

    def truncate(
        self,
        messages: list[dict[str, Any]],
        target_tokens: int,
        counter: TokenCounter,
    ) -> list[dict[str, Any]]:
        """Truncate using sliding window.

        Args:
            messages: Messages to truncate.
            target_tokens: Target token count (ignored for window).
            counter: Token counter.

        Returns:
            Truncated messages.
        """
        if not messages:
            return []

        # Separate system messages
        system_messages = []
        other_messages = []

        for msg in messages:
            if self.preserve_system and msg.get("role") == "system":
                system_messages.append(msg)
            else:
                other_messages.append(msg)

        # Keep window of recent messages
        if len(other_messages) > self.window_size:
            other_messages = other_messages[-self.window_size:]

        # Combine
        result = system_messages + other_messages

        logger.debug(
            f"Sliding window: {len(messages)} -> {len(result)} messages"
        )

        return result


class TokenBudgetStrategy(TruncationStrategy):
    """Truncate to fit within token budget.

    Removes oldest messages (except system) until within budget.
    """

    def __init__(self, preserve_system: bool = True) -> None:
        """Initialize token budget strategy.

        Args:
            preserve_system: Whether to preserve system messages.
        """
        self.preserve_system = preserve_system

    def truncate(
        self,
        messages: list[dict[str, Any]],
        target_tokens: int,
        counter: TokenCounter,
    ) -> list[dict[str, Any]]:
        """Truncate to fit token budget.

        Args:
            messages: Messages to truncate.
            target_tokens: Maximum tokens allowed.
            counter: Token counter.

        Returns:
            Truncated messages.
        """
        if not messages:
            return []

        current_tokens = self._count_messages(messages, counter)

        if current_tokens <= target_tokens:
            return messages

        # Separate system messages
        system_messages = []
        other_messages = []

        for msg in messages:
            if self.preserve_system and msg.get("role") == "system":
                system_messages.append(msg)
            else:
                other_messages.append(msg)

        # Calculate tokens needed for system messages
        system_tokens = self._count_messages(system_messages, counter)
        available_tokens = target_tokens - system_tokens

        if available_tokens <= 0:
            logger.warning("System messages exceed budget")
            return system_messages

        # Remove oldest messages until within budget
        result = list(other_messages)

        while result and self._count_messages(result, counter) > available_tokens:
            # Remove oldest (first) message
            removed = result.pop(0)
            logger.debug(f"Removed message: {removed.get('role')}")

        final = system_messages + result

        logger.debug(
            f"Token budget: {len(messages)} -> {len(final)} messages, "
            f"{current_tokens} -> {self._count_messages(final, counter)} tokens"
        )

        return final


class SmartTruncationStrategy(TruncationStrategy):
    """Preserve first and last messages, remove middle.

    Keeps important context at conversation start and
    recent context at the end.
    """

    def __init__(
        self,
        preserve_first: int = 2,
        preserve_last: int = 10,
        preserve_system: bool = True,
    ) -> None:
        """Initialize smart truncation strategy.

        Args:
            preserve_first: First N messages to keep.
            preserve_last: Last N messages to keep.
            preserve_system: Whether to preserve system messages.
        """
        self.preserve_first = preserve_first
        self.preserve_last = preserve_last
        self.preserve_system = preserve_system

    def truncate(
        self,
        messages: list[dict[str, Any]],
        target_tokens: int,
        counter: TokenCounter,
    ) -> list[dict[str, Any]]:
        """Truncate keeping ends, removing middle.

        Args:
            messages: Messages to truncate.
            target_tokens: Maximum tokens allowed.
            counter: Token counter.

        Returns:
            Truncated messages.
        """
        if not messages:
            return []

        # Separate system messages
        system_messages = []
        other_messages = []

        for msg in messages:
            if self.preserve_system and msg.get("role") == "system":
                system_messages.append(msg)
            else:
                other_messages.append(msg)

        # If small enough, keep all
        total_preserve = self.preserve_first + self.preserve_last
        if len(other_messages) <= total_preserve:
            return system_messages + other_messages

        # Keep first and last
        first_msgs = other_messages[: self.preserve_first]
        last_msgs = other_messages[-self.preserve_last:]

        # Add truncation marker
        truncation_marker = {
            "role": "system",
            "content": f"[{len(other_messages) - total_preserve} messages omitted]",
        }

        result = system_messages + first_msgs + [truncation_marker] + last_msgs

        # Check if within budget, if not, reduce last messages
        while (
            self._count_messages(result, counter) > target_tokens
            and len(last_msgs) > 1
        ):
            last_msgs.pop(0)
            result = system_messages + first_msgs + [truncation_marker] + last_msgs

        logger.debug(
            f"Smart truncation: {len(messages)} -> {len(result)} messages"
        )

        return result


class SelectiveTruncationStrategy(TruncationStrategy):
    """Selectively preserve messages by criteria.

    Allows preserving messages marked as important or
    filtering by role.
    """

    def __init__(
        self,
        preserve_roles: set[str] | None = None,
        preserve_marked: bool = True,
        mark_key: str = "_preserve",
    ) -> None:
        """Initialize selective strategy.

        Args:
            preserve_roles: Roles to always preserve.
            preserve_marked: Preserve messages with mark_key.
            mark_key: Key in message metadata for preservation.
        """
        self.preserve_roles = preserve_roles or {"system"}
        self.preserve_marked = preserve_marked
        self.mark_key = mark_key

    def truncate(
        self,
        messages: list[dict[str, Any]],
        target_tokens: int,
        counter: TokenCounter,
    ) -> list[dict[str, Any]]:
        """Truncate selectively.

        Args:
            messages: Messages to truncate.
            target_tokens: Maximum tokens.
            counter: Token counter.

        Returns:
            Truncated messages.
        """
        if not messages:
            return []

        # Separate preserved and removable
        preserved = []
        removable = []

        for msg in messages:
            role = msg.get("role", "")
            marked = msg.get(self.mark_key, False)

            if role in self.preserve_roles or (self.preserve_marked and marked):
                preserved.append(msg)
            else:
                removable.append(msg)

        # Check if preserved alone fits
        preserved_tokens = self._count_messages(preserved, counter)
        if preserved_tokens >= target_tokens:
            logger.warning("Preserved messages exceed budget")
            return preserved

        # Add removable from end until budget
        available = target_tokens - preserved_tokens
        result = list(preserved)
        added = []

        for msg in reversed(removable):
            msg_tokens = counter.count_message(msg)
            if self._count_messages(added + [msg], counter) <= available:
                added.insert(0, msg)
            else:
                break

        # Merge in order
        result.extend(added)

        # Sort by original order
        msg_order = {id(m): i for i, m in enumerate(messages)}
        result.sort(key=lambda m: msg_order.get(id(m), 0))

        return result


class CompositeStrategy(TruncationStrategy):
    """Chain multiple strategies.

    Applies strategies in order until within budget.
    """

    def __init__(self, strategies: list[TruncationStrategy]) -> None:
        """Initialize composite strategy.

        Args:
            strategies: Strategies to apply in order.
        """
        self.strategies = strategies

    def truncate(
        self,
        messages: list[dict[str, Any]],
        target_tokens: int,
        counter: TokenCounter,
    ) -> list[dict[str, Any]]:
        """Truncate using chained strategies.

        Args:
            messages: Messages to truncate.
            target_tokens: Maximum tokens.
            counter: Token counter.

        Returns:
            Truncated messages.
        """
        result = messages

        for strategy in self.strategies:
            result = strategy.truncate(result, target_tokens, counter)

            if self._count_messages(result, counter) <= target_tokens:
                break

        return result
```

---

## File 4: src/forge/context/compaction.py

```python
"""Context compaction via summarization."""

import logging
from typing import Any, TYPE_CHECKING

from .tokens import TokenCounter

if TYPE_CHECKING:
    pass  # LLM types would go here

logger = logging.getLogger(__name__)


SUMMARY_PROMPT = """Summarize the following conversation concisely.
Preserve key decisions, code changes, and important context.
The summary will be used to continue the conversation.

Conversation:
{conversation}

Provide a brief summary (max {max_tokens} tokens):"""


class ContextCompactor:
    """Compacts context via LLM summarization.

    Uses an LLM to summarize older conversation history,
    replacing many messages with a concise summary.
    """

    def __init__(
        self,
        llm: Any,  # OpenRouterLLM
        summary_prompt: str = SUMMARY_PROMPT,
        max_summary_tokens: int = 500,
        min_messages_to_summarize: int = 5,
    ) -> None:
        """Initialize compactor.

        Args:
            llm: LLM client for summarization.
            summary_prompt: Prompt template for summarization.
            max_summary_tokens: Maximum tokens for summary.
            min_messages_to_summarize: Minimum messages before summarizing.
        """
        self.llm = llm
        self.summary_prompt = summary_prompt
        self.max_summary_tokens = max_summary_tokens
        self.min_messages_to_summarize = min_messages_to_summarize

    async def compact(
        self,
        messages: list[dict[str, Any]],
        target_tokens: int,
        counter: TokenCounter,
        preserve_last: int = 10,
    ) -> list[dict[str, Any]]:
        """Compact messages via summarization.

        Args:
            messages: Messages to compact.
            target_tokens: Target token count.
            counter: Token counter.
            preserve_last: Number of recent messages to preserve.

        Returns:
            Compacted message list.
        """
        if not messages:
            return []

        # Separate system and other messages
        system_messages = []
        other_messages = []

        for msg in messages:
            if msg.get("role") == "system":
                system_messages.append(msg)
            else:
                other_messages.append(msg)

        # If too few messages, don't summarize
        if len(other_messages) <= self.min_messages_to_summarize + preserve_last:
            return messages

        # Split into messages to summarize and to preserve
        to_summarize = other_messages[:-preserve_last]
        to_preserve = other_messages[-preserve_last:]

        # Check if summarization would help
        if len(to_summarize) < self.min_messages_to_summarize:
            return messages

        # Summarize
        try:
            summary = await self.summarize_messages(to_summarize)

            summary_message = {
                "role": "system",
                "content": f"[Previous conversation summary]\n{summary}",
            }

            result = system_messages + [summary_message] + to_preserve

            # Verify we're within budget
            if counter.count_messages(result) <= target_tokens:
                logger.info(
                    f"Compacted {len(to_summarize)} messages to summary"
                )
                return result
            else:
                logger.warning("Summary still exceeds budget")
                return messages

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return messages

    async def summarize_messages(
        self,
        messages: list[dict[str, Any]],
    ) -> str:
        """Summarize a list of messages.

        Args:
            messages: Messages to summarize.

        Returns:
            Summary text.
        """
        # Format messages for summary
        conversation = self._format_for_summary(messages)

        # Build prompt
        prompt = self.summary_prompt.format(
            conversation=conversation,
            max_tokens=self.max_summary_tokens,
        )

        # Call LLM
        response = await self.llm.ainvoke([{"role": "user", "content": prompt}])

        return response.content

    def _format_for_summary(self, messages: list[dict[str, Any]]) -> str:
        """Format messages for summarization.

        Args:
            messages: Messages to format.

        Returns:
            Formatted conversation string.
        """
        lines = []

        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # Truncate long content
            if len(content) > 500:
                content = content[:500] + "..."

            lines.append(f"{role}: {content}")

        return "\n".join(lines)


class ToolResultCompactor:
    """Compacts large tool results.

    Truncates tool output that exceeds token limits.
    """

    def __init__(
        self,
        max_result_tokens: int = 1000,
        truncation_message: str = "\n[Output truncated - {removed} tokens removed]",
    ) -> None:
        """Initialize tool result compactor.

        Args:
            max_result_tokens: Maximum tokens per tool result.
            truncation_message: Message to append when truncating.
        """
        self.max_result_tokens = max_result_tokens
        self.truncation_message = truncation_message

    def compact_result(
        self,
        result: str,
        counter: TokenCounter,
    ) -> str:
        """Compact a tool result if too large.

        Args:
            result: Tool result text.
            counter: Token counter.

        Returns:
            Compacted result.
        """
        if not result:
            return result

        tokens = counter.count(result)

        if tokens <= self.max_result_tokens:
            return result

        # Binary search for truncation point
        target_tokens = self.max_result_tokens - 50  # Reserve for message

        # Estimate characters per token
        chars_per_token = len(result) / tokens
        estimated_chars = int(target_tokens * chars_per_token)

        # Truncate
        truncated = result[:estimated_chars]

        # Find a good break point (newline or space)
        for i in range(min(100, len(truncated))):
            pos = estimated_chars - i
            if pos > 0 and result[pos] in "\n ":
                truncated = result[:pos]
                break

        removed = tokens - counter.count(truncated)
        message = self.truncation_message.format(removed=removed)

        return truncated + message

    def compact_message(
        self,
        message: dict[str, Any],
        counter: TokenCounter,
    ) -> dict[str, Any]:
        """Compact tool message if needed.

        Args:
            message: Tool result message.
            counter: Token counter.

        Returns:
            Possibly compacted message.
        """
        if message.get("role") != "tool":
            return message

        content = message.get("content", "")
        compacted = self.compact_result(content, counter)

        if compacted != content:
            return {**message, "content": compacted}

        return message
```

---

## File 5: src/forge/context/manager.py

```python
"""Central context management."""

import logging
from enum import Enum
from typing import Any

from .compaction import ContextCompactor, ToolResultCompactor
from .limits import ContextTracker
from .strategies import (
    CompositeStrategy,
    SlidingWindowStrategy,
    SmartTruncationStrategy,
    TokenBudgetStrategy,
    TruncationStrategy,
)
from .tokens import TokenCounter, get_counter

logger = logging.getLogger(__name__)


class TruncationMode(str, Enum):
    """Truncation mode selection."""

    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUDGET = "token_budget"
    SMART = "smart"
    SUMMARIZE = "summarize"


def get_strategy(mode: TruncationMode) -> TruncationStrategy:
    """Get truncation strategy for mode.

    Args:
        mode: Truncation mode.

    Returns:
        TruncationStrategy instance.
    """
    if mode == TruncationMode.SLIDING_WINDOW:
        return SlidingWindowStrategy()
    elif mode == TruncationMode.TOKEN_BUDGET:
        return TokenBudgetStrategy()
    elif mode == TruncationMode.SMART:
        return SmartTruncationStrategy()
    elif mode == TruncationMode.SUMMARIZE:
        # Summarize falls back to smart truncation
        return CompositeStrategy([
            SmartTruncationStrategy(),
            TokenBudgetStrategy(),
        ])
    else:
        return SmartTruncationStrategy()


class ContextManager:
    """Central context management.

    Coordinates token counting, tracking, and truncation
    to keep context within model limits.
    """

    def __init__(
        self,
        model: str,
        mode: TruncationMode = TruncationMode.SMART,
        llm: Any | None = None,
        auto_truncate: bool = True,
    ) -> None:
        """Initialize context manager.

        Args:
            model: Model name for limits and counting.
            mode: Truncation mode to use.
            llm: LLM client for summarization (optional).
            auto_truncate: Automatically truncate on overflow.
        """
        self.model = model
        self.mode = mode
        self.auto_truncate = auto_truncate

        # Initialize components
        self.counter = get_counter(model)
        self.tracker = ContextTracker.for_model(model)
        self.strategy = get_strategy(mode)

        # Optional compactors
        self.compactor = ContextCompactor(llm) if llm else None
        self.tool_compactor = ToolResultCompactor()

        # Internal state
        self._messages: list[dict[str, Any]] = []
        self._system_prompt: str = ""

    def set_system_prompt(self, prompt: str) -> int:
        """Set the system prompt.

        Args:
            prompt: System prompt text.

        Returns:
            Token count for prompt.
        """
        self._system_prompt = prompt
        return self.tracker.set_system_prompt(prompt)

    def set_tool_definitions(self, tools: list[dict[str, Any]]) -> int:
        """Set tool definitions.

        Args:
            tools: Tool definition list.

        Returns:
            Token count for tools.
        """
        return self.tracker.set_tool_definitions(tools)

    def add_message(self, message: dict[str, Any]) -> None:
        """Add a message to context.

        Automatically truncates if needed and auto_truncate is enabled.

        Args:
            message: Message to add.
        """
        # Compact tool results if needed
        if message.get("role") == "tool":
            message = self.tool_compactor.compact_message(message, self.counter)

        self._messages.append(message)
        self.tracker.add_message(message)

        # Check for overflow
        if self.auto_truncate and self.tracker.exceeds_limit():
            self._truncate()

    def add_messages(self, messages: list[dict[str, Any]]) -> None:
        """Add multiple messages.

        Args:
            messages: Messages to add.
        """
        for message in messages:
            self.add_message(message)

    def get_messages(self) -> list[dict[str, Any]]:
        """Get current message list.

        Returns:
            Current messages.
        """
        return list(self._messages)

    def get_context_for_request(self) -> list[dict[str, Any]]:
        """Get messages ready for LLM request.

        Includes system prompt as first message.

        Returns:
            Messages for LLM request.
        """
        messages = []

        if self._system_prompt:
            messages.append({
                "role": "system",
                "content": self._system_prompt,
            })

        messages.extend(self._messages)
        return messages

    def _truncate(self) -> None:
        """Truncate messages to fit within limit."""
        target_tokens = self.tracker.budget.conversation_budget

        truncated = self.strategy.truncate(
            self._messages,
            target_tokens,
            self.counter,
        )

        if len(truncated) < len(self._messages):
            logger.info(
                f"Truncated context: {len(self._messages)} -> {len(truncated)} messages"
            )
            self._messages = truncated
            self.tracker.update(truncated)

    async def compact_if_needed(self, threshold: float = 0.9) -> bool:
        """Compact context if usage exceeds threshold.

        Args:
            threshold: Usage percentage to trigger compaction.

        Returns:
            True if compaction occurred.
        """
        if not self.compactor:
            return False

        usage = self.tracker.usage_percentage()

        if usage < threshold * 100:
            return False

        target_tokens = int(self.tracker.budget.conversation_budget * 0.7)

        compacted = await self.compactor.compact(
            self._messages,
            target_tokens,
            self.counter,
        )

        if len(compacted) < len(self._messages):
            self._messages = compacted
            self.tracker.update(compacted)
            return True

        return False

    @property
    def token_usage(self) -> int:
        """Current token usage.

        Returns:
            Total tokens in use.
        """
        return self.tracker.current_tokens()

    @property
    def available_tokens(self) -> int:
        """Available tokens for new content.

        Returns:
            Available tokens.
        """
        return self.tracker.available_tokens()

    @property
    def usage_percentage(self) -> float:
        """Context usage percentage.

        Returns:
            Usage as percentage.
        """
        return self.tracker.usage_percentage()

    @property
    def is_near_limit(self) -> bool:
        """Check if near context limit.

        Returns:
            True if over 80% usage.
        """
        return self.usage_percentage > 80

    def reset(self) -> None:
        """Clear all messages."""
        self._messages = []
        self.tracker.reset()

    def get_stats(self) -> dict[str, Any]:
        """Get context statistics.

        Returns:
            Dictionary of stats.
        """
        return {
            "model": self.model,
            "mode": self.mode.value,
            "message_count": len(self._messages),
            "token_usage": self.token_usage,
            "available_tokens": self.available_tokens,
            "usage_percentage": self.usage_percentage,
            "max_tokens": self.tracker.limits.max_tokens,
            "effective_limit": self.tracker.limits.effective_limit,
        }
```

---

## File 6: src/forge/context/__init__.py

```python
"""Context management package.

This package provides context window management for Code-Forge,
including token counting, truncation strategies, and compaction.

Example:
    from forge.context import ContextManager, TruncationMode

    # Create manager for model
    manager = ContextManager(
        model="anthropic/claude-3-opus",
        mode=TruncationMode.SMART,
    )

    # Set system prompt
    manager.set_system_prompt("You are a helpful assistant.")

    # Add messages
    manager.add_message({"role": "user", "content": "Hello"})
    manager.add_message({"role": "assistant", "content": "Hi there!"})

    # Check usage
    print(f"Usage: {manager.usage_percentage:.1f}%")

    # Get messages for request
    messages = manager.get_context_for_request()
"""

from .tokens import (
    TokenCounter,
    TiktokenCounter,
    ApproximateCounter,
    CachingCounter,
    get_counter,
)
from .limits import (
    ContextBudget,
    ContextLimits,
    ContextTracker,
)
from .strategies import (
    TruncationStrategy,
    SlidingWindowStrategy,
    TokenBudgetStrategy,
    SmartTruncationStrategy,
    SelectiveTruncationStrategy,
    CompositeStrategy,
)
from .compaction import (
    ContextCompactor,
    ToolResultCompactor,
)
from .manager import (
    TruncationMode,
    ContextManager,
)

__all__ = [
    # Tokens
    "TokenCounter",
    "TiktokenCounter",
    "ApproximateCounter",
    "CachingCounter",
    "get_counter",
    # Limits
    "ContextBudget",
    "ContextLimits",
    "ContextTracker",
    # Strategies
    "TruncationStrategy",
    "SlidingWindowStrategy",
    "TokenBudgetStrategy",
    "SmartTruncationStrategy",
    "SelectiveTruncationStrategy",
    "CompositeStrategy",
    # Compaction
    "ContextCompactor",
    "ToolResultCompactor",
    # Manager
    "TruncationMode",
    "ContextManager",
]
```

---

## Integration Notes

### With Session Management (Phase 5.1)

```python
from forge.sessions import SessionManager, SessionMessage
from forge.context import ContextManager

# Create context manager
ctx = ContextManager(model="claude-3-opus")

# Sync with session - use to_llm_message() for proper conversion
session = SessionManager.get_instance().current_session
for msg in session.messages:
    # Use the adapter method to convert SessionMessage -> dict
    ctx.add_message(msg.to_llm_message())

# Get context for LLM
messages = ctx.get_context_for_request()

# When receiving from LLM, convert back to SessionMessage
from_llm: dict = {"role": "assistant", "content": "Hello!"}
session_msg = SessionMessage.from_llm_message(from_llm)
session.add_message(session_msg)
```

### With LangChain Integration (Phase 3.2)

```python
from forge.langchain import OpenRouterLLM
from forge.context import ContextManager, TruncationMode

llm = OpenRouterLLM(model="anthropic/claude-3-opus")

# Enable summarization
ctx = ContextManager(
    model="anthropic/claude-3-opus",
    mode=TruncationMode.SUMMARIZE,
    llm=llm,
)
```

---

## Next Steps

After implementing Phase 5.2:
1. Verify all tests pass
2. Run type checking with mypy
3. Proceed to Phase 6.1 (Slash Commands)
