"""Unit tests for callback handlers."""

from uuid import uuid4

import pytest
from langchain_core.outputs import LLMResult, Generation

from code_forge.langchain.callbacks import (
    CompositeCallback,
    LoggingCallback,
    CodeForgeCallbackHandler,
    StreamingCallback,
    TokenTrackingCallback,
)


class TestCodeForgeCallbackHandler:
    """Tests for base callback handler."""

    def test_name_default(self) -> None:
        """Test default name."""
        handler = CodeForgeCallbackHandler()
        assert handler.name == "forge"

    def test_raise_error_default(self) -> None:
        """Test default raise_error is False."""
        handler = CodeForgeCallbackHandler()
        assert handler.raise_error is False

    def test_safe_call_catches_errors(self) -> None:
        """Test that _safe_call catches errors when raise_error=False."""
        handler = CodeForgeCallbackHandler(raise_error=False)

        def failing_func() -> None:
            raise ValueError("Test error")

        # Should not raise
        handler._safe_call(failing_func)

    def test_safe_call_raises_errors(self) -> None:
        """Test that _safe_call raises errors when raise_error=True."""
        handler = CodeForgeCallbackHandler(raise_error=True)

        def failing_func() -> None:
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            handler._safe_call(failing_func)


class TestTokenTrackingCallback:
    """Tests for token tracking callback."""

    def test_initial_state(self) -> None:
        """Test initial counter values are zero."""
        tracker = TokenTrackingCallback()

        assert tracker.total_prompt_tokens == 0
        assert tracker.total_completion_tokens == 0
        assert tracker.call_count == 0

    def test_on_llm_end_records_usage(self) -> None:
        """Test that on_llm_end records token usage."""
        tracker = TokenTrackingCallback()

        response = LLMResult(
            generations=[[Generation(text="Hello")]],
            llm_output={"usage": {"prompt_tokens": 100, "completion_tokens": 50}},
        )

        tracker.on_llm_end(response, run_id=uuid4())

        assert tracker.total_prompt_tokens == 100
        assert tracker.total_completion_tokens == 50
        assert tracker.call_count == 1

    def test_accumulates_usage(self) -> None:
        """Test that usage is accumulated across calls."""
        tracker = TokenTrackingCallback()

        response1 = LLMResult(
            generations=[[Generation(text="Hello")]],
            llm_output={"usage": {"prompt_tokens": 100, "completion_tokens": 50}},
        )
        response2 = LLMResult(
            generations=[[Generation(text="World")]],
            llm_output={"usage": {"prompt_tokens": 50, "completion_tokens": 25}},
        )

        tracker.on_llm_end(response1, run_id=uuid4())
        tracker.on_llm_end(response2, run_id=uuid4())

        assert tracker.total_prompt_tokens == 150
        assert tracker.total_completion_tokens == 75
        assert tracker.call_count == 2

    def test_get_usage(self) -> None:
        """Test get_usage returns TokenUsage object."""
        tracker = TokenTrackingCallback()
        tracker.total_prompt_tokens = 100
        tracker.total_completion_tokens = 50

        usage = tracker.get_usage()

        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150

    def test_reset(self) -> None:
        """Test reset clears all counters."""
        tracker = TokenTrackingCallback()
        tracker.total_prompt_tokens = 100
        tracker.total_completion_tokens = 50
        tracker.call_count = 5

        tracker.reset()

        assert tracker.total_prompt_tokens == 0
        assert tracker.total_completion_tokens == 0
        assert tracker.call_count == 0

    def test_handles_missing_usage(self) -> None:
        """Test handling response without usage info."""
        tracker = TokenTrackingCallback()

        response = LLMResult(
            generations=[[Generation(text="Hello")]],
            llm_output=None,
        )

        tracker.on_llm_end(response, run_id=uuid4())

        # Should not crash, counters stay at 0
        assert tracker.total_prompt_tokens == 0
        assert tracker.call_count == 1


