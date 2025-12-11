"""Theme definitions for Code-Forge CLI.

This module provides color theme definitions for the terminal interface,
supporting both dark and light themes with consistent color semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class Theme:
    """Color theme definition.

    All colors are specified as hex color codes.

    Attributes:
        name: Theme identifier.
        background: Background color.
        foreground: Primary text color.
        accent: Accent color for highlights.
        success: Success/positive color.
        warning: Warning color.
        error: Error/negative color.
        dim: Dimmed/secondary text color.
        status_bar_bg: Status bar background.
        status_bar_fg: Status bar foreground.
    """

    name: str
    background: str
    foreground: str
    accent: str
    success: str
    warning: str
    error: str
    dim: str
    status_bar_bg: str
    status_bar_fg: str

    def to_dict(self) -> dict[str, str]:
        """Convert theme to dictionary.

        Returns:
            Dictionary mapping color names to hex values.
        """
        return {
            "background": self.background,
            "foreground": self.foreground,
            "accent": self.accent,
            "success": self.success,
            "warning": self.warning,
            "error": self.error,
            "dim": self.dim,
            "status_bar_bg": self.status_bar_bg,
            "status_bar_fg": self.status_bar_fg,
        }

    def to_prompt_toolkit_style(self) -> dict[str, str]:
        """Convert theme to prompt_toolkit style dictionary.

        Returns:
            Dictionary suitable for prompt_toolkit Style.from_dict().
        """
        return {
            "": f"fg:{self.foreground}",
            "prompt": f"fg:{self.accent} bold",
            "continuation": f"fg:{self.dim}",
            "bottom-toolbar": f"bg:{self.status_bar_bg} fg:{self.status_bar_fg}",
            "bottom-toolbar.text": f"fg:{self.status_bar_fg}",
        }


# Dark theme - Tokyo Night inspired
DARK_THEME = Theme(
    name="dark",
    background="#1a1b26",
    foreground="#c0caf5",
    accent="#7aa2f7",
    success="#9ece6a",
    warning="#e0af68",
    error="#f7768e",
    dim="#565f89",
    status_bar_bg="#24283b",
    status_bar_fg="#c0caf5",
)

# Light theme - clean and readable
LIGHT_THEME = Theme(
    name="light",
    background="#f5f5f5",
    foreground="#1a1b26",
    accent="#2563eb",
    success="#22c55e",
    warning="#eab308",
    error="#ef4444",
    dim="#6b7280",
    status_bar_bg="#e5e7eb",
    status_bar_fg="#1a1b26",
)


class ThemeRegistry:
    """Registry of available themes.

    Provides lookup and management of color themes.
    """

    _themes: ClassVar[dict[str, Theme]] = {
        "dark": DARK_THEME,
        "light": LIGHT_THEME,
    }
    _default: ClassVar[str] = "dark"

    @classmethod
    def get(cls, name: str) -> Theme:
        """Get theme by name.

        Args:
            name: Theme name (case-insensitive).

        Returns:
            Theme instance. Returns default theme if name not found.
        """
        normalized = name.strip().lower()
        return cls._themes.get(normalized, cls._themes[cls._default])

    @classmethod
    def get_default(cls) -> Theme:
        """Get the default theme.

        Returns:
            Default theme instance.
        """
        return cls._themes[cls._default]

    @classmethod
    def list_themes(cls) -> list[str]:
        """List available theme names.

        Returns:
            List of theme names.
        """
        return list(cls._themes.keys())

    @classmethod
    def register(cls, theme: Theme) -> None:
        """Register a custom theme.

        Args:
            theme: Theme to register.
        """
        cls._themes[theme.name.lower()] = theme

    @classmethod
    def set_default(cls, name: str) -> None:
        """Set the default theme.

        Args:
            name: Theme name to set as default.

        Raises:
            ValueError: If theme name is not registered.
        """
        normalized = name.strip().lower()
        if normalized not in cls._themes:
            raise ValueError(f"Unknown theme: {name}")
        cls._default = normalized
