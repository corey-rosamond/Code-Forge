# Phase 2.2: File Tools - Implementation Plan

**Phase:** 2.2
**Name:** File Tools
**Dependencies:** Phase 2.1 (Tool System Foundation)

---

## Overview

Phase 2.2 implements the five core file operation tools:
1. **Read** - Read file contents
2. **Write** - Write/create files
3. **Edit** - Find and replace in files
4. **Glob** - Find files by pattern
5. **Grep** - Search file contents

All tools extend `BaseTool` from Phase 2.1.

---

## Architecture

```
src/opencode/tools/
├── __init__.py          # Updated exports
├── base.py              # From Phase 2.1
├── registry.py          # From Phase 2.1
├── executor.py          # From Phase 2.1
└── file/
    ├── __init__.py      # File tools exports
    ├── read.py          # ReadTool
    ├── write.py         # WriteTool
    ├── edit.py          # EditTool
    ├── glob.py          # GlobTool
    └── grep.py          # GrepTool
```

---

## Implementation Steps

### Step 1: Create File Tools Package

Create the `src/opencode/tools/file/` directory structure and `__init__.py`:

```python
# src/opencode/tools/file/__init__.py
"""File operation tools for OpenCode."""

from opencode.tools.file.read import ReadTool
from opencode.tools.file.write import WriteTool
from opencode.tools.file.edit import EditTool
from opencode.tools.file.glob import GlobTool
from opencode.tools.file.grep import GrepTool

__all__ = [
    "ReadTool",
    "WriteTool",
    "EditTool",
    "GlobTool",
    "GrepTool",
]


def register_file_tools(registry: "ToolRegistry") -> None:
    """Register all file tools with the registry."""
    from opencode.tools.registry import ToolRegistry

    registry.register(ReadTool())
    registry.register(WriteTool())
    registry.register(EditTool())
    registry.register(GlobTool())
    registry.register(GrepTool())
```

### Step 2: Implement ReadTool