class TestLoggingCallback:
    """Tests for logging callback."""

    def test_name_default(self) -> None:
        """Test default name."""
        logger = LoggingCallback()
        assert logger.name == "logger"

    def test_on_llm_start_records_time(self) -> None:
        """Test that on_llm_start records start time."""
        logger = LoggingCallback()
        run_id = uuid4()

        logger.on_llm_start(
            serialized={"kwargs": {"model": "test-model"}},
            prompts=["Hello"],
            run_id=run_id,
        )

        assert run_id in logger._start_times

    def test_on_llm_end_removes_time(self) -> None:
        """Test that on_llm_end removes start time."""
        logger = LoggingCallback()
        run_id = uuid4()

        logger._start_times[run_id] = 12345.0

        response = LLMResult(
            generations=[[Generation(text="Hello")]],
            llm_output={"usage": {"total_tokens": 100}},
        )

        logger.on_llm_end(response, run_id=run_id)

        assert run_id not in logger._start_times

    def test_on_llm_error_removes_time(self) -> None:
        """Test that on_llm_error removes start time."""
        logger = LoggingCallback()
        run_id = uuid4()

        logger._start_times[run_id] = 12345.0

        logger.on_llm_error(ValueError("Test"), run_id=run_id)

        assert run_id not in logger._start_times

    def test_on_tool_start_records_time(self) -> None:
        """Test that on_tool_start records start time."""
        logger = LoggingCallback()
        run_id = uuid4()

        logger.on_tool_start(
            serialized={"name": "read_file"},
            input_str="test input",
            run_id=run_id,
        )

        assert run_id in logger._start_times

    def test_on_tool_end_removes_time(self) -> None:
        """Test that on_tool_end removes start time."""
        logger = LoggingCallback()
        run_id = uuid4()

        logger._start_times[run_id] = 12345.0

        logger.on_tool_end(output="result", run_id=run_id)

        assert run_id not in logger._start_times


class TestStreamingCallback:
    """Tests for streaming callback."""

    def test_initial_buffer_empty(self) -> None:
        """Test buffer starts empty."""
        streamer = StreamingCallback()
        assert streamer.get_buffer() == ""

    def test_on_llm_new_token_accumulates(self) -> None:
        """Test that tokens are accumulated in buffer."""
        streamer = StreamingCallback()

        streamer.on_llm_new_token("Hello", run_id=uuid4())
        streamer.on_llm_new_token(" ", run_id=uuid4())
        streamer.on_llm_new_token("World", run_id=uuid4())

        assert streamer.get_buffer() == "Hello World"

    def test_on_token_callback(self) -> None:
        """Test that on_token callback is called."""
        tokens_received: list[str] = []

        def on_token(token: str) -> None:
            tokens_received.append(token)

        streamer = StreamingCallback(on_token=on_token)

        streamer.on_llm_new_token("Hello", run_id=uuid4())
        streamer.on_llm_new_token(" ", run_id=uuid4())
        streamer.on_llm_new_token("World", run_id=uuid4())

        assert tokens_received == ["Hello", " ", "World"]

    def test_on_complete_callback(self) -> None:
        """Test that on_complete callback is called with full buffer."""
        completed_text: list[str] = []

        def on_complete(text: str) -> None:
            completed_text.append(text)

        streamer = StreamingCallback(on_complete=on_complete)

        streamer.on_llm_new_token("Hello World", run_id=uuid4())

        response = LLMResult(generations=[[Generation(text="Hello World")]])
        streamer.on_llm_end(response, run_id=uuid4())

        assert completed_text == ["Hello World"]

    def test_on_llm_end_clears_buffer(self) -> None:
        """Test that on_llm_end clears the buffer."""
        streamer = StreamingCallback()

        streamer.on_llm_new_token("Hello", run_id=uuid4())
        response = LLMResult(generations=[[Generation(text="Hello")]])
        streamer.on_llm_end(response, run_id=uuid4())

        assert streamer.get_buffer() == ""

    def test_clear_buffer(self) -> None:
        """Test manual buffer clearing."""
        streamer = StreamingCallback()

        streamer.on_llm_new_token("Hello", run_id=uuid4())
        streamer.clear_buffer()

        assert streamer.get_buffer() == ""


