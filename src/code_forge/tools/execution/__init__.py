"""Execution tools for Code-Forge."""

from code_forge.tools.execution.bash import BashTool
from code_forge.tools.execution.bash_output import BashOutputTool
from code_forge.tools.execution.kill_shell import KillShellTool
from code_forge.tools.execution.shell_manager import (
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
    from code_forge.tools.registry import ToolRegistry

    registry = ToolRegistry()
    registry.register(BashTool())
    registry.register(BashOutputTool())
    registry.register(KillShellTool())
