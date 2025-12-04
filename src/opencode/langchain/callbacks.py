"""Callback handlers for LangChain integration."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

if TYPE_CHECKING:
    from opencode.llm.models import TokenUsage


@dataclass
class OpenCodeCallbackHandler(BaseCallbackHandler):
    """
    Base callback handler for OpenCode.

    Provides a foundation for custom callback handlers with
    common utility methods.
    """

    name: str = "opencode"
    raise_error: bool = False

    def _safe_call(self, func: Any, *args: Any, **kwargs: Any) -> None:
        """Safely call a function, handling errors."""
        try:
            func(*args, **kwargs)
        except Exception as e:
            if self.raise_error:
                raise
            logging.warning(f"Callback error in {func.__name__}: {e}")


@dataclass
class TokenTrackingCallback(OpenCodeCallbackHandler):
    """
    Tracks token usage across LLM calls.

    Aggregates prompt and completion tokens for monitoring
    costs and usage patterns.

    Example:
        ```python
        tracker = TokenTrackingCallback()
        llm = OpenRouterLLM(client=client, model="...")

        response = llm.invoke(messages, config={"callbacks": [tracker]})

        print(f"Tokens used: {tracker.get_usage().total_tokens}")
        ```
    """

    name: str = "token_tracker"
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    call_count: int = 0

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Record token usage from LLM response."""
        self.call_count += 1

        if response.llm_output:
            usage = response.llm_output.get("usage", {})
            self.total_prompt_tokens += usage.get("prompt_tokens", 0)
            self.total_completion_tokens += usage.get("completion_tokens", 0)

    def get_usage(self) -> TokenUsage:
        """
        Get accumulated token usage.

        Returns:
            TokenUsage dataclass with totals
        """
        from opencode.llm.models import TokenUsage

        return TokenUsage(
            prompt_tokens=self.total_prompt_tokens,
            completion_tokens=self.total_completion_tokens,
            total_tokens=self.total_prompt_tokens + self.total_completion_tokens,
        )

    def reset(self) -> None:
        """Reset all counters to zero."""
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.call_count = 0


@dataclass
class LoggingCallback(OpenCodeCallbackHandler):
    """
    Logs all LLM and tool events for debugging.

    Provides detailed logging of the agent execution flow
    including timing information.

    Example:
        ```python
        import logging
        logging.basicConfig(level=logging.INFO)

        logger = LoggingCallback()
        agent.run(input, callbacks=[logger])
        ```
    """

    name: str = "logger"
    logger: logging.Logger = field(
        default_factory=lambda: logging.getLogger("opencode.langchain")
    )
    log_level: int = logging.INFO
    _start_times: dict[UUID, float] = field(default_factory=dict)

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Log LLM call start."""
        self._start_times[run_id] = time.time()
        model = serialized.get("kwargs", {}).get("model", "unknown")
        self.logger.log(
            self.log_level,
            f"LLM start: model={model}, prompts={len(prompts)}",
        )

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Log LLM call completion."""
        duration = time.time() - self._start_times.pop(run_id, time.time())
        usage = response.llm_output.get("usage", {}) if response.llm_output else {}
        self.logger.log(
            self.log_level,
            f"LLM end: duration={duration:.2f}s, tokens={usage.get('total_tokens', 0)}",
        )

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Log LLM errors."""
        self._start_times.pop(run_id, None)
        self.logger.error(f"LLM error: {error}")

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Log tool execution start."""
        self._start_times[run_id] = time.time()
        name = serialized.get("name", "unknown")
        self.logger.log(
            self.log_level,
            f"Tool start: {name}",
        )

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Log tool execution completion."""
        duration = time.time() - self._start_times.pop(run_id, time.time())
        output_preview = output[:100] + "..." if len(output) > 100 else output
        self.logger.log(
            self.log_level,
            f"Tool end: duration={duration:.2f}s, output={output_preview}",
        )

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Log tool errors."""
        self._start_times.pop(run_id, None)
        self.logger.error(f"Tool error: {error}")


@dataclass
class StreamingCallback(OpenCodeCallbackHandler):
    """
    Handles streaming output for display.

    Collects streamed tokens and provides callbacks for
    real-time display updates.

    Example:
        ```python
        def on_token(token: str):
            print(token, end="", flush=True)

        streamer = StreamingCallback(on_token=on_token)
        llm.invoke(messages, config={"callbacks": [streamer]})
        ```
    """

    name: str = "streamer"
    on_token: Any = None  # Callable[[str], None]
    on_complete: Any = None  # Callable[[str], None]
    _buffer: str = ""

    def on_llm_new_token(
        self,
        token: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle new streamed token."""
        self._buffer += token
        if self.on_token:
            self.on_token(token)

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle stream completion."""
        if self.on_complete:
            self.on_complete(self._buffer)
        self._buffer = ""

    def get_buffer(self) -> str:
        """Get accumulated content."""
        return self._buffer

    def clear_buffer(self) -> None:
        """Clear the buffer."""
        self._buffer = ""


@dataclass
class CompositeCallback(OpenCodeCallbackHandler):
    """
    Combines multiple callbacks into one.

    Useful when you want to apply several callbacks
    without managing them separately.

    Example:
        ```python
        composite = CompositeCallback(callbacks=[
            TokenTrackingCallback(),
            LoggingCallback(),
            StreamingCallback(on_token=print),
        ])

        llm.invoke(messages, config={"callbacks": [composite]})
        ```
    """

    name: str = "composite"
    callbacks: list[BaseCallbackHandler] = field(default_factory=list)

    def on_llm_start(self, *args: Any, **kwargs: Any) -> None:
        """Dispatch to all callbacks."""
        for cb in self.callbacks:
            if hasattr(cb, "on_llm_start"):
                cb.on_llm_start(*args, **kwargs)

    def on_llm_end(self, *args: Any, **kwargs: Any) -> None:
        """Dispatch to all callbacks."""
        for cb in self.callbacks:
            if hasattr(cb, "on_llm_end"):
                cb.on_llm_end(*args, **kwargs)

    def on_llm_error(self, *args: Any, **kwargs: Any) -> None:
        """Dispatch to all callbacks."""
        for cb in self.callbacks:
            if hasattr(cb, "on_llm_error"):
                cb.on_llm_error(*args, **kwargs)

    def on_llm_new_token(self, *args: Any, **kwargs: Any) -> None:
        """Dispatch to all callbacks."""
        for cb in self.callbacks:
            if hasattr(cb, "on_llm_new_token"):
                cb.on_llm_new_token(*args, **kwargs)

    def on_tool_start(self, *args: Any, **kwargs: Any) -> None:
        """Dispatch to all callbacks."""
        for cb in self.callbacks:
            if hasattr(cb, "on_tool_start"):
                cb.on_tool_start(*args, **kwargs)

    def on_tool_end(self, *args: Any, **kwargs: Any) -> None:
        """Dispatch to all callbacks."""
        for cb in self.callbacks:
            if hasattr(cb, "on_tool_end"):
                cb.on_tool_end(*args, **kwargs)

    def on_tool_error(self, *args: Any, **kwargs: Any) -> None:
        """Dispatch to all callbacks."""
        for cb in self.callbacks:
            if hasattr(cb, "on_tool_error"):
                cb.on_tool_error(*args, **kwargs)