```python
# src/opencode/tools/file/read.py
"""Read tool implementation."""

from __future__ import annotations

import os
import mimetypes
from pathlib import Path
from typing import Any, List

from opencode.tools.base import (
    BaseTool,
    ToolParameter,
    ToolResult,
    ExecutionContext,
    ToolCategory,
)


class ReadTool(BaseTool):
    """
    Read contents of a file from the filesystem.

    Supports text files, images (returns base64), PDFs (extracts text),
    and Jupyter notebooks (returns formatted cells).
    """

    MAX_LINE_LENGTH = 2000
    DEFAULT_LIMIT = 2000
    MAX_LIMIT = 10000
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB limit for images
    MAX_PDF_SIZE = 50 * 1024 * 1024    # 50MB limit for PDFs
    MAX_NOTEBOOK_SIZE = 20 * 1024 * 1024  # 20MB limit for notebooks

    @property
    def name(self) -> str:
        return "Read"

    @property
    def description(self) -> str:
        return """Reads a file from the local filesystem.

Usage:
- The file_path parameter must be an absolute path, not a relative path
- By default, it reads up to 2000 lines starting from the beginning
- You can optionally specify a line offset and limit for long files
- Lines longer than 2000 characters will be truncated
- Results are returned with line numbers starting at 1
- Can read images (PNG, JPG), PDFs, and Jupyter notebooks (.ipynb)
- This tool can only read files, not directories"""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.FILE

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type="string",
                description="The absolute path to the file to read",
                required=True,
                min_length=1,
            ),
            ToolParameter(
                name="offset",
                type="integer",
                description="The line number to start reading from (1-indexed). "
                "Only provide if the file is too large to read at once.",
                required=False,
                minimum=1,
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="The number of lines to read. "
                "Only provide if the file is too large to read at once.",
                required=False,
                minimum=1,
                maximum=10000,
            ),
        ]

    async def _execute(
        self, context: ExecutionContext, **kwargs: Any
    ) -> ToolResult:
        file_path = kwargs["file_path"]
        offset = kwargs.get("offset", 1)
        limit = kwargs.get("limit", self.DEFAULT_LIMIT)

        # Validate path is absolute
        if not os.path.isabs(file_path):
            return ToolResult.fail(
                f"file_path must be an absolute path, got: {file_path}"
            )

        # Check file exists
        if not os.path.exists(file_path):
            return ToolResult.fail(f"File not found: {file_path}")

        # Check it's not a directory
        if os.path.isdir(file_path):
            return ToolResult.fail(
                f"Cannot read directory: {file_path}. "
                "Use ls command via Bash tool to list directory contents."
            )

        # Detect file type
        mime_type, _ = mimetypes.guess_type(file_path)

        try:
            # Handle images
            if mime_type and mime_type.startswith("image/"):
                return await self._read_image(file_path, mime_type)

            # Handle PDFs
            if mime_type == "application/pdf" or file_path.endswith(".pdf"):
                return await self._read_pdf(file_path)

            # Handle Jupyter notebooks
            if file_path.endswith(".ipynb"):
                return await self._read_notebook(file_path)

            # Handle text files
            return await self._read_text(file_path, offset, limit)

        except PermissionError:
            return ToolResult.fail(f"Permission denied: {file_path}")
        except UnicodeDecodeError:
            return ToolResult.fail(
                f"Cannot decode file as text: {file_path}. "
                "It may be a binary file."
            )
        except Exception as e:
            return ToolResult.fail(f"Error reading file: {str(e)}")

    async def _read_text(
        self, file_path: str, offset: int, limit: int
    ) -> ToolResult:
        """Read a text file with line numbers."""
        lines = []
        line_count = 0
        total_lines = 0

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, start=1):
                total_lines = i

                # Skip lines before offset
                if i < offset:
                    continue

                # Stop after limit
                if line_count >= limit:
                    continue

                # Truncate long lines
                line = line.rstrip("\n\r")
                if len(line) > self.MAX_LINE_LENGTH:
                    line = line[: self.MAX_LINE_LENGTH] + "..."

                # Format with line number
                lines.append(f"{i:6d}\t{line}")
                line_count += 1

        content = "\n".join(lines)

        metadata = {
            "file_path": file_path,
            "lines_read": line_count,
            "total_lines": total_lines,
            "offset": offset,
            "limit": limit,
        }

        if total_lines > offset + limit - 1:
            metadata["truncated"] = True
            metadata["remaining_lines"] = total_lines - (offset + limit - 1)

        return ToolResult.ok(content, **metadata)

    async def _read_image(self, file_path: str, mime_type: str) -> ToolResult:
        """Read an image file and return base64 encoded data."""
        import base64
        import os

        # Check file size before reading to prevent memory issues
        file_size = os.path.getsize(file_path)
        if file_size > self.MAX_IMAGE_SIZE:
            return ToolResult.fail(
                f"Image file too large: {file_size / 1024 / 1024:.1f}MB "
                f"(max: {self.MAX_IMAGE_SIZE / 1024 / 1024:.0f}MB)"
            )

        with open(file_path, "rb") as f:
            data = f.read()

        encoded = base64.b64encode(data).decode("ascii")

        return ToolResult.ok(
            f"[Image: {mime_type}]\nBase64 data: {encoded[:100]}...",
            file_path=file_path,
            mime_type=mime_type,
            size_bytes=len(data),
            is_image=True,
            base64_data=encoded,
        )

    async def _read_pdf(self, file_path: str) -> ToolResult:
        """Read a PDF file and extract text content."""
        import os

        # Check file size before reading to prevent memory issues
        file_size = os.path.getsize(file_path)
        if file_size > self.MAX_PDF_SIZE:
            return ToolResult.fail(
                f"PDF file too large: {file_size / 1024 / 1024:.1f}MB "
                f"(max: {self.MAX_PDF_SIZE / 1024 / 1024:.0f}MB)"
            )

        try:
            import pypdf

            reader = pypdf.PdfReader(file_path)
            pages = []

            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                pages.append(f"--- Page {i + 1} ---\n{text}")

            content = "\n\n".join(pages)

            return ToolResult.ok(
                content,
                file_path=file_path,
                page_count=len(reader.pages),
                is_pdf=True,
            )
        except ImportError:
            return ToolResult.fail(
                "pypdf library not installed. Install with: pip install pypdf"
            )

    async def _read_notebook(self, file_path: str) -> ToolResult:
        """Read a Jupyter notebook and format cells."""
        import json
        import os

        # Check file size before reading to prevent memory issues
        file_size = os.path.getsize(file_path)
        if file_size > self.MAX_NOTEBOOK_SIZE:
            return ToolResult.fail(
                f"Notebook file too large: {file_size / 1024 / 1024:.1f}MB "
                f"(max: {self.MAX_NOTEBOOK_SIZE / 1024 / 1024:.0f}MB)"
            )

        with open(file_path, "r", encoding="utf-8") as f:
            notebook = json.load(f)

        cells = []
        for i, cell in enumerate(notebook.get("cells", [])):
            cell_type = cell.get("cell_type", "unknown")
            source = "".join(cell.get("source", []))

            cells.append(f"--- Cell {i + 1} ({cell_type}) ---\n{source}")

            # Include outputs for code cells
            if cell_type == "code":
                outputs = cell.get("outputs", [])
                for output in outputs:
                    if "text" in output:
                        cells.append(f"Output:\n{''.join(output['text'])}")

        content = "\n\n".join(cells)

        return ToolResult.ok(
            content,
            file_path=file_path,
            cell_count=len(notebook.get("cells", [])),
            is_notebook=True,
        )
```

