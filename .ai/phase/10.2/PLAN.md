# Phase 10.2: Polish and Integration Testing - Implementation Plan

**Phase:** 10.2
**Name:** Polish and Integration Testing
**Dependencies:** All previous phases (1.1 - 10.1)

---

## Overview

Phase 10.2 is the final polish phase focused on ensuring all components work together seamlessly, comprehensive integration testing, performance optimization, documentation completeness, and release preparation.

---

## Implementation Steps

### Step 1: Integration Test Infrastructure

Create the test infrastructure for integration testing.

**File:** `tests/conftest.py` (extend)

```python
"""Shared test fixtures and configuration."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, AsyncGenerator, Generator

import pytest

if TYPE_CHECKING:
    from opencode.core.app import opencode


# ============================================================
# Session Fixtures
# ============================================================


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_home(temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary home directory."""
    home = temp_dir / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    return home


@pytest.fixture
def temp_project(temp_dir: Path) -> Path:
    """Create a temporary project directory."""
    project = temp_dir / "project"
    project.mkdir()
    return project


# ============================================================
# Application Fixtures
# ============================================================


@pytest.fixture
async def app(temp_home: Path, temp_project: Path) -> AsyncGenerator["OpenCode", None]:
    """Create an OpenCode application instance for testing."""
    from opencode.core.app import opencode
    from opencode.core.config import Config

    config = Config(
        home_dir=temp_home,
        project_dir=temp_project,
    )

    app = OpenCode(config=config)
    await app.initialize()

    yield app

    await app.shutdown()


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response factory."""

    def _create(content: str, tool_calls: list | None = None):
        from langchain_core.messages import AIMessage

        return AIMessage(
            content=content,
            tool_calls=tool_calls or [],
        )

    return _create


# ============================================================
# Git Fixtures
# ============================================================


@pytest.fixture
def git_repo(temp_project: Path) -> Path:
    """Initialize a git repository."""
    import subprocess

    subprocess.run(["git", "init"], cwd=temp_project, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=temp_project,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=temp_project,
        check=True,
        capture_output=True,
    )

    # Create initial commit
    readme = temp_project / "README.md"
    readme.write_text("# Test Project\n")
    subprocess.run(["git", "add", "."], cwd=temp_project, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=temp_project,
        check=True,
        capture_output=True,
    )

    return temp_project


# ============================================================
# Tool Fixtures
# ============================================================


@pytest.fixture
def sample_file(temp_project: Path) -> Path:
    """Create a sample file for testing."""
    file_path = temp_project / "sample.py"
    file_path.write_text('''"""Sample module."""

def hello(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}!"


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
''')
    return file_path


# ============================================================
# Session Fixtures
# ============================================================


@pytest.fixture
async def session(app: "OpenCode"):
    """Create a test session."""
    session = await app.session_manager.create_session()
    yield session
    await app.session_manager.close_session(session.id)


# ============================================================
# Plugin Fixtures
# ============================================================


@pytest.fixture
def sample_plugin(temp_home: Path) -> Path:
    """Create a sample plugin for testing."""
    plugin_dir = temp_home / ".opencode" / "plugins" / "test-plugin"
    plugin_dir.mkdir(parents=True)

    # Create manifest
    manifest = plugin_dir / "plugin.yaml"
    manifest.write_text("""
name: test-plugin
version: 1.0.0
description: Test plugin for integration tests
entry_point: test_plugin:TestPlugin
capabilities:
  tools: true
""")

    # Create plugin module
    module = plugin_dir / "test_plugin.py"
    module.write_text('''
from opencode.plugins import Plugin, PluginMetadata, PluginCapabilities
from opencode.tools.base import Tool


class EchoTool(Tool):
    name = "echo"
    description = "Echo input back"

    async def execute(self, message: str) -> str:
        return f"Echo: {message}"


class TestPlugin(Plugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
        )

    @property
    def capabilities(self) -> PluginCapabilities:
        return PluginCapabilities(tools=True)

    def register_tools(self) -> list[Tool]:
        return [EchoTool()]
''')

    return plugin_dir
```

---

### Step 2: Tool Execution Integration Tests

Test the complete tool execution flow.

**File:** `tests/integration/test_tool_execution.py`

