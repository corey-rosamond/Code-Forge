"""Unit tests for context compaction."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from opencode.context.compaction import ContextCompactor, ToolResultCompactor
from opencode.context.tokens import ApproximateCounter


class TestContextCompactor:
    """Tests for ContextCompactor."""

    @pytest.fixture
    def mock_llm(self) -> AsyncMock:
        """Create a mock LLM."""
        llm = AsyncMock()
        response = MagicMock()
        response.content = "This is a summary of the conversation."
        llm.ainvoke.return_value = response
        return llm

    @pytest.fixture
    def compactor(self, mock_llm: AsyncMock) -> ContextCompactor:
        """Create a compactor with mock LLM."""
        return ContextCompactor(
            llm=mock_llm,
            max_summary_tokens=500,
            min_messages_to_summarize=3,
        )

    @pytest.mark.asyncio
    async def test_compact_empty_messages(
        self, compactor: ContextCompactor
    ) -> None:
        """Should return empty list for empty input."""
        counter = ApproximateCounter()
        result = await compactor.compact([], 1000, counter)
        assert result == []

    @pytest.mark.asyncio
    async def test_compact_too_few_messages(
        self, compactor: ContextCompactor, mock_llm: AsyncMock
    ) -> None:
        """Should return original if too few messages."""
        counter = ApproximateCounter()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]

        result = await compactor.compact(messages, 1000, counter, preserve_last=1)

        # Should return original (not enough to summarize)
        assert result == messages
        mock_llm.ainvoke.assert_not_called()

    @pytest.mark.asyncio
    async def test_compact_preserves_recent(
        self, compactor: ContextCompactor
    ) -> None:
        """Should preserve recent messages."""
        counter = ApproximateCounter()
        messages = [
            {"role": "user", "content": f"Message {i}"} for i in range(20)
        ]

        result = await compactor.compact(messages, 100000, counter, preserve_last=5)

        # Should preserve last 5
        preserved_content = [m["content"] for m in result if "Message" in m["content"]]
        for i in range(15, 20):
            assert f"Message {i}" in preserved_content

    @pytest.mark.asyncio
    async def test_compact_creates_summary_message(
        self, compactor: ContextCompactor
    ) -> None:
        """Should create summary message."""
        counter = ApproximateCounter()
        messages = [
            {"role": "user", "content": f"Message {i}"} for i in range(20)
        ]

        result = await compactor.compact(messages, 100000, counter, preserve_last=5)

        # Should have a summary message
        summary_msgs = [m for m in result if "[Previous conversation summary]" in m.get("content", "")]
        assert len(summary_msgs) == 1

    @pytest.mark.asyncio
    async def test_compact_preserves_system_messages(
        self, compactor: ContextCompactor
    ) -> None:
        """Should preserve system messages."""
        counter = ApproximateCounter()
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": "You are helpful"},
        ] + [
            {"role": "user", "content": f"Message {i}"} for i in range(20)
        ]

        result = await compactor.compact(messages, 100000, counter, preserve_last=3)

        # System message should be preserved
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "You are helpful"

    @pytest.mark.asyncio
    async def test_compact_handles_llm_failure(
        self, mock_llm: AsyncMock
    ) -> None:
        """Should return original on LLM failure."""
        mock_llm.ainvoke.side_effect = Exception("LLM error")
        compactor = ContextCompactor(llm=mock_llm)
        counter = ApproximateCounter()

        messages = [
            {"role": "user", "content": f"Message {i}"} for i in range(20)
        ]

        result = await compactor.compact(messages, 1000, counter, preserve_last=5)

        # Should return original on error
        assert result == messages

    @pytest.mark.asyncio
    async def test_compact_returns_original_if_summary_too_large(
        self, mock_llm: AsyncMock
    ) -> None:
        """Should return original if summary exceeds budget."""
        # Make LLM return very long summary
        response = MagicMock()
        response.content = "x" * 10000
        mock_llm.ainvoke.return_value = response

        compactor = ContextCompactor(llm=mock_llm)
        counter = ApproximateCounter()

        messages = [
            {"role": "user", "content": f"Message {i}"} for i in range(20)
        ]

        # Very small budget
        result = await compactor.compact(messages, 10, counter, preserve_last=5)

        # Should return original
        assert result == messages

    @pytest.mark.asyncio
    async def test_summarize_messages(
        self, compactor: ContextCompactor, mock_llm: AsyncMock
    ) -> None:
        """Should call LLM with formatted messages."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        summary = await compactor.summarize_messages(messages)

        assert summary == "This is a summary of the conversation."
        mock_llm.ainvoke.assert_called_once()

        # Check prompt was formatted
        call_args = mock_llm.ainvoke.call_args[0][0]
        assert len(call_args) == 1
        assert "user: Hello" in call_args[0]["content"]
        assert "assistant: Hi there!" in call_args[0]["content"]

    def test_format_for_summary(self, compactor: ContextCompactor) -> None:
        """Should format messages as role: content."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]

        formatted = compactor._format_for_summary(messages)

        assert "user: Hello" in formatted
        assert "assistant: Hi!" in formatted

    def test_format_for_summary_truncates_long_content(
        self, compactor: ContextCompactor
    ) -> None:
        """Should truncate content over 500 chars."""
        messages = [
            {"role": "user", "content": "x" * 600},
        ]

        formatted = compactor._format_for_summary(messages)

        assert len(formatted) < 600
        assert "..." in formatted


class TestToolResultCompactor:
    """Tests for ToolResultCompactor."""

    def test_compact_result_empty(self) -> None:
        """Should return empty string for empty input."""
        compactor = ToolResultCompactor()
        counter = ApproximateCounter()

        result = compactor.compact_result("", counter)
        assert result == ""

    def test_compact_result_small_unchanged(self) -> None:
        """Should not change results under limit."""
        compactor = ToolResultCompactor(max_result_tokens=1000)
        counter = ApproximateCounter()

        text = "Small result"
        result = compactor.compact_result(text, counter)

        assert result == text

    def test_compact_result_truncates_large(self) -> None:
        """Should truncate large results."""
        compactor = ToolResultCompactor(max_result_tokens=100)
        counter = ApproximateCounter()

        # Use real words so approximate counter gives realistic counts
        text = "word " * 1000  # 1000 words ~= 1300 tokens
        result = compactor.compact_result(text, counter)

        # Should be truncated
        assert len(result) < len(text)
        assert counter.count(result) <= 150  # Some overhead

    def test_compact_result_adds_truncation_message(self) -> None:
        """Should add truncation message."""
        compactor = ToolResultCompactor(max_result_tokens=50)
        counter = ApproximateCounter()

        # Use real words so approximate counter gives realistic counts
        text = "word " * 500  # ~650 tokens
        result = compactor.compact_result(text, counter)

        assert "truncated" in result.lower()

    def test_compact_result_custom_truncation_message(self) -> None:
        """Should use custom truncation message."""
        compactor = ToolResultCompactor(
            max_result_tokens=50,
            truncation_message="\n[CUSTOM: {removed} tokens cut]",
        )
        counter = ApproximateCounter()

        # Use real words so approximate counter gives realistic counts
        text = "word " * 500
        result = compactor.compact_result(text, counter)

        assert "CUSTOM:" in result
        assert "tokens cut" in result

    def test_compact_message_non_tool_unchanged(self) -> None:
        """Should not change non-tool messages."""
        compactor = ToolResultCompactor()
        counter = ApproximateCounter()

        message: dict[str, Any] = {"role": "user", "content": "x" * 5000}
        result = compactor.compact_message(message, counter)

        assert result == message

    def test_compact_message_tool_small_unchanged(self) -> None:
        """Should not change small tool messages."""
        compactor = ToolResultCompactor(max_result_tokens=1000)
        counter = ApproximateCounter()

        message: dict[str, Any] = {"role": "tool", "content": "Small output"}
        result = compactor.compact_message(message, counter)

        assert result == message

    def test_compact_message_tool_large_truncated(self) -> None:
        """Should truncate large tool messages."""
        compactor = ToolResultCompactor(max_result_tokens=50)
        counter = ApproximateCounter()

        # Use real words so approximate counter gives realistic counts
        message: dict[str, Any] = {"role": "tool", "content": "word " * 500}
        result = compactor.compact_message(message, counter)

        assert len(result["content"]) < len(message["content"])
        assert "truncated" in result["content"].lower()

    def test_compact_message_preserves_other_fields(self) -> None:
        """Should preserve other message fields."""
        compactor = ToolResultCompactor(max_result_tokens=50)
        counter = ApproximateCounter()

        # Use real words so approximate counter gives realistic counts
        message: dict[str, Any] = {
            "role": "tool",
            "content": "word " * 500,
            "tool_call_id": "call_123",
            "name": "read_file",
        }
        result = compactor.compact_message(message, counter)

        assert result["tool_call_id"] == "call_123"
        assert result["name"] == "read_file"

    def test_finds_good_break_point(self) -> None:
        """Should truncate at word/line boundary when possible."""
        compactor = ToolResultCompactor(max_result_tokens=50)
        counter = ApproximateCounter()

        # Text with natural break points
        text = "word1 word2 word3 word4 word5 " * 100  # Many words
        result = compactor.compact_result(text, counter)

        # Result should be truncated
        assert len(result) < len(text)
        # Should have truncation message
        assert "truncated" in result.lower()
