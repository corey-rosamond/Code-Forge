"""Tests for command base classes."""

from __future__ import annotations

import pytest

from code_forge.commands.base import (
    ArgumentType,
    Command,
    CommandArgument,
    CommandCategory,
    CommandResult,
    SubcommandHandler,
)
from code_forge.commands.executor import CommandContext
from code_forge.commands.parser import ParsedCommand


class TestArgumentType:
    """Tests for ArgumentType enum."""

    def test_string_type(self) -> None:
        """Test STRING type value."""
        assert ArgumentType.STRING.value == "string"

    def test_integer_type(self) -> None:
        """Test INTEGER type value."""
        assert ArgumentType.INTEGER.value == "integer"

    def test_boolean_type(self) -> None:
        """Test BOOLEAN type value."""
        assert ArgumentType.BOOLEAN.value == "boolean"

    def test_choice_type(self) -> None:
        """Test CHOICE type value."""
        assert ArgumentType.CHOICE.value == "choice"

    def test_path_type(self) -> None:
        """Test PATH type value."""
        assert ArgumentType.PATH.value == "path"


class TestCommandArgument:
    """Tests for CommandArgument dataclass."""

    def test_basic_creation(self) -> None:
        """Test basic CommandArgument creation."""
        arg = CommandArgument(name="id", description="Session ID")
        assert arg.name == "id"
        assert arg.description == "Session ID"
        assert arg.required is True
        assert arg.default is None
        assert arg.type == ArgumentType.STRING
        assert arg.choices == []

    def test_optional_argument(self) -> None:
        """Test optional argument."""
        arg = CommandArgument(name="limit", required=False, default="10")
        assert arg.required is False
        assert arg.default == "10"

    def test_validate_required_missing(self) -> None:
        """Test validation fails for missing required."""
        arg = CommandArgument(name="id", required=True)
        valid, error = arg.validate(None)
        assert valid is False
        assert "Missing required argument" in error

    def test_validate_required_present(self) -> None:
        """Test validation passes for present required."""
        arg = CommandArgument(name="id", required=True)
        valid, error = arg.validate("abc123")
        assert valid is True
        assert error is None

    def test_validate_optional_missing(self) -> None:
        """Test validation passes for missing optional."""
        arg = CommandArgument(name="limit", required=False)
        valid, error = arg.validate(None)
        assert valid is True
        assert error is None

    def test_validate_integer_valid(self) -> None:
        """Test INTEGER validation with valid value."""
        arg = CommandArgument(name="limit", type=ArgumentType.INTEGER)
        valid, error = arg.validate("10")
        assert valid is True

    def test_validate_integer_invalid(self) -> None:
        """Test INTEGER validation with invalid value."""
        arg = CommandArgument(name="limit", type=ArgumentType.INTEGER)
        valid, error = arg.validate("abc")
        assert valid is False
        assert "must be an integer" in error

    def test_validate_boolean_valid(self) -> None:
        """Test BOOLEAN validation with valid values."""
        arg = CommandArgument(name="flag", type=ArgumentType.BOOLEAN)
        for val in ["true", "false", "yes", "no", "1", "0", "TRUE", "FALSE"]:
            valid, error = arg.validate(val)
            assert valid is True

    def test_validate_boolean_invalid(self) -> None:
        """Test BOOLEAN validation with invalid value."""
        arg = CommandArgument(name="flag", type=ArgumentType.BOOLEAN)
        valid, error = arg.validate("maybe")
        assert valid is False
        assert "must be a boolean" in error

    def test_validate_choice_valid(self) -> None:
        """Test CHOICE validation with valid value."""
        arg = CommandArgument(
            name="mode",
            type=ArgumentType.CHOICE,
            choices=["a", "b", "c"],
        )
        valid, error = arg.validate("b")
        assert valid is True

    def test_validate_choice_invalid(self) -> None:
        """Test CHOICE validation with invalid value."""
        arg = CommandArgument(
            name="mode",
            type=ArgumentType.CHOICE,
            choices=["a", "b", "c"],
        )
        valid, error = arg.validate("d")
        assert valid is False
        assert "must be one of" in error


class TestCommandResult:
    """Tests for CommandResult dataclass."""

    def test_basic_creation(self) -> None:
        """Test basic CommandResult creation."""
        result = CommandResult(success=True)
        assert result.success is True
        assert result.output == ""
        assert result.error is None
        assert result.data is None

    def test_ok_classmethod(self) -> None:
        """Test ok() class method."""
        result = CommandResult.ok("Success!")
        assert result.success is True
        assert result.output == "Success!"
        assert result.error is None

    def test_ok_with_data(self) -> None:
        """Test ok() with data."""
        result = CommandResult.ok("Done", data={"action": "exit"})
        assert result.success is True
        assert result.data == {"action": "exit"}

    def test_fail_classmethod(self) -> None:
        """Test fail() class method."""
        result = CommandResult.fail("Error!")
        assert result.success is False
        assert result.error == "Error!"

    def test_fail_with_output(self) -> None:
        """Test fail() with output."""
        result = CommandResult.fail("Error!", output="Some output")
        assert result.success is False
        assert result.error == "Error!"
        assert result.output == "Some output"


