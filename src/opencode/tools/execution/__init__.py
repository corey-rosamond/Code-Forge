"""Execution tools for OpenCode."""

from opencode.tools.execution.bash import BashTool
from opencode.tools.execution.bash_output import BashOutputTool
from opencode.tools.execution.kill_shell import KillShellTool
from opencode.tools.execution.shell_manager import (
    ShellManager,
    ShellProcess,
    ShellStatus,
)

__all__ = [
    "BashOutputTool",
    "BashTool",
    "KillShellTool",
    "ShellManager",
    "ShellProcess",
    "ShellStatus",
    "register_execution_tools",
]


def register_execution_tools() -> None:
    """Register all execution tools with the registry."""
    from opencode.tools.registry import ToolRegistry

    registry = ToolRegistry()
    registry.register(BashTool())
    registry.register(BashOutputTool())
    registry.register(KillShellTool())
