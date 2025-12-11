"""Hook configuration management."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from code_forge.hooks.registry import Hook

logger = logging.getLogger(__name__)


# Default hooks (empty - user must configure)
DEFAULT_HOOKS: list[Hook] = []


class HookConfig:
    """Manages hook configuration files."""

    GLOBAL_FILE = "hooks.json"
    PROJECT_FILE = ".forge/hooks.json"

    @classmethod
    def get_config_dir(cls) -> Path:
        """Get the global config directory."""
        # Use XDG_CONFIG_HOME if available, otherwise ~/.config
        import os

        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            config_dir = Path(xdg_config) / "forge"
        else:
            config_dir = Path.home() / ".config" / "forge"
        return config_dir

    @classmethod
    def get_global_path(cls) -> Path:
        """Get path to global hooks file."""
        return cls.get_config_dir() / cls.GLOBAL_FILE

    @classmethod
    def get_project_path(cls, project_root: Path | None = None) -> Path | None:
        """Get path to project hooks file."""
        if project_root is None:
            return None
        return project_root / cls.PROJECT_FILE

    @classmethod
    def load_global(cls) -> list[Hook]:
        """
        Load global hooks.

        Returns:
            List of hooks from global config
        """
        path = cls.get_global_path()

        if not path.exists():
            return list(DEFAULT_HOOKS)

        try:
            with path.open(encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)

            hooks = [Hook.from_dict(h) for h in data.get("hooks", [])]
            logger.debug("Loaded %d global hooks", len(hooks))
            return hooks

        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            logger.warning("Error loading global hooks: %s", e)
            return list(DEFAULT_HOOKS)

    @classmethod
    def load_project(cls, project_root: Path | None) -> list[Hook]:
        """
        Load project-specific hooks.

        Args:
            project_root: Path to project root

        Returns:
            List of project hooks
        """
        path = cls.get_project_path(project_root)

        if path is None or not path.exists():
            return []

        try:
            with path.open(encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)

            hooks = [Hook.from_dict(h) for h in data.get("hooks", [])]
            logger.debug("Loaded %d project hooks", len(hooks))
            return hooks

        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            logger.warning("Error loading project hooks: %s", e)
            return []

    @classmethod
    def save_global(cls, hooks: list[Hook]) -> None:
        """Save global hooks."""
        path = cls.get_global_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "hooks": [h.to_dict() for h in hooks],
        }

        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.debug("Saved %d global hooks", len(hooks))

    @classmethod
    def save_project(cls, project_root: Path, hooks: list[Hook]) -> None:
        """Save project hooks."""
        path = project_root / cls.PROJECT_FILE
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "hooks": [h.to_dict() for h in hooks],
        }

        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.debug("Saved %d project hooks", len(hooks))

    @classmethod
    def load_all(cls, project_root: Path | None = None) -> list[Hook]:
        """
        Load all hooks (global + project).

        Args:
            project_root: Optional project root path

        Returns:
            Combined list of hooks
        """
        hooks = cls.load_global()
        hooks.extend(cls.load_project(project_root))
        return hooks


# Example hook templates
HOOK_TEMPLATES: dict[str, Hook] = {
    "log_all": Hook(
        event_pattern="*",
        command='echo "[$(date)] $FORGE_EVENT" >> ~/.config/forge/events.log',
        description="Log all events to file",
    ),
    "notify_session_start": Hook(
        event_pattern="session:start",
        command="notify-send 'Code-Forge' 'Session started'",
        description="Desktop notification on session start",
    ),
    "git_auto_commit": Hook(
        event_pattern="tool:post_execute:write",
        command=(
            "git add -A && "
            "git diff --cached --quiet || "
            "git commit -m 'Auto-save: file written'"
        ),
        timeout=30.0,
        description="Auto-commit on file writes",
    ),
    "block_sudo": Hook(
        event_pattern="tool:pre_execute:bash",
        command=(
            'if echo "$FORGE_TOOL_ARGS" | grep -q "sudo"; then '
            'echo "sudo blocked by hook"; exit 1; fi'
        ),
        description="Block sudo commands in bash",
    ),
}
