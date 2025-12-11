"""
Permission system for Code-Forge.

This package provides permission checking and user confirmation
for tool execution, ensuring safety while maintaining usability.

Example:
    ```python
    from code_forge.permissions import (
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

from code_forge.permissions.checker import (
    PermissionChecker,
    ToolPermissionError,
)
from code_forge.permissions.config import (
    DEFAULT_RULES,
    PermissionConfig,
)
from code_forge.permissions.models import (
    TOOL_CATEGORIES,
    PermissionCategory,
    PermissionLevel,
    PermissionResult,
    PermissionRule,
    get_tool_category,
)
from code_forge.permissions.prompt import (
    ConfirmationChoice,
    ConfirmationRequest,
    PermissionPrompt,
    create_rule_from_choice,
)
from code_forge.permissions.rules import (
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