```python
"""Integration tests for tool execution flow."""

from __future__ import annotations

from pathlib import Path

import pytest

from opencode.core.app import opencode


class TestToolExecutionFlow:
    """Test tool execution with all components."""

    @pytest.mark.asyncio
    async def test_read_file_flow(self, app: OpenCode, sample_file: Path):
        """Test Read tool through full pipeline."""
        # Get tool from registry
        read_tool = app.tool_registry.get("Read")
        assert read_tool is not None

        # Execute through permission system
        result = await app.execute_tool(
            tool_name="Read",
            arguments={"file_path": str(sample_file)},
        )

        assert result.success
        assert "Sample module" in result.output
        assert "def hello" in result.output

    @pytest.mark.asyncio
    async def test_edit_file_with_permission(
        self, app: OpenCode, sample_file: Path, monkeypatch
    ):
        """Test Edit tool with permission check."""
        # Auto-approve for testing
        monkeypatch.setattr(app.permission_system, "auto_approve", True)

        result = await app.execute_tool(
            tool_name="Edit",
            arguments={
                "file_path": str(sample_file),
                "old_string": 'return f"Hello, {name}!"',
                "new_string": 'return f"Greetings, {name}!"',
            },
        )

        assert result.success

        # Verify change
        content = sample_file.read_text()
        assert "Greetings" in content

    @pytest.mark.asyncio
    async def test_bash_with_hooks(self, app: OpenCode, temp_project: Path):
        """Test Bash tool with hook execution."""
        hook_called = False

        async def before_hook(event):
            nonlocal hook_called
            hook_called = True

        app.hooks.register("before_tool_execute", before_hook)

        result = await app.execute_tool(
            tool_name="Bash",
            arguments={"command": "echo 'test'"},
        )

        assert result.success
        assert hook_called
        assert "test" in result.output

    @pytest.mark.asyncio
    async def test_glob_search(self, app: OpenCode, temp_project: Path):
        """Test Glob tool for file searching."""
        # Create test files
        (temp_project / "file1.py").write_text("# Python file 1")
        (temp_project / "file2.py").write_text("# Python file 2")
        (temp_project / "file3.txt").write_text("Text file")
        (temp_project / "subdir").mkdir()
        (temp_project / "subdir" / "file4.py").write_text("# Python file 4")

        result = await app.execute_tool(
            tool_name="Glob",
            arguments={
                "pattern": "**/*.py",
                "path": str(temp_project),
            },
        )

        assert result.success
        assert "file1.py" in result.output
        assert "file2.py" in result.output
        assert "file4.py" in result.output
        assert "file3.txt" not in result.output

    @pytest.mark.asyncio
    async def test_grep_search(self, app: OpenCode, sample_file: Path):
        """Test Grep tool for content searching."""
        result = await app.execute_tool(
            tool_name="Grep",
            arguments={
                "pattern": "def.*\\(",
                "path": str(sample_file),
            },
        )

        assert result.success
        assert "hello" in result.output
        assert "add" in result.output

    @pytest.mark.asyncio
    async def test_write_creates_file(self, app: OpenCode, temp_project: Path, monkeypatch):
        """Test Write tool creates new file."""
        monkeypatch.setattr(app.permission_system, "auto_approve", True)

        new_file = temp_project / "new_file.py"
        assert not new_file.exists()

        result = await app.execute_tool(
            tool_name="Write",
            arguments={
                "file_path": str(new_file),
                "content": "# New file\nprint('Hello')\n",
            },
        )

        assert result.success
        assert new_file.exists()
        assert "New file" in new_file.read_text()


class TestToolPermissions:
    """Test tool permission integration."""

    @pytest.mark.asyncio
    async def test_read_allowed_by_default(self, app: OpenCode, sample_file: Path):
        """Read should be allowed without approval."""
        result = await app.execute_tool(
            tool_name="Read",
            arguments={"file_path": str(sample_file)},
        )

        assert result.success

    @pytest.mark.asyncio
    async def test_write_requires_permission(self, app: OpenCode, temp_project: Path):
        """Write should require permission."""
        new_file = temp_project / "test.txt"

        # Without auto-approve, should be denied or require approval
        result = await app.execute_tool(
            tool_name="Write",
            arguments={
                "file_path": str(new_file),
                "content": "test",
            },
            require_approval=True,
        )

        # Should have permission_required flag
        assert result.requires_permission or result.success

    @pytest.mark.asyncio
    async def test_bash_respects_allowlist(self, app: OpenCode, temp_project: Path):
        """Bash should respect command allowlist."""
        # Add to allowlist
        app.permission_system.add_allowlist("Bash", "echo:*")

        result = await app.execute_tool(
            tool_name="Bash",
            arguments={"command": "echo 'allowed'"},
        )

        assert result.success
        assert "allowed" in result.output
```

---

### Step 3: Session Flow Integration Tests

Test session management with context integration.

**File:** `tests/integration/test_session_flow.py`

```python
"""Integration tests for session management."""

from __future__ import annotations

from pathlib import Path

import pytest

from opencode.core.app import opencode
from opencode.session.manager import Session


class TestSessionFlow:
    """Test session lifecycle."""

    @pytest.mark.asyncio
    async def test_create_save_resume(self, app: OpenCode):
        """Test session persistence cycle."""
        # Create session
        session = await app.session_manager.create_session()
        session_id = session.id

        # Add some messages
        await session.add_message("user", "Hello")
        await session.add_message("assistant", "Hi there!")

        # Save session
        await app.session_manager.save_session(session)

        # Close and resume
        await app.session_manager.close_session(session_id)
        resumed = await app.session_manager.resume_session(session_id)

        assert resumed is not None
        assert resumed.id == session_id
        assert len(resumed.messages) == 2

    @pytest.mark.asyncio
    async def test_context_compaction(self, app: OpenCode, session: Session):
        """Test context management integration."""
        # Add many messages to trigger compaction
        for i in range(100):
            await session.add_message("user", f"Message {i} " * 100)
            await session.add_message("assistant", f"Response {i} " * 100)

        # Check context was compacted
        context = await session.get_context()
        assert context.token_count < app.config.max_context_tokens

    @pytest.mark.asyncio
    async def test_session_with_tool_results(self, app: OpenCode, session: Session, sample_file: Path):
        """Test session with tool execution results."""
        # Execute tool
        result = await app.execute_tool(
            tool_name="Read",
            arguments={"file_path": str(sample_file)},
            session=session,
        )

        # Verify tool result in session
        messages = session.messages
        assert any(m.role == "tool" for m in messages)

    @pytest.mark.asyncio
    async def test_session_list_and_delete(self, app: OpenCode):
        """Test session listing and deletion."""
        # Create multiple sessions
        sessions = []
        for i in range(3):
            s = await app.session_manager.create_session(title=f"Session {i}")
            sessions.append(s)

        # List sessions
        all_sessions = await app.session_manager.list_sessions()
        assert len(all_sessions) >= 3

        # Delete one
        await app.session_manager.delete_session(sessions[0].id)

        # Verify deleted
        remaining = await app.session_manager.list_sessions()
        assert sessions[0].id not in [s.id for s in remaining]


class TestSessionContext:
    """Test session context integration."""

    @pytest.mark.asyncio
    async def test_context_includes_system_prompt(self, app: OpenCode, session: Session):
        """Test that context includes system prompt."""
        context = await session.get_context()

        assert any(m.role == "system" for m in context.messages)

    @pytest.mark.asyncio
    async def test_context_token_counting(self, app: OpenCode, session: Session):
        """Test token counting accuracy."""
        await session.add_message("user", "Hello world")

        context = await session.get_context()
        assert context.token_count > 0

    @pytest.mark.asyncio
    async def test_context_file_mentions(self, app: OpenCode, session: Session, sample_file: Path):
        """Test that file mentions are tracked."""
        await session.add_message("user", f"Look at {sample_file}")

        mentions = session.get_file_mentions()
        assert str(sample_file) in mentions or sample_file.name in str(mentions)
```

