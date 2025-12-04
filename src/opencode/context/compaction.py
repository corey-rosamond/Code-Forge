"""Context compaction via summarization."""

import logging
from typing import Any, Protocol

from .tokens import TokenCounter

logger = logging.getLogger(__name__)


SUMMARY_PROMPT = """Summarize the following conversation concisely.
Preserve key decisions, code changes, and important context.
The summary will be used to continue the conversation.

Conversation:
{conversation}

Provide a brief summary (max {max_tokens} tokens):"""


class LLMProtocol(Protocol):
    """Protocol for LLM clients that support async invocation."""

    async def ainvoke(
        self, messages: list[dict[str, Any]]
    ) -> Any:  # Returns object with .content
        """Invoke the LLM asynchronously."""
        ...


class ContextCompactor:
    """Compacts context via LLM summarization.

    Uses an LLM to summarize older conversation history,
    replacing many messages with a concise summary.
    """

    def __init__(
        self,
        llm: LLMProtocol,
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
        system_messages: list[dict[str, Any]] = []
        other_messages: list[dict[str, Any]] = []

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

            summary_message: dict[str, Any] = {
                "role": "system",
                "content": f"[Previous conversation summary]\n{summary}",
            }

            result = [*system_messages, summary_message, *to_preserve]

            # Verify we're within budget
            if counter.count_messages(result) <= target_tokens:
                logger.info(f"Compacted {len(to_summarize)} messages to summary")
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

        return str(response.content)

    def _format_for_summary(self, messages: list[dict[str, Any]]) -> str:
        """Format messages for summarization.

        Args:
            messages: Messages to format.

        Returns:
            Formatted conversation string.
        """
        lines: list[str] = []

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
