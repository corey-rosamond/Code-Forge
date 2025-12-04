"""Result type for operations that can fail."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")
U = TypeVar("U")


class Result(BaseModel, Generic[T]):
    """Result type for operations that can fail.

    Provides explicit success/failure handling without exceptions
    for expected failure cases.

    Note: Using frozen=False to allow Pydantic v2 compatibility with generics.
    """

    model_config = {"frozen": False, "arbitrary_types_allowed": True}

    success: bool
    value: T | None = None
    error: str | None = None

    @classmethod
    def ok(cls, value: T) -> Result[T]:
        """Create successful result.

        Args:
            value: The success value.

        Returns:
            A Result with success=True and the given value.
        """
        return cls(success=True, value=value)

    @classmethod
    def fail(cls, error: str) -> Result[T]:
        """Create failed result.

        Args:
            error: The error message.

        Returns:
            A Result with success=False and the given error.
        """
        return cls(success=False, error=error)

    def unwrap(self) -> T:
        """Get value or raise if failed.

        Returns:
            The success value.

        Raises:
            ValueError: If the result is a failure or value is None.
        """
        if not self.success:
            raise ValueError(f"Result failed: {self.error}")
        if self.value is None:
            raise ValueError("Result succeeded but value is None")
        return self.value

    def unwrap_or(self, default: T) -> T:
        """Get value or return default if failed.

        Args:
            default: The default value to return on failure.

        Returns:
            The success value or the default.
        """
        if self.success and self.value is not None:
            return self.value
        return default

    def map(self, func: Callable[[T], U]) -> Result[U]:
        """Apply function to value if successful.

        Args:
            func: Function to apply to the value.

        Returns:
            A new Result with the transformed value, or the original error.
        """
        if self.success and self.value is not None:
            try:
                return Result[U].ok(func(self.value))
            except Exception as e:
                return Result[U].fail(str(e))
        return Result[U].fail(self.error or "No value")

    def is_ok(self) -> bool:
        """Check if result is successful.

        Returns:
            True if successful, False otherwise.
        """
        return self.success

    def is_err(self) -> bool:
        """Check if result is a failure.

        Returns:
            True if failed, False otherwise.
        """
        return not self.success