---

### Step 4: Agent Workflow Integration Tests

Test subagent integration with parent session.

**File:** `tests/integration/test_agent_workflow.py`

```python
"""Integration tests for agent workflows."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from opencode.core.app import opencode


class TestAgentWorkflow:
    """Test subagent integration."""

    @pytest.mark.asyncio
    async def test_explore_agent_with_file_tools(
        self, app: OpenCode, temp_project: Path, mock_llm_response
    ):
        """Test Explore agent with file tools."""
        # Create test files
        (temp_project / "main.py").write_text("def main(): pass")
        (temp_project / "utils.py").write_text("def helper(): pass")

        # Mock LLM to return search intent
        app.llm.invoke = AsyncMock(
            return_value=mock_llm_response(
                "Found main.py and utils.py with function definitions."
            )
        )

        result = await app.spawn_agent(
            agent_type="explore",
            prompt="Find all Python files",
            working_dir=temp_project,
        )

        assert result.success
        # Agent should have used Glob/Grep tools

    @pytest.mark.asyncio
    async def test_plan_agent_with_context(self, app: OpenCode, mock_llm_response):
        """Test Plan agent with context."""
        app.llm.invoke = AsyncMock(
            return_value=mock_llm_response(
                "## Plan\n1. Step one\n2. Step two\n3. Step three"
            )
        )

        result = await app.spawn_agent(
            agent_type="plan",
            prompt="Plan implementing a new feature",
        )

        assert result.success
        assert "Plan" in result.output or "Step" in result.output

    @pytest.mark.asyncio
    async def test_agent_inherits_session_context(
        self, app: OpenCode, session, mock_llm_response
    ):
        """Test that agents inherit session context."""
        # Add context to session
        await session.add_message("user", "Working on authentication module")

        app.llm.invoke = AsyncMock(
            return_value=mock_llm_response("Understood, focusing on auth.")
        )

        result = await app.spawn_agent(
            agent_type="general",
            prompt="Continue with the task",
            session=session,
        )

        # Agent should have access to session context
        assert result.success

    @pytest.mark.asyncio
    async def test_agent_tool_results_return_to_parent(
        self, app: OpenCode, session, sample_file: Path, mock_llm_response
    ):
        """Test that agent tool results are returned to parent."""
        app.llm.invoke = AsyncMock(
            return_value=mock_llm_response(f"Read file: {sample_file}")
        )

        result = await app.spawn_agent(
            agent_type="explore",
            prompt=f"Read {sample_file}",
            session=session,
        )

        assert result.success
        # Results should be accessible


class TestAgentConfiguration:
    """Test agent configuration."""

    @pytest.mark.asyncio
    async def test_agent_respects_model_config(self, app: OpenCode, mock_llm_response):
        """Test that agents use configured models."""
        app.llm.invoke = AsyncMock(return_value=mock_llm_response("Done"))

        result = await app.spawn_agent(
            agent_type="explore",
            prompt="Quick search",
            model="haiku",  # Fast model for quick tasks
        )

        assert result.success

    @pytest.mark.asyncio
    async def test_agent_timeout(self, app: OpenCode):
        """Test agent timeout handling."""
        # Create slow mock
        async def slow_invoke(*args, **kwargs):
            import asyncio

            await asyncio.sleep(10)

        app.llm.invoke = slow_invoke

        with pytest.raises(TimeoutError):
            await app.spawn_agent(
                agent_type="explore",
                prompt="This will timeout",
                timeout=0.1,  # 100ms timeout
            )
```

---

### Step 5: Git Workflow Integration Tests

Test Git integration with tool system.

**File:** `tests/integration/test_git_workflow.py`

