# Phase 2.2: File Tools - Completion Criteria

**Phase:** 2.2
**Name:** File Tools
**Dependencies:** Phase 2.1 (Tool System Foundation)

---

## Definition of Done

All of the following criteria must be met before Phase 2.2 is considered complete.

---

## Checklist

### ReadTool (src/forge/tools/file/read.py)
- [ ] ReadTool class extends BaseTool
- [ ] name property returns "Read"
- [ ] category property returns ToolCategory.FILE
- [ ] parameters include: file_path (required), offset (optional), limit (optional)
- [ ] Reads text files with line numbers
- [ ] Respects offset parameter (1-indexed)
- [ ] Respects limit parameter (default 2000, max 10000)
- [ ] Truncates lines longer than 2000 characters
- [ ] Returns error for non-absolute paths
- [ ] Returns error for non-existent files
- [ ] Returns error for directories
- [ ] Detects and handles image files (returns base64)
- [ ] Detects and handles PDF files (extracts text)
- [ ] Detects and handles Jupyter notebooks (formats cells)
- [ ] Handles permission denied gracefully
- [ ] Handles encoding errors gracefully
- [ ] Metadata includes: file_path, lines_read, total_lines

### WriteTool (src/forge/tools/file/write.py)
- [ ] WriteTool class extends BaseTool
- [ ] name property returns "Write"
- [ ] category property returns ToolCategory.FILE
- [ ] parameters include: file_path (required), content (required)
- [ ] Creates new files
- [ ] Overwrites existing files
- [ ] Creates parent directories if needed
- [ ] Returns error for non-absolute paths
- [ ] Handles permission denied gracefully
- [ ] Supports dry_run mode
- [ ] Metadata includes: file_path, bytes_written, created (bool)

### EditTool (src/forge/tools/file/edit.py)
- [ ] EditTool class extends BaseTool
- [ ] name property returns "Edit"
- [ ] category property returns ToolCategory.FILE
- [ ] parameters include: file_path, old_string, new_string, replace_all
- [ ] Replaces exact string matches
- [ ] Returns error if old_string not found
- [ ] Returns error if old_string not unique (without replace_all)
- [ ] Returns error if old_string equals new_string
- [ ] Supports replace_all=true for multiple replacements
- [ ] Returns error for non-existent files
- [ ] Preserves file encoding
- [ ] Supports dry_run mode
- [ ] Metadata includes: file_path, replacements count

### GlobTool (src/forge/tools/file/glob.py)
- [ ] GlobTool class extends BaseTool
- [ ] name property returns "Glob"
- [ ] category property returns ToolCategory.FILE
- [ ] parameters include: pattern (required), path (optional)
- [ ] Supports ** recursive patterns
- [ ] Supports * single-level patterns
- [ ] Filters out .git, node_modules, __pycache__ by default
- [ ] Returns only files (not directories)
- [ ] Sorts results by modification time (newest first)
- [ ] Limits results to MAX_RESULTS (1000)
- [ ] Uses working_dir when path not provided
- [ ] Metadata includes: pattern, count, truncated

### GrepTool (src/forge/tools/file/grep.py)
- [ ] GrepTool class extends BaseTool
- [ ] name property returns "Grep"
- [ ] category property returns ToolCategory.FILE
- [ ] parameters include: pattern, path, glob, type, output_mode, -i, -n, -A, -B, -C, multiline, head_limit, offset
- [ ] Supports regex patterns
- [ ] Returns error for invalid regex
- [ ] Supports case-insensitive search (-i)
- [ ] Supports line numbers (-n)
- [ ] Supports context lines (-A, -B, -C)
- [ ] Supports multiline mode
- [ ] Supports output_mode: content, files_with_matches, count
- [ ] Supports file type filter (py, js, ts, etc.)
- [ ] Supports glob filter
- [ ] Supports pagination (head_limit, offset)
- [ ] Skips binary files
- [ ] Metadata includes: pattern, total_matches, returned_matches

### Package Structure
- [ ] src/forge/tools/file/__init__.py exists
- [ ] __init__.py exports all tools
- [ ] register_file_tools() function registers all tools
- [ ] src/forge/tools/__init__.py updated to include file tools

### Tool Registration
- [ ] All tools can be registered in ToolRegistry
- [ ] All tools generate valid OpenAI schemas
- [ ] All tools generate valid Anthropic schemas
- [ ] No duplicate tool names

### Security
- [ ] All paths validated as absolute
- [ ] Path traversal attempts detected
- [ ] Binary file detection working
- [ ] Large file handling (streaming/limits)

### Testing
- [ ] Unit tests for ReadTool (all scenarios)
- [ ] Unit tests for WriteTool (all scenarios)
- [ ] Unit tests for EditTool (all scenarios)
- [ ] Unit tests for GlobTool (all scenarios)
- [ ] Unit tests for GrepTool (all scenarios)
- [ ] Integration tests for tool workflows
- [ ] Test coverage ≥ 90%

