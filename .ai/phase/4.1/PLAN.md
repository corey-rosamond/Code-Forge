# Phase 4.1: Permission System - Implementation Plan

**Phase:** 4.1
**Name:** Permission System
**Dependencies:** Phase 2.1 (Tool System Foundation)

---

## Implementation Order

1. Permission models (levels, categories)
2. Rule definition and pattern matching
3. Rule set and evaluation
4. Permission checker
5. User confirmation prompts
6. Configuration loading/saving
7. Integration with tool executor
8. Package exports and tests

---

## Step 1: Permission Models

Create `src/forge/permissions/models.py`:

```python
"""Permission data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PermissionLevel(str, Enum):
    """
    Permission levels in order of restrictiveness.

    ALLOW: Execute without user confirmation
    ASK: Require user confirmation before execution
    DENY: Block execution entirely
    """

    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"

    def __lt__(self, other: "PermissionLevel") -> bool:
        """Compare permission levels. ALLOW < ASK < DENY."""
        if not isinstance(other, PermissionLevel):
            return NotImplemented
        order = [PermissionLevel.ALLOW, PermissionLevel.ASK, PermissionLevel.DENY]
        return order.index(self) < order.index(other)

    def __le__(self, other: "PermissionLevel") -> bool:
        return self == other or self < other

    def __gt__(self, other: "PermissionLevel") -> bool:
        if not isinstance(other, PermissionLevel):
            return NotImplemented
        return not (self <= other)

    def __ge__(self, other: "PermissionLevel") -> bool:
        return self == other or self > other


class PermissionCategory(str, Enum):
    """Categories of operations for permission grouping."""

    READ = "read_operations"
    WRITE = "write_operations"
    EXECUTE = "execute_operations"
    NETWORK = "network_operations"
    DESTRUCTIVE = "destructive_operations"
    OTHER = "other_operations"


@dataclass
class PermissionResult:
    """
    Result of a permission check.

    Attributes:
        level: The determined permission level
        rule: The rule that matched (if any)
        reason: Human-readable explanation
    """

    level: PermissionLevel
    rule: "PermissionRule | None" = None
    reason: str = ""

    @property
    def allowed(self) -> bool:
        """Check if execution is allowed without confirmation."""
        return self.level == PermissionLevel.ALLOW

    @property
    def needs_confirmation(self) -> bool:
        """Check if user confirmation is required."""
        return self.level == PermissionLevel.ASK

    @property
    def denied(self) -> bool:
        """Check if execution is denied."""
        return self.level == PermissionLevel.DENY


@dataclass
class PermissionRule:
    """
    A single permission rule.

    Attributes:
        pattern: Pattern to match (e.g., "tool:bash", "arg:file_path:/etc/*")
        permission: Permission level to apply when matched
        description: Human-readable description
        enabled: Whether the rule is active
        priority: Manual priority override (higher = checked first)
    """

    pattern: str
    permission: PermissionLevel
    description: str = ""
    enabled: bool = True
    priority: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize rule to dictionary."""
        return {
            "pattern": self.pattern,
            "permission": self.permission.value,
            "description": self.description,
            "enabled": self.enabled,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PermissionRule":
        """Deserialize rule from dictionary."""
        return cls(
            pattern=data["pattern"],
            permission=PermissionLevel(data["permission"]),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
            priority=data.get("priority", 0),
        )


# Category mappings for tools
TOOL_CATEGORIES: dict[str, PermissionCategory] = {
    "read": PermissionCategory.READ,
    "glob": PermissionCategory.READ,
    "grep": PermissionCategory.READ,
    "write": PermissionCategory.WRITE,
    "edit": PermissionCategory.WRITE,
    "notebook_edit": PermissionCategory.WRITE,
    "bash": PermissionCategory.EXECUTE,
    "bash_output": PermissionCategory.READ,
    "kill_shell": PermissionCategory.EXECUTE,
    "web_fetch": PermissionCategory.NETWORK,
    "web_search": PermissionCategory.NETWORK,
}


def get_tool_category(tool_name: str) -> PermissionCategory:
    """Get the permission category for a tool."""
    return TOOL_CATEGORIES.get(tool_name, PermissionCategory.OTHER)
```

---

## Step 2: Pattern Matching

Create `src/forge/permissions/rules.py`:

