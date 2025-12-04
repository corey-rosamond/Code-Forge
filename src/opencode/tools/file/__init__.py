"""File manipulation tools for OpenCode.

This package provides tools for reading, writing, editing, and searching files.
"""

from opencode.tools.file.edit import EditTool
from opencode.tools.file.glob import GlobTool
from opencode.tools.file.grep import GrepTool
from opencode.tools.file.read import ReadTool
from opencode.tools.file.write import WriteTool

__all__ = [
    "EditTool",
    "GlobTool",
    "GrepTool",
    "ReadTool",
    "WriteTool",
    "register_file_tools",
]


def register_file_tools() -> None:
    """Register all file tools with the global registry."""
    from opencode.tools.registry import ToolRegistry

    registry = ToolRegistry()
    registry.register(ReadTool())
    registry.register(WriteTool())
    registry.register(EditTool())
    registry.register(GlobTool())
    registry.register(GrepTool())
