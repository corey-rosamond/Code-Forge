"""Unit tests for LLM routing utilities."""

import pytest

from opencode.llm.routing import (
    MODEL_ALIASES,
    RouteVariant,
    apply_variant,
    parse_model_id,
    resolve_model_alias,
)


class TestRouteVariant:
    """Tests for RouteVariant enum."""

    def test_default_value(self) -> None:
        assert RouteVariant.DEFAULT.value == ""

    def test_nitro_value(self) -> None:
        assert RouteVariant.NITRO.value == ":nitro"

    def test_floor_value(self) -> None:
        assert RouteVariant.FLOOR.value == ":floor"

    def test_online_value(self) -> None:
        assert RouteVariant.ONLINE.value == ":online"

    def test_thinking_value(self) -> None:
        assert RouteVariant.THINKING.value == ":thinking"


class TestApplyVariant:
    """Tests for apply_variant function."""

    def test_apply_nitro(self) -> None:
        result = apply_variant("anthropic/claude-3-opus", RouteVariant.NITRO)
        assert result == "anthropic/claude-3-opus:nitro"

    def test_apply_floor(self) -> None:
        result = apply_variant("openai/gpt-4", RouteVariant.FLOOR)
        assert result == "openai/gpt-4:floor"

    def test_apply_online(self) -> None:
        result = apply_variant("anthropic/claude-3-sonnet", RouteVariant.ONLINE)
        assert result == "anthropic/claude-3-sonnet:online"

    def test_apply_thinking(self) -> None:
        result = apply_variant("anthropic/claude-3-opus", RouteVariant.THINKING)
        assert result == "anthropic/claude-3-opus:thinking"

    def test_apply_default_unchanged(self) -> None:
        result = apply_variant("anthropic/claude-3-opus", RouteVariant.DEFAULT)
        assert result == "anthropic/claude-3-opus"


class TestParseModelId:
    """Tests for parse_model_id function."""

    def test_parse_nitro_variant(self) -> None:
        base, variant = parse_model_id("anthropic/claude-3-opus:nitro")
        assert base == "anthropic/claude-3-opus"
        assert variant == RouteVariant.NITRO

    def test_parse_floor_variant(self) -> None:
        base, variant = parse_model_id("openai/gpt-4:floor")
        assert base == "openai/gpt-4"
        assert variant == RouteVariant.FLOOR

    def test_parse_online_variant(self) -> None:
        base, variant = parse_model_id("anthropic/claude-3-sonnet:online")
        assert base == "anthropic/claude-3-sonnet"
        assert variant == RouteVariant.ONLINE

    def test_parse_thinking_variant(self) -> None:
        base, variant = parse_model_id("anthropic/claude-3-opus:thinking")
        assert base == "anthropic/claude-3-opus"
        assert variant == RouteVariant.THINKING

    def test_parse_no_variant(self) -> None:
        base, variant = parse_model_id("anthropic/claude-3-opus")
        assert base == "anthropic/claude-3-opus"
        assert variant is None

    def test_parse_unknown_suffix(self) -> None:
        base, variant = parse_model_id("anthropic/claude-3-opus:unknown")
        assert base == "anthropic/claude-3-opus:unknown"
        assert variant is None


class TestResolveModelAlias:
    """Tests for resolve_model_alias function."""

    def test_resolve_claude_3_opus(self) -> None:
        result = resolve_model_alias("claude-3-opus")
        assert result == "anthropic/claude-3-opus"

    def test_resolve_claude_3_sonnet(self) -> None:
        result = resolve_model_alias("claude-3-sonnet")
        assert result == "anthropic/claude-3-sonnet"

    def test_resolve_claude_3_haiku(self) -> None:
        result = resolve_model_alias("claude-3-haiku")
        assert result == "anthropic/claude-3-haiku"

    def test_resolve_gpt_4(self) -> None:
        result = resolve_model_alias("gpt-4")
        assert result == "openai/gpt-4"

    def test_resolve_gpt_4_turbo(self) -> None:
        result = resolve_model_alias("gpt-4-turbo")
        assert result == "openai/gpt-4-turbo"

    def test_resolve_gpt_4o(self) -> None:
        result = resolve_model_alias("gpt-4o")
        assert result == "openai/gpt-4o"

    def test_unknown_alias_passes_through(self) -> None:
        result = resolve_model_alias("custom/my-model")
        assert result == "custom/my-model"

    def test_full_model_id_passes_through(self) -> None:
        result = resolve_model_alias("anthropic/claude-3-opus")
        assert result == "anthropic/claude-3-opus"

    def test_empty_model_id_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            resolve_model_alias("")

    def test_whitespace_model_id_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            resolve_model_alias("   ")


class TestModelAliases:
    """Tests for MODEL_ALIASES dictionary."""

    def test_contains_common_aliases(self) -> None:
        assert "claude-3-opus" in MODEL_ALIASES
        assert "gpt-4" in MODEL_ALIASES
        assert "gemini-pro" in MODEL_ALIASES

    def test_all_values_have_provider_prefix(self) -> None:
        for alias, full_id in MODEL_ALIASES.items():
            assert "/" in full_id, f"Alias {alias} should map to provider/model format"
