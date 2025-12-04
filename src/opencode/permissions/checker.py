"""Permission checker for tool execution."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from opencode.permissions.models import (
    PermissionLevel,
    PermissionResult,
    PermissionRule,
)
from opencode.permissions.rules import RuleSet

if TYPE_CHECKING:
    from pathlib import Path


class PermissionChecker:
    """
    Checks permissions for tool execution.

    Evaluates rules from multiple sources in order:
    1. Session rules (temporary, highest priority)
    2. Project rules (from .opencode/permissions.json)
    3. Global rules (from user config)
    4. Default permission

    Example:
        ```python
        checker = PermissionChecker()
        result = checker.check("bash", {"command": "ls -la"})

        if result.allowed:
            # Execute immediately
            pass
        elif result.needs_confirmation:
            # Ask user
            pass
        else:  # result.denied
            # Block execution
            pass
        ```
    """

    def __init__(
        self,
        global_rules: RuleSet | None = None,
        project_rules: RuleSet | None = None,
    ) -> None:
        """
        Initialize permission checker.

        Args:
            global_rules: Rules from user configuration
            project_rules: Rules from project configuration
        """
        self.global_rules = global_rules or RuleSet()
        self.project_rules = project_rules
        self.session_rules = RuleSet()

    def check(self, tool_name: str, arguments: dict[str, Any]) -> PermissionResult:
        """
        Check permission for a tool execution.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            PermissionResult with determined permission level
        """
        # Check session rules first (highest priority)
        session_result = self.session_rules.evaluate(tool_name, arguments)
        if session_result.rule is not None:
            return session_result

        # Check project rules
        if self.project_rules:
            project_result = self.project_rules.evaluate(tool_name, arguments)
            if project_result.rule is not None:
                return project_result

        # Check global rules
        global_result = self.global_rules.evaluate(tool_name, arguments)
        if global_result.rule is not None:
            return global_result

        # Use global default
        return PermissionResult(
            level=self.global_rules.default,
            rule=None,
            reason=f"Using global default: {self.global_rules.default.value}",
        )

    def add_session_rule(self, rule: PermissionRule) -> None:
        """
        Add a temporary session rule.

        Session rules take highest priority and are cleared
        when the session ends.
        """
        # Remove existing rule with same pattern if any
        self.session_rules.remove_rule(rule.pattern)
        self.session_rules.add_rule(rule)

    def remove_session_rule(self, pattern: str) -> bool:
        """Remove a session rule by pattern."""
        return self.session_rules.remove_rule(pattern)

    def clear_session_rules(self) -> None:
        """Clear all session rules."""
        self.session_rules = RuleSet()

    def get_session_rules(self) -> list[PermissionRule]:
        """Get all session rules."""
        return list(self.session_rules.rules)

    def allow_always(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> None:
        """
        Create session rule to always allow this tool/arguments.

        Args:
            tool_name: Tool to allow
            arguments: Optional specific arguments to allow
        """
        pattern = f"tool:{tool_name}"

        # If arguments specified, make more specific pattern
        if arguments:
            # Create pattern for first argument (most common case)
            for key, value in arguments.items():
                pattern += f",arg:{key}:{value}"
                break  # Just use first argument

        self.add_session_rule(
            PermissionRule(
                pattern=pattern,
                permission=PermissionLevel.ALLOW,
                description=f"Session allow: {pattern}",
                priority=100,  # High priority for session rules
            )
        )

    def deny_always(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> None:
        """
        Create session rule to always deny this tool/arguments.

        Args:
            tool_name: Tool to deny
            arguments: Optional specific arguments to deny
        """
        pattern = f"tool:{tool_name}"

        if arguments:
            for key, value in arguments.items():
                pattern += f",arg:{key}:{value}"
                break

        self.add_session_rule(
            PermissionRule(
                pattern=pattern,
                permission=PermissionLevel.DENY,
                description=f"Session deny: {pattern}",
                priority=100,
            )
        )

    @classmethod
    def from_config(cls, project_root: Path | None = None) -> PermissionChecker:
        """
        Create permission checker from configuration.

        Args:
            project_root: Optional project root path for project rules

        Returns:
            Configured PermissionChecker
        """
        from opencode.permissions.config import PermissionConfig

        global_rules = PermissionConfig.load_global()
        project_rules = PermissionConfig.load_project(project_root)

        return cls(global_rules=global_rules, project_rules=project_rules)


class ToolPermissionError(Exception):
    """
    Raised when permission is denied for a tool execution.

    Note: Named ToolPermissionError to avoid shadowing the builtin
    PermissionError exception. Using the same name as the builtin would
    cause subtle bugs when code expects to catch OSError/PermissionError
    from file operations but accidentally catches this instead.
    """

    def __init__(
        self,
        result: PermissionResult,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> None:
        """
        Initialize permission error.

        Args:
            result: The permission check result
            tool_name: Name of the denied tool
            arguments: Tool arguments that were denied
        """
        self.result = result
        self.tool_name = tool_name
        self.arguments = arguments
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the error message."""
        return (
            f"Permission denied for tool '{self.tool_name}': {self.result.reason}"
        )