class TestCompositeCallback:
    """Tests for composite callback."""

    def test_dispatches_to_all_callbacks(self) -> None:
        """Test that events are dispatched to all callbacks."""
        tracker = TokenTrackingCallback()
        streamer = StreamingCallback()

        composite = CompositeCallback(callbacks=[tracker, streamer])

        response = LLMResult(
            generations=[[Generation(text="Hello")]],
            llm_output={"usage": {"prompt_tokens": 50, "completion_tokens": 25}},
        )

        composite.on_llm_end(response, run_id=uuid4())

        # Both should have received the event
        assert tracker.call_count == 1

    def test_on_llm_start(self) -> None:
        """Test on_llm_start dispatch."""
        callbacks_called: list[str] = []

        class TestCallback(CodeForgeCallbackHandler):
            def on_llm_start(self, *args, **kwargs) -> None:
                callbacks_called.append(self.name)

        cb1 = TestCallback(name="cb1")
        cb2 = TestCallback(name="cb2")

        composite = CompositeCallback(callbacks=[cb1, cb2])
        composite.on_llm_start(
            serialized={},
            prompts=[],
            run_id=uuid4(),
        )

        assert callbacks_called == ["cb1", "cb2"]

    def test_on_tool_events(self) -> None:
        """Test tool event dispatch."""
        tool_starts: list[str] = []
        tool_ends: list[str] = []

        class TestCallback(CodeForgeCallbackHandler):
            def on_tool_start(self, *args, **kwargs) -> None:
                tool_starts.append(self.name)

            def on_tool_end(self, *args, **kwargs) -> None:
                tool_ends.append(self.name)

        cb1 = TestCallback(name="cb1")
        cb2 = TestCallback(name="cb2")

        composite = CompositeCallback(callbacks=[cb1, cb2])

        composite.on_tool_start(
            serialized={"name": "test"},
            input_str="",
            run_id=uuid4(),
        )
        composite.on_tool_end(output="result", run_id=uuid4())

        assert tool_starts == ["cb1", "cb2"]
        assert tool_ends == ["cb1", "cb2"]

    def test_handles_callbacks_without_methods(self) -> None:
        """Test that missing methods are handled gracefully."""

        class MinimalCallback:
            pass

        minimal = MinimalCallback()
        composite = CompositeCallback(callbacks=[minimal])

        # Should not raise even though minimal has no methods
        composite.on_llm_start(serialized={}, prompts=[], run_id=uuid4())
        composite.on_llm_end(
            LLMResult(generations=[]),
            run_id=uuid4(),
        )

    def test_on_llm_error_dispatch(self) -> None:
        """Test on_llm_error is dispatched to all callbacks."""
        errors_received: list[str] = []

        class ErrorCallback(CodeForgeCallbackHandler):
            def on_llm_error(self, error, *args, **kwargs) -> None:
                errors_received.append(str(error))

        cb1 = ErrorCallback(name="cb1")
        cb2 = ErrorCallback(name="cb2")

        composite = CompositeCallback(callbacks=[cb1, cb2])
        composite.on_llm_error(ValueError("Test error"), run_id=uuid4())

        assert len(errors_received) == 2
        assert all("Test error" in e for e in errors_received)

    def test_on_llm_new_token_dispatch(self) -> None:
        """Test on_llm_new_token is dispatched to all callbacks."""
        tokens_received: list[str] = []

        class TokenCallback(CodeForgeCallbackHandler):
            def on_llm_new_token(self, token, *args, **kwargs) -> None:
                tokens_received.append(token)

        cb1 = TokenCallback(name="cb1")
        cb2 = TokenCallback(name="cb2")

        composite = CompositeCallback(callbacks=[cb1, cb2])
        composite.on_llm_new_token("hello", run_id=uuid4())

        # Both callbacks should receive the token
        assert tokens_received == ["hello", "hello"]

    def test_on_tool_error_dispatch(self) -> None:
        """Test on_tool_error is dispatched to all callbacks."""
        errors_received: list[str] = []

        class ErrorCallback(CodeForgeCallbackHandler):
            def on_tool_error(self, error, *args, **kwargs) -> None:
                errors_received.append(str(error))

        cb1 = ErrorCallback(name="cb1")
        cb2 = ErrorCallback(name="cb2")

        composite = CompositeCallback(callbacks=[cb1, cb2])
        composite.on_tool_error(RuntimeError("Tool failed"), run_id=uuid4())

        assert len(errors_received) == 2


