# Phase 2.2: File Tools - Requirements

**Phase:** 2.2
**Name:** File Tools
**Status:** Not Started
**Dependencies:** Phase 2.1 (Tool System Foundation)

---

## Overview

This phase implements the file operation tools that allow the AI assistant to interact with the filesystem. These tools provide capabilities for reading, writing, editing, and searching files.

---

## Functional Requirements

### FR-2.2.1: Read Tool
- Read entire file contents
- Read partial file with offset (line number)
- Read partial file with limit (max lines)
- Support text files with any encoding
- Support binary file detection
- Support image files (return base64 or file info)
- Support PDF files (extract text)
- Support Jupyter notebooks (.ipynb)
- Display line numbers in output
- Handle files up to configurable max size
- Truncate long lines with indicator
- Return error for non-existent files
- Return error for directories

### FR-2.2.2: Write Tool
- Write content to new files
- Overwrite existing files
- Create parent directories if needed
- Preserve file permissions when overwriting
- Support text content only
- Validate path is absolute
- Require file to be read first before overwrite (safety)
- Return bytes written in metadata
- Support dry run mode

### FR-2.2.3: Edit Tool
- Find and replace text in files
- Replace exact string matches
- Support `replace_all` flag for multiple occurrences
- Fail if old_string not found
- Fail if old_string not unique (without replace_all)
- Preserve file encoding
- Preserve line endings (LF/CRLF)
- Return diff-style output showing changes
- Support dry run mode

### FR-2.2.4: Glob Tool
- Find files matching glob patterns
- Support ** for recursive matching
- Support * for single-level matching
- Support ? for single character
- Support [abc] character classes
- Search from specified directory or cwd
- Return files sorted by modification time (newest first)
- Limit results to configurable maximum
- Exclude hidden files by default (configurable)
- Exclude common ignore patterns (.git, node_modules, __pycache__)
- Return absolute paths

### FR-2.2.5: Grep Tool
- Search file contents with regex patterns
- Support literal string search mode
- Support case-insensitive search (-i)
- Support context lines before (-B)
- Support context lines after (-A)
- Support context lines both (-C)
- Support line numbers in output (-n)
- Support multiline matching mode
- Limit to specific file types (--type)
- Filter with glob pattern (--glob)
- Output modes: content, files_with_matches, count
- Paginate results with offset and limit
- Return file paths sorted by relevance

---

## Non-Functional Requirements

