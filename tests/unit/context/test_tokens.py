"""Unit tests for token counting implementations."""

import threading
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from code_forge.context.tokens import (
    ApproximateCounter,
    CachingCounter,
    TiktokenCounter,
    TokenCounter,
    get_counter,
)


class TestTokenCounter:
    """Tests for TokenCounter base class."""

    def test_count_message_delegates_to_count_messages(self) -> None:
        """count_message should delegate to count_messages with single message."""

        class TestCounter(TokenCounter):
            def count(self, text: str) -> int:
                return len(text)

            def count_messages(self, messages: list[dict[str, Any]]) -> int:
                return len(messages) * 10

        counter = TestCounter()
        message = {"role": "user", "content": "Hello"}

        result = counter.count_message(message)

        assert result == 10


class TestTiktokenCounter:
    """Tests for TiktokenCounter."""

    def test_count_empty_string(self) -> None:
        """Empty string should return 0 tokens."""
        counter = TiktokenCounter()
        assert counter.count("") == 0

    def test_count_simple_text(self) -> None:
        """Should count tokens in simple text."""
        counter = TiktokenCounter()
        text = "Hello, world!"
        tokens = counter.count(text)
        assert tokens > 0

    def test_count_with_model(self) -> None:
        """Should work with model name."""
        counter = TiktokenCounter(model="gpt-4")
        text = "Hello, world!"
        tokens = counter.count(text)
        assert tokens > 0

    def test_count_with_unknown_model_uses_default(self) -> None:
        """Unknown model should use default encoding."""
        counter = TiktokenCounter(model="unknown-model-xyz")
        text = "Hello, world!"
        tokens = counter.count(text)
        assert tokens > 0

    def test_count_messages_empty(self) -> None:
        """Empty messages should return 0."""
        counter = TiktokenCounter()
        assert counter.count_messages([]) == 0

    def test_count_messages_single(self) -> None:
        """Should count single message with overhead."""
        counter = TiktokenCounter()
        messages = [{"role": "user", "content": "Hello"}]
        tokens = counter.count_messages(messages)
        # Should include message overhead + content + reply overhead
        assert tokens > counter.count("Hello")

    def test_count_messages_multiple(self) -> None:
        """Should count multiple messages."""
        counter = TiktokenCounter()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        tokens = counter.count_messages(messages)
        assert tokens > 0

    def test_count_messages_with_tool_calls(self) -> None:
        """Should count messages with tool calls."""
        counter = TiktokenCounter()
        messages = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "function": {
                            "name": "read_file",
                            "arguments": '{"path": "/tmp/file.txt"}',
                        },
                    }
                ],
            }
        ]
        tokens = counter.count_messages(messages)
        assert tokens > 0

    def test_count_messages_with_tool_result(self) -> None:
        """Should count tool result messages."""
        counter = TiktokenCounter()
        messages = [
            {
                "role": "tool",
                "content": "File contents here",
                "tool_call_id": "call_123",
            }
        ]
        tokens = counter.count_messages(messages)
        assert tokens > 0

    def test_count_messages_with_name(self) -> None:
        """Should count messages with name field."""
        counter = TiktokenCounter()
        messages = [{"role": "user", "content": "Hello", "name": "Alice"}]
        tokens_with_name = counter.count_messages(messages)

        messages_no_name = [{"role": "user", "content": "Hello"}]
        tokens_no_name = counter.count_messages(messages_no_name)

        assert tokens_with_name > tokens_no_name

    def test_fallback_when_tiktoken_unavailable(self) -> None:
        """Should fall back to approximate counting when tiktoken not available."""
        counter = TiktokenCounter()
        counter._encoding = None  # Simulate tiktoken unavailable

        text = "Hello, world!"
        tokens = counter.count(text)
        assert tokens > 0


class TestApproximateCounter:
    """Tests for ApproximateCounter."""

    def test_count_empty_string(self) -> None:
        """Empty string should return 0."""
        counter = ApproximateCounter()
        assert counter.count("") == 0

    def test_count_simple_words(self) -> None:
        """Should count words with tokens_per_word ratio."""
        counter = ApproximateCounter(tokens_per_word=1.3)
        text = "one two three four five"
        tokens = counter.count(text)
        # 5 words * 1.3 = 6.5, plus some for spaces
        assert 5 <= tokens <= 10

    def test_count_with_punctuation(self) -> None:
        """Should count punctuation as character tokens."""
        counter = ApproximateCounter(tokens_per_word=1.0, tokens_per_char=0.25)
        text = "Hello!!!"
        tokens = counter.count(text)
        # 1 word + 3 punctuation chars * 0.25 = ~1.75
        assert tokens >= 1

    def test_count_messages_empty(self) -> None:
        """Empty messages should return 0."""
        counter = ApproximateCounter()
        assert counter.count_messages([]) == 0

    def test_count_messages_with_overhead(self) -> None:
        """Should include message overhead."""
        counter = ApproximateCounter()
        messages = [{"role": "user", "content": "Hi"}]
        tokens = counter.count_messages(messages)
        # Should include 4 token overhead per message
        assert tokens >= 4

    def test_count_messages_with_tool_calls(self) -> None:
        """Should count tool calls in messages."""
        counter = ApproximateCounter()
        messages = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "read_file",
                            "arguments": '{"path": "/tmp"}',
                        }
                    }
                ],
            }
        ]
        tokens = counter.count_messages(messages)
        assert tokens > 10  # Should include tool call overhead

    def test_custom_tokens_per_word(self) -> None:
        """Should respect custom tokens_per_word."""
        counter1 = ApproximateCounter(tokens_per_word=1.0)
        counter2 = ApproximateCounter(tokens_per_word=2.0)

        text = "one two three"
        tokens1 = counter1.count(text)
        tokens2 = counter2.count(text)

        assert tokens2 > tokens1


