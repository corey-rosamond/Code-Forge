"""Tests for agent result handling."""

import json
from datetime import datetime

import pytest

from opencode.agents.result import AgentResult, AggregatedResult


class TestAgentResult:
    """Tests for AgentResult dataclass."""

    def test_success_result(self) -> None:
        """Test creating a success result."""
        result = AgentResult(
            success=True,
            output="Task completed",
        )
        assert result.success is True
        assert result.output == "Task completed"
        assert result.error is None

    def test_failure_result(self) -> None:
        """Test creating a failure result."""
        result = AgentResult(
            success=False,
            output="",
            error="Something went wrong",
        )
        assert result.success is False
        assert result.error == "Something went wrong"

    def test_default_values(self) -> None:
        """Test default values."""
        result = AgentResult(success=True, output="")
        assert result.data is None
        assert result.error is None
        assert result.tokens_used == 0
        assert result.time_seconds == 0.0
        assert result.tool_calls == 0
        assert result.metadata == {}
        assert isinstance(result.timestamp, datetime)

    def test_full_result(self) -> None:
        """Test result with all fields."""
        result = AgentResult(
            success=True,
            output="Found 5 files",
            data={"files": ["a.py", "b.py"]},
            tokens_used=1500,
            time_seconds=3.2,
            tool_calls=10,
            metadata={"agent_type": "explore"},
        )
        assert result.data["files"] == ["a.py", "b.py"]
        assert result.tokens_used == 1500
        assert result.time_seconds == 3.2
        assert result.tool_calls == 10
        assert result.metadata["agent_type"] == "explore"

    def test_ok_factory(self) -> None:
        """Test ok class method."""
        result = AgentResult.ok("Done", data={"count": 5})
        assert result.success is True
        assert result.output == "Done"
        assert result.data == {"count": 5}
        assert result.error is None

    def test_ok_with_kwargs(self) -> None:
        """Test ok with additional kwargs."""
        result = AgentResult.ok(
            "Done",
            tokens_used=100,
            time_seconds=1.5,
        )
        assert result.tokens_used == 100
        assert result.time_seconds == 1.5

    def test_fail_factory(self) -> None:
        """Test fail class method."""
        result = AgentResult.fail("Error occurred")
        assert result.success is False
        assert result.error == "Error occurred"
        assert result.output == ""

    def test_fail_with_output(self) -> None:
        """Test fail with partial output."""
        result = AgentResult.fail(
            "Timeout",
            output="Partial results here",
        )
        assert result.success is False
        assert result.error == "Timeout"
        assert result.output == "Partial results here"

    def test_cancelled_factory(self) -> None:
        """Test cancelled class method."""
        result = AgentResult.cancelled()
        assert result.success is False
        assert "cancelled" in result.error.lower()

    def test_cancelled_with_output(self) -> None:
        """Test cancelled with partial output."""
        result = AgentResult.cancelled(output="Partial work")
        assert result.output == "Partial work"

    def test_timeout_factory(self) -> None:
        """Test timeout class method."""
        result = AgentResult.timeout()
        assert result.success is False
        assert "timed out" in result.error.lower()

    def test_timeout_with_output(self) -> None:
        """Test timeout with partial output."""
        result = AgentResult.timeout(output="Work before timeout")
        assert result.output == "Work before timeout"

    def test_to_dict(self) -> None:
        """Test serialization to dict."""
        result = AgentResult.ok("Done", data={"key": "value"})
        d = result.to_dict()

        assert d["success"] is True
        assert d["output"] == "Done"
        assert d["data"] == {"key": "value"}
        assert d["error"] is None
        assert "timestamp" in d

    def test_to_dict_complex_data(self) -> None:
        """Test serialization handles complex data."""
        result = AgentResult.ok(
            "Done",
            data={
                "nested": {"list": [1, 2, 3]},
                "tuple": (1, 2),
            }
        )
        d = result.to_dict()
        assert d["data"]["nested"]["list"] == [1, 2, 3]
        assert d["data"]["tuple"] == [1, 2]  # Tuples become lists

    def test_to_dict_unknown_type(self) -> None:
        """Test serialization converts unknown types to string."""
        class CustomObj:
            def __str__(self) -> str:
                return "custom"

        result = AgentResult.ok("Done", data=CustomObj())
        d = result.to_dict()
        assert d["data"] == "custom"

    def test_to_json(self) -> None:
        """Test JSON serialization."""
        result = AgentResult.ok("Done")
        json_str = result.to_json()

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["success"] is True
        assert parsed["output"] == "Done"

    def test_from_dict(self) -> None:
        """Test deserialization from dict."""
        d = {
            "success": True,
            "output": "Task done",
            "data": {"count": 5},
            "error": None,
            "tokens_used": 1000,
            "time_seconds": 2.5,
            "tool_calls": 8,
            "metadata": {"key": "value"},
            "timestamp": "2024-01-15T10:30:00",
        }

        result = AgentResult.from_dict(d)

        assert result.success is True
        assert result.output == "Task done"
        assert result.data == {"count": 5}
        assert result.tokens_used == 1000
        assert result.timestamp.year == 2024

    def test_from_dict_minimal(self) -> None:
        """Test deserialization with minimal data."""
        d = {
            "success": False,
            "output": "",
            "error": "Failed",
        }

        result = AgentResult.from_dict(d)

        assert result.success is False
        assert result.error == "Failed"
        assert result.tokens_used == 0

    def test_from_dict_no_timestamp(self) -> None:
        """Test deserialization without timestamp."""
        d = {
            "success": True,
            "output": "Done",
        }

        result = AgentResult.from_dict(d)
        assert isinstance(result.timestamp, datetime)