class TestLoggingCallbackEdgeCases:
    """Edge case tests for LoggingCallback."""

    def test_on_tool_error_removes_time(self) -> None:
        """Test that on_tool_error removes start time."""
        logger = LoggingCallback()
        run_id = uuid4()

        logger._start_times[run_id] = 12345.0

        logger.on_tool_error(ValueError("Error"), run_id=run_id)

        assert run_id not in logger._start_times

    def test_handles_missing_start_time(self) -> None:
        """Test graceful handling when start time is missing."""
        logger = LoggingCallback()
        run_id = uuid4()

        # No start time recorded - should not crash
        response = LLMResult(
            generations=[[Generation(text="Hello")]],
            llm_output={"usage": {"total_tokens": 100}},
        )

        # Should handle missing start time gracefully
        logger.on_llm_end(response, run_id=run_id)
        logger.on_tool_end(output="result", run_id=run_id)

    def test_handles_missing_llm_output(self) -> None:
        """Test handling of response without llm_output."""
        logger = LoggingCallback()
        run_id = uuid4()

        logger._start_times[run_id] = 12345.0

        response = LLMResult(
            generations=[[Generation(text="Hello")]],
            llm_output=None,
        )

        # Should not crash
        logger.on_llm_end(response, run_id=run_id)


class TestStreamingCallbackEdgeCases:
    """Edge case tests for StreamingCallback."""

    def test_no_callbacks_set(self) -> None:
        """Test behavior when no callbacks are set."""
        streamer = StreamingCallback()

        # Should not crash without callbacks
        streamer.on_llm_new_token("Hello", run_id=uuid4())
        assert streamer.get_buffer() == "Hello"

        response = LLMResult(generations=[[Generation(text="Hello")]])
        streamer.on_llm_end(response, run_id=uuid4())
        assert streamer.get_buffer() == ""

    def test_multiple_streams(self) -> None:
        """Test handling multiple sequential streams."""
        completed: list[str] = []

        def on_complete(text):
            completed.append(text)

        streamer = StreamingCallback(on_complete=on_complete)

        # First stream
        streamer.on_llm_new_token("Stream 1", run_id=uuid4())
        response = LLMResult(generations=[[Generation(text="Stream 1")]])
        streamer.on_llm_end(response, run_id=uuid4())

        # Second stream
        streamer.on_llm_new_token("Stream 2", run_id=uuid4())
        response = LLMResult(generations=[[Generation(text="Stream 2")]])
        streamer.on_llm_end(response, run_id=uuid4())

        assert completed == ["Stream 1", "Stream 2"]


class TestTokenTrackingCallbackEdgeCases:
    """Edge case tests for TokenTrackingCallback."""

    def test_handles_empty_usage(self) -> None:
        """Test handling of empty usage dict."""
        tracker = TokenTrackingCallback()

        response = LLMResult(
            generations=[[Generation(text="Hello")]],
            llm_output={"usage": {}},
        )

        tracker.on_llm_end(response, run_id=uuid4())

        # Should default to 0 for missing keys
        assert tracker.total_prompt_tokens == 0
        assert tracker.total_completion_tokens == 0
        assert tracker.call_count == 1

    def test_handles_partial_usage(self) -> None:
        """Test handling of partial usage data."""
        tracker = TokenTrackingCallback()

        response = LLMResult(
            generations=[[Generation(text="Hello")]],
            llm_output={"usage": {"prompt_tokens": 50}},  # No completion_tokens
        )

        tracker.on_llm_end(response, run_id=uuid4())

        assert tracker.total_prompt_tokens == 50
        assert tracker.total_completion_tokens == 0