```python
"""Permission rule definition and pattern matching."""

from __future__ import annotations

import fnmatch
import functools
import re
from dataclasses import dataclass, field
from typing import Any

from forge.permissions.models import (
    PermissionLevel,
    PermissionResult,
    PermissionRule,
    PermissionCategory,
    get_tool_category,
)


class PatternMatcher:
    """
    Matches tool/argument patterns against values.

    Pattern formats:
    - tool:name - Match tool by name
    - tool:name* - Match tool with glob
    - arg:name:pattern - Match argument value
    - category:name - Match tool category
    - Combined with comma: tool:bash,arg:command:*rm*

    Thread Safety:
    - Uses functools.lru_cache for compiled regex patterns
    - LRU eviction prevents unbounded memory growth
    """

    @staticmethod
    @functools.lru_cache(maxsize=256)
    def _compile_regex(pattern: str) -> re.Pattern | None:
        """Compile and cache a regex pattern.

        Returns None if pattern is invalid.
        """
        try:
            return re.compile(pattern)
        except re.error:
            return None

    @classmethod
    def match(cls, pattern: str, tool_name: str, arguments: dict[str, Any]) -> bool:
        """
        Check if a pattern matches the given tool and arguments.

        Args:
            pattern: The pattern to match
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            True if pattern matches
        """
        # Parse pattern into components
        components = cls.parse_pattern(pattern)

        # All components must match
        for comp_type, comp_name, comp_pattern in components:
            if comp_type == "tool":
                if not cls._match_value(comp_pattern, tool_name):
                    return False

            elif comp_type == "arg":
                arg_value = arguments.get(comp_name)
                if arg_value is None:
                    return False
                if not cls._match_value(comp_pattern, str(arg_value)):
                    return False

            elif comp_type == "category":
                tool_category = get_tool_category(tool_name)
                if tool_category.value != comp_pattern and tool_category.name.lower() != comp_pattern:
                    return False

        return True

    @classmethod
    def parse_pattern(cls, pattern: str) -> list[tuple[str, str, str]]:
        """
        Parse a pattern into components.

        Returns list of (type, name, pattern) tuples.
        - type: "tool", "arg", or "category"
        - name: argument name (for arg type) or empty
        - pattern: the pattern to match

        Examples:
        - "tool:bash" -> [("tool", "", "bash")]
        - "arg:command:*rm*" -> [("arg", "command", "*rm*")]
        - "tool:bash,arg:command:*" -> [("tool", "", "bash"), ("arg", "command", "*")]
        """
        components = []

        # Split on comma for combined patterns
        parts = pattern.split(",")

        for part in parts:
            part = part.strip()

            if part.startswith("tool:"):
                # tool:pattern
                components.append(("tool", "", part[5:]))

            elif part.startswith("arg:"):
                # arg:name:pattern
                rest = part[4:]
                if ":" in rest:
                    name, pat = rest.split(":", 1)
                    components.append(("arg", name, pat))
                else:
                    # arg:name with no pattern means any value
                    components.append(("arg", rest, "*"))

            elif part.startswith("category:"):
                # category:name
                components.append(("category", "", part[9:]))

            else:
                # Assume it's a tool pattern
                components.append(("tool", "", part))

        return components

    @classmethod
    def _match_value(cls, pattern: str, value: str) -> bool:
        """
        Match a single pattern against a value.

        Supports:
        - Exact match: "bash" == "bash"
        - Glob pattern: "*.py" matches "test.py"
        - Regex pattern: "^/tmp/.*" matches "/tmp/foo"
        """
        # Empty pattern matches nothing
        if not pattern:
            return False

        # Exact match
        if pattern == value:
            return True

        # Check if it's a regex pattern (starts with ^, ends with $, or contains
        # regex-specific chars that aren't glob chars)
        if cls._is_regex(pattern):
            return cls._match_regex(pattern, value)

        # Glob pattern
        return cls._match_glob(pattern, value)

    @classmethod
    def _is_regex(cls, pattern: str) -> bool:
        """Check if pattern is a regex (vs glob)."""
        # Regex indicators
        regex_chars = {"^", "$", "+", "\\", "(", ")", "{", "}", "|"}

        # If pattern has regex-specific chars, treat as regex
        for char in regex_chars:
            if char in pattern:
                return True

        return False

    @classmethod
    def _match_glob(cls, pattern: str, value: str) -> bool:
        """Match using glob/fnmatch pattern."""
        return fnmatch.fnmatch(value, pattern)

    @classmethod
    def _match_regex(cls, pattern: str, value: str) -> bool:
        """Match using regex pattern."""
        compiled = cls._compile_regex(pattern)
        if compiled is None:
            return False  # Invalid regex
        return bool(compiled.search(value))

    @classmethod
    def specificity(cls, pattern: str) -> int:
        """
        Calculate pattern specificity score.

        Higher score = more specific pattern.
        Used to determine rule precedence.
        """
        components = cls.parse_pattern(pattern)
        score = 0

        for comp_type, comp_name, comp_pattern in components:
            # Base score for having a component
            score += 10

            # Tool patterns
            if comp_type == "tool":
                if "*" not in comp_pattern and "?" not in comp_pattern:
                    score += 20  # Exact tool match
                else:
                    score += 5  # Glob pattern

            # Argument patterns are more specific
            elif comp_type == "arg":
                score += 30  # Having argument constraint
                if "*" not in comp_pattern and "?" not in comp_pattern:
                    score += 20  # Exact argument match
                else:
                    score += 5

            # Category is less specific than tool
            elif comp_type == "category":
                score += 5

        return score


@dataclass
class RuleSet:
    """
    Collection of permission rules with evaluation logic.

    Rules are evaluated in order of:
    1. Priority (higher first)
    2. Specificity (more specific first)
    3. Permission level (more restrictive wins ties)
    """

    rules: list[PermissionRule] = field(default_factory=list)
    default: PermissionLevel = PermissionLevel.ASK

    def add_rule(self, rule: PermissionRule) -> None:
        """Add a rule to the set."""
        self.rules.append(rule)

    def remove_rule(self, pattern: str) -> bool:
        """
        Remove a rule by pattern.

        Returns True if a rule was removed.
        """
        for i, rule in enumerate(self.rules):
            if rule.pattern == pattern:
                self.rules.pop(i)
                return True
        return False

    def get_rule(self, pattern: str) -> PermissionRule | None:
        """Get a rule by pattern."""
        for rule in self.rules:
            if rule.pattern == pattern:
                return rule
        return None

    def evaluate(self, tool_name: str, arguments: dict[str, Any]) -> PermissionResult:
        """
        Evaluate rules to determine permission for a tool execution.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            PermissionResult with the determined level and matching rule
        """
        # Find all matching rules
        matches: list[tuple[PermissionRule, int]] = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            if PatternMatcher.match(rule.pattern, tool_name, arguments):
                specificity = PatternMatcher.specificity(rule.pattern)
                matches.append((rule, specificity))

        if not matches:
            # No matching rules, use default
            return PermissionResult(
                level=self.default,
                rule=None,
                reason=f"No matching rules, using default: {self.default.value}",
            )

        # Sort by priority (desc), specificity (desc), then restrictiveness (desc)
        def sort_key(item: tuple[PermissionRule, int]) -> tuple[int, int, int]:
            rule, spec = item
            # Negate for descending order
            perm_order = [PermissionLevel.ALLOW, PermissionLevel.ASK, PermissionLevel.DENY]
            return (-rule.priority, -spec, -perm_order.index(rule.permission))

        matches.sort(key=sort_key)

        # Most important match wins
        best_rule, _ = matches[0]

        return PermissionResult(
            level=best_rule.permission,
            rule=best_rule,
            reason=best_rule.description or f"Matched rule: {best_rule.pattern}",
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize rule set to dictionary."""
        return {
            "default": self.default.value,
            "rules": [rule.to_dict() for rule in self.rules],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RuleSet":
        """Deserialize rule set from dictionary."""
        return cls(
            rules=[PermissionRule.from_dict(r) for r in data.get("rules", [])],
            default=PermissionLevel(data.get("default", "ask")),
        )

    def __len__(self) -> int:
        return len(self.rules)

    def __iter__(self):
        return iter(self.rules)
```

