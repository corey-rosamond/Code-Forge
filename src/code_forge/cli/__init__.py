"""CLI package for Code-Forge.

This package provides the command-line interface including:
- REPL (Read-Eval-Print Loop) for interactive sessions
- Status bar for runtime information display
- Theme support for customizable appearance
"""

from code_forge.cli.main import main
from code_forge.cli.repl import InputHandler, CodeForgeREPL, OutputRenderer
from code_forge.cli.status import StatusBar, StatusBarObserver
from code_forge.cli.themes import (
    DARK_THEME,
    LIGHT_THEME,
    Theme,
    ThemeRegistry,
)

__all__ = [
    "DARK_THEME",
    "LIGHT_THEME",
    "InputHandler",
    "CodeForgeREPL",
    "OutputRenderer",
    "StatusBar",
    "StatusBarObserver",
    "Theme",
    "ThemeRegistry",
    "main",
]
