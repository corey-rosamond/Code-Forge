"""Model routing and variants for OpenRouter."""

from enum import Enum


class RouteVariant(str, Enum):
    """OpenRouter routing variants."""

    DEFAULT = ""
    NITRO = ":nitro"  # Fastest providers
    FLOOR = ":floor"  # Cheapest providers
    ONLINE = ":online"  # Web search enabled
    THINKING = ":thinking"  # Extended reasoning (Claude)


def apply_variant(model_id: str, variant: RouteVariant) -> str:
    """
    Apply routing variant to model ID.

    Args:
        model_id: Base model ID (e.g., "anthropic/claude-3-opus")
        variant: Routing variant to apply

    Returns:
        Model ID with variant suffix

    Example:
        apply_variant("anthropic/claude-3-opus", RouteVariant.NITRO)
        # Returns: "anthropic/claude-3-opus:nitro"
    """
    if variant == RouteVariant.DEFAULT or not variant.value:
        return model_id
    return f"{model_id}{variant.value}"


def parse_model_id(model_id: str) -> tuple[str, RouteVariant | None]:
    """
    Parse model ID to extract base model and variant.

    Args:
        model_id: Model ID potentially with variant

    Returns:
        Tuple of (base_model_id, variant or None)

    Example:
        parse_model_id("anthropic/claude-3-opus:nitro")
        # Returns: ("anthropic/claude-3-opus", RouteVariant.NITRO)
    """
    for variant in RouteVariant:
        if variant.value and model_id.endswith(variant.value):
            base = model_id[: -len(variant.value)]
            return base, variant
    return model_id, None


# Common model aliases
MODEL_ALIASES: dict[str, str] = {
    "claude-3-opus": "anthropic/claude-3-opus",
    "claude-3-sonnet": "anthropic/claude-3-sonnet",
    "claude-3-haiku": "anthropic/claude-3-haiku",
    "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
    "gpt-4": "openai/gpt-4",
    "gpt-4-turbo": "openai/gpt-4-turbo",
    "gpt-4o": "openai/gpt-4o",
    "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
    "gemini-pro": "google/gemini-pro",
    "gemini-ultra": "google/gemini-ultra",
    "llama-3-70b": "meta-llama/llama-3-70b-instruct",
    "mixtral-8x7b": "mistralai/mixtral-8x7b-instruct",
}


def resolve_model_alias(model_id: str) -> str:
    """
    Resolve model alias to full model ID.

    Args:
        model_id: Model ID or alias to resolve.

    Returns:
        Full model ID.

    Raises:
        ValueError: If model_id is empty or None.
    """
    if not model_id or not model_id.strip():
        raise ValueError("model_id cannot be empty or None")
    return MODEL_ALIASES.get(model_id, model_id)
