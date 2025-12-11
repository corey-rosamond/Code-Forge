"""Unit tests for truncation strategies."""

from typing import Any
from unittest.mock import MagicMock

import pytest

from code_forge.context.strategies import (
    CompositeStrategy,
    SelectiveTruncationStrategy,
    SlidingWindowStrategy,
    SmartTruncationStrategy,
    TokenBudgetStrategy,
    TruncationStrategy,
)
from code_forge.context.tokens import ApproximateCounter, TokenCounter


def make_messages(count: int, content_size: int = 10) -> list[dict[str, Any]]:
    """Create test messages."""
    return [
        {"role": "user" if i % 2 == 0 else "assistant", "content": "x" * content_size}
        for i in range(count)
    ]


class TestSlidingWindowStrategy:
    """Tests for SlidingWindowStrategy."""

    def test_empty_messages(self) -> None:
        """Should return empty list for empty input."""
        strategy = SlidingWindowStrategy()
        counter = ApproximateCounter()

        result = strategy.truncate([], 1000, counter)
        assert result == []

    def test_no_truncation_when_under_window(self) -> None:
        """Should keep all messages when under window size."""
        strategy = SlidingWindowStrategy(window_size=10)
        counter = ApproximateCounter()
        messages = make_messages(5)

        result = strategy.truncate(messages, 10000, counter)
        assert len(result) == 5

    def test_truncation_keeps_recent(self) -> None:
        """Should keep most recent messages."""
        strategy = SlidingWindowStrategy(window_size=3)
        counter = ApproximateCounter()
        messages = [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Second"},
            {"role": "user", "content": "Third"},
            {"role": "assistant", "content": "Fourth"},
            {"role": "user", "content": "Fifth"},
        ]

        result = strategy.truncate(messages, 10000, counter)

        assert len(result) == 3
        assert result[0]["content"] == "Third"
        assert result[1]["content"] == "Fourth"
        assert result[2]["content"] == "Fifth"

    def test_preserves_system_messages(self) -> None:
        """Should preserve system messages when preserve_system=True."""
        strategy = SlidingWindowStrategy(window_size=2, preserve_system=True)
        counter = ApproximateCounter()
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Second"},
            {"role": "user", "content": "Third"},
        ]

        result = strategy.truncate(messages, 10000, counter)

        # Should have system + 2 recent
        assert len(result) == 3
        assert result[0]["role"] == "system"
        assert result[1]["content"] == "Second"
        assert result[2]["content"] == "Third"

    def test_no_preserve_system(self) -> None:
        """Should not preserve system messages when preserve_system=False."""
        strategy = SlidingWindowStrategy(window_size=2, preserve_system=False)
        counter = ApproximateCounter()
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Second"},
            {"role": "user", "content": "Third"},
        ]

        result = strategy.truncate(messages, 10000, counter)

        # Should have just 2 recent (no system)
        assert len(result) == 2


class TestTokenBudgetStrategy:
    """Tests for TokenBudgetStrategy."""

    def test_empty_messages(self) -> None:
        """Should return empty list for empty input."""
        strategy = TokenBudgetStrategy()
        counter = ApproximateCounter()

        result = strategy.truncate([], 1000, counter)
        assert result == []

    def test_no_truncation_when_under_budget(self) -> None:
        """Should keep all messages when under budget."""
        strategy = TokenBudgetStrategy()
        counter = ApproximateCounter()
        messages = make_messages(5)

        result = strategy.truncate(messages, 100000, counter)
        assert len(result) == 5

    def test_truncation_removes_oldest(self) -> None:
        """Should remove oldest messages first."""
        strategy = TokenBudgetStrategy()
        counter = ApproximateCounter()
        # Use real words so token count is realistic
        messages = [
            {"role": "user", "content": "word " * 50},      # ~65 tokens
            {"role": "assistant", "content": "word " * 50}, # ~65 tokens
            {"role": "user", "content": "final " * 50},     # ~65 tokens
        ]

        # Small budget to force truncation
        result = strategy.truncate(messages, 80, counter)

        # Should keep recent messages
        assert len(result) < 3
        if len(result) > 0:
            assert result[-1]["content"] == "final " * 50

    def test_preserves_system_messages(self) -> None:
        """Should preserve system messages."""
        strategy = TokenBudgetStrategy(preserve_system=True)
        counter = ApproximateCounter()
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "A" * 100},
            {"role": "assistant", "content": "B" * 100},
        ]

        result = strategy.truncate(messages, 50, counter)

        # System should be preserved
        assert any(m["role"] == "system" for m in result)

    def test_system_messages_exceed_budget(self) -> None:
        """Should return only system if system exceeds budget."""
        strategy = TokenBudgetStrategy(preserve_system=True)
        counter = ApproximateCounter()
        messages = [
            {"role": "system", "content": "A" * 1000},
            {"role": "user", "content": "Hello"},
        ]

        result = strategy.truncate(messages, 10, counter)

        # Should only have system message
        assert len(result) == 1
        assert result[0]["role"] == "system"