class TestAggregatedResult:
    """Tests for AggregatedResult dataclass."""

    def test_empty_results(self) -> None:
        """Test with empty results list."""
        agg = AggregatedResult(results=[])
        assert agg.total_tokens == 0
        assert agg.total_time == 0.0
        assert agg.total_tool_calls == 0
        assert agg.success_count == 0
        assert agg.failure_count == 0

    def test_single_success(self) -> None:
        """Test with single successful result."""
        result = AgentResult.ok(
            "Done",
            tokens_used=1000,
            time_seconds=5.0,
            tool_calls=10,
        )
        agg = AggregatedResult(results=[result])

        assert agg.total_tokens == 1000
        assert agg.total_time == 5.0
        assert agg.total_tool_calls == 10
        assert agg.success_count == 1
        assert agg.failure_count == 0

    def test_single_failure(self) -> None:
        """Test with single failed result."""
        result = AgentResult.fail(
            "Error",
            tokens_used=500,
            time_seconds=2.0,
            tool_calls=5,
        )
        agg = AggregatedResult(results=[result])

        assert agg.success_count == 0
        assert agg.failure_count == 1

    def test_mixed_results(self) -> None:
        """Test with mixed success/failure results."""
        results = [
            AgentResult.ok("Done 1", tokens_used=1000, time_seconds=5.0, tool_calls=10),
            AgentResult.fail("Error", tokens_used=500, time_seconds=2.0, tool_calls=5),
            AgentResult.ok("Done 2", tokens_used=1500, time_seconds=3.0, tool_calls=8),
        ]
        agg = AggregatedResult(results=results)

        assert agg.total_tokens == 3000
        assert agg.total_time == 10.0
        assert agg.total_tool_calls == 23
        assert agg.success_count == 2
        assert agg.failure_count == 1

    def test_all_succeeded_true(self) -> None:
        """Test all_succeeded returns True when all succeed."""
        results = [
            AgentResult.ok("Done 1"),
            AgentResult.ok("Done 2"),
        ]
        agg = AggregatedResult(results=results)
        assert agg.all_succeeded is True

    def test_all_succeeded_false(self) -> None:
        """Test all_succeeded returns False with failures."""
        results = [
            AgentResult.ok("Done"),
            AgentResult.fail("Error"),
        ]
        agg = AggregatedResult(results=results)
        assert agg.all_succeeded is False

    def test_all_succeeded_empty(self) -> None:
        """Test all_succeeded is False for empty results."""
        agg = AggregatedResult(results=[])
        assert agg.all_succeeded is False

    def test_any_succeeded_true(self) -> None:
        """Test any_succeeded returns True with some successes."""
        results = [
            AgentResult.fail("Error"),
            AgentResult.ok("Done"),
            AgentResult.fail("Error 2"),
        ]
        agg = AggregatedResult(results=results)
        assert agg.any_succeeded is True

    def test_any_succeeded_false(self) -> None:
        """Test any_succeeded returns False with all failures."""
        results = [
            AgentResult.fail("Error 1"),
            AgentResult.fail("Error 2"),
        ]
        agg = AggregatedResult(results=results)
        assert agg.any_succeeded is False

    def test_get_successful(self) -> None:
        """Test filtering successful results."""
        results = [
            AgentResult.ok("Done 1"),
            AgentResult.fail("Error"),
            AgentResult.ok("Done 2"),
        ]
        agg = AggregatedResult(results=results)

        successful = agg.get_successful()
        assert len(successful) == 2
        assert all(r.success for r in successful)

    def test_get_failed(self) -> None:
        """Test filtering failed results."""
        results = [
            AgentResult.ok("Done"),
            AgentResult.fail("Error 1"),
            AgentResult.fail("Error 2"),
        ]
        agg = AggregatedResult(results=results)

        failed = agg.get_failed()
        assert len(failed) == 2
        assert all(not r.success for r in failed)

    def test_to_dict(self) -> None:
        """Test serialization to dict."""
        results = [
            AgentResult.ok("Done", tokens_used=100),
            AgentResult.fail("Error", tokens_used=50),
        ]
        agg = AggregatedResult(results=results)
        d = agg.to_dict()

        assert len(d["results"]) == 2
        assert d["total_tokens"] == 150
        assert d["success_count"] == 1
        assert d["failure_count"] == 1

    def test_to_json(self) -> None:
        """Test JSON serialization."""
        results = [AgentResult.ok("Done")]
        agg = AggregatedResult(results=results)
        json_str = agg.to_json()

        parsed = json.loads(json_str)
        assert parsed["success_count"] == 1