---

## Verification Commands

```bash
# 1. Verify module structure
ls -la src/forge/tools/file/
# Expected: __init__.py, read.py, write.py, edit.py, glob.py, grep.py

# 2. Test imports
python -c "
from forge.tools.file import (
    ReadTool, WriteTool, EditTool, GlobTool, GrepTool,
    register_file_tools
)
print('All file tool imports successful')
"

# 3. Test ReadTool
python -c "
import asyncio
from forge.tools.file import ReadTool
from forge.tools.base import ExecutionContext

tool = ReadTool()
ctx = ExecutionContext(working_dir='/tmp')

# Create test file
import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write('Line 1\nLine 2\nLine 3\n')
    path = f.name

# Test read
result = asyncio.run(tool.execute(ctx, file_path=path))
assert result.success, f'Read failed: {result.error}'
assert 'Line 1' in result.output
assert result.metadata['lines_read'] == 3
print(f'ReadTool: OK (read {result.metadata[\"lines_read\"]} lines)')

# Cleanup
import os
os.unlink(path)
"

# 4. Test WriteTool
python -c "
import asyncio
import tempfile
import os
from forge.tools.file import WriteTool
from forge.tools.base import ExecutionContext

tool = WriteTool()
ctx = ExecutionContext(working_dir='/tmp')

# Test write new file
path = tempfile.mktemp(suffix='.txt')
result = asyncio.run(tool.execute(ctx, file_path=path, content='Hello, World!'))
assert result.success, f'Write failed: {result.error}'
assert os.path.exists(path)
assert result.metadata['bytes_written'] == 13
print('WriteTool: OK')

# Cleanup
os.unlink(path)
"

# 5. Test EditTool
python -c "
import asyncio
import tempfile
import os
from forge.tools.file import EditTool
from forge.tools.base import ExecutionContext

tool = EditTool()
ctx = ExecutionContext(working_dir='/tmp')

# Create test file
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write('old_value = 1')
    path = f.name

# Test edit
result = asyncio.run(tool.execute(
    ctx,
    file_path=path,
    old_string='old_value',
    new_string='new_value'
))
assert result.success, f'Edit failed: {result.error}'

# Verify change
with open(path) as f:
    content = f.read()
assert 'new_value = 1' in content
print('EditTool: OK')

# Cleanup
os.unlink(path)
"

# 6. Test GlobTool
python -c "
import asyncio
import tempfile
import os
from forge.tools.file import GlobTool
from forge.tools.base import ExecutionContext

tool = GlobTool()

# Create temp directory with files
tmpdir = tempfile.mkdtemp()
for name in ['test1.py', 'test2.py', 'readme.txt']:
    open(os.path.join(tmpdir, name), 'w').close()

ctx = ExecutionContext(working_dir=tmpdir)

# Test glob
result = asyncio.run(tool.execute(ctx, pattern='*.py'))
assert result.success, f'Glob failed: {result.error}'
assert result.metadata['count'] == 2
print(f'GlobTool: OK (found {result.metadata[\"count\"]} files)')

# Cleanup
import shutil
shutil.rmtree(tmpdir)
"

# 7. Test GrepTool
python -c "
import asyncio
import tempfile
import os
from forge.tools.file import GrepTool
from forge.tools.base import ExecutionContext

tool = GrepTool()

# Create test file
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    f.write('# TODO: Fix this\ndef hello():\n    print(\"hello\")\n')
    path = f.name

ctx = ExecutionContext(working_dir=os.path.dirname(path))

# Test grep
result = asyncio.run(tool.execute(
    ctx,
    pattern='TODO',
    path=path,
    output_mode='content'
))
assert result.success, f'Grep failed: {result.error}'
assert 'TODO' in result.output
print('GrepTool: OK')

# Cleanup
os.unlink(path)
"

# 8. Test tool registration
python -c "
from forge.tools.registry import ToolRegistry
from forge.tools.file import register_file_tools

ToolRegistry.reset()
registry = ToolRegistry()
register_file_tools(registry)

assert registry.exists('Read')
assert registry.exists('Write')
assert registry.exists('Edit')
assert registry.exists('Glob')
assert registry.exists('Grep')
print(f'Tool registration: OK ({registry.count()} tools)')
"

# 9. Test schema generation
python -c "
from forge.tools.file import ReadTool, GrepTool

read_tool = ReadTool()
grep_tool = GrepTool()

# OpenAI schema
openai_schema = read_tool.to_openai_schema()
assert openai_schema['type'] == 'function'
assert openai_schema['function']['name'] == 'Read'
assert 'file_path' in openai_schema['function']['parameters']['properties']

# Anthropic schema
anthropic_schema = grep_tool.to_anthropic_schema()
assert anthropic_schema['name'] == 'Grep'
assert 'pattern' in anthropic_schema['input_schema']['properties']

print('Schema generation: OK')
"

# 10. Test error handling
python -c "
import asyncio
from forge.tools.file import ReadTool, EditTool
from forge.tools.base import ExecutionContext

ctx = ExecutionContext(working_dir='/tmp')
read_tool = ReadTool()
edit_tool = EditTool()

# Test non-existent file
result = asyncio.run(read_tool.execute(ctx, file_path='/nonexistent/file.txt'))
assert not result.success
assert 'not found' in result.error.lower()

# Test relative path
result = asyncio.run(read_tool.execute(ctx, file_path='relative/path.txt'))
assert not result.success
assert 'absolute' in result.error.lower()

# Test same old/new string
result = asyncio.run(edit_tool.execute(
    ctx,
    file_path='/tmp/test.txt',
    old_string='same',
    new_string='same'
))
assert not result.success
assert 'different' in result.error.lower()

print('Error handling: OK')
"

# 11. Test dry run mode
python -c "
import asyncio
import tempfile
import os
from forge.tools.file import WriteTool
from forge.tools.base import ExecutionContext

tool = WriteTool()
path = tempfile.mktemp(suffix='.txt')
ctx = ExecutionContext(working_dir='/tmp', dry_run=True)

result = asyncio.run(tool.execute(ctx, file_path=path, content='test'))
assert result.success
assert 'Dry Run' in result.output
assert not os.path.exists(path), 'File should not be created in dry run'
print('Dry run mode: OK')
"

# 12. Run all unit tests
pytest tests/unit/tools/file/ -v --cov=forge.tools.file --cov-report=term-missing

# Expected: All tests pass, coverage ≥ 90%

# 13. Type checking
mypy src/forge/tools/file/ --strict
# Expected: No errors

# 14. Linting
ruff check src/forge/tools/file/
# Expected: No errors
```