### Step 3: Implement WriteTool

```python
# src/opencode/tools/file/write.py
"""Write tool implementation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List

from opencode.tools.base import (
    BaseTool,
    ToolParameter,
    ToolResult,
    ExecutionContext,
    ToolCategory,
)


class WriteTool(BaseTool):
    """
    Write content to a file on the filesystem.

    Creates parent directories if needed.
    Overwrites existing files (must be read first).
    """

    @property
    def name(self) -> str:
        return "Write"

    @property
    def description(self) -> str:
        return """Writes a file to the local filesystem.

Usage:
- This tool will overwrite the existing file if there is one
- If this is an existing file, you MUST use the Read tool first
- Creates parent directories if they don't exist
- The file_path must be an absolute path
- Prefer using Edit tool for modifying existing files"""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.FILE

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type="string",
                description="The absolute path to the file to write",
                required=True,
                min_length=1,
            ),
            ToolParameter(
                name="content",
                type="string",
                description="The content to write to the file",
                required=True,
            ),
        ]

    async def _execute(
        self, context: ExecutionContext, **kwargs: Any
    ) -> ToolResult:
        file_path = kwargs["file_path"]
        content = kwargs["content"]

        # Validate path is absolute
        if not os.path.isabs(file_path):
            return ToolResult.fail(
                f"file_path must be an absolute path, got: {file_path}"
            )

        # Dry run mode
        if context.dry_run:
            byte_count = len(content.encode("utf-8"))
            exists = "overwrite" if os.path.exists(file_path) else "create"
            return ToolResult.ok(
                f"[Dry Run] Would {exists} {file_path} with {byte_count} bytes",
                file_path=file_path,
                bytes_written=byte_count,
                dry_run=True,
            )

        try:
            # Create parent directories if needed
            parent_dir = os.path.dirname(file_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)

            # Check if file exists (for metadata)
            existed = os.path.exists(file_path)

            # Write the file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            byte_count = len(content.encode("utf-8"))
            action = "Updated" if existed else "Created"

            return ToolResult.ok(
                f"{action} {file_path} ({byte_count} bytes)",
                file_path=file_path,
                bytes_written=byte_count,
                created=not existed,
            )

        except PermissionError:
            return ToolResult.fail(f"Permission denied: {file_path}")
        except OSError as e:
            return ToolResult.fail(f"OS error writing file: {str(e)}")
        except Exception as e:
            return ToolResult.fail(f"Error writing file: {str(e)}")
```