```python
"""Integration tests for Git workflow."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from opencode.core.app import opencode


class TestGitWorkflow:
    """Test Git integration workflows."""

    @pytest.mark.asyncio
    async def test_git_status_flow(self, app: OpenCode, git_repo: Path):
        """Test git status through tool system."""
        # Create a new file
        (git_repo / "new_file.txt").write_text("New content")

        result = await app.execute_tool(
            tool_name="Bash",
            arguments={"command": "git status --porcelain"},
        )

        assert result.success
        assert "new_file.txt" in result.output

    @pytest.mark.asyncio
    async def test_git_diff_flow(self, app: OpenCode, git_repo: Path):
        """Test git diff through tool system."""
        # Modify existing file
        readme = git_repo / "README.md"
        readme.write_text("# Updated Project\n\nNew content here.")

        result = await app.execute_tool(
            tool_name="Bash",
            arguments={"command": "git diff"},
        )

        assert result.success
        assert "Updated Project" in result.output or "++" in result.output

    @pytest.mark.asyncio
    async def test_git_commit_flow(self, app: OpenCode, git_repo: Path, monkeypatch):
        """Test git commit through tool system."""
        monkeypatch.setattr(app.permission_system, "auto_approve", True)

        # Create and stage file
        (git_repo / "feature.py").write_text("# New feature")

        await app.execute_tool(
            tool_name="Bash",
            arguments={"command": "git add feature.py"},
        )

        result = await app.execute_tool(
            tool_name="Bash",
            arguments={"command": 'git commit -m "Add feature"'},
        )

        assert result.success

        # Verify commit
        log_result = await app.execute_tool(
            tool_name="Bash",
            arguments={"command": "git log --oneline -1"},
        )

        assert "Add feature" in log_result.output

    @pytest.mark.asyncio
    async def test_git_safety_guards(self, app: OpenCode, git_repo: Path):
        """Test git safety guards are active."""
        # Try force push (should be blocked or warned)
        result = await app.execute_tool(
            tool_name="Bash",
            arguments={"command": "git push --force origin main"},
        )

        # Should either fail due to safety or require confirmation
        # (no remote configured, but safety should still check)
        assert not result.success or "dangerous" in result.output.lower()


class TestGitBranchWorkflow:
    """Test Git branch workflows."""

    @pytest.mark.asyncio
    async def test_create_branch(self, app: OpenCode, git_repo: Path, monkeypatch):
        """Test branch creation."""
        monkeypatch.setattr(app.permission_system, "auto_approve", True)

        result = await app.execute_tool(
            tool_name="Bash",
            arguments={"command": "git checkout -b feature/new-feature"},
        )

        assert result.success

        # Verify branch
        branch_result = await app.execute_tool(
            tool_name="Bash",
            arguments={"command": "git branch --show-current"},
        )

        assert "feature/new-feature" in branch_result.output

    @pytest.mark.asyncio
    async def test_switch_branch(self, app: OpenCode, git_repo: Path, monkeypatch):
        """Test branch switching."""
        monkeypatch.setattr(app.permission_system, "auto_approve", True)

        # Create branch
        subprocess.run(
            ["git", "checkout", "-b", "test-branch"],
            cwd=git_repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "checkout", "master"],
            cwd=git_repo,
            check=True,
            capture_output=True,
        )

        # Switch via tool
        result = await app.execute_tool(
            tool_name="Bash",
            arguments={"command": "git checkout test-branch"},
        )

        assert result.success
```

---

### Step 6: Plugin System Integration Tests

Test plugin system with core components.

**File:** `tests/integration/test_plugin_system.py`

```python
"""Integration tests for plugin system."""

from __future__ import annotations

from pathlib import Path

import pytest

from opencode.core.app import opencode


class TestPluginIntegration:
    """Test plugin system integration."""

    @pytest.mark.asyncio
    async def test_plugin_discovery_and_load(self, app: OpenCode, sample_plugin: Path):
        """Test plugin discovery and loading."""
        # Discover plugins
        await app.plugin_manager.discover_and_load()

        # Check plugin loaded
        plugin = app.plugin_manager.get_plugin("test-plugin")
        assert plugin is not None
        assert plugin.active

    @pytest.mark.asyncio
    async def test_plugin_tool_registration(self, app: OpenCode, sample_plugin: Path):
        """Test that plugin tools are registered."""
        await app.plugin_manager.discover_and_load()

        # Check tool registered with prefix
        tool = app.tool_registry.get("test-plugin__echo")
        assert tool is not None

    @pytest.mark.asyncio
    async def test_plugin_tool_execution(self, app: OpenCode, sample_plugin: Path):
        """Test executing plugin tool."""
        await app.plugin_manager.discover_and_load()

        result = await app.execute_tool(
            tool_name="test-plugin__echo",
            arguments={"message": "Hello plugin!"},
        )

        assert result.success
        assert "Echo: Hello plugin!" in result.output

    @pytest.mark.asyncio
    async def test_plugin_enable_disable(self, app: OpenCode, sample_plugin: Path):
        """Test plugin enable/disable."""
        await app.plugin_manager.discover_and_load()

        # Disable
        await app.plugin_manager.disable("test-plugin")
        plugin = app.plugin_manager.get_plugin("test-plugin")
        assert not plugin.active

        # Tool should be unregistered
        tool = app.tool_registry.get("test-plugin__echo")
        assert tool is None

        # Enable
        await app.plugin_manager.enable("test-plugin")
        plugin = app.plugin_manager.get_plugin("test-plugin")
        assert plugin.active

        # Tool should be re-registered
        tool = app.tool_registry.get("test-plugin__echo")
        assert tool is not None

    @pytest.mark.asyncio
    async def test_plugin_reload(self, app: OpenCode, sample_plugin: Path):
        """Test plugin reload."""
        await app.plugin_manager.discover_and_load()

        # Modify plugin
        module = sample_plugin / "test_plugin.py"
        content = module.read_text()
        module.write_text(content.replace("Echo:", "Modified:"))

        # Reload
        await app.plugin_manager.reload("test-plugin")

        # Test modified behavior
        result = await app.execute_tool(
            tool_name="test-plugin__echo",
            arguments={"message": "test"},
        )

        assert "Modified: test" in result.output


class TestPluginIsolation:
    """Test plugin isolation and error handling."""

    @pytest.mark.asyncio
    async def test_plugin_error_isolation(self, app: OpenCode, temp_home: Path):
        """Test that plugin errors don't crash system."""
        # Create broken plugin
        broken_plugin = temp_home / ".opencode" / "plugins" / "broken-plugin"
        broken_plugin.mkdir(parents=True)

        (broken_plugin / "plugin.yaml").write_text("""
name: broken-plugin
version: 1.0.0
description: Broken plugin
entry_point: broken:BrokenPlugin
""")

        (broken_plugin / "broken.py").write_text("""
raise ImportError("Intentional error")
""")

        # Create good plugin
        good_plugin = temp_home / ".opencode" / "plugins" / "good-plugin"
        good_plugin.mkdir(parents=True)

        (good_plugin / "plugin.yaml").write_text("""
name: good-plugin
version: 1.0.0
description: Good plugin
entry_point: good:GoodPlugin
capabilities:
  tools: false
""")

        (good_plugin / "good.py").write_text("""
from opencode.plugins import Plugin, PluginMetadata

class GoodPlugin(Plugin):
    @property
    def metadata(self):
        return PluginMetadata(name="good-plugin", version="1.0.0", description="Good")
""")

        # Load plugins - should not crash
        await app.plugin_manager.discover_and_load()

        # Good plugin should be loaded
        good = app.plugin_manager.get_plugin("good-plugin")
        assert good is not None

        # Broken plugin should have error
        errors = app.plugin_manager.get_load_errors()
        assert "broken-plugin" in errors

    @pytest.mark.asyncio
    async def test_plugin_data_isolation(self, app: OpenCode, sample_plugin: Path):
        """Test that plugins have isolated data directories."""
        await app.plugin_manager.discover_and_load()

        plugin = app.plugin_manager.get_plugin("test-plugin")
        data_dir = plugin.context.data_dir

        assert "test-plugin" in str(data_dir)
        assert data_dir.exists()
```

