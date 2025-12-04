"""Glob tool implementation."""

from __future__ import annotations

import fnmatch
import glob as glob_module
import os
from pathlib import Path
from typing import Any, ClassVar

from opencode.tools.base import (
    BaseTool,
    ExecutionContext,
    ToolCategory,
    ToolParameter,
    ToolResult,
)


class GlobTool(BaseTool):
    """Find files matching a glob pattern.

    Returns files sorted by modification time (newest first).
    """

    # Patterns to exclude by default
    DEFAULT_EXCLUDES: ClassVar[set[str]] = {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".env",
        "dist",
        "build",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "*.pyc",
        "*.pyo",
    }

    MAX_RESULTS: ClassVar[int] = 1000

    @property
    def name(self) -> str:
        return "Glob"

    @property
    def description(self) -> str:
        return """Fast file pattern matching tool that works with any codebase size.

Usage:
- Supports glob patterns like "**/*.js" or "src/**/*.ts"
- Returns matching file paths sorted by modification time
- Use this tool when you need to find files by name patterns
- For content search, use Grep tool instead"""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.FILE

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="pattern",
                type="string",
                description="The glob pattern to match files against",
                required=True,
                min_length=1,
            ),
            ToolParameter(
                name="path",
                type="string",
                description="The directory to search in. "
                "Defaults to current working directory.",
                required=False,
            ),
        ]

    async def _execute(
        self, context: ExecutionContext, **kwargs: Any
    ) -> ToolResult:
        pattern = kwargs["pattern"]
        base_path = kwargs.get("path") or context.working_dir

        # Validate base path
        if not os.path.isdir(base_path):
            return ToolResult.fail(f"Directory not found: {base_path}")

        try:
            # Build full pattern
            if os.path.isabs(pattern):
                full_pattern = pattern
            else:
                full_pattern = os.path.join(base_path, pattern)

            # Find matching files
            matches = glob_module.glob(full_pattern, recursive=True)

            # Filter to files only
            files = [f for f in matches if os.path.isfile(f)]

            # Exclude common patterns
            files = self._filter_excludes(files)

            # Sort by modification time (newest first)
            files.sort(key=lambda f: os.path.getmtime(f), reverse=True)

            # Limit results
            truncated = len(files) > self.MAX_RESULTS
            if truncated:
                files = files[: self.MAX_RESULTS]

            # Format output
            output = "\n".join(files) if files else "No matches found"

            return ToolResult.ok(
                output,
                pattern=pattern,
                base_path=base_path,
                count=len(files),
                truncated=truncated,
            )

        except OSError as e:
            return ToolResult.fail(f"Error searching files: {e!s}")

    def _filter_excludes(self, files: list[str]) -> list[str]:
        """Filter out files matching exclude patterns.

        Handles two types of patterns:
        - Wildcard patterns (*.pyc): Match file extensions
        - Directory patterns (node_modules): Match exact directory names in path
        """
        result = []
        for f in files:
            path = Path(f)
            parts = path.parts
            excluded = False

            for exclude in self.DEFAULT_EXCLUDES:
                if exclude.startswith("*"):
                    # Wildcard pattern - use fnmatch for proper glob matching
                    if fnmatch.fnmatch(path.name, exclude):
                        excluded = True
                        break
                elif exclude in parts:
                    # Directory name - must be exact match in path components
                    # This correctly handles "node_modules" without matching
                    # "my_node_modules" or "node_modules_backup"
                    excluded = True
                    break

            if not excluded:
                result.append(f)

        return result