### Step 4: Implement EditTool

```python
# src/opencode/tools/file/edit.py
"""Edit tool implementation."""

from __future__ import annotations

import os
from typing import Any, List

from opencode.tools.base import (
    BaseTool,
    ToolParameter,
    ToolResult,
    ExecutionContext,
    ToolCategory,
)


class EditTool(BaseTool):
    """
    Edit a file by performing exact string replacements.

    The old_string must be found exactly in the file.
    Without replace_all, the old_string must be unique.
    """

    @property
    def name(self) -> str:
        return "Edit"

    @property
    def description(self) -> str:
        return """Performs exact string replacements in files.

Usage:
- You must use the Read tool first before editing
- The edit will FAIL if old_string is not found in the file
- The edit will FAIL if old_string appears multiple times (without replace_all)
- Use replace_all=true to replace all occurrences
- Preserves file encoding and line endings
- new_string must be different from old_string"""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.FILE

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type="string",
                description="The absolute path to the file to modify",
                required=True,
                min_length=1,
            ),
            ToolParameter(
                name="old_string",
                type="string",
                description="The text to replace (must be found exactly)",
                required=True,
            ),
            ToolParameter(
                name="new_string",
                type="string",
                description="The text to replace it with (must differ from old_string)",
                required=True,
            ),
            ToolParameter(
                name="replace_all",
                type="boolean",
                description="Replace all occurrences (default: false)",
                required=False,
                default=False,
            ),
        ]

    async def _execute(
        self, context: ExecutionContext, **kwargs: Any
    ) -> ToolResult:
        file_path = kwargs["file_path"]
        old_string = kwargs["old_string"]
        new_string = kwargs["new_string"]
        replace_all = kwargs.get("replace_all", False)

        # Validate path is absolute
        if not os.path.isabs(file_path):
            return ToolResult.fail(
                f"file_path must be an absolute path, got: {file_path}"
            )

        # Check file exists
        if not os.path.exists(file_path):
            return ToolResult.fail(f"File not found: {file_path}")

        # Check old != new
        if old_string == new_string:
            return ToolResult.fail(
                "new_string must be different from old_string"
            )

        try:
            # Read current content, preserving encoding
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Count occurrences
            count = content.count(old_string)

            if count == 0:
                return ToolResult.fail(
                    f"old_string not found in {file_path}. "
                    "Make sure you've read the file first and the string "
                    "matches exactly (including whitespace and indentation)."
                )

            if count > 1 and not replace_all:
                # Find line numbers where it occurs
                lines_with_match = []
                for i, line in enumerate(content.splitlines(), 1):
                    if old_string in line:
                        lines_with_match.append(i)

                return ToolResult.fail(
                    f"old_string found {count} times (lines: {lines_with_match}). "
                    "Either:\n"
                    "1. Provide more surrounding context to make it unique\n"
                    "2. Use replace_all=true to replace all occurrences"
                )

            # Perform replacement
            if replace_all:
                new_content = content.replace(old_string, new_string)
                replacements = count
            else:
                new_content = content.replace(old_string, new_string, 1)
                replacements = 1

            # Dry run mode
            if context.dry_run:
                return ToolResult.ok(
                    f"[Dry Run] Would replace {replacements} occurrence(s) "
                    f"in {file_path}",
                    file_path=file_path,
                    replacements=replacements,
                    dry_run=True,
                )

            # Write back
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return ToolResult.ok(
                f"Replaced {replacements} occurrence(s) in {file_path}",
                file_path=file_path,
                replacements=replacements,
            )

        except PermissionError:
            return ToolResult.fail(f"Permission denied: {file_path}")
        except UnicodeDecodeError:
            return ToolResult.fail(
                f"Cannot read file as text: {file_path}. "
                "It may be a binary file."
            )
        except Exception as e:
            return ToolResult.fail(f"Error editing file: {str(e)}")
```

