"""Configuration commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..base import (
    Command,
    CommandArgument,
    CommandCategory,
    CommandResult,
    SubcommandHandler,
)

if TYPE_CHECKING:
    from ..executor import CommandContext
    from ..parser import ParsedCommand


class ConfigGetCommand(Command):
    """Get a configuration value."""

    name = "get"
    description = "Get configuration value"
    usage = "/config get <key>"
    arguments = [
        CommandArgument(
            name="key",
            description="Configuration key to get",
            required=True,
        ),
    ]

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Get config value."""
        if context.config is None:
            return CommandResult.fail("Configuration not available")

        key = parsed.get_arg(0)
        if not key:
            return CommandResult.fail("Key required")

        # Try to get the config value
        try:
            value = getattr(context.config, key, None)
            if value is None:
                # Try nested access for llm.model, etc.
                parts = key.split(".")
                current: object = context.config
                for part in parts:
                    current = getattr(current, part, None)
                    if current is None:
                        return CommandResult.fail(f"Configuration key not found: {key}")
                value = current
            return CommandResult.ok(str(value))
        except AttributeError:
            return CommandResult.fail(f"Configuration key not found: {key}")


class ConfigSetCommand(Command):
    """Set a configuration value."""

    name = "set"
    description = "Set configuration value"
    usage = "/config set <key> <value>"
    arguments = [
        CommandArgument(
            name="key",
            description="Configuration key to set",
            required=True,
        ),
        CommandArgument(
            name="value",
            description="Value to set",
            required=True,
        ),
    ]

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Set config value."""
        if context.config is None:
            return CommandResult.fail("Configuration not available")

        key = parsed.get_arg(0)
        value = parsed.get_arg(1)

        if not key:
            return CommandResult.fail("Key required")
        if value is None:
            return CommandResult.fail("Value required")

        # Try to set the config value
        try:
            # Handle type conversion for common types
            current_value = getattr(context.config, key, None)
            if current_value is not None:
                if isinstance(current_value, bool):
                    value = value.lower() in ("true", "yes", "1")  # type: ignore[assignment]
                elif isinstance(current_value, int):
                    value = int(value)  # type: ignore[assignment]
                elif isinstance(current_value, float):
                    value = float(value)  # type: ignore[assignment]

            setattr(context.config, key, value)
            return CommandResult.ok(f"Configuration updated: {key} = {value}")
        except (AttributeError, ValueError) as e:
            return CommandResult.fail(f"Failed to set configuration: {e}")


class ConfigCommand(SubcommandHandler):
    """Configuration management."""

    name = "config"
    aliases = ["cfg"]
    description = "Configuration management"
    usage = "/config [subcommand]"
    category = CommandCategory.CONFIG
    subcommands = {
        "get": ConfigGetCommand(),
        "set": ConfigSetCommand(),
    }

    async def execute_default(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Show current configuration."""
        if context.config is None:
            return CommandResult.fail("Configuration not available")

        lines = ["Current Configuration:", ""]

        # Get relevant config fields
        config_fields = [
            ("model", "llm.model"),
            ("temperature", "llm.temperature"),
            ("max_tokens", "llm.max_tokens"),
        ]

        for display_name, attr_path in config_fields:
            try:
                parts = attr_path.split(".")
                current: object = context.config
                for part in parts:
                    current = getattr(current, part, None)
                    if current is None:
                        break
                if current is not None:
                    lines.append(f"  {display_name}: {current}")
            except AttributeError:
                pass

        # Add any direct attributes
        direct_attrs = ["debug", "auto_save", "auto_save_interval"]
        for attr in direct_attrs:
            value = getattr(context.config, attr, None)
            if value is not None:
                lines.append(f"  {attr}: {value}")

        if len(lines) == 2:  # Only header
            lines.append("  (no configuration values available)")

        return CommandResult.ok("\n".join(lines))


class ModelCommand(Command):
    """Show or set current model."""

    name = "model"
    description = "Show or set current model"
    usage = "/model [name]"
    category = CommandCategory.CONFIG
    arguments = [
        CommandArgument(
            name="name",
            description="Model name to switch to",
            required=False,
        ),
    ]

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Show or set model."""
        model_name = parsed.get_arg(0)

        if model_name:
            # Set new model
            if context.config is None:
                return CommandResult.fail("Configuration not available")

            try:
                # Try to set via llm config
                if hasattr(context.config, "llm") and context.config.llm:
                    context.config.llm.model = model_name
                else:
                    return CommandResult.fail("LLM configuration not available")

                # Update context limits if context manager is available
                if context.context_manager:
                    try:
                        # Update model directly on context manager
                        context.context_manager.model = model_name
                    except Exception:
                        pass  # Context manager may not support this

                return CommandResult.ok(f"Model changed to: {model_name}")
            except Exception as e:
                return CommandResult.fail(f"Failed to set model: {e}")
        else:
            # Show current model
            if context.config is None:
                return CommandResult.fail("Configuration not available")

            try:
                model = None
                if hasattr(context.config, "llm") and context.config.llm:
                    model = getattr(context.config.llm, "model", None)

                if model:
                    return CommandResult.ok(f"Current model: {model}")
                else:
                    return CommandResult.ok("No model configured")
            except Exception as e:
                return CommandResult.fail(f"Failed to get model: {e}")


def get_commands() -> list[Command]:
    """Get all config commands."""
    return [
        ConfigCommand(),
        ModelCommand(),
    ]