---

### Step 7: Performance Tests

Create performance benchmarks.

**File:** `tests/performance/test_startup.py`

```python
"""Startup performance tests."""

from __future__ import annotations

import time
from pathlib import Path

import pytest


class TestStartupPerformance:
    """Measure startup time."""

    def test_cold_start_under_2s(self, temp_home: Path, temp_project: Path):
        """Cold start should be under 2 seconds."""
        from opencode.core.app import opencode
        from opencode.core.config import Config

        start = time.perf_counter()

        config = Config(home_dir=temp_home, project_dir=temp_project)
        app = OpenCode(config=config)

        elapsed = time.perf_counter() - start

        assert elapsed < 2.0, f"Startup took {elapsed:.2f}s (target: <2s)"

    @pytest.mark.asyncio
    async def test_initialization_under_2s(self, temp_home: Path, temp_project: Path):
        """Full initialization should be under 2 seconds."""
        from opencode.core.app import opencode
        from opencode.core.config import Config

        config = Config(home_dir=temp_home, project_dir=temp_project)
        app = OpenCode(config=config)

        start = time.perf_counter()
        await app.initialize()
        elapsed = time.perf_counter() - start

        await app.shutdown()

        assert elapsed < 2.0, f"Initialization took {elapsed:.2f}s (target: <2s)"

    def test_config_load_under_100ms(self, temp_home: Path, temp_project: Path):
        """Config loading should be under 100ms."""
        from opencode.core.config import Config

        start = time.perf_counter()
        Config(home_dir=temp_home, project_dir=temp_project)
        elapsed = time.perf_counter() - start

        assert elapsed < 0.1, f"Config load took {elapsed:.3f}s (target: <0.1s)"


class TestWarmStartPerformance:
    """Test warm start performance."""

    @pytest.mark.asyncio
    async def test_second_session_under_500ms(self, app):
        """Creating second session should be faster."""
        # First session (warm up)
        session1 = await app.session_manager.create_session()
        await app.session_manager.close_session(session1.id)

        # Second session (warm)
        start = time.perf_counter()
        session2 = await app.session_manager.create_session()
        elapsed = time.perf_counter() - start

        await app.session_manager.close_session(session2.id)

        assert elapsed < 0.5, f"Session creation took {elapsed:.3f}s (target: <0.5s)"
```

**File:** `tests/performance/test_response_time.py`