### NFR-2.2.1: Performance
- File operations complete in < 100ms for typical files
- Large file handling with streaming (don't load entire file)
- Glob operations use efficient filesystem traversal
- Grep uses optimized regex engine

### NFR-2.2.2: Security
- Validate all paths are within allowed directories
- No symlink following outside allowed paths
- No access to system-sensitive files
- Path traversal attack prevention

### NFR-2.2.3: Reliability
- Handle encoding errors gracefully
- Handle permission errors with clear messages
- Handle disk full errors
- Handle concurrent access safely

---

## Technical Specifications

### Read Tool

```python
class ReadTool(BaseTool):
    """Read contents of a file from the filesystem."""

    @property
    def name(self) -> str:
        return "Read"

    @property
    def description(self) -> str:
        return """Reads a file from the local filesystem.

Usage:
- The file_path parameter must be an absolute path
- By default, reads up to 2000 lines from the beginning
- Optionally specify offset and limit for partial reads
- Lines longer than 2000 characters are truncated
- Results include line numbers starting at 1
- Can read images, PDFs, and Jupyter notebooks"""

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
            ),
            ToolParameter(
                name="offset",
                type="integer",
                description="Line number to start reading from (1-indexed)",
                required=False,
                default=1,
                minimum=1,
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="Maximum number of lines to read",
                required=False,
                default=2000,
                minimum=1,
                maximum=10000,
            ),
        ]

    async def _execute(
        self, context: ExecutionContext, **kwargs
    ) -> ToolResult:
        file_path = kwargs["file_path"]
        offset = kwargs.get("offset", 1)
        limit = kwargs.get("limit", 2000)

        # Validate path
        if not os.path.isabs(file_path):
            return ToolResult.fail("file_path must be an absolute path")

        if not os.path.exists(file_path):
            return ToolResult.fail(f"File not found: {file_path}")

        if os.path.isdir(file_path):
            return ToolResult.fail(f"Cannot read directory: {file_path}")

        # Read file with line numbers
        try:
            content = self._read_file(file_path, offset, limit)
            return ToolResult.ok(
                content,
                file_path=file_path,
                lines_read=len(content.splitlines()),
            )
        except Exception as e:
            return ToolResult.fail(str(e))
```

### Write Tool

```python
class WriteTool(BaseTool):
    """Write content to a file on the filesystem."""

    @property
    def name(self) -> str:
        return "Write"

    @property
    def description(self) -> str:
        return """Writes content to a file on the filesystem.

Usage:
- The file_path must be an absolute path
- Will overwrite existing files
- Creates parent directories if needed
- Existing files must be read first before writing
- Use Edit tool for find/replace operations"""

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
            ),
            ToolParameter(
                name="content",
                type="string",
                description="The content to write to the file",
                required=True,
            ),
        ]

    async def _execute(
        self, context: ExecutionContext, **kwargs
    ) -> ToolResult:
        file_path = kwargs["file_path"]
        content = kwargs["content"]

        if not os.path.isabs(file_path):
            return ToolResult.fail("file_path must be an absolute path")

        if context.dry_run:
            return ToolResult.ok(
                f"[Dry Run] Would write {len(content)} bytes to {file_path}"
            )

        try:
            # Create parent directories
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return ToolResult.ok(
                f"Successfully wrote {len(content)} bytes to {file_path}",
                file_path=file_path,
                bytes_written=len(content.encode("utf-8")),
            )
        except Exception as e:
            return ToolResult.fail(str(e))
```

### Edit Tool

```python
class EditTool(BaseTool):
    """Edit a file by replacing text."""

    @property
    def name(self) -> str:
        return "Edit"

    @property
    def description(self) -> str:
        return """Performs exact string replacements in files.

Usage:
- The file must be read first before editing
- old_string must be found exactly in the file
- Without replace_all, old_string must be unique
- Use replace_all=true to replace all occurrences
- Preserves file encoding and line endings"""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.FILE

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type="string",
                description="The absolute path to the file to edit",
                required=True,
            ),
            ToolParameter(
                name="old_string",
                type="string",
                description="The exact text to find and replace",
                required=True,
            ),
            ToolParameter(
                name="new_string",
                type="string",
                description="The text to replace with",
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
        self, context: ExecutionContext, **kwargs
    ) -> ToolResult:
        file_path = kwargs["file_path"]
        old_string = kwargs["old_string"]
        new_string = kwargs["new_string"]
        replace_all = kwargs.get("replace_all", False)

        if not os.path.isabs(file_path):
            return ToolResult.fail("file_path must be an absolute path")

        if not os.path.exists(file_path):
            return ToolResult.fail(f"File not found: {file_path}")

        try:
            # Read current content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check occurrences
            count = content.count(old_string)

            if count == 0:
                return ToolResult.fail(
                    f"old_string not found in {file_path}"
                )

            if count > 1 and not replace_all:
                return ToolResult.fail(
                    f"old_string found {count} times. Use replace_all=true "
                    "or provide more context to make it unique."
                )

            # Perform replacement
            if replace_all:
                new_content = content.replace(old_string, new_string)
                replacements = count
            else:
                new_content = content.replace(old_string, new_string, 1)
                replacements = 1

            if context.dry_run:
                return ToolResult.ok(
                    f"[Dry Run] Would replace {replacements} occurrence(s)",
                    replacements=replacements,
                )

            # Write back
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return ToolResult.ok(
                f"Replaced {replacements} occurrence(s) in {file_path}",
                file_path=file_path,
                replacements=replacements,
            )
        except Exception as e:
            return ToolResult.fail(str(e))
```

### Glob Tool

```python
class GlobTool(BaseTool):
    """Find files matching a glob pattern."""

    @property
    def name(self) -> str:
        return "Glob"

    @property
    def description(self) -> str:
        return """Fast file pattern matching tool.

Usage:
- Supports glob patterns like "**/*.py" or "src/**/*.ts"
- Returns matching file paths sorted by modification time
- Use this to find files by name patterns"""

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
            ),
            ToolParameter(
                name="path",
                type="string",
                description="Directory to search in (default: working directory)",
                required=False,
            ),
        ]

    async def _execute(
        self, context: ExecutionContext, **kwargs
    ) -> ToolResult:
        pattern = kwargs["pattern"]
        path = kwargs.get("path", context.working_dir)

        try:
            import glob as glob_module

            # Build full pattern
            if os.path.isabs(pattern):
                full_pattern = pattern
            else:
                full_pattern = os.path.join(path, pattern)

            # Find matching files
            matches = glob_module.glob(full_pattern, recursive=True)

            # Filter to files only, sort by mtime
            files = [f for f in matches if os.path.isfile(f)]
            files.sort(key=lambda f: os.path.getmtime(f), reverse=True)

            return ToolResult.ok(
                "\n".join(files),
                count=len(files),
                pattern=pattern,
            )
        except Exception as e:
            return ToolResult.fail(str(e))
```

### Grep Tool

```python
class GrepTool(BaseTool):
    """Search file contents with regex."""

    @property
    def name(self) -> str:
        return "Grep"

    @property
    def description(self) -> str:
        return """A powerful search tool built on ripgrep.

Usage:
- Supports full regex syntax
- Filter files with glob parameter
- Output modes: content, files_with_matches, count"""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.FILE

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="pattern",
                type="string",
                description="Regular expression pattern to search for",
                required=True,
            ),
            ToolParameter(
                name="path",
                type="string",
                description="File or directory to search in",
                required=False,
            ),
            ToolParameter(
                name="glob",
                type="string",
                description="Glob pattern to filter files (e.g., '*.py')",
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
                description="Show line numbers",
                required=False,
                default=True,
            ),
            ToolParameter(
                name="-A",
                type="integer",
                description="Lines of context after match",
                required=False,
                minimum=0,
            ),
            ToolParameter(
                name="-B",
                type="integer",
                description="Lines of context before match",
                required=False,
                minimum=0,
            ),
            ToolParameter(
                name="-C",
                type="integer",
                description="Lines of context before and after",
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
```

---

## Acceptance Criteria

### Definition of Done

- [ ] ReadTool implemented and tested
- [ ] WriteTool implemented and tested
- [ ] EditTool implemented and tested
- [ ] GlobTool implemented and tested
- [ ] GrepTool implemented and tested
- [ ] All tools registered in ToolRegistry
- [ ] All tools generate valid schemas
- [ ] Security validations in place
- [ ] Error handling comprehensive
- [ ] Tests achieve ≥90% coverage

---

## Out of Scope

The following are NOT part of Phase 2.2:
- NotebookEdit tool (Phase 2.4 or later)
- Binary file editing
- Network file systems
- File watching/monitoring
- Compression/archive handling

---

## Notes

These tools form the foundation of file operations. They are used extensively by the AI assistant to:
- Read and understand code
- Make changes to files
- Search for patterns in the codebase
- Navigate the project structure