---

## Step 3: Permission Checker

Create `src/forge/permissions/checker.py`:

```python
"""Permission checker for tool execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from forge.permissions.models import (
    PermissionLevel,
    PermissionResult,
    PermissionRule,
)
from forge.permissions.rules import RuleSet

if TYPE_CHECKING:
    from forge.config import Config


class PermissionChecker:
    """
    Checks permissions for tool execution.

    Evaluates rules from multiple sources in order:
    1. Session rules (temporary, highest priority)
    2. Project rules (from .src/forge/permissions.json)
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
    ):
        """
        Initialize permission checker.

        Args:
            global_rules: Rules from user configuration
            project_rules: Rules from project configuration
        """
        self.global_rules = global_rules or RuleSet()
        self.project_rules = project_rules
        self.session_rules = RuleSet()

    def check(self, tool_name: str, arguments: dict) -> PermissionResult:
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

    def allow_always(self, tool_name: str, arguments: dict | None = None) -> None:
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

    def deny_always(self, tool_name: str, arguments: dict | None = None) -> None:
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
    def from_config(cls, config: "Config") -> "PermissionChecker":
        """
        Create permission checker from configuration.

        Args:
            config: Application configuration

        Returns:
            Configured PermissionChecker
        """
        from forge.permissions.config import PermissionConfig

        global_rules = PermissionConfig.load_global()
        project_rules = PermissionConfig.load_project(config.project_root)

        return cls(global_rules=global_rules, project_rules=project_rules)


class ToolPermissionError(Exception):
    """Raised when permission is denied for a tool execution.

    Note: Named ToolPermissionError to avoid shadowing the builtin
    PermissionError exception. Using the same name as the builtin would
    cause subtle bugs when code expects to catch OSError/PermissionError
    from file operations but accidentally catches this instead.
    """

    def __init__(self, result: PermissionResult, tool_name: str, arguments: dict):
        self.result = result
        self.tool_name = tool_name
        self.arguments = arguments
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        return (
            f"Permission denied for tool '{self.tool_name}': {self.result.reason}"
        )
```