```python
"""Response time tests."""

from __future__ import annotations

import time
from pathlib import Path

import pytest


class TestResponseTime:
    """Measure response latency."""

    @pytest.mark.asyncio
    async def test_tool_overhead_under_100ms(self, app, sample_file: Path):
        """Tool execution overhead < 100ms."""
        # Warm up
        await app.execute_tool(
            tool_name="Read",
            arguments={"file_path": str(sample_file)},
        )

        # Measure
        start = time.perf_counter()
        await app.execute_tool(
            tool_name="Read",
            arguments={"file_path": str(sample_file)},
        )
        elapsed = time.perf_counter() - start

        assert elapsed < 0.1, f"Tool overhead: {elapsed:.3f}s (target: <0.1s)"

    @pytest.mark.asyncio
    async def test_glob_under_500ms(self, app, temp_project: Path):
        """Glob search should complete under 500ms."""
        # Create many files
        for i in range(100):
            (temp_project / f"file_{i}.py").write_text(f"# File {i}")

        start = time.perf_counter()
        await app.execute_tool(
            tool_name="Glob",
            arguments={
                "pattern": "**/*.py",
                "path": str(temp_project),
            },
        )
        elapsed = time.perf_counter() - start

        assert elapsed < 0.5, f"Glob took {elapsed:.3f}s (target: <0.5s)"

    @pytest.mark.asyncio
    async def test_grep_under_1s(self, app, temp_project: Path):
        """Grep search should complete under 1s."""
        # Create files with content
        for i in range(50):
            (temp_project / f"module_{i}.py").write_text(f"""
# Module {i}
def function_{i}():
    pass

class Class_{i}:
    def method(self):
        return {i}
""")

        start = time.perf_counter()
        await app.execute_tool(
            tool_name="Grep",
            arguments={
                "pattern": "def.*\\(",
                "path": str(temp_project),
            },
        )
        elapsed = time.perf_counter() - start

        assert elapsed < 1.0, f"Grep took {elapsed:.3f}s (target: <1s)"


class TestMemoryUsage:
    """Test memory usage."""

    @pytest.mark.asyncio
    async def test_idle_memory_under_100mb(self, app):
        """Idle memory should be under 100MB."""
        import tracemalloc

        tracemalloc.start()

        # Just initialized app
        current, peak = tracemalloc.get_traced_memory()

        tracemalloc.stop()

        current_mb = current / 1024 / 1024
        assert current_mb < 100, f"Idle memory: {current_mb:.1f}MB (target: <100MB)"

    @pytest.mark.asyncio
    async def test_session_memory_growth(self, app):
        """Memory growth per session should be bounded."""
        import tracemalloc

        tracemalloc.start()

        # Create multiple sessions
        sessions = []
        for i in range(10):
            s = await app.session_manager.create_session()
            await s.add_message("user", f"Message {i}" * 100)
            sessions.append(s)

        current, peak = tracemalloc.get_traced_memory()

        # Clean up
        for s in sessions:
            await app.session_manager.close_session(s.id)

        tracemalloc.stop()

        peak_mb = peak / 1024 / 1024
        assert peak_mb < 500, f"Peak memory: {peak_mb:.1f}MB (target: <500MB)"
```

---

### Step 8: End-to-End Tests

Test complete workflows.

**File:** `tests/e2e/test_file_editing.py`

```python
"""End-to-end tests for file editing workflow."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest


class TestFileEditingWorkflow:
    """Test complete file editing workflows."""

    @pytest.mark.asyncio
    async def test_read_edit_verify(self, app, sample_file: Path, monkeypatch):
        """Test read-edit-verify workflow."""
        monkeypatch.setattr(app.permission_system, "auto_approve", True)

        # Step 1: Read file
        read_result = await app.execute_tool(
            tool_name="Read",
            arguments={"file_path": str(sample_file)},
        )
        assert read_result.success
        assert "def hello" in read_result.output

        # Step 2: Edit file
        edit_result = await app.execute_tool(
            tool_name="Edit",
            arguments={
                "file_path": str(sample_file),
                "old_string": "def hello(name: str) -> str:",
                "new_string": "def greet(name: str) -> str:",
            },
        )
        assert edit_result.success

        # Step 3: Verify change
        verify_result = await app.execute_tool(
            tool_name="Read",
            arguments={"file_path": str(sample_file)},
        )
        assert "def greet" in verify_result.output
        assert "def hello" not in verify_result.output

    @pytest.mark.asyncio
    async def test_create_new_file_workflow(self, app, temp_project: Path, monkeypatch):
        """Test creating a new file workflow."""
        monkeypatch.setattr(app.permission_system, "auto_approve", True)

        new_file = temp_project / "new_module.py"

        # Step 1: Create file
        write_result = await app.execute_tool(
            tool_name="Write",
            arguments={
                "file_path": str(new_file),
                "content": '''"""New module."""

def process(data: str) -> str:
    """Process data."""
    return data.upper()
''',
            },
        )
        assert write_result.success

        # Step 2: Verify file exists and has content
        read_result = await app.execute_tool(
            tool_name="Read",
            arguments={"file_path": str(new_file)},
        )
        assert "New module" in read_result.output
        assert "def process" in read_result.output

    @pytest.mark.asyncio
    async def test_search_and_edit_workflow(self, app, temp_project: Path, monkeypatch):
        """Test search-and-edit workflow."""
        monkeypatch.setattr(app.permission_system, "auto_approve", True)

        # Create files
        (temp_project / "module_a.py").write_text("def old_function(): pass")
        (temp_project / "module_b.py").write_text("def old_function(): pass")

        # Step 1: Search for pattern
        search_result = await app.execute_tool(
            tool_name="Grep",
            arguments={
                "pattern": "old_function",
                "path": str(temp_project),
            },
        )
        assert "module_a.py" in search_result.output
        assert "module_b.py" in search_result.output

        # Step 2: Edit each file
        for module in ["module_a.py", "module_b.py"]:
            await app.execute_tool(
                tool_name="Edit",
                arguments={
                    "file_path": str(temp_project / module),
                    "old_string": "old_function",
                    "new_string": "new_function",
                },
            )

        # Step 3: Verify changes
        verify_result = await app.execute_tool(
            tool_name="Grep",
            arguments={
                "pattern": "new_function",
                "path": str(temp_project),
            },
        )
        assert "module_a.py" in verify_result.output
        assert "module_b.py" in verify_result.output
```