### Step 5: Implement GlobTool

```python
# src/opencode/tools/file/glob.py
"""Glob tool implementation."""

from __future__ import annotations

import os
import glob as glob_module
from pathlib import Path
from typing import Any, List

from opencode.tools.base import (
    BaseTool,
    ToolParameter,
    ToolResult,
    ExecutionContext,
    ToolCategory,
)


class GlobTool(BaseTool):
    """
    Find files matching a glob pattern.

    Returns files sorted by modification time (newest first).
    """

    # Patterns to exclude by default
    DEFAULT_EXCLUDES = {
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

    MAX_RESULTS = 1000

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
    def parameters(self) -> List[ToolParameter]:
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
            output = "\n".join(files)

            return ToolResult.ok(
                output,
                pattern=pattern,
                base_path=base_path,
                count=len(files),
                truncated=truncated,
            )

        except Exception as e:
            return ToolResult.fail(f"Error searching files: {str(e)}")

    def _filter_excludes(self, files: List[str]) -> List[str]:
        """Filter out files matching exclude patterns.

        Handles two types of patterns:
        - Wildcard patterns (*.pyc): Match file extensions
        - Directory patterns (node_modules): Match exact directory names in path
        """
        import fnmatch

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
                else:
                    # Directory name - must be exact match in path components
                    # This correctly handles "node_modules" without matching
                    # "my_node_modules" or "node_modules_backup"
                    if exclude in parts:
                        excluded = True
                        break

            if not excluded:
                result.append(f)

        return result
```

### Step 6: Implement GrepTool