---

## Quality Gates

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Test Coverage | ≥ 90% | `pytest --cov` |
| Type Hints | 100% public APIs | `mypy --strict` |
| Lint Errors | 0 | `ruff check` |
| McCabe Complexity | ≤ 10 | `ruff check --select=C901` |
| All Tools Registered | 5 tools | Manual verification |

---

## Files to Create

| File | Purpose |
|------|---------|
| `src/forge/tools/file/__init__.py` | Package exports and registration |
| `src/forge/tools/file/read.py` | ReadTool implementation |
| `src/forge/tools/file/write.py` | WriteTool implementation |
| `src/forge/tools/file/edit.py` | EditTool implementation |
| `src/forge/tools/file/glob.py` | GlobTool implementation |
| `src/forge/tools/file/grep.py` | GrepTool implementation |
| `tests/unit/tools/file/__init__.py` | Test package |
| `tests/unit/tools/file/test_read.py` | ReadTool tests |
| `tests/unit/tools/file/test_write.py` | WriteTool tests |
| `tests/unit/tools/file/test_edit.py` | EditTool tests |
| `tests/unit/tools/file/test_glob.py` | GlobTool tests |
| `tests/unit/tools/file/test_grep.py` | GrepTool tests |
| `tests/unit/tools/file/test_integration.py` | Integration tests |

---

## Dependencies to Verify

Ensure these are in `pyproject.toml`:
```toml
[tool.poetry.dependencies]
pypdf = "^4.0"  # For PDF reading

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-asyncio = "^0.23"
pytest-cov = "^4.1"
```

---

## Manual Testing Checklist

- [ ] Read a Python source file
- [ ] Read a large file (>2000 lines) with offset/limit
- [ ] Read an image file (PNG or JPG)
- [ ] Read a PDF file (if pypdf installed)
- [ ] Read a Jupyter notebook
- [ ] Write a new file
- [ ] Overwrite an existing file
- [ ] Edit a file with single replacement
- [ ] Edit a file with replace_all
- [ ] Glob to find Python files
- [ ] Grep to search for a pattern
- [ ] Grep with context lines
- [ ] Test all tools in dry run mode
- [ ] Verify error messages are clear

---

## Integration Points

Phase 2.2 provides tools for:

| Consumer | What It Uses |
|----------|--------------|
| Phase 3.2 (LangChain) | File tools for agent actions |
| Phase 4.1 (Permissions) | Tool names for permission rules |
| Phase 6.1 (Slash Commands) | Tool execution for commands |

---

## Sign-Off

Phase 2.2 is complete when:

1. [ ] All checklist items above are checked
2. [ ] All verification commands pass
3. [ ] All quality gates are met
4. [ ] Manual testing checklist completed
5. [ ] Code has been reviewed (if applicable)
6. [ ] No TODO comments remain in Phase 2.2 code

---

## Next Phase

After completing Phase 2.2, proceed to:
- **Phase 2.3: Execution Tools**

Phase 2.3 will implement:
- BashTool
- BashOutputTool
- KillShellTool

These all extend BaseTool from Phase 2.1.