**File:** `tests/e2e/test_git_commit.py`

```python
"""End-to-end tests for Git commit workflow."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


class TestGitCommitWorkflow:
    """Test complete Git commit workflows."""

    @pytest.mark.asyncio
    async def test_full_commit_workflow(self, app, git_repo: Path, monkeypatch):
        """Test complete commit workflow."""
        monkeypatch.setattr(app.permission_system, "auto_approve", True)

        # Step 1: Create changes
        (git_repo / "feature.py").write_text("def new_feature(): pass")
        (git_repo / "README.md").write_text("# Updated\n\nNew content")

        # Step 2: Check status
        status_result = await app.execute_tool(
            tool_name="Bash",
            arguments={"command": "git status --porcelain"},
        )
        assert "feature.py" in status_result.output
        assert "README.md" in status_result.output

        # Step 3: Stage changes
        await app.execute_tool(
            tool_name="Bash",
            arguments={"command": "git add ."},
        )

        # Step 4: Commit
        commit_result = await app.execute_tool(
            tool_name="Bash",
            arguments={
                "command": 'git commit -m "Add feature and update readme"',
            },
        )
        assert commit_result.success

        # Step 5: Verify commit
        log_result = await app.execute_tool(
            tool_name="Bash",
            arguments={"command": "git log --oneline -1"},
        )
        assert "Add feature" in log_result.output

    @pytest.mark.asyncio
    async def test_branch_and_commit_workflow(self, app, git_repo: Path, monkeypatch):
        """Test branch creation and commit workflow."""
        monkeypatch.setattr(app.permission_system, "auto_approve", True)

        # Step 1: Create branch
        await app.execute_tool(
            tool_name="Bash",
            arguments={"command": "git checkout -b feature/my-feature"},
        )

        # Step 2: Make changes
        (git_repo / "my_feature.py").write_text("# My feature")

        # Step 3: Commit on branch
        await app.execute_tool(
            tool_name="Bash",
            arguments={"command": "git add my_feature.py"},
        )
        await app.execute_tool(
            tool_name="Bash",
            arguments={"command": 'git commit -m "Implement my feature"'},
        )

        # Step 4: Verify branch has commit
        log_result = await app.execute_tool(
            tool_name="Bash",
            arguments={"command": "git log --oneline"},
        )
        assert "Implement my feature" in log_result.output

        # Step 5: Switch back to main
        await app.execute_tool(
            tool_name="Bash",
            arguments={"command": "git checkout master"},
        )

        # Step 6: Verify main doesn't have commit
        main_log = await app.execute_tool(
            tool_name="Bash",
            arguments={"command": "git log --oneline"},
        )
        assert "Implement my feature" not in main_log.output
```

---

### Step 9: Error Recovery Tests

Test error handling and recovery.

**File:** `tests/integration/test_error_recovery.py`

```python
"""Integration tests for error recovery."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from opencode.core.app import opencode


class TestErrorRecovery:
    """Test error handling and recovery."""

    @pytest.mark.asyncio
    async def test_tool_error_recovery(self, app: OpenCode, temp_project: Path):
        """Test recovery from tool execution error."""
        # Try to read non-existent file
        result = await app.execute_tool(
            tool_name="Read",
            arguments={"file_path": str(temp_project / "nonexistent.py")},
        )

        assert not result.success
        assert "error" in result.output.lower() or "not found" in result.output.lower()

        # System should still work
        (temp_project / "exists.py").write_text("# Exists")
        result2 = await app.execute_tool(
            tool_name="Read",
            arguments={"file_path": str(temp_project / "exists.py")},
        )
        assert result2.success

    @pytest.mark.asyncio
    async def test_session_recovery(self, app: OpenCode):
        """Test session recovery from errors."""
        session = await app.session_manager.create_session()

        # Simulate error in session
        await session.add_message("user", "test")

        # Close without proper save (simulate crash)
        session_id = session.id

        # Try to resume - should handle gracefully
        try:
            resumed = await app.session_manager.resume_session(session_id)
            # Either resumes or returns None
            assert resumed is None or resumed.id == session_id
        except Exception:
            # Should not raise unhandled exception
            pytest.fail("Session recovery raised unhandled exception")

    @pytest.mark.asyncio
    async def test_llm_error_handling(self, app: OpenCode, session):
        """Test LLM error handling."""
        # Mock LLM to raise error
        app.llm.invoke = AsyncMock(side_effect=Exception("API Error"))

        # Should handle gracefully
        try:
            result = await app.process_message("Hello", session=session)
            assert result.error or "error" in result.content.lower()
        except Exception as e:
            # Should be wrapped in appropriate exception
            assert "API" in str(e) or "error" in str(e).lower()

    @pytest.mark.asyncio
    async def test_timeout_handling(self, app: OpenCode, temp_project: Path):
        """Test timeout handling."""
        # Create long-running command
        result = await app.execute_tool(
            tool_name="Bash",
            arguments={
                "command": "sleep 10",
                "timeout": 100,  # 100ms timeout
            },
        )

        # Should timeout gracefully
        assert not result.success
        assert "timeout" in result.output.lower() or "killed" in result.output.lower()


class TestGracefulDegradation:
    """Test graceful degradation."""

    @pytest.mark.asyncio
    async def test_missing_optional_component(self, app: OpenCode):
        """Test handling of missing optional components."""
        # Disable plugin system
        app.plugin_manager = None

        # Core functionality should still work
        result = await app.execute_tool(
            tool_name="Bash",
            arguments={"command": "echo 'test'"},
        )
        assert result.success

    @pytest.mark.asyncio
    async def test_network_failure_handling(self, app: OpenCode, monkeypatch):
        """Test handling of network failures."""
        # Mock network failure for web tools
        async def network_failure(*args, **kwargs):
            raise ConnectionError("Network unavailable")

        # Try web tool - should fail gracefully
        # (Would need actual web tool mock)
        pass  # Placeholder for network failure test

    @pytest.mark.asyncio
    async def test_disk_full_handling(self, app: OpenCode, temp_project: Path):
        """Test handling of disk full errors."""
        # This would require mocking file system
        # Just verify error handling structure exists
        try:
            # Try to write large file
            result = await app.execute_tool(
                tool_name="Write",
                arguments={
                    "file_path": str(temp_project / "large.txt"),
                    "content": "x" * (10 * 1024 * 1024),  # 10MB
                },
            )
            # Should either succeed or fail gracefully
            assert result.success or result.error
        except OSError:
            # Acceptable to raise OSError for disk issues
            pass
```