class TestSmartTruncationStrategy:
    """Tests for SmartTruncationStrategy."""

    def test_empty_messages(self) -> None:
        """Should return empty list for empty input."""
        strategy = SmartTruncationStrategy()
        counter = ApproximateCounter()

        result = strategy.truncate([], 1000, counter)
        assert result == []

    def test_no_truncation_when_small(self) -> None:
        """Should keep all messages when <= preserve_first + preserve_last."""
        strategy = SmartTruncationStrategy(preserve_first=2, preserve_last=3)
        counter = ApproximateCounter()
        messages = make_messages(4)

        result = strategy.truncate(messages, 100000, counter)
        assert len(result) == 4

    def test_keeps_first_and_last(self) -> None:
        """Should keep first and last messages, remove middle."""
        strategy = SmartTruncationStrategy(
            preserve_first=2, preserve_last=2, preserve_system=False
        )
        counter = ApproximateCounter()
        messages = [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Second"},
            {"role": "user", "content": "Third"},
            {"role": "assistant", "content": "Fourth"},
            {"role": "user", "content": "Fifth"},
            {"role": "assistant", "content": "Sixth"},
        ]

        result = strategy.truncate(messages, 100000, counter)

        # Should have: first 2 + marker + last 2 = 5
        assert len(result) == 5
        assert result[0]["content"] == "First"
        assert result[1]["content"] == "Second"
        assert "omitted" in result[2]["content"]
        assert result[3]["content"] == "Fifth"
        assert result[4]["content"] == "Sixth"

    def test_truncation_marker_content(self) -> None:
        """Truncation marker should show omitted count."""
        strategy = SmartTruncationStrategy(
            preserve_first=1, preserve_last=1, preserve_system=False
        )
        counter = ApproximateCounter()
        messages = make_messages(10)

        result = strategy.truncate(messages, 100000, counter)

        # Find the marker
        marker = next(m for m in result if "omitted" in m.get("content", ""))
        assert "[8 messages omitted]" in marker["content"]

    def test_preserves_system_messages(self) -> None:
        """Should preserve system messages."""
        strategy = SmartTruncationStrategy(
            preserve_first=1, preserve_last=1, preserve_system=True
        )
        counter = ApproximateCounter()
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "1"},
            {"role": "assistant", "content": "2"},
            {"role": "user", "content": "3"},
            {"role": "assistant", "content": "4"},
        ]

        result = strategy.truncate(messages, 100000, counter)

        # System should be at start
        assert result[0]["role"] == "system"

    def test_reduces_last_when_over_budget(self) -> None:
        """Should reduce last messages when over budget."""
        strategy = SmartTruncationStrategy(
            preserve_first=1, preserve_last=5, preserve_system=False
        )
        counter = ApproximateCounter()
        # Use real words so token count is realistic
        messages = [{"role": "user", "content": "word " * 20} for _ in range(20)]

        # Small budget to force reduction
        result = strategy.truncate(messages, 200, counter)

        # Should have fewer messages than the original
        assert len(result) < 20