---

## Step 4: User Confirmation

Create `src/forge/permissions/prompt.py`:

```python
"""User confirmation prompts for permission requests."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from forge.permissions.models import PermissionRule, PermissionLevel


class ConfirmationChoice(str, Enum):
    """User choices for permission confirmation."""

    ALLOW = "allow"
    ALLOW_ALWAYS = "allow_always"
    DENY = "deny"
    DENY_ALWAYS = "deny_always"
    TIMEOUT = "timeout"


@dataclass
class ConfirmationRequest:
    """
    Request for user confirmation.

    Attributes:
        tool_name: Name of the tool requesting permission
        arguments: Tool arguments
        description: Description of what the tool will do
        timeout: Timeout in seconds (0 = no timeout)
    """

    tool_name: str
    arguments: dict[str, Any]
    description: str = ""
    timeout: float = 30.0


class PermissionPrompt:
    """
    Handles user confirmation prompts.

    This is an abstract base that can be implemented for different
    UI contexts (terminal, GUI, etc.).
    """

    def __init__(
        self,
        input_handler: Callable[[str], str] | None = None,
        output_handler: Callable[[str], None] | None = None,
    ):
        """
        Initialize prompt handler.

        Args:
            input_handler: Function to get user input
            output_handler: Function to display output
        """
        self.input_handler = input_handler or input
        self.output_handler = output_handler or print

    def format_request(self, request: ConfirmationRequest) -> str:
        """
        Format a confirmation request for display.

        Args:
            request: The confirmation request

        Returns:
            Formatted string for display
        """
        lines = [
            "┌" + "─" * 60 + "┐",
            "│  Permission Required" + " " * 39 + "│",
            "├" + "─" * 60 + "┤",
            f"│  Tool: {request.tool_name:<51} │",
        ]

        # Format arguments
        for key, value in request.arguments.items():
            value_str = str(value)
            if len(value_str) > 45:
                value_str = value_str[:42] + "..."
            lines.append(f"│  {key}: {value_str:<50} │"[:62] + " │")

        # Add description if present
        if request.description:
            lines.append("│" + " " * 60 + "│")
            desc = request.description
            if len(desc) > 56:
                desc = desc[:53] + "..."
            lines.append(f"│  {desc:<57} │")

        lines.extend([
            "│" + " " * 60 + "│",
            "│  [a] Allow    [A] Allow Always    [d] Deny    [D] Deny Always│",
            "└" + "─" * 60 + "┘",
        ])

        return "\n".join(lines)

    def confirm(self, request: ConfirmationRequest) -> ConfirmationChoice:
        """
        Prompt user for confirmation (synchronous).

        Args:
            request: The confirmation request

        Returns:
            User's choice
        """
        self.output_handler(self.format_request(request))
        self.output_handler("")

        try:
            response = self.input_handler("Choice [a/A/d/D]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return ConfirmationChoice.DENY

        return self._parse_response(response)

    async def confirm_async(self, request: ConfirmationRequest) -> ConfirmationChoice:
        """
        Prompt user for confirmation (asynchronous with timeout).

        Args:
            request: The confirmation request

        Returns:
            User's choice, or TIMEOUT if timed out
        """
        self.output_handler(self.format_request(request))
        self.output_handler("")

        if request.timeout > 0:
            try:
                # Run input in executor with timeout
                loop = asyncio.get_event_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: self.input_handler("Choice [a/A/d/D]: ").strip().lower(),
                    ),
                    timeout=request.timeout,
                )
                return self._parse_response(response)
            except asyncio.TimeoutError:
                self.output_handler("\nTimeout - permission denied.")
                return ConfirmationChoice.TIMEOUT
            except (EOFError, KeyboardInterrupt):
                return ConfirmationChoice.DENY
        else:
            # No timeout
            return self.confirm(request)

    def _parse_response(self, response: str) -> ConfirmationChoice:
        """Parse user response into choice."""
        if response == "a":
            return ConfirmationChoice.ALLOW
        elif response == "A":
            return ConfirmationChoice.ALLOW_ALWAYS
        elif response in ("d", ""):  # Default to deny
            return ConfirmationChoice.DENY
        elif response == "D":
            return ConfirmationChoice.DENY_ALWAYS
        else:
            # Invalid input defaults to deny
            return ConfirmationChoice.DENY


def create_rule_from_choice(
    choice: ConfirmationChoice,
    tool_name: str,
    arguments: dict[str, Any],
) -> PermissionRule | None:
    """
    Create a permission rule from a confirmation choice.

    Only creates rules for "always" choices.

    Args:
        choice: The user's choice
        tool_name: Name of the tool
        arguments: Tool arguments

    Returns:
        PermissionRule if an "always" choice, else None
    """
    if choice == ConfirmationChoice.ALLOW_ALWAYS:
        # Create allow rule for this tool
        pattern = f"tool:{tool_name}"
        return PermissionRule(
            pattern=pattern,
            permission=PermissionLevel.ALLOW,
            description=f"User allowed: {tool_name}",
            priority=100,
        )

    elif choice == ConfirmationChoice.DENY_ALWAYS:
        # Create deny rule for this tool
        pattern = f"tool:{tool_name}"
        return PermissionRule(
            pattern=pattern,
            permission=PermissionLevel.DENY,
            description=f"User denied: {tool_name}",
            priority=100,
        )

    return None
```

