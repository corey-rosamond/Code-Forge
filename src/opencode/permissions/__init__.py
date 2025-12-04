"""
Permission system for OpenCode.

This package provides permission checking and user confirmation
for tool execution, ensuring safety while maintaining usability.

Example:
    ```python
    from opencode.permissions import (
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

from opencode.permissions.checker import (
    PermissionChecker,
    ToolPermissionError,
)
from opencode.permissions.config import (
    DEFAULT_RULES,
    PermissionConfig,
)
from opencode.permissions.models import (
    TOOL_CATEGORIES,
    PermissionCategory,
    PermissionLevel,
    PermissionResult,
    PermissionRule,
    get_tool_category,
)
from opencode.permissions.prompt import (
    ConfirmationChoice,
    ConfirmationRequest,
    PermissionPrompt,
    create_rule_from_choice,
)
from opencode.permissions.rules import (
    PatternMatcher,
    RuleSet,
)

__all__ = [
    "DEFAULT_RULES",
    "TOOL_CATEGORIES",
    "ConfirmationChoice",
    "ConfirmationRequest",
    "PatternMatcher",
    "PermissionCategory",
    "PermissionChecker",
    "PermissionConfig",
    "PermissionLevel",
    "PermissionPrompt",
    "PermissionResult",
    "PermissionRule",
    "RuleSet",
    "ToolPermissionError",
    "create_rule_from_choice",
    "get_tool_category",
]
