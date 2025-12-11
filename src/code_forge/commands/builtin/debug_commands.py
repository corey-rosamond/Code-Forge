"""Debug commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..base import Command, CommandArgument, CommandCategory, CommandResult

if TYPE_CHECKING:
    from ..executor import CommandContext
    from ..parser import ParsedCommand


class DebugCommand(Command):
    """Toggle debug mode."""

    name = "debug"
    aliases = ["dbg"]
    description = "Toggle debug mode"
    usage = "/debug"
    category = CommandCategory.DEBUG

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Toggle debug mode."""
        # Debug state is stored on the REPL instance if available
        if context.repl is None:
            return CommandResult.fail("REPL not available for debug mode")

        try:
            current = getattr(context.repl, "debug", False)
            new_value = not current
            context.repl.debug = new_value

            if new_value:
                return CommandResult.ok(
                    "Debug mode enabled.\nYou will see detailed execution information."
                )
            else:
                return CommandResult.ok("Debug mode disabled.")
        except Exception as e:
            return CommandResult.fail(f"Failed to toggle debug mode: {e}")


class TokensCommand(Command):
    """Show token usage."""

    name = "tokens"
    description = "Show token usage"
    usage = "/tokens"
    category = CommandCategory.DEBUG

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Show token usage."""
        lines = ["Token Usage (Current Session):", ""]

        # Get session token info if available
        if context.session_manager and context.session_manager.has_current:
            session = context.session_manager.current_session
            if session:
                lines.append(f"  Prompt Tokens: {session.total_prompt_tokens:,}")
                lines.append(f"  Completion Tokens: {session.total_completion_tokens:,}")
                total = session.total_prompt_tokens + session.total_completion_tokens
                lines.append(f"  Total Tokens: {total:,}")
                lines.append("")

        # Get context budget info if available
        if context.context_manager:
            try:
                stats = context.context_manager.get_stats()
                lines.append("Context Budget:")

                if "system_tokens" in stats:
                    lines.append(f"  System Prompt: {stats['system_tokens']:,} tokens")
                if "tools_tokens" in stats:
                    lines.append(f"  Tools: {stats['tools_tokens']:,} tokens")
                if "token_count" in stats:
                    lines.append(f"  Conversation: {stats['token_count']:,} tokens")
                if "max_tokens" in stats:
                    available = stats["max_tokens"] - stats.get("token_count", 0)
                    lines.append(f"  Available: {available:,} tokens")
            except Exception:
                pass

        if len(lines) == 2:  # Only header
            lines.append("  No token usage data available.")

        return CommandResult.ok("\n".join(lines))


class HistoryCommand(Command):
    """Show message history."""

    name = "history"
    description = "Show message history"
    usage = "/history [--limit N]"
    category = CommandCategory.DEBUG
    arguments = [
        CommandArgument(
            name="limit",
            description="Number of messages to show",
            required=False,
        ),
    ]

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """Show history."""
        if context.session_manager is None or not context.session_manager.has_current:
            return CommandResult.fail("No active session")

        session = context.session_manager.current_session
        if session is None:
            return CommandResult.fail("No active session")

        limit_str = parsed.get_kwarg("limit", "20")
        if limit_str is None:
            limit_str = "20"
        try:
            limit = int(limit_str)
        except ValueError:
            return CommandResult.fail(f"Invalid limit: {limit_str}")

        messages = session.messages
        total = len(messages)

        if total == 0:
            return CommandResult.ok("No messages in history.")

        # Show last N messages
        display_messages = messages[-limit:] if limit < total else messages
        start_idx = max(0, total - limit)

        lines = [f"Message History ({total} messages):", ""]

        for i, msg in enumerate(display_messages):
            idx = start_idx + i + 1
            role = msg.role
            content = msg.content

            # Truncate long content
            if len(content) > 100:
                content = content[:97] + "..."

            # Replace newlines for display
            content = content.replace("\n", " ")

            lines.append(f"[{idx}] {role}:")
            lines.append(f"    {content}")

            # Show tool calls if present
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_names = [
                    tc.get("name", "unknown") if isinstance(tc, dict) else str(tc)
                    for tc in msg.tool_calls
                ]
                lines.append(f"    [Tool calls: {', '.join(tool_names)}]")

            lines.append("")

        if total > limit:
            lines.append(f"... ({total - limit} earlier messages not shown)")

        return CommandResult.ok("\n".join(lines))


class ToolsCommand(Command):
    """List available tools."""

    name = "tools"
    description = "List available tools"
    usage = "/tools"
    category = CommandCategory.DEBUG

    async def execute(
        self,
        parsed: ParsedCommand,
        context: CommandContext,
    ) -> CommandResult:
        """List tools."""
        try:
            from code_forge.tools.registry import ToolRegistry

            registry = ToolRegistry()  # Singleton via __new__
            tools = list(registry.list_all())

            if not tools:
                return CommandResult.ok("No tools available.")

            lines = [f"Available Tools ({len(tools)}):", ""]

            # Group by category if possible
            categorized: dict[str, list[tuple[str, str]]] = {}

            for tool in tools:
                category = getattr(tool, "category", "Other")
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append((tool.name, tool.description))

            for category, tool_list in sorted(categorized.items()):
                lines.append(f"{category}:")
                for name, description in sorted(tool_list):
                    # Truncate long descriptions
                    if len(description) > 50:
                        description = description[:47] + "..."
                    lines.append(f"  {name:<15} {description}")
                lines.append("")

            return CommandResult.ok("\n".join(lines))
        except ImportError:
            return CommandResult.fail("Tool registry not available")
        except Exception as e:
            return CommandResult.fail(f"Failed to list tools: {e}")


def get_commands() -> list[Command]:
    """Get all debug commands."""
    return [
        DebugCommand(),
        TokensCommand(),
        HistoryCommand(),
        ToolsCommand(),
    ]