```python
# src/opencode/tools/file/grep.py
"""Grep tool implementation."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, List, Optional

from opencode.tools.base import (
    BaseTool,
    ToolParameter,
    ToolResult,
    ExecutionContext,
    ToolCategory,
)


class GrepTool(BaseTool):
    """
    Search file contents with regular expressions.

    Inspired by ripgrep, supports context lines and multiple output modes.
    """

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    DEFAULT_HEAD_LIMIT = 100

    @property
    def name(self) -> str:
        return "Grep"

    @property
    def description(self) -> str:
        return """A powerful search tool built on ripgrep.

Usage:
- Supports full regex syntax (e.g., "log.*Error", "function\\s+\\w+")
- Filter files with glob parameter (e.g., "*.js", "**/*.tsx")
- Output modes: "content" shows lines, "files_with_matches" shows paths, "count" shows counts
- Use -i for case-insensitive, -A/-B/-C for context lines"""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.FILE

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="pattern",
                type="string",
                description="The regular expression pattern to search for",
                required=True,
                min_length=1,
            ),
            ToolParameter(
                name="path",
                type="string",
                description="File or directory to search in. "
                "Defaults to current working directory.",
                required=False,
            ),
            ToolParameter(
                name="glob",
                type="string",
                description="Glob pattern to filter files (e.g., '*.py', '*.{ts,tsx}')",
                required=False,
            ),
            ToolParameter(
                name="type",
                type="string",
                description="File type to search (e.g., 'py', 'js', 'rust')",
                required=False,
            ),
            ToolParameter(
                name="output_mode",
                type="string",
                description="Output mode",
                required=False,
                default="files_with_matches",
                enum=["content", "files_with_matches", "count"],
            ),
            ToolParameter(
                name="-i",
                type="boolean",
                description="Case insensitive search",
                required=False,
                default=False,
            ),
            ToolParameter(
                name="-n",
                type="boolean",
                description="Show line numbers in output (for content mode)",
                required=False,
                default=True,
            ),
            ToolParameter(
                name="-A",
                type="integer",
                description="Number of lines to show after each match",
                required=False,
                minimum=0,
            ),
            ToolParameter(
                name="-B",
                type="integer",
                description="Number of lines to show before each match",
                required=False,
                minimum=0,
            ),
            ToolParameter(
                name="-C",
                type="integer",
                description="Number of lines to show before and after each match",
                required=False,
                minimum=0,
            ),
            ToolParameter(
                name="multiline",
                type="boolean",
                description="Enable multiline matching mode",
                required=False,
                default=False,
            ),
            ToolParameter(
                name="head_limit",
                type="integer",
                description="Limit output to first N results",
                required=False,
            ),
            ToolParameter(
                name="offset",
                type="integer",
                description="Skip first N results",
                required=False,
                default=0,
            ),
        ]

    async def _execute(
        self, context: ExecutionContext, **kwargs: Any
    ) -> ToolResult:
        pattern = kwargs["pattern"]
        search_path = kwargs.get("path") or context.working_dir
        glob_filter = kwargs.get("glob")
        type_filter = kwargs.get("type")
        output_mode = kwargs.get("output_mode", "files_with_matches")
        case_insensitive = kwargs.get("-i", False)
        show_line_numbers = kwargs.get("-n", True)
        after_context = kwargs.get("-A", 0)
        before_context = kwargs.get("-B", 0)
        both_context = kwargs.get("-C", 0)
        multiline = kwargs.get("multiline", False)
        head_limit = kwargs.get("head_limit", self.DEFAULT_HEAD_LIMIT)
        offset = kwargs.get("offset", 0)

        # Context lines
        if both_context:
            after_context = both_context
            before_context = both_context

        try:
            # Compile regex
            flags = re.MULTILINE if multiline else 0
            if case_insensitive:
                flags |= re.IGNORECASE

            try:
                regex = re.compile(pattern, flags)
            except re.error as e:
                return ToolResult.fail(f"Invalid regex pattern: {str(e)}")

            # Get files to search
            files = self._get_files(search_path, glob_filter, type_filter)

            # Search files
            results = []
            for file_path in files:
                file_results = self._search_file(
                    file_path,
                    regex,
                    output_mode,
                    show_line_numbers,
                    before_context,
                    after_context,
                )
                if file_results:
                    results.extend(file_results)

            # Apply offset and limit
            total_results = len(results)
            results = results[offset:]
            if head_limit:
                results = results[:head_limit]

            # Format output
            output = self._format_output(results, output_mode)

            return ToolResult.ok(
                output,
                pattern=pattern,
                total_matches=total_results,
                returned_matches=len(results),
                offset=offset,
                head_limit=head_limit,
            )

        except Exception as e:
            return ToolResult.fail(f"Error searching: {str(e)}")

    def _get_files(
        self,
        search_path: str,
        glob_filter: Optional[str],
        type_filter: Optional[str],
    ) -> List[str]:
        """Get list of files to search."""
        import glob as glob_module

        # Type to extension mapping
        type_extensions = {
            "py": ["*.py"],
            "js": ["*.js", "*.jsx"],
            "ts": ["*.ts", "*.tsx"],
            "rust": ["*.rs"],
            "go": ["*.go"],
            "java": ["*.java"],
            "c": ["*.c", "*.h"],
            "cpp": ["*.cpp", "*.hpp", "*.cc", "*.hh"],
            "md": ["*.md"],
            "json": ["*.json"],
            "yaml": ["*.yaml", "*.yml"],
        }

        if os.path.isfile(search_path):
            return [search_path]

        files = []

        if glob_filter:
            pattern = os.path.join(search_path, "**", glob_filter)
            files = glob_module.glob(pattern, recursive=True)
        elif type_filter and type_filter in type_extensions:
            for ext in type_extensions[type_filter]:
                pattern = os.path.join(search_path, "**", ext)
                files.extend(glob_module.glob(pattern, recursive=True))
        else:
            # Search all files
            for root, _, filenames in os.walk(search_path):
                for filename in filenames:
                    files.append(os.path.join(root, filename))

        # Filter to readable files
        return [f for f in files if os.path.isfile(f) and self._is_text_file(f)]

    def _is_text_file(self, file_path: str) -> bool:
        """Check if file appears to be text."""
        try:
            # Check file size
            if os.path.getsize(file_path) > self.MAX_FILE_SIZE:
                return False

            # Try to read first chunk
            with open(file_path, "rb") as f:
                chunk = f.read(1024)
                # Check for null bytes (binary indicator)
                return b"\x00" not in chunk
        except (OSError, PermissionError):
            return False

    def _search_file(
        self,
        file_path: str,
        regex: re.Pattern,
        output_mode: str,
        show_line_numbers: bool,
        before_context: int,
        after_context: int,
    ) -> List[dict]:
        """Search a single file for matches."""
        results = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except (OSError, PermissionError):
            return results

        match_count = 0

        for i, line in enumerate(lines):
            if regex.search(line):
                match_count += 1

                if output_mode == "files_with_matches":
                    # Just need to know this file matches
                    return [{"file": file_path}]
                elif output_mode == "count":
                    continue
                else:  # content
                    # Get context lines
                    start = max(0, i - before_context)
                    end = min(len(lines), i + after_context + 1)

                    context_lines = []
                    for j in range(start, end):
                        prefix = ">" if j == i else " "
                        line_num = f"{j + 1}:" if show_line_numbers else ""
                        context_lines.append(
                            f"{prefix}{line_num}{lines[j].rstrip()}"
                        )

                    results.append({
                        "file": file_path,
                        "line": i + 1,
                        "content": "\n".join(context_lines),
                    })

        if output_mode == "count" and match_count > 0:
            results.append({"file": file_path, "count": match_count})

        return results

    def _format_output(self, results: List[dict], output_mode: str) -> str:
        """Format search results for output."""
        if not results:
            return "No matches found"

        if output_mode == "files_with_matches":
            # Deduplicate and return file paths
            files = sorted(set(r["file"] for r in results))
            return "\n".join(files)

        elif output_mode == "count":
            lines = []
            for r in results:
                lines.append(f"{r['file']}: {r['count']}")
            return "\n".join(lines)

        else:  # content
            sections = []
            for r in results:
                sections.append(f"{r['file']}:{r['line']}\n{r['content']}")
            return "\n\n".join(sections)
```

