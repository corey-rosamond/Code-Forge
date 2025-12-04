"""Tests for GlobTool."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from opencode.tools.base import ExecutionContext
from opencode.tools.file.glob import GlobTool


@pytest.fixture
def glob_tool() -> GlobTool:
    """Create a GlobTool instance."""
    return GlobTool()


@pytest.fixture
def context(tmp_path: Path) -> ExecutionContext:
    """Create an execution context."""
    return ExecutionContext(working_dir=str(tmp_path))


@pytest.fixture
def sample_directory(tmp_path: Path) -> Path:
    """Create a sample directory structure."""
    # Create directory structure
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("main code")
    (tmp_path / "src" / "utils.py").write_text("utils code")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("tests")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "README.md").write_text("readme")
    (tmp_path / "config.json").write_text("{}")
    (tmp_path / "setup.py").write_text("setup")
    return tmp_path


class TestGlobToolProperties:
    """Test GlobTool properties."""

    def test_name(self, glob_tool: GlobTool) -> None:
        assert glob_tool.name == "Glob"

    def test_description(self, glob_tool: GlobTool) -> None:
        assert "pattern" in glob_tool.description.lower()
        assert "**/*.js" in glob_tool.description

    def test_category(self, glob_tool: GlobTool) -> None:
        from opencode.tools.base import ToolCategory

        assert glob_tool.category == ToolCategory.FILE

    def test_parameters(self, glob_tool: GlobTool) -> None:
        params = glob_tool.parameters
        param_names = [p.name for p in params]
        assert "pattern" in param_names
        assert "path" in param_names


class TestGlobToolBasicPatterns:
    """Test basic glob patterns."""

    @pytest.mark.asyncio
    async def test_find_all_python_files(
        self, glob_tool: GlobTool, context: ExecutionContext, sample_directory: Path
    ) -> None:
        result = await glob_tool.execute(
            context, pattern="**/*.py", path=str(sample_directory)
        )
        assert result.success
        assert "main.py" in result.output
        assert "utils.py" in result.output
        assert "test_main.py" in result.output
        assert "setup.py" in result.output
        assert result.metadata["count"] == 4

    @pytest.mark.asyncio
    async def test_find_files_in_directory(
        self, glob_tool: GlobTool, context: ExecutionContext, sample_directory: Path
    ) -> None:
        result = await glob_tool.execute(
            context, pattern="src/*.py", path=str(sample_directory)
        )
        assert result.success
        assert "main.py" in result.output
        assert "utils.py" in result.output
        assert "test_main.py" not in result.output

    @pytest.mark.asyncio
    async def test_find_specific_file(
        self, glob_tool: GlobTool, context: ExecutionContext, sample_directory: Path
    ) -> None:
        result = await glob_tool.execute(
            context, pattern="**/README.md", path=str(sample_directory)
        )
        assert result.success
        assert "README.md" in result.output
        assert result.metadata["count"] == 1

    @pytest.mark.asyncio
    async def test_find_multiple_extensions(
        self, glob_tool: GlobTool, context: ExecutionContext, sample_directory: Path
    ) -> None:
        result = await glob_tool.execute(
            context, pattern="**/*.json", path=str(sample_directory)
        )
        assert result.success
        assert "config.json" in result.output


class TestGlobToolDefaultExcludes:
    """Test default exclude patterns."""

    @pytest.mark.asyncio
    async def test_exclude_node_modules(
        self, glob_tool: GlobTool, context: ExecutionContext, tmp_path: Path
    ) -> None:
        # Create node_modules
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "pkg" / "index.js").parent.mkdir(parents=True)
        (tmp_path / "node_modules" / "pkg" / "index.js").write_text("module")
        (tmp_path / "src" / "app.js").parent.mkdir(parents=True)
        (tmp_path / "src" / "app.js").write_text("app")

        result = await glob_tool.execute(
            context, pattern="**/*.js", path=str(tmp_path)
        )
        assert result.success
        assert "app.js" in result.output
        # Only app.js should be found, not the node_modules/pkg/index.js
        assert result.metadata["count"] == 1
        # Check that node_modules path component is not in any result
        assert "/node_modules/" not in result.output

    @pytest.mark.asyncio
    async def test_exclude_pycache(
        self, glob_tool: GlobTool, context: ExecutionContext, tmp_path: Path
    ) -> None:
        # Create __pycache__
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "module.cpython-311.pyc").write_bytes(b"")
        (tmp_path / "module.py").write_text("code")

        result = await glob_tool.execute(
            context, pattern="**/*", path=str(tmp_path)
        )
        assert result.success
        assert "__pycache__" not in result.output
        assert "module.py" in result.output

    @pytest.mark.asyncio
    async def test_exclude_pyc_files(
        self, glob_tool: GlobTool, context: ExecutionContext, tmp_path: Path
    ) -> None:
        (tmp_path / "module.py").write_text("code")
        (tmp_path / "module.pyc").write_bytes(b"bytecode")

        result = await glob_tool.execute(
            context, pattern="**/*", path=str(tmp_path)
        )
        assert result.success
        assert "module.py" in result.output
        assert ".pyc" not in result.output

    @pytest.mark.asyncio
    async def test_exclude_git_directory(
        self, glob_tool: GlobTool, context: ExecutionContext, tmp_path: Path
    ) -> None:
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("git config")
        (tmp_path / "file.txt").write_text("content")

        result = await glob_tool.execute(
            context, pattern="**/*", path=str(tmp_path)
        )
        assert result.success
        assert "file.txt" in result.output
        assert ".git" not in result.output

    @pytest.mark.asyncio
    async def test_exclude_venv(
        self, glob_tool: GlobTool, context: ExecutionContext, tmp_path: Path
    ) -> None:
        (tmp_path / ".venv" / "lib").mkdir(parents=True)
        (tmp_path / ".venv" / "lib" / "python.py").write_text("venv")
        (tmp_path / "app.py").write_text("app")

        result = await glob_tool.execute(
            context, pattern="**/*.py", path=str(tmp_path)
        )
        assert result.success
        assert "app.py" in result.output
        assert ".venv" not in result.output


class TestGlobToolSorting:
    """Test modification time sorting."""

    @pytest.mark.asyncio
    async def test_sorted_by_modification_time(
        self, glob_tool: GlobTool, context: ExecutionContext, tmp_path: Path
    ) -> None:
        # Create files with different modification times
        old_file = tmp_path / "old.txt"
        old_file.write_text("old content")
        time.sleep(0.1)
        new_file = tmp_path / "new.txt"
        new_file.write_text("new content")

        result = await glob_tool.execute(
            context, pattern="*.txt", path=str(tmp_path)
        )
        assert result.success
        # Newer file should come first
        lines = result.output.strip().split("\n")
        assert "new.txt" in lines[0]
        assert "old.txt" in lines[1]


class TestGlobToolNoMatches:
    """Test behavior when no files match."""

    @pytest.mark.asyncio
    async def test_no_matches(
        self, glob_tool: GlobTool, context: ExecutionContext, tmp_path: Path
    ) -> None:
        (tmp_path / "file.txt").write_text("content")
        result = await glob_tool.execute(
            context, pattern="**/*.xyz", path=str(tmp_path)
        )
        assert result.success
        assert "no matches" in result.output.lower()
        assert result.metadata["count"] == 0


class TestGlobToolErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_invalid_directory(
        self, glob_tool: GlobTool, context: ExecutionContext, tmp_path: Path
    ) -> None:
        result = await glob_tool.execute(
            context, pattern="*.txt", path=str(tmp_path / "nonexistent")
        )
        assert not result.success
        assert result.error is not None
        assert "not found" in result.error.lower()


class TestGlobToolResultLimit:
    """Test result limiting."""

    @pytest.mark.asyncio
    async def test_results_limited(
        self, glob_tool: GlobTool, context: ExecutionContext, tmp_path: Path
    ) -> None:
        # Create many files
        for i in range(10):
            (tmp_path / f"file{i:03d}.txt").write_text(f"content {i}")

        result = await glob_tool.execute(
            context, pattern="*.txt", path=str(tmp_path)
        )
        assert result.success
        assert result.metadata["count"] == 10


class TestGlobToolDefaultPath:
    """Test using default working directory."""

    @pytest.mark.asyncio
    async def test_uses_working_dir_when_no_path(
        self, glob_tool: GlobTool, sample_directory: Path
    ) -> None:
        context = ExecutionContext(working_dir=str(sample_directory))
        result = await glob_tool.execute(
            context, pattern="**/*.py"
        )
        assert result.success
        assert result.metadata["count"] == 4
        assert result.metadata["base_path"] == str(sample_directory)