class TestCommandCategory:
    """Tests for CommandCategory enum."""

    def test_all_categories_exist(self) -> None:
        """Test all expected categories exist."""
        assert CommandCategory.GENERAL.value == "general"
        assert CommandCategory.SESSION.value == "session"
        assert CommandCategory.CONTEXT.value == "context"
        assert CommandCategory.CONTROL.value == "control"
        assert CommandCategory.CONFIG.value == "config"
        assert CommandCategory.DEBUG.value == "debug"


class TestCommand:
    """Tests for Command abstract base class."""

    class TestableCommand(Command):
        """Concrete command for testing."""

        name = "test"
        aliases = ["t"]
        description = "Test command"
        usage = "/test <arg>"
        category = CommandCategory.GENERAL
        arguments = [
            CommandArgument(name="arg", description="Test argument"),
        ]

        async def execute(
            self,
            parsed: ParsedCommand,
            context: CommandContext,
        ) -> CommandResult:
            return CommandResult.ok("Test executed")

    def test_command_attributes(self) -> None:
        """Test command has expected attributes."""
        cmd = self.TestableCommand()
        assert cmd.name == "test"
        assert cmd.aliases == ["t"]
        assert cmd.description == "Test command"
        assert cmd.usage == "/test <arg>"
        assert cmd.category == CommandCategory.GENERAL
        assert len(cmd.arguments) == 1

    def test_validate_required_present(self) -> None:
        """Test validation passes when required arg present."""
        cmd = self.TestableCommand()
        parsed = ParsedCommand(name="test", args=["value"])
        errors = cmd.validate(parsed)
        assert errors == []

    def test_validate_required_missing(self) -> None:
        """Test validation fails when required arg missing."""
        cmd = self.TestableCommand()
        parsed = ParsedCommand(name="test", args=[])
        errors = cmd.validate(parsed)
        assert len(errors) == 1
        assert "Missing required argument" in errors[0]

    def test_get_help(self) -> None:
        """Test help text generation."""
        cmd = self.TestableCommand()
        help_text = cmd.get_help()
        assert "/test" in help_text
        assert "Test command" in help_text
        assert "/test <arg>" in help_text
        assert "t" in help_text  # alias
        assert "arg" in help_text  # argument name

    @pytest.mark.asyncio
    async def test_execute(self) -> None:
        """Test command execution."""
        cmd = self.TestableCommand()
        parsed = ParsedCommand(name="test", args=["value"])
        context = CommandContext()
        result = await cmd.execute(parsed, context)
        assert result.success is True
        assert result.output == "Test executed"


class TestSubcommandHandler:
    """Tests for SubcommandHandler class."""

    class ListSubcommand(Command):
        name = "list"
        description = "List items"

        async def execute(
            self,
            parsed: ParsedCommand,
            context: CommandContext,
        ) -> CommandResult:
            return CommandResult.ok("Listed items")

    class NewSubcommand(Command):
        name = "new"
        description = "Create new"

        async def execute(
            self,
            parsed: ParsedCommand,
            context: CommandContext,
        ) -> CommandResult:
            return CommandResult.ok(f"Created: {parsed.get_arg(0, 'default')}")

    class TestableHandler(SubcommandHandler):
        name = "test"
        aliases = ["t"]
        description = "Test handler"
        category = CommandCategory.GENERAL
        subcommands = {}

        def __init__(self) -> None:
            self.subcommands = {
                "list": TestSubcommandHandler.ListSubcommand(),
                "new": TestSubcommandHandler.NewSubcommand(),
            }

    @pytest.mark.asyncio
    async def test_execute_subcommand(self) -> None:
        """Test executing a known subcommand."""
        handler = self.TestableHandler()
        parsed = ParsedCommand(name="test", args=["list"])
        context = CommandContext()
        result = await handler.execute(parsed, context)
        assert result.success is True
        assert result.output == "Listed items"

    @pytest.mark.asyncio
    async def test_execute_subcommand_with_args(self) -> None:
        """Test subcommand receives remaining args."""
        handler = self.TestableHandler()
        parsed = ParsedCommand(name="test", args=["new", "myitem"])
        context = CommandContext()
        result = await handler.execute(parsed, context)
        assert result.success is True
        assert "myitem" in result.output

    @pytest.mark.asyncio
    async def test_execute_unknown_subcommand(self) -> None:
        """Test executing unknown subcommand returns error."""
        handler = self.TestableHandler()
        parsed = ParsedCommand(name="test", args=["unknown"])
        context = CommandContext()
        result = await handler.execute(parsed, context)
        assert result.success is False
        assert "Unknown subcommand" in result.error

    @pytest.mark.asyncio
    async def test_execute_no_subcommand(self) -> None:
        """Test executing without subcommand calls default."""
        handler = self.TestableHandler()
        parsed = ParsedCommand(name="test", args=[])
        context = CommandContext()
        result = await handler.execute(parsed, context)
        # Default shows help
        assert result.success is True
        assert "Subcommands:" in result.output

    def test_get_help_includes_subcommands(self) -> None:
        """Test help includes subcommand listing."""
        handler = self.TestableHandler()
        help_text = handler.get_help()
        assert "Subcommands:" in help_text
        assert "/test list" in help_text
        assert "/test new" in help_text
        assert "List items" in help_text
        assert "Create new" in help_text
