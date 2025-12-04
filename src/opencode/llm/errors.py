"""LLM-specific error classes."""

from opencode.core.errors import OpenCodeError


class LLMError(OpenCodeError):
    """Base class for LLM errors."""

    pass


class AuthenticationError(LLMError):
    """API key is invalid or missing."""

    def __init__(self, message: str = "Invalid or missing API key") -> None:
        super().__init__(message)


class RateLimitError(LLMError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ModelNotFoundError(LLMError):
    """Requested model not found."""

    def __init__(self, model_id: str) -> None:
        super().__init__(f"Model not found: {model_id}")
        self.model_id = model_id


class ContextLengthError(LLMError):
    """Context length exceeded."""

    def __init__(
        self,
        message: str = "Context length exceeded",
        max_tokens: int | None = None,
        requested_tokens: int | None = None,
    ) -> None:
        super().__init__(message)
        self.max_tokens = max_tokens
        self.requested_tokens = requested_tokens


class ContentPolicyError(LLMError):
    """Content violates policy."""

    def __init__(self, message: str = "Content violates policy") -> None:
        super().__init__(message)


class ProviderError(LLMError):
    """Error from upstream provider."""

    def __init__(self, message: str, provider: str | None = None) -> None:
        super().__init__(message)
        self.provider = provider
