"""CLI package for OpenCode.

This package provides the command-line interface including:
- REPL (Read-Eval-Print Loop) for interactive sessions
- Status bar for runtime information display
- Theme support for customizable appearance
"""

from opencode.cli.main import main
from opencode.cli.repl import InputHandler, OpenCodeREPL, OutputRenderer
from opencode.cli.status import StatusBar, StatusBarObserver
from opencode.cli.themes import (
    DARK_THEME,
    LIGHT_THEME,
    Theme,
    ThemeRegistry,
)

__all__ = [
    "DARK_THEME",
    "LIGHT_THEME",
    "InputHandler",
    "OpenCodeREPL",
    "OutputRenderer",
    "StatusBar",
    "StatusBarObserver",
    "Theme",
    "ThemeRegistry",
    "main",
]
