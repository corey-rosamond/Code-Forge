"""Tests for Result type."""

from __future__ import annotations

import pytest

from opencode.utils.result import Result


class TestResultOk:
    """Tests for successful Result creation."""

    def test_create_ok_result(self) -> None:
        """Result.ok should create successful result."""
        result = Result.ok("success value")
        assert result.success is True
        assert result.value == "success value"
        assert result.error is None

    def test_ok_result_with_different_types(self) -> None:
        """Result.ok should work with various types."""
        int_result = Result.ok(42)
        assert int_result.value == 42

        list_result = Result.ok([1, 2, 3])
        assert list_result.value == [1, 2, 3]

        dict_result = Result.ok({"key": "value"})
        assert dict_result.value == {"key": "value"}

    def test_ok_result_is_ok(self) -> None:
        """Result.ok should have is_ok() return True."""
        result = Result.ok("test")
        assert result.is_ok() is True
        assert result.is_err() is False


class TestResultFail:
    """Tests for failed Result creation."""

    def test_create_fail_result(self) -> None:
        """Result.fail should create failed result."""
        result: Result[str] = Result.fail("something went wrong")
        assert result.success is False
        assert result.value is None
        assert result.error == "something went wrong"

    def test_fail_result_is_err(self) -> None:
        """Result.fail should have is_err() return True."""
        result: Result[str] = Result.fail("error")
        assert result.is_err() is True
        assert result.is_ok() is False


class TestResultUnwrap:
    """Tests for Result.unwrap method."""

    def test_unwrap_ok_result(self) -> None:
        """unwrap should return value for successful result."""
        result = Result.ok(42)
        assert result.unwrap() == 42

    def test_unwrap_fail_result_raises(self) -> None:
        """unwrap should raise ValueError for failed result."""
        result: Result[int] = Result.fail("failed")
        with pytest.raises(ValueError) as exc_info:
            result.unwrap()
        assert "failed" in str(exc_info.value)

    def test_unwrap_ok_result_with_none_value_raises(self) -> None:
        """unwrap should raise if success=True but value is None."""
        result: Result[str] = Result(success=True, value=None)
        with pytest.raises(ValueError) as exc_info:
            result.unwrap()
        assert "None" in str(exc_info.value)


class TestResultUnwrapOr:
    """Tests for Result.unwrap_or method."""

    def test_unwrap_or_ok_result(self) -> None:
        """unwrap_or should return value for successful result."""
        result = Result.ok("actual")
        assert result.unwrap_or("default") == "actual"

    def test_unwrap_or_fail_result(self) -> None:
        """unwrap_or should return default for failed result."""
        result: Result[str] = Result.fail("error")
        assert result.unwrap_or("default") == "default"

    def test_unwrap_or_with_none_value(self) -> None:
        """unwrap_or should return default if value is None."""
        result: Result[str] = Result(success=True, value=None)
        assert result.unwrap_or("default") == "default"


class TestResultMap:
    """Tests for Result.map method."""

    def test_map_ok_result(self) -> None:
        """map should apply function to successful result."""
        result = Result.ok(5)
        mapped = result.map(lambda x: x * 2)
        assert mapped.success is True
        assert mapped.value == 10

    def test_map_fail_result(self) -> None:
        """map should propagate error for failed result."""
        result: Result[int] = Result.fail("original error")
        mapped = result.map(lambda x: x * 2)
        assert mapped.success is False
        assert mapped.error == "original error"

    def test_map_with_exception(self) -> None:
        """map should catch exceptions and return failed result."""
        result = Result.ok(5)

        def bad_func(x: int) -> int:
            raise ValueError("computation failed")

        mapped = result.map(bad_func)
        assert mapped.success is False
        assert "computation failed" in str(mapped.error)

    def test_map_type_transformation(self) -> None:
        """map should handle type transformations."""
        result = Result.ok(42)
        mapped = result.map(str)
        assert mapped.value == "42"


class TestResultChaining:
    """Tests for chaining Result operations."""

    def test_chain_multiple_maps(self) -> None:
        """Multiple map calls should chain correctly."""
        result = Result.ok(2)
        final = result.map(lambda x: x + 3).map(lambda x: x * 2)
        assert final.value == 10

    def test_chain_stops_at_error(self) -> None:
        """Chained maps should stop propagating at first error."""

        def fail_if_five(x: int) -> int:
            if x == 5:
                raise ValueError("got five")
            return x + 1

        result = Result.ok(4)
        final = result.map(fail_if_five).map(fail_if_five).map(fail_if_five)
        assert final.success is False
        assert "got five" in str(final.error)