### Step 7: Register File Tools

Update `src/opencode/tools/__init__.py` to include file tools registration:

```python
# src/opencode/tools/__init__.py
"""OpenCode tool system."""

from opencode.tools.base import (
    BaseTool,
    ToolParameter,
    ToolResult,
    ExecutionContext,
    ToolCategory,
    ToolExecution,
)
from opencode.tools.registry import ToolRegistry
from opencode.tools.executor import ToolExecutor

# File tools
from opencode.tools.file import (
    ReadTool,
    WriteTool,
    EditTool,
    GlobTool,
    GrepTool,
    register_file_tools,
)

__all__ = [
    # Base classes
    "BaseTool",
    "ToolParameter",
    "ToolResult",
    "ExecutionContext",
    "ToolCategory",
    "ToolExecution",
    # Registry and executor
    "ToolRegistry",
    "ToolExecutor",
    # File tools
    "ReadTool",
    "WriteTool",
    "EditTool",
    "GlobTool",
    "GrepTool",
    "register_file_tools",
]


def register_all_tools(registry: ToolRegistry) -> None:
    """Register all built-in tools with the registry."""
    register_file_tools(registry)
    # Future: register_execution_tools(registry)
    # Future: register_web_tools(registry)
```

---

## Testing Strategy

### Unit Tests