class TestSelectiveTruncationStrategy:
    """Tests for SelectiveTruncationStrategy."""

    def test_empty_messages(self) -> None:
        """Should return empty list for empty input."""
        strategy = SelectiveTruncationStrategy()
        counter = ApproximateCounter()

        result = strategy.truncate([], 1000, counter)
        assert result == []

    def test_preserve_by_role(self) -> None:
        """Should preserve messages by role."""
        strategy = SelectiveTruncationStrategy(
            preserve_roles={"system", "user"}, preserve_marked=False
        )
        counter = ApproximateCounter()
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "User"},
            {"role": "assistant", "content": "Assistant"},
            {"role": "tool", "content": "Tool"},
        ]

        result = strategy.truncate(messages, 50, counter)

        roles = {m["role"] for m in result}
        assert "system" in roles
        assert "user" in roles

    def test_preserve_marked_messages(self) -> None:
        """Should preserve messages marked with _preserve."""
        strategy = SelectiveTruncationStrategy(
            preserve_roles=set(), preserve_marked=True
        )
        counter = ApproximateCounter()
        messages = [
            {"role": "user", "content": "Not important"},
            {"role": "user", "content": "Important", "_preserve": True},
            {"role": "assistant", "content": "Response"},
        ]

        result = strategy.truncate(messages, 50, counter)

        # Important message should be preserved
        assert any(m.get("_preserve") for m in result)

    def test_custom_mark_key(self) -> None:
        """Should use custom mark key."""
        strategy = SelectiveTruncationStrategy(
            preserve_roles=set(), preserve_marked=True, mark_key="keep"
        )
        counter = ApproximateCounter()
        messages = [
            {"role": "user", "content": "No keep"},
            {"role": "user", "content": "Has keep", "keep": True},
        ]

        result = strategy.truncate(messages, 50, counter)

        # Message with 'keep' should be preserved
        assert any(m.get("keep") for m in result)

    def test_adds_removable_from_recent(self) -> None:
        """Should add removable messages from most recent first."""
        strategy = SelectiveTruncationStrategy(
            preserve_roles={"system"}, preserve_marked=False
        )
        counter = ApproximateCounter()
        messages = [
            {"role": "system", "content": "Sys"},
            {"role": "user", "content": "Old"},
            {"role": "user", "content": "New"},
        ]

        result = strategy.truncate(messages, 100, counter)

        # Should preserve system and add recent messages
        assert len(result) >= 1


class TestCompositeStrategy:
    """Tests for CompositeStrategy."""

    def test_empty_strategies(self) -> None:
        """Should return input for empty strategy list."""
        strategy = CompositeStrategy([])
        counter = ApproximateCounter()
        messages = make_messages(5)

        result = strategy.truncate(messages, 1000, counter)
        assert len(result) == 5

    def test_chains_strategies(self) -> None:
        """Should apply strategies in order."""
        mock_strategy1 = MagicMock(spec=TruncationStrategy)
        # Return messages with real words that still exceed the 100 token budget
        over_budget_messages = [
            {"role": "user", "content": "word " * 50}  # ~65 tokens per message
            for _ in range(10)
        ]
        mock_strategy1.truncate.return_value = over_budget_messages

        mock_strategy2 = MagicMock(spec=TruncationStrategy)
        mock_strategy2.truncate.return_value = make_messages(5)

        strategy = CompositeStrategy([mock_strategy1, mock_strategy2])
        counter = ApproximateCounter()
        messages = make_messages(20)

        result = strategy.truncate(messages, 100, counter)

        mock_strategy1.truncate.assert_called_once()
        mock_strategy2.truncate.assert_called_once()
        assert len(result) == 5

    def test_stops_when_within_budget(self) -> None:
        """Should stop applying strategies when within budget."""
        # First strategy brings within budget
        strategy1 = SlidingWindowStrategy(window_size=3)

        mock_strategy2 = MagicMock(spec=TruncationStrategy)

        strategy = CompositeStrategy([strategy1, mock_strategy2])
        counter = ApproximateCounter()
        messages = make_messages(10)

        # Large budget so first strategy result is within budget
        result = strategy.truncate(messages, 100000, counter)

        # Second strategy should not be called
        mock_strategy2.truncate.assert_not_called()
        assert len(result) == 3

    def test_real_composite(self) -> None:
        """Test with real strategies."""
        strategy = CompositeStrategy(
            [
                SmartTruncationStrategy(preserve_first=2, preserve_last=3),
                TokenBudgetStrategy(),
            ]
        )
        counter = ApproximateCounter()
        messages = make_messages(100, content_size=50)

        result = strategy.truncate(messages, 500, counter)

        # Should be within budget
        tokens = counter.count_messages(result)
        assert tokens <= 500


class TestStrategyIntegration:
    """Integration tests for strategies."""

    def test_strategies_preserve_message_order(self) -> None:
        """Strategies should preserve relative message order."""
        strategies: list[TruncationStrategy] = [
            SlidingWindowStrategy(window_size=5),
            TokenBudgetStrategy(),
            SmartTruncationStrategy(preserve_first=1, preserve_last=2),
        ]

        counter = ApproximateCounter()

        for strategy in strategies:
            messages = [{"role": "user", "content": str(i)} for i in range(10)]
            result = strategy.truncate(messages, 10000, counter)

            # Extract content as integers (excluding system markers)
            contents = []
            for m in result:
                try:
                    contents.append(int(m["content"]))
                except ValueError:
                    pass  # Skip markers

            # Verify order is preserved
            for i in range(len(contents) - 1):
                assert contents[i] < contents[i + 1]
