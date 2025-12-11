"""Tests for command parser."""

from __future__ import annotations

import pytest

from code_forge.commands.parser import CommandParser, ParsedCommand


class TestParsedCommand:
    """Tests for ParsedCommand dataclass."""

    def test_basic_creation(self) -> None:
        """Test basic ParsedCommand creation."""
        cmd = ParsedCommand(name="help")
        assert cmd.name == "help"
        assert cmd.args == []
        assert cmd.kwargs == {}
        assert cmd.flags == set()
        assert cmd.raw == ""

    def test_has_args_empty(self) -> None:
        """Test has_args returns False when no args."""
        cmd = ParsedCommand(name="help")
        assert cmd.has_args is False

    def test_has_args_with_args(self) -> None:
        """Test has_args returns True when args present."""
        cmd = ParsedCommand(name="session", args=["list"])
        assert cmd.has_args is True

    def test_get_arg_valid_index(self) -> None:
        """Test get_arg with valid index."""
        cmd = ParsedCommand(name="session", args=["resume", "abc123"])
        assert cmd.get_arg(0) == "resume"
        assert cmd.get_arg(1) == "abc123"

    def test_get_arg_invalid_index(self) -> None:
        """Test get_arg with invalid index returns default."""
        cmd = ParsedCommand(name="session", args=["resume"])
        assert cmd.get_arg(5) is None
        assert cmd.get_arg(5, "default") == "default"

    def test_get_arg_negative_index(self) -> None:
        """Test get_arg with negative index returns default."""
        cmd = ParsedCommand(name="session", args=["resume"])
        assert cmd.get_arg(-1) is None

    def test_get_kwarg_present(self) -> None:
        """Test get_kwarg with present key."""
        cmd = ParsedCommand(name="session", kwargs={"limit": "10"})
        assert cmd.get_kwarg("limit") == "10"

    def test_get_kwarg_missing(self) -> None:
        """Test get_kwarg with missing key returns default."""
        cmd = ParsedCommand(name="session", kwargs={})
        assert cmd.get_kwarg("limit") is None
        assert cmd.get_kwarg("limit", "20") == "20"

    def test_has_flag_present(self) -> None:
        """Test has_flag with present flag."""
        cmd = ParsedCommand(name="debug", flags={"verbose", "v"})
        assert cmd.has_flag("verbose") is True
        assert cmd.has_flag("v") is True

    def test_has_flag_missing(self) -> None:
        """Test has_flag with missing flag."""
        cmd = ParsedCommand(name="debug", flags=set())
        assert cmd.has_flag("verbose") is False

    def test_subcommand_present(self) -> None:
        """Test subcommand property when present."""
        cmd = ParsedCommand(name="session", args=["list", "abc"])
        assert cmd.subcommand == "list"

    def test_subcommand_empty(self) -> None:
        """Test subcommand property when empty."""
        cmd = ParsedCommand(name="session", args=[])
        assert cmd.subcommand is None

    def test_rest_args(self) -> None:
        """Test rest_args property."""
        cmd = ParsedCommand(name="session", args=["list", "abc", "def"])
        assert cmd.rest_args == ["abc", "def"]

    def test_rest_args_empty(self) -> None:
        """Test rest_args when only one arg."""
        cmd = ParsedCommand(name="session", args=["list"])
        assert cmd.rest_args == []


class TestCommandParserIsCommand:
    """Tests for CommandParser.is_command method."""

    def test_is_command_valid(self) -> None:
        """Test valid command detection."""
        parser = CommandParser()
        assert parser.is_command("/help") is True
        assert parser.is_command("/session") is True
        assert parser.is_command("/Session") is True

    def test_is_command_with_args(self) -> None:
        """Test command with arguments."""
        parser = CommandParser()
        assert parser.is_command("/session list") is True
        assert parser.is_command("/session list --limit 10") is True

    def test_is_command_not_command(self) -> None:
        """Test non-command input."""
        parser = CommandParser()
        assert parser.is_command("hello") is False
        assert parser.is_command("hello world") is False

    def test_is_command_slash_alone(self) -> None:
        """Test slash alone is not a command."""
        parser = CommandParser()
        assert parser.is_command("/") is False

    def test_is_command_slash_number(self) -> None:
        """Test slash followed by number is not a command."""
        parser = CommandParser()
        assert parser.is_command("/123") is False
        assert parser.is_command("/1abc") is False

    def test_is_command_slash_special(self) -> None:
        """Test slash followed by special char is not a command."""
        parser = CommandParser()
        assert parser.is_command("/-test") is False
        assert parser.is_command("/@test") is False
        assert parser.is_command("/ test") is False

    def test_is_command_with_whitespace(self) -> None:
        """Test command with leading/trailing whitespace."""
        parser = CommandParser()
        assert parser.is_command("  /help  ") is True
        assert parser.is_command("\t/help\n") is True