---

## Step 5: Configuration Loading

Create `src/forge/permissions/config.py`:

```python
"""Permission configuration management."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from forge.permissions.models import PermissionLevel, PermissionRule
from forge.permissions.rules import RuleSet

if TYPE_CHECKING:
    from forge.config import Config

logger = logging.getLogger(__name__)


# Default permission rules
DEFAULT_RULES: list[PermissionRule] = [
    # Allow read operations
    PermissionRule(
        pattern="tool:read",
        permission=PermissionLevel.ALLOW,
        description="Allow file reading",
    ),
    PermissionRule(
        pattern="tool:glob",
        permission=PermissionLevel.ALLOW,
        description="Allow file searching",
    ),
    PermissionRule(
        pattern="tool:grep",
        permission=PermissionLevel.ALLOW,
        description="Allow content searching",
    ),
    PermissionRule(
        pattern="tool:bash_output",
        permission=PermissionLevel.ALLOW,
        description="Allow reading shell output",
    ),

    # Ask for write operations
    PermissionRule(
        pattern="tool:write",
        permission=PermissionLevel.ASK,
        description="Confirm file writing",
    ),
    PermissionRule(
        pattern="tool:edit",
        permission=PermissionLevel.ASK,
        description="Confirm file editing",
    ),
    PermissionRule(
        pattern="tool:notebook_edit",
        permission=PermissionLevel.ASK,
        description="Confirm notebook editing",
    ),

    # Ask for execution
    PermissionRule(
        pattern="tool:bash",
        permission=PermissionLevel.ASK,
        description="Confirm shell commands",
    ),
    PermissionRule(
        pattern="tool:kill_shell",
        permission=PermissionLevel.ASK,
        description="Confirm killing shell",
    ),

    # Deny dangerous patterns
    PermissionRule(
        pattern="tool:bash,arg:command:*rm -rf*",
        permission=PermissionLevel.DENY,
        description="Block recursive force delete",
        priority=50,
    ),
    PermissionRule(
        pattern="tool:bash,arg:command:*rm -fr*",
        permission=PermissionLevel.DENY,
        description="Block recursive force delete",
        priority=50,
    ),
    PermissionRule(
        pattern="tool:bash,arg:command:*> /dev/*",
        permission=PermissionLevel.DENY,
        description="Block writing to devices",
        priority=50,
    ),
    PermissionRule(
        pattern="tool:bash,arg:command:*mkfs*",
        permission=PermissionLevel.DENY,
        description="Block filesystem creation",
        priority=50,
    ),
    PermissionRule(
        pattern="tool:bash,arg:command:*dd if=*",
        permission=PermissionLevel.DENY,
        description="Block dd command",
        priority=50,
    ),
    PermissionRule(
        pattern="tool:write,arg:file_path:/etc/*",
        permission=PermissionLevel.DENY,
        description="Block writing to /etc",
        priority=50,
    ),
    PermissionRule(
        pattern="tool:write,arg:file_path:/usr/*",
        permission=PermissionLevel.DENY,
        description="Block writing to /usr",
        priority=50,
    ),
    PermissionRule(
        pattern="tool:edit,arg:file_path:/etc/*",
        permission=PermissionLevel.DENY,
        description="Block editing /etc files",
        priority=50,
    ),
]


class PermissionConfig:
    """Manages permission configuration files."""

    GLOBAL_FILE = "permissions.json"
    PROJECT_FILE = ".src/forge/permissions.json"

    @classmethod
    def get_global_path(cls) -> Path:
        """Get path to global permissions file."""
        from forge.config import Config

        config_dir = Config.get_config_dir()
        return config_dir / cls.GLOBAL_FILE

    @classmethod
    def get_project_path(cls, project_root: Path | None = None) -> Path | None:
        """Get path to project permissions file."""
        if project_root is None:
            return None
        return project_root / cls.PROJECT_FILE

    @classmethod
    def load_global(cls) -> RuleSet:
        """
        Load global permission rules.

        If no global config exists, returns default rules.
        """
        path = cls.get_global_path()

        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                rules = RuleSet.from_dict(data)
                logger.debug(f"Loaded {len(rules)} global permission rules")
                return rules
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Error loading global permissions: {e}")

        # Return default rules
        return cls.get_default_rules()

    @classmethod
    def load_project(cls, project_root: Path | None) -> RuleSet | None:
        """
        Load project-specific permission rules.

        Returns None if no project config exists.
        """
        path = cls.get_project_path(project_root)

        if path is None or not path.exists():
            return None

        try:
            with open(path) as f:
                data = json.load(f)
            rules = RuleSet.from_dict(data)
            logger.debug(f"Loaded {len(rules)} project permission rules")
            return rules
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Error loading project permissions: {e}")
            return None

    @classmethod
    def save_global(cls, rules: RuleSet) -> None:
        """Save global permission rules."""
        path = cls.get_global_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(rules.to_dict(), f, indent=2)

        logger.debug(f"Saved {len(rules)} global permission rules")

    @classmethod
    def save_project(cls, project_root: Path, rules: RuleSet) -> None:
        """Save project-specific permission rules."""
        path = project_root / cls.PROJECT_FILE
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(rules.to_dict(), f, indent=2)

        logger.debug(f"Saved {len(rules)} project permission rules")

    @classmethod
    def get_default_rules(cls) -> RuleSet:
        """Get the default permission rules."""
        return RuleSet(
            rules=list(DEFAULT_RULES),
            default=PermissionLevel.ASK,
        )

    @classmethod
    def reset_to_defaults(cls) -> None:
        """Reset global permissions to defaults."""
        cls.save_global(cls.get_default_rules())
```