1. **ReadTool Tests**
   - Read existing text file
   - Read with offset and limit
   - Read non-existent file
   - Read directory (error)
   - Read binary file detection
   - Read image file
   - Read PDF file
   - Read Jupyter notebook
   - Handle encoding errors

2. **WriteTool Tests**
   - Write new file
   - Overwrite existing file
   - Create parent directories
   - Permission denied error
   - Dry run mode

3. **EditTool Tests**
   - Replace single occurrence
   - Replace all occurrences
   - String not found error
   - Non-unique string error
   - Same old/new string error
   - Preserve encoding
   - Dry run mode

4. **GlobTool Tests**
   - Match simple patterns
   - Match recursive patterns
   - Filter excludes
   - Empty results
   - Sort by modification time

5. **GrepTool Tests**
   - Simple regex match
   - Case insensitive search
   - Context lines
   - Output modes
   - File type filter
   - Glob filter

### Integration Tests

1. Read file, edit, read again to verify changes
2. Write file, read back, verify content
3. Glob to find files, grep to search content
4. Full workflow: search, read, edit, verify

---

## Dependencies

Ensure these are in `pyproject.toml`:

```toml
[tool.poetry.dependencies]
pypdf = "^4.0"  # For PDF reading
```

---

## Security Considerations

1. **Path Validation**: All paths must be absolute and validated
2. **Path Traversal**: Prevent `../` attacks
3. **Symlinks**: Don't follow symlinks outside working directory
4. **File Size Limits**: Enforce maximum file sizes
5. **Binary Detection**: Detect and handle binary files appropriately
6. **Encoding Safety**: Handle encoding errors gracefully

### Path Traversal Prevention Implementation

Add this utility function to `src/opencode/tools/file/utils.py`:

```python
# src/opencode/tools/file/utils.py
"""Security utilities for file operations."""

import os
from pathlib import Path
from typing import Tuple


def validate_path_security(
    file_path: str,
    base_dir: str | None = None,
    allow_symlinks: bool = False,
) -> Tuple[bool, str | None]:
    """Validate a file path for security issues.

    Checks for:
    - Path traversal attacks (../)
    - Symlinks escaping allowed directory
    - Absolute path requirements

    Args:
        file_path: Path to validate.
        base_dir: Optional base directory to restrict access.
        allow_symlinks: Whether to allow symlinks.

    Returns:
        Tuple of (is_valid, error_message).
        If valid, error_message is None.
    """
    # Must be absolute
    if not os.path.isabs(file_path):
        return False, f"Path must be absolute: {file_path}"

    # Resolve to canonical path (resolves .., symlinks, etc.)
    try:
        resolved = Path(file_path).resolve()
    except (OSError, RuntimeError) as e:
        return False, f"Invalid path: {e}"

    # Check for path traversal by comparing resolved vs original
    # If resolved path differs significantly, there may be traversal
    original_parts = Path(file_path).parts
    if ".." in original_parts:
        return False, "Path traversal not allowed (contains ..)"

    # Check symlinks if not allowed
    if not allow_symlinks and Path(file_path).is_symlink():
        return False, "Symlinks not allowed"

    # Check base directory restriction
    if base_dir:
        base_resolved = Path(base_dir).resolve()
        try:
            resolved.relative_to(base_resolved)
        except ValueError:
            return False, f"Path must be within {base_dir}"

    return True, None


def is_safe_filename(filename: str) -> bool:
    """Check if a filename is safe (no path separators).

    Args:
        filename: Filename to check.

    Returns:
        True if safe.
    """
    return os.path.sep not in filename and "/" not in filename and "\\" not in filename
```

Update ReadTool to use the validator (add after "Validate path is absolute"):

```python
# In ReadTool._execute(), after checking if path is absolute:

# Security validation
from opencode.tools.file.utils import validate_path_security
is_valid, error = validate_path_security(file_path)
if not is_valid:
    return ToolResult.fail(error)
```
