"""File manipulation tools for Code-Forge.

This package provides tools for reading, writing, editing, and searching files.
"""

from code_forge.tools.file.edit import EditTool
from code_forge.tools.file.glob import GlobTool
from code_forge.tools.file.grep import GrepTool
from code_forge.tools.file.read import ReadTool
from code_forge.tools.file.write import WriteTool

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
    from code_forge.tools.registry import ToolRegistry

    registry = ToolRegistry()
    registry.register(ReadTool())
    registry.register(WriteTool())
    registry.register(EditTool())
    registry.register(GlobTool())
    registry.register(GrepTool())