---

## Step 6: Package Exports

Create `src/forge/permissions/__init__.py`:

```python
"""
Permission system for Code-Forge.

This package provides permission checking and user confirmation
for tool execution, ensuring safety while maintaining usability.

Example:
    ```python
    from forge.permissions import (
        PermissionChecker,
        PermissionLevel,
        PermissionRule,
        PermissionPrompt,
        ConfirmationChoice,
    )

    # Create checker
    checker = PermissionChecker()

    # Check permission
    result = checker.check("bash", {"command": "ls -la"})

    if result.allowed:
        # Execute immediately
        pass
    elif result.needs_confirmation:
        # Ask user
        prompt = PermissionPrompt()
        choice = prompt.confirm(ConfirmationRequest(
            tool_name="bash",
            arguments={"command": "ls -la"},
            description="List directory contents",
        ))

        if choice in (ConfirmationChoice.ALLOW, ConfirmationChoice.ALLOW_ALWAYS):
            # Execute
            pass
    else:
        # Denied
        pass
    ```
"""

from forge.permissions.models import (
    PermissionLevel,
    PermissionCategory,
    PermissionResult,
    PermissionRule,
    TOOL_CATEGORIES,
    get_tool_category,
)
from forge.permissions.rules import (
    PatternMatcher,
    RuleSet,
)
from forge.permissions.checker import (
    PermissionChecker,
    ToolPermissionError,
)
from forge.permissions.prompt import (
    ConfirmationChoice,
    ConfirmationRequest,
    PermissionPrompt,
    create_rule_from_choice,
)
from forge.permissions.config import (
    PermissionConfig,
    DEFAULT_RULES,
)

__all__ = [
    # Models
    "PermissionLevel",
    "PermissionCategory",
    "PermissionResult",
    "PermissionRule",
    "TOOL_CATEGORIES",
    "get_tool_category",
    # Rules
    "PatternMatcher",
    "RuleSet",
    # Checker
    "PermissionChecker",
    "ToolPermissionError",
    # Prompt
    "ConfirmationChoice",
    "ConfirmationRequest",
    "PermissionPrompt",
    "create_rule_from_choice",
    # Config
    "PermissionConfig",
    "DEFAULT_RULES",
]
```

