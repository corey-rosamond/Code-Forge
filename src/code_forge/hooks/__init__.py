"""
Hooks system for Code-Forge.

This package provides a hooks mechanism that allows users to
execute custom shell commands in response to various events
in the Code-Forge lifecycle.

Example:
    ```python
    from code_forge.hooks import (
        HookRegistry,
        HookExecutor,
        HookEvent,
        Hook,
        fire_event,
    )

    # Register a hook
    registry = HookRegistry.get_instance()
    registry.register(Hook(
        event_pattern="tool:pre_execute",
        command="echo 'Executing tool: $FORGE_TOOL_NAME'",
    ))

    # Fire an event
    event = HookEvent.tool_pre_execute("bash", {"command": "ls"})
    results = await fire_event(event)

    # Check results
    for result in results:
        if not result.should_continue:
            print(f"Blocked by hook: {result.hook.event_pattern}")
    ```
"""

from code_forge.hooks.config import (
    DEFAULT_HOOKS,
    HOOK_TEMPLATES,
    HookConfig,
)
from code_forge.hooks.events import (
    EventType,
    HookEvent,
)
from code_forge.hooks.executor import (
    HookBlockedError,
    HookExecutor,
    HookResult,
    fire_event,
)
from code_forge.hooks.registry import (
    Hook,
    HookRegistry,
)

__all__ = [
    "DEFAULT_HOOKS",
    "HOOK_TEMPLATES",
    "EventType",
    "Hook",
    "HookBlockedError",
    "HookConfig",
    "HookEvent",
    "HookExecutor",
    "HookRegistry",
    "HookResult",
    "fire_event",
]