class TestCachingCounter:
    """Tests for CachingCounter."""

    def test_init_requires_positive_cache_size(self) -> None:
        """Should raise ValueError for non-positive cache size."""
        base = ApproximateCounter()

        with pytest.raises(ValueError, match="must be positive"):
            CachingCounter(base, max_cache_size=0)

        with pytest.raises(ValueError, match="must be positive"):
            CachingCounter(base, max_cache_size=-1)

    def test_count_delegates_to_wrapped_counter(self) -> None:
        """Should delegate to wrapped counter."""
        base = ApproximateCounter()
        caching = CachingCounter(base)

        text = "Hello, world!"
        expected = base.count(text)
        actual = caching.count(text)

        assert actual == expected

    def test_count_caches_result(self) -> None:
        """Should cache result for repeated calls."""
        base = MagicMock(spec=TokenCounter)
        base.count.return_value = 10

        caching = CachingCounter(base)

        # First call
        result1 = caching.count("Hello")
        # Second call (should be cached)
        result2 = caching.count("Hello")

        assert result1 == result2
        assert base.count.call_count == 1  # Only called once

    def test_cache_hit_updates_stats(self) -> None:
        """Should track cache hits."""
        base = ApproximateCounter()
        caching = CachingCounter(base)

        caching.count("Hello")
        caching.count("Hello")

        stats = caching.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_cache_eviction_lru(self) -> None:
        """Should evict least recently used entries."""
        base = ApproximateCounter()
        caching = CachingCounter(base, max_cache_size=2)

        # Fill cache
        caching.count("one")
        caching.count("two")

        # Access "one" to make it more recent
        caching.count("one")

        # Add "three" - should evict "two"
        caching.count("three")

        stats = caching.get_stats()
        assert stats["size"] == 2

    def test_count_messages_delegates(self) -> None:
        """count_messages should delegate to wrapped counter."""
        base = MagicMock(spec=TokenCounter)
        base.count_messages.return_value = 50

        caching = CachingCounter(base)
        messages = [{"role": "user", "content": "Hello"}]

        result = caching.count_messages(messages)

        assert result == 50
        base.count_messages.assert_called_once_with(messages)

    def test_clear_cache(self) -> None:
        """Should clear cache and reset stats."""
        base = ApproximateCounter()
        caching = CachingCounter(base)

        caching.count("Hello")
        caching.count("Hello")

        caching.clear_cache()

        stats = caching.get_stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0

    def test_get_stats_hit_rate(self) -> None:
        """Should calculate hit rate percentage."""
        base = ApproximateCounter()
        caching = CachingCounter(base)

        # 1 miss, then 3 hits = 75% hit rate
        caching.count("Hello")
        caching.count("Hello")
        caching.count("Hello")
        caching.count("Hello")

        stats = caching.get_stats()
        assert stats["hit_rate_percent"] == 75

    def test_thread_safety(self) -> None:
        """Should be thread-safe."""
        base = ApproximateCounter()
        caching = CachingCounter(base, max_cache_size=100)

        results: list[int] = []

        def count_many() -> None:
            for i in range(50):
                result = caching.count(f"text_{i % 10}")
                results.append(result)

        threads = [threading.Thread(target=count_many) for _ in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All operations should complete without error
        assert len(results) == 250


class TestGetCounter:
    """Tests for get_counter factory function."""

    def test_returns_caching_counter(self) -> None:
        """Should return a CachingCounter."""
        counter = get_counter("gpt-4")
        assert isinstance(counter, CachingCounter)

    def test_tiktoken_for_known_models(self) -> None:
        """Should use TiktokenCounter for known models."""
        for model in ["gpt-4", "gpt-3.5", "claude", "anthropic"]:
            counter = get_counter(model)
            assert isinstance(counter, CachingCounter)
            assert isinstance(counter._counter, TiktokenCounter)

    def test_approximate_for_unknown_models(self) -> None:
        """Should use ApproximateCounter for unknown models."""
        counter = get_counter("unknown-model-xyz")
        assert isinstance(counter, CachingCounter)
        assert isinstance(counter._counter, ApproximateCounter)

    def test_case_insensitive(self) -> None:
        """Model name matching should be case insensitive."""
        counter1 = get_counter("GPT-4")
        counter2 = get_counter("gpt-4")

        # Both should get TiktokenCounter
        assert isinstance(counter1._counter, TiktokenCounter)
        assert isinstance(counter2._counter, TiktokenCounter)


class TestTokenCountingAccuracy:
    """Tests for token counting accuracy."""

    def test_approximate_vs_tiktoken_within_range(self) -> None:
        """Approximate counter should be within reasonable range of tiktoken."""
        tiktoken_counter = TiktokenCounter()
        approx_counter = ApproximateCounter()

        texts = [
            "Hello, world!",
            "The quick brown fox jumps over the lazy dog.",
            "def foo(x):\n    return x * 2",
            "This is a longer piece of text that contains multiple sentences. "
            "It should test the token counting more thoroughly.",
        ]

        for text in texts:
            tiktoken_tokens = tiktoken_counter.count(text)
            approx_tokens = approx_counter.count(text)

            # Allow 50% variance for approximate counter
            assert approx_tokens > 0
            if tiktoken_tokens > 0:
                ratio = approx_tokens / tiktoken_tokens
                assert 0.5 <= ratio <= 2.0, f"Ratio {ratio} for text: {text[:30]}..."