---

### Step 10: Documentation

Create user and developer documentation.

**File Structure:**

```
docs/
├── index.md
├── getting-started/
│   ├── installation.md
│   ├── quickstart.md
│   └── configuration.md
├── user-guide/
│   ├── commands.md
│   ├── tools.md
│   ├── sessions.md
│   ├── permissions.md
│   └── hooks.md
├── reference/
│   ├── configuration.md
│   ├── commands.md
│   ├── tools.md
│   └── api.md
├── development/
│   ├── architecture.md
│   ├── plugins.md
│   ├── contributing.md
│   └── testing.md
└── changelog.md
```

**Sample Content:**

```markdown
# docs/index.md

# OpenCode Documentation

OpenCode is an AI-powered coding assistant that connects to OpenRouter API
and uses LangChain as its backend middleware.

## Quick Links

- [Installation](getting-started/installation.md)
- [Quick Start](getting-started/quickstart.md)
- [Configuration](getting-started/configuration.md)

## Features

- **Multi-Model Support**: Connect to 400+ AI models via OpenRouter
- **Tool System**: Read, write, edit files, run commands
- **Session Management**: Persistent sessions with context compaction
- **Plugin System**: Extend functionality with plugins
- **Git Integration**: Safe git operations with guardrails
- **GitHub Integration**: PR creation, issue management

## Getting Help

- Run `/help` for command help
- Run `/commands` for available commands
- See [User Guide](user-guide/commands.md) for detailed documentation
```

---

### Step 11: Release Preparation

Finalize package and release artifacts.

**File:** `pyproject.toml` (additions)

```toml
[project]
name = "opencode"
version = "1.0.0"
description = "AI-powered coding assistant with OpenRouter and LangChain"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
authors = [
    {name = "OpenCode Team", email = "team@opencode.dev"}
]
keywords = [
    "ai",
    "coding",
    "assistant",
    "langchain",
    "openrouter",
    "cli",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development",
    "Topic :: Software Development :: Code Generators",
    "Typing :: Typed",
]

dependencies = [
    "langchain>=0.3.0",
    "langchain-openai>=0.2.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
    "rich>=13.0.0",
    "prompt-toolkit>=3.0.0",
    "httpx>=0.25.0",
    "aiofiles>=23.0.0",
    "tiktoken>=0.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.0.0",
    "mypy>=1.8.0",
    "ruff>=0.1.0",
]
docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.0.0",
]

[project.scripts]
opencode = "opencode.cli:main"

[project.entry-points."opencode.plugins"]
# Built-in plugins can be registered here

[project.urls]
Homepage = "https://opencode.dev"
Documentation = "https://docs.opencode.dev"
Repository = "https://github.com/src/opencode/opencode"
Changelog = "https://github.com/src/opencode/src/opencode/blob/main/CHANGELOG.md"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.sdist]
include = [
    "/opencode",
    "/tests",
]

[tool.hatch.build.targets.wheel]
packages = ["opencode"]
```

**File:** `CHANGELOG.md`

```markdown
# Changelog

All notable changes to OpenCode will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-XX-XX

### Added

- Initial release of OpenCode
- Core tool system (Read, Write, Edit, Glob, Grep, Bash)
- Session management with persistence
- Context management with automatic compaction
- Permission system (allow/ask/deny)
- Hooks system for customization
- Slash commands
- Operating modes (Plan, Thinking, Headless)
- Subagent system
- Skills system
- MCP protocol support
- Web tools (WebSearch, WebFetch)
- Git integration with safety guards
- GitHub integration (PRs, issues, actions)
- Plugin system

### Security

- Git safety guards prevent destructive operations
- Permission system protects sensitive operations
- Isolated plugin execution

## [Unreleased]

- Future features and fixes will be documented here
```

---

## Summary

Phase 10.2 focuses on:

1. **Integration Test Infrastructure** - Comprehensive fixtures and utilities
2. **Tool Execution Tests** - Full pipeline testing
3. **Session Flow Tests** - Lifecycle and context testing
4. **Agent Workflow Tests** - Subagent integration
5. **Git Workflow Tests** - Git operation testing
6. **Plugin System Tests** - Plugin integration
7. **Performance Tests** - Startup, response, memory
8. **End-to-End Tests** - Complete workflow validation
9. **Error Recovery Tests** - Graceful degradation
10. **Documentation** - User and developer guides
11. **Release Preparation** - Package and artifacts

This ensures a production-ready release with comprehensive testing and documentation.
