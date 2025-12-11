"""Context management commands."""

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


class ContextCompactCommand(Command):
    """Compact context via summarization."""

    name = "compact"
    description = "Compact context via summarization"
    usage = "/context compact"

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Compact context."""
        if context.context_manager is None:
            return CommandResult.fail("Context manager not available")

        try:
            stats_before = context.context_manager.get_stats()
            # Use threshold of 0.0 to always compact
            await context.context_manager.compact_if_needed(threshold=0.0)
            stats_after = context.context_manager.get_stats()

            tokens_saved = stats_before.get("token_count", 0) - stats_after.get(
                "token_count", 0
            )
            if tokens_saved > 0:
                lines = [
                    "Context compacted.",
                    f"Before: {stats_before.get('token_count', 0)} tokens",
                    f"After: {stats_after.get('token_count', 0)} tokens",
                    f"Savings: {tokens_saved} tokens",
                ]
            else:
                lines = ["Context already compact. No changes made."]

            return CommandResult.ok("\n".join(lines))
        except Exception as e:
            return CommandResult.fail(f"Compaction failed: {e}")


class ContextResetCommand(Command):
    """Reset context to empty state."""

    name = "reset"
    description = "Clear all context"
    usage = "/context reset"

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Reset context."""
        if context.context_manager is None:
            return CommandResult.fail("Context manager not available")

        context.context_manager.reset()
        return CommandResult.ok("Context cleared.\nMessages: 0\nTokens: 0")


class ContextModeCommand(Command):
    """Set truncation mode."""

    name = "mode"
    description = "Set truncation mode"
    usage = "/context mode <mode>"
    arguments = [
        CommandArgument(
            name="mode",
            description="Truncation mode (sliding_window, token_budget, smart, summarize)",
            required=True,
        ),
    ]

    VALID_MODES = ["sliding_window", "token_budget", "smart", "summarize"]

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Set mode."""
        if context.context_manager is None:
            return CommandResult.fail("Context manager not available")

        mode = parsed.get_arg(0)
        if not mode:
            return CommandResult.fail("Mode required")

        if mode not in self.VALID_MODES:
            valid_modes = ", ".join(self.VALID_MODES)
            return CommandResult.fail(
                f'Invalid mode: "{mode}". Valid options: {valid_modes}'
            )

        try:
            from code_forge.context.manager import TruncationMode, get_strategy

            # Convert string to TruncationMode enum
            mode_enum = TruncationMode(mode)
            context.context_manager.mode = mode_enum
            context.context_manager.strategy = get_strategy(mode_enum)
            return CommandResult.ok(f"Truncation mode set to: {mode}")
        except ValueError:
            valid_modes = ", ".join(self.VALID_MODES)
            return CommandResult.fail(f'Invalid mode: "{mode}". Valid: {valid_modes}')
        except Exception as e:
            return CommandResult.fail(f"Failed to set mode: {e}")


class ContextCommand(SubcommandHandler):
    """Context management."""

    name = "context"
    aliases = ["ctx", "c"]
    description = "Context management"
    usage = "/context [subcommand]"
    category = CommandCategory.CONTEXT
    subcommands = {
        "compact": ContextCompactCommand(),
        "reset": ContextResetCommand(),
        "mode": ContextModeCommand(),
    }

    async def execute_default(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Show context status."""
        if context.context_manager is None:
            return CommandResult.fail("Context manager not available")

        try:
            stats = context.context_manager.get_stats()

            lines = [
                "Context Status:",
                f"  Model: {stats.get('model', 'unknown')}",
                f"  Mode: {stats.get('mode', 'unknown')}",
                f"  Messages: {stats.get('message_count', 0)}",
            ]

            token_count = stats.get("token_count", 0)
            max_tokens = stats.get("max_tokens", 0)
            if max_tokens > 0:
                usage_pct = (token_count / max_tokens) * 100
                available = max_tokens - token_count
                lines.append(
                    f"  Token Usage: {token_count:,} / {max_tokens:,} ({usage_pct:.1f}%)"
                )
                lines.append(f"  Available: {available:,} tokens")
            else:
                lines.append(f"  Tokens: {token_count:,}")

            if "system_tokens" in stats:
                lines.append(f"  System Prompt: {stats['system_tokens']:,} tokens")

            if "tools_tokens" in stats:
                lines.append(f"  Tools: {stats['tools_tokens']:,} tokens")

            return CommandResult.ok("\n".join(lines))
        except Exception as e:
            return CommandResult.fail(f"Failed to get context stats: {e}")


def get_commands() -> list[Command]:
    """Get all context commands."""
    return [ContextCommand()]
