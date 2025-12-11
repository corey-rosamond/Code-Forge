"""Tests for hook configuration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from code_forge.hooks.config import (
    DEFAULT_HOOKS,
    HOOK_TEMPLATES,
    HookConfig,
)
from code_forge.hooks.registry import Hook


class TestHookConfigPaths:
    """Tests for HookConfig path methods."""

    def test_get_config_dir(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config dir uses XDG_CONFIG_HOME if set."""
        monkeypatch.setenv("XDG_CONFIG_HOME", "/custom/config")
        path = HookConfig.get_config_dir()
        assert path == Path("/custom/config/forge")

    def test_get_config_dir_default(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Config dir defaults to ~/.config/code_forge."""
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        monkeypatch.setenv("HOME", str(tmp_path))
        path = HookConfig.get_config_dir()
        assert path == tmp_path / ".config" / "forge"

    def test_get_global_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Global path is in config dir."""
        monkeypatch.setenv("XDG_CONFIG_HOME", "/config")
        path = HookConfig.get_global_path()
        assert path == Path("/config/forge/hooks.json")

    def test_get_project_path_with_root(self) -> None:
        """Project path is in project directory."""
        project_root = Path("/project")
        path = HookConfig.get_project_path(project_root)
        assert path == Path("/project/.forge/hooks.json")

    def test_get_project_path_none(self) -> None:
        """Project path is None when no root."""
        path = HookConfig.get_project_path(None)
        assert path is None


class TestHookConfigLoadGlobal:
    """Tests for HookConfig.load_global()."""

    def test_load_global_returns_defaults_when_no_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Returns default hooks when no config file."""
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        hooks = HookConfig.load_global()
        assert hooks == list(DEFAULT_HOOKS)

    def test_load_global_reads_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Reads hooks from config file."""
        config_dir = tmp_path / "forge"
        config_dir.mkdir()
        config_file = config_dir / "hooks.json"
        config_file.write_text(
            json.dumps(
                {
                    "hooks": [
                        {"event": "tool:*", "command": "echo test"},
                        {"event": "llm:*", "command": "echo llm"},
                    ]
                }
            )
        )

        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        hooks = HookConfig.load_global()

        assert len(hooks) == 2
        assert hooks[0].event_pattern == "tool:*"
        assert hooks[1].event_pattern == "llm:*"

    def test_load_global_handles_corrupted_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Returns defaults for corrupted config file."""
        config_dir = tmp_path / "forge"
        config_dir.mkdir()
        config_file = config_dir / "hooks.json"
        config_file.write_text("not valid json {{{")

        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        hooks = HookConfig.load_global()

        assert hooks == list(DEFAULT_HOOKS)

    def test_load_global_handles_invalid_structure(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Returns defaults for invalid JSON structure."""
        config_dir = tmp_path / "forge"
        config_dir.mkdir()
        config_file = config_dir / "hooks.json"
        config_file.write_text(json.dumps({"wrong": "structure"}))

        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        hooks = HookConfig.load_global()

        assert hooks == []  # Empty because "hooks" key is missing


class TestHookConfigLoadProject:
    """Tests for HookConfig.load_project()."""

    def test_load_project_returns_empty_when_no_root(self) -> None:
        """Returns empty list when no project root."""
        hooks = HookConfig.load_project(None)
        assert hooks == []

    def test_load_project_returns_empty_when_no_file(self, tmp_path: Path) -> None:
        """Returns empty list when no config file."""
        hooks = HookConfig.load_project(tmp_path)
        assert hooks == []

    def test_load_project_reads_file(self, tmp_path: Path) -> None:
        """Reads hooks from project config file."""
        config_dir = tmp_path / ".forge"
        config_dir.mkdir()
        config_file = config_dir / "hooks.json"
        config_file.write_text(
            json.dumps(
                {
                    "hooks": [
                        {"event": "tool:pre_execute:bash", "command": "echo project"},
                    ]
                }
            )
        )

        hooks = HookConfig.load_project(tmp_path)

        assert len(hooks) == 1
        assert hooks[0].event_pattern == "tool:pre_execute:bash"

    def test_load_project_handles_corrupted_file(self, tmp_path: Path) -> None:
        """Returns empty for corrupted config file."""
        config_dir = tmp_path / ".forge"
        config_dir.mkdir()
        config_file = config_dir / "hooks.json"
        config_file.write_text("not valid json")

        hooks = HookConfig.load_project(tmp_path)
        assert hooks == []


class TestHookConfigSaveGlobal:
    """Tests for HookConfig.save_global()."""

    def test_save_global_creates_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Saves hooks to global config file."""
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

        hooks = [
            Hook(event_pattern="tool:*", command="echo test"),
            Hook(event_pattern="llm:*", command="echo llm"),
        ]
        HookConfig.save_global(hooks)

        config_file = tmp_path / "forge" / "hooks.json"
        assert config_file.exists()

        data = json.loads(config_file.read_text())
        assert len(data["hooks"]) == 2

    def test_save_global_creates_directory(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Creates config directory if needed."""
        config_dir = tmp_path / "new_config"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(config_dir))

        hooks = [Hook(event_pattern="test", command="echo")]
        HookConfig.save_global(hooks)

        assert (config_dir / "forge" / "hooks.json").exists()

    def test_save_global_roundtrip(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Saved hooks can be loaded back."""
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

        original = [
            Hook(
                event_pattern="tool:*",
                command="echo test",
                timeout=15.0,
                description="Test hook",
            ),
        ]
        HookConfig.save_global(original)
        loaded = HookConfig.load_global()

        assert len(loaded) == 1
        assert loaded[0].event_pattern == original[0].event_pattern
        assert loaded[0].timeout == original[0].timeout
        assert loaded[0].description == original[0].description


class TestHookConfigSaveProject:
    """Tests for HookConfig.save_project()."""

    def test_save_project_creates_file(self, tmp_path: Path) -> None:
        """Saves hooks to project config file."""
        hooks = [Hook(event_pattern="tool:*", command="echo project")]
        HookConfig.save_project(tmp_path, hooks)

        config_file = tmp_path / ".forge" / "hooks.json"
        assert config_file.exists()

        data = json.loads(config_file.read_text())
        assert len(data["hooks"]) == 1

    def test_save_project_creates_directory(self, tmp_path: Path) -> None:
        """Creates .forge directory if needed."""
        hooks = [Hook(event_pattern="test", command="echo")]
        HookConfig.save_project(tmp_path, hooks)

        assert (tmp_path / ".forge").is_dir()

    def test_save_project_roundtrip(self, tmp_path: Path) -> None:
        """Saved project hooks can be loaded back."""
        original = [
            Hook(
                event_pattern="tool:post_execute:write",
                command="git add -A",
                timeout=30.0,
            ),
        ]
        HookConfig.save_project(tmp_path, original)
        loaded = HookConfig.load_project(tmp_path)

        assert len(loaded) == 1
        assert loaded[0].event_pattern == original[0].event_pattern
        assert loaded[0].timeout == original[0].timeout


class TestHookConfigLoadAll:
    """Tests for HookConfig.load_all()."""

    def test_load_all_combines_sources(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Loads hooks from both global and project."""
        # Set up global config
        global_dir = tmp_path / "global"
        global_dir.mkdir()
        global_config = global_dir / "forge"
        global_config.mkdir()
        (global_config / "hooks.json").write_text(
            json.dumps({"hooks": [{"event": "session:*", "command": "echo global"}]})
        )

        # Set up project config
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        project_config = project_dir / ".forge"
        project_config.mkdir()
        (project_config / "hooks.json").write_text(
            json.dumps({"hooks": [{"event": "tool:*", "command": "echo project"}]})
        )

        monkeypatch.setenv("XDG_CONFIG_HOME", str(global_dir))
        hooks = HookConfig.load_all(project_dir)

        assert len(hooks) == 2
        patterns = [h.event_pattern for h in hooks]
        assert "session:*" in patterns
        assert "tool:*" in patterns

    def test_load_all_without_project(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Loads only global hooks when no project."""
        global_dir = tmp_path / "global"
        global_dir.mkdir()
        global_config = global_dir / "forge"
        global_config.mkdir()
        (global_config / "hooks.json").write_text(
            json.dumps({"hooks": [{"event": "session:*", "command": "echo global"}]})
        )

        monkeypatch.setenv("XDG_CONFIG_HOME", str(global_dir))
        hooks = HookConfig.load_all(None)

        assert len(hooks) == 1
        assert hooks[0].event_pattern == "session:*"


class TestHookTemplates:
    """Tests for HOOK_TEMPLATES."""

    def test_templates_exist(self) -> None:
        """All expected templates exist."""
        assert "log_all" in HOOK_TEMPLATES
        assert "notify_session_start" in HOOK_TEMPLATES
        assert "git_auto_commit" in HOOK_TEMPLATES
        assert "block_sudo" in HOOK_TEMPLATES

    def test_log_all_template(self) -> None:
        """log_all template matches all events."""
        hook = HOOK_TEMPLATES["log_all"]
        assert hook.event_pattern == "*"
        assert "log" in hook.description.lower()

    def test_notify_session_start_template(self) -> None:
        """notify_session_start template is configured correctly."""
        hook = HOOK_TEMPLATES["notify_session_start"]
        assert hook.event_pattern == "session:start"
        assert "notify-send" in hook.command

    def test_git_auto_commit_template(self) -> None:
        """git_auto_commit template is configured correctly."""
        hook = HOOK_TEMPLATES["git_auto_commit"]
        assert hook.event_pattern == "tool:post_execute:write"
        assert "git" in hook.command
        assert hook.timeout == 30.0

    def test_block_sudo_template(self) -> None:
        """block_sudo template blocks sudo commands."""
        hook = HOOK_TEMPLATES["block_sudo"]
        assert hook.event_pattern == "tool:pre_execute:bash"
        assert "sudo" in hook.command
        assert "exit 1" in hook.command

    def test_templates_are_valid_hooks(self) -> None:
        """All templates are valid Hook instances."""
        for name, hook in HOOK_TEMPLATES.items():
            assert isinstance(hook, Hook), f"{name} is not a Hook"
            assert hook.event_pattern, f"{name} has no event_pattern"
            assert hook.command, f"{name} has no command"


class TestDefaultHooks:
    """Tests for DEFAULT_HOOKS."""

    def test_default_hooks_is_list(self) -> None:
        """DEFAULT_HOOKS is a list."""
        assert isinstance(DEFAULT_HOOKS, list)

    def test_default_hooks_empty(self) -> None:
        """DEFAULT_HOOKS is empty by default."""
        # User must explicitly configure hooks
        assert len(DEFAULT_HOOKS) == 0
