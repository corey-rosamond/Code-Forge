"""
Agent result handling.

Provides structured result types for agent execution outcomes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class AgentResult:
    """Result from agent execution.

    Attributes:
        success: Whether execution succeeded.
        output: Human-readable output text.
        data: Structured data (varies by agent type).
        error: Error message if failed.
        tokens_used: Tokens consumed.
        time_seconds: Execution time.
        tool_calls: Number of tool invocations.
        metadata: Additional result metadata.
        timestamp: When result was created.
    """

    success: bool
    output: str
    data: Any = None
    error: str | None = None
    tokens_used: int = 0
    time_seconds: float = 0.0
    tool_calls: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def ok(
        cls,
        output: str,
        data: Any = None,
        **kwargs: Any,
    ) -> AgentResult:
        """Create successful result.

        Args:
            output: Human-readable output.
            data: Structured data.
            **kwargs: Additional fields.

        Returns:
            Successful AgentResult.
        """
        return cls(success=True, output=output, data=data, **kwargs)

    @classmethod
    def fail(
        cls,
        error: str,
        output: str = "",
        **kwargs: Any,
    ) -> AgentResult:
        """Create failure result.

        Args:
            error: Error message.
            output: Partial output (if any).
            **kwargs: Additional fields.

        Returns:
            Failed AgentResult.
        """
        return cls(success=False, output=output, error=error, **kwargs)

    @classmethod
    def cancelled(cls, output: str = "") -> AgentResult:
        """Create cancelled result.

        Args:
            output: Partial output (if any).

        Returns:
            Cancelled AgentResult.
        """
        return cls(
            success=False,
            output=output,
            error="Agent execution was cancelled",
        )

    @classmethod
    def timeout(cls, output: str = "") -> AgentResult:
        """Create timeout result.

        Args:
            output: Partial output (if any).

        Returns:
            Timed out AgentResult.
        """
        return cls(
            success=False,
            output=output,
            error="Agent execution timed out",
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "success": self.success,
            "output": self.output,
            "data": self._serialize_data(self.data),
            "error": self.error,
            "tokens_used": self.tokens_used,
            "time_seconds": self.time_seconds,
            "tool_calls": self.tool_calls,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    def _serialize_data(self, data: Any) -> Any:
        """Serialize data for JSON compatibility.

        Args:
            data: Data to serialize.

        Returns:
            JSON-serializable data.
        """
        if data is None:
            return None
        if isinstance(data, (str, int, float, bool)):
            return data
        if isinstance(data, (list, tuple)):
            return [self._serialize_data(item) for item in data]
        if isinstance(data, dict):
            return {str(k): self._serialize_data(v) for k, v in data.items()}
        # Convert unknown types to string
        return str(data)

    def to_json(self) -> str:
        """Serialize to JSON string.

        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentResult:
        """Deserialize from dictionary.

        Args:
            data: Dictionary to deserialize.

        Returns:
            AgentResult instance.
        """
        timestamp_str = data.get("timestamp")
        timestamp = (
            datetime.fromisoformat(timestamp_str)
            if timestamp_str
            else datetime.now()
        )

        return cls(
            success=data["success"],
            output=data["output"],
            data=data.get("data"),
            error=data.get("error"),
            tokens_used=data.get("tokens_used", 0),
            time_seconds=data.get("time_seconds", 0.0),
            tool_calls=data.get("tool_calls", 0),
            metadata=data.get("metadata", {}),
            timestamp=timestamp,
        )


@dataclass
class AggregatedResult:
    """Aggregated results from multiple agents.

    Used when running parallel agents and combining results.

    Attributes:
        results: List of individual agent results.
        total_tokens: Sum of tokens used.
        total_time: Sum of execution times.
        total_tool_calls: Sum of tool calls.
        success_count: Number of successful results.
        failure_count: Number of failed results.
    """

    results: list[AgentResult]
    total_tokens: int = 0
    total_time: float = 0.0
    total_tool_calls: int = 0
    success_count: int = 0
    failure_count: int = 0

    def __post_init__(self) -> None:
        """Calculate totals from results."""
        self.total_tokens = 0
        self.total_time = 0.0
        self.total_tool_calls = 0
        self.success_count = 0
        self.failure_count = 0

        for result in self.results:
            self.total_tokens += result.tokens_used
            self.total_time += result.time_seconds
            self.total_tool_calls += result.tool_calls
            if result.success:
                self.success_count += 1
            else:
                self.failure_count += 1

    @property
    def all_succeeded(self) -> bool:
        """Check if all agents succeeded.

        Returns:
            True if all results are successful.
        """
        return self.failure_count == 0 and self.success_count > 0

    @property
    def any_succeeded(self) -> bool:
        """Check if any agent succeeded.

        Returns:
            True if at least one result is successful.
        """
        return self.success_count > 0

    def get_successful(self) -> list[AgentResult]:
        """Get only successful results.

        Returns:
            List of successful AgentResults.
        """
        return [r for r in self.results if r.success]

    def get_failed(self) -> list[AgentResult]:
        """Get only failed results.

        Returns:
            List of failed AgentResults.
        """
        return [r for r in self.results if not r.success]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "results": [r.to_dict() for r in self.results],
            "total_tokens": self.total_tokens,
            "total_time": self.total_time,
            "total_tool_calls": self.total_tool_calls,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
        }

    def to_json(self) -> str:
        """Serialize to JSON string.

        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(), indent=2)