class TestCommandParserParse:
    """Tests for CommandParser.parse method."""

    def test_parse_simple(self) -> None:
        """Test parsing simple command."""
        parser = CommandParser()
        result = parser.parse("/help")
        assert result.name == "help"
        assert result.args == []
        assert result.kwargs == {}
        assert result.flags == set()

    def test_parse_with_positional_args(self) -> None:
        """Test parsing command with positional arguments."""
        parser = CommandParser()
        result = parser.parse("/session resume abc123")
        assert result.name == "session"
        assert result.args == ["resume", "abc123"]

    def test_parse_with_kwarg_space(self) -> None:
        """Test parsing --key value syntax."""
        parser = CommandParser()
        result = parser.parse("/session list --limit 10")
        assert result.name == "session"
        assert result.args == ["list"]
        assert result.kwargs == {"limit": "10"}

    def test_parse_with_kwarg_equals(self) -> None:
        """Test parsing --key=value syntax."""
        parser = CommandParser()
        result = parser.parse("/session list --limit=10")
        assert result.name == "session"
        assert result.args == ["list"]
        assert result.kwargs == {"limit": "10"}

    def test_parse_with_flag(self) -> None:
        """Test parsing --flag without value."""
        parser = CommandParser()
        result = parser.parse("/debug --verbose")
        assert result.name == "debug"
        assert result.flags == {"verbose"}

    def test_parse_with_short_flag(self) -> None:
        """Test parsing -f short flag."""
        parser = CommandParser()
        result = parser.parse("/debug -v")
        assert result.name == "debug"
        assert result.flags == {"v"}

    def test_parse_quoted_string(self) -> None:
        """Test parsing quoted string argument."""
        parser = CommandParser()
        result = parser.parse('/session title "My New Session"')
        assert result.name == "session"
        assert "My New Session" in result.args

    def test_parse_single_quoted_string(self) -> None:
        """Test parsing single-quoted string argument."""
        parser = CommandParser()
        result = parser.parse("/session title 'My New Session'")
        assert result.name == "session"
        assert "My New Session" in result.args

    def test_parse_case_insensitive(self) -> None:
        """Test command name is case-insensitive."""
        parser = CommandParser()
        result = parser.parse("/HELP")
        assert result.name == "help"

        result = parser.parse("/Session")
        assert result.name == "session"

    def test_parse_complex_command(self) -> None:
        """Test parsing complex command with multiple arg types."""
        parser = CommandParser()
        result = parser.parse('/session new --title "Test" --verbose -v')
        assert result.name == "session"
        assert "new" in result.args
        assert result.kwargs == {"title": "Test"}
        assert "verbose" in result.flags
        assert "v" in result.flags

    def test_parse_invalid_not_command(self) -> None:
        """Test parsing non-command raises ValueError."""
        parser = CommandParser()
        with pytest.raises(ValueError, match="Not a valid command"):
            parser.parse("hello")

    def test_parse_invalid_empty(self) -> None:
        """Test parsing slash alone raises ValueError."""
        parser = CommandParser()
        with pytest.raises(ValueError):
            parser.parse("/")

    def test_parse_preserves_raw(self) -> None:
        """Test raw input is preserved."""
        parser = CommandParser()
        result = parser.parse("/session list")
        assert result.raw == "/session list"

    def test_parse_unbalanced_quotes_fallback(self) -> None:
        """Test parsing with unbalanced quotes falls back to simple split."""
        parser = CommandParser()
        result = parser.parse('/session title "incomplete')
        assert result.name == "session"
        # Should split by whitespace as fallback


class TestCommandParserSuggest:
    """Tests for CommandParser.suggest_command method."""

    def test_suggest_exact_match(self) -> None:
        """Test no suggestion for exact match."""
        parser = CommandParser()
        suggestion = parser.suggest_command("/help", ["help", "session", "exit"])
        assert suggestion is None

    def test_suggest_typo(self) -> None:
        """Test suggestion for typo."""
        parser = CommandParser()
        suggestion = parser.suggest_command("/sesion", ["help", "session", "exit"])
        assert suggestion == "session"

    def test_suggest_close_match(self) -> None:
        """Test suggestion for close match."""
        parser = CommandParser()
        suggestion = parser.suggest_command("/hlp", ["help", "session", "exit"])
        assert suggestion == "help"

    def test_suggest_no_close_match(self) -> None:
        """Test no suggestion for no close match."""
        parser = CommandParser()
        suggestion = parser.suggest_command("/xyz", ["help", "session", "exit"])
        assert suggestion is None

    def test_suggest_not_command(self) -> None:
        """Test no suggestion for non-command."""
        parser = CommandParser()
        suggestion = parser.suggest_command("hello", ["help", "session"])
        assert suggestion is None


class TestLevenshteinDistance:
    """Tests for Levenshtein distance calculation."""

    def test_similarity_identical(self) -> None:
        """Test similarity of identical strings."""
        parser = CommandParser()
        assert parser._similarity("help", "help") == 1.0

    def test_similarity_empty(self) -> None:
        """Test similarity with empty string."""
        parser = CommandParser()
        assert parser._similarity("", "help") == 0.0
        assert parser._similarity("help", "") == 0.0

    def test_similarity_different(self) -> None:
        """Test similarity of different strings."""
        parser = CommandParser()
        # "session" vs "sesion" - 1 deletion, should be high
        sim = parser._similarity("session", "sesion")
        assert sim > 0.8

    def test_levenshtein_identical(self) -> None:
        """Test distance of identical strings is 0."""
        parser = CommandParser()
        assert parser._levenshtein_distance("help", "help") == 0

    def test_levenshtein_one_off(self) -> None:
        """Test distance with one character difference."""
        parser = CommandParser()
        assert parser._levenshtein_distance("help", "helps") == 1
        assert parser._levenshtein_distance("help", "helq") == 1

    def test_levenshtein_completely_different(self) -> None:
        """Test distance of completely different strings."""
        parser = CommandParser()
        assert parser._levenshtein_distance("abc", "xyz") == 3