---

## Step 7: Integration with Tool Executor

Update `src/forge/tools/executor.py` to integrate permissions:

```python
# Add to ToolExecutor class

from forge.permissions import (
    PermissionChecker,
    PermissionPrompt,
    PermissionError,
    ConfirmationRequest,
    ConfirmationChoice,
    create_rule_from_choice,
)


class ToolExecutor:
    """Tool executor with permission checking."""

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        permission_checker: PermissionChecker | None = None,
        permission_prompt: PermissionPrompt | None = None,
    ):
        self.registry = registry or ToolRegistry.get_instance()
        self.permission_checker = permission_checker or PermissionChecker()
        self.permission_prompt = permission_prompt or PermissionPrompt()

    async def execute(
        self,
        tool: BaseTool,
        params: dict,
        context: ExecutionContext,
    ) -> ToolResult:
        """Execute a tool with permission checking."""
        # Check permission
        result = self.permission_checker.check(tool.name, params)

        if result.denied:
            raise PermissionError(result, tool.name, params)

        if result.needs_confirmation:
            # Get user confirmation
            request = ConfirmationRequest(
                tool_name=tool.name,
                arguments=params,
                description=tool.description,
            )

            choice = await self.permission_prompt.confirm_async(request)

            # Handle "always" choices
            if choice in (ConfirmationChoice.ALLOW_ALWAYS, ConfirmationChoice.DENY_ALWAYS):
                rule = create_rule_from_choice(choice, tool.name, params)
                if rule:
                    self.permission_checker.add_session_rule(rule)

            # Check if allowed
            if choice not in (ConfirmationChoice.ALLOW, ConfirmationChoice.ALLOW_ALWAYS):
                raise PermissionError(
                    PermissionResult(
                        level=PermissionLevel.DENY,
                        reason="User denied permission",
                    ),
                    tool.name,
                    params,
                )

        # Permission granted - execute tool
        return await tool.execute(params, context)
```

---

## Testing Strategy

### Test Files Structure

```
tests/unit/permissions/
├── __init__.py
├── test_models.py
├── test_rules.py
├── test_checker.py
├── test_prompt.py
└── test_config.py
```

### Key Test Cases

1. **test_models.py**
   - Test PermissionLevel comparison
   - Test PermissionResult properties
   - Test PermissionRule serialization

2. **test_rules.py**
   - Test PatternMatcher.match for various patterns
   - Test glob patterns
   - Test regex patterns
   - Test combined patterns
   - Test RuleSet.evaluate

3. **test_checker.py**
   - Test permission check with no rules
   - Test permission check with matching rules
   - Test session rule priority
   - Test allow_always and deny_always

4. **test_prompt.py**
   - Test prompt formatting
   - Test response parsing
   - Test rule creation from choices

5. **test_config.py**
   - Test default rules loading
   - Test config file loading
   - Test config file saving
