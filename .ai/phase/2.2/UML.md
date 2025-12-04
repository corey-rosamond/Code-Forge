# Phase 2.2: File Tools - UML Diagrams

**Phase:** 2.2
**Name:** File Tools
**Dependencies:** Phase 2.1 (Tool System Foundation)

---

## 1. Class Diagram - File Tools Overview

```mermaid
classDiagram
    class BaseTool {
        <<abstract>>
        +name: str*
        +description: str*
        +category: ToolCategory*
        +parameters: List~ToolParameter~*
        +execute(context, **kwargs) ToolResult
        #_execute(context, **kwargs)* ToolResult
    }

    class ReadTool {
        +name = "Read"
        +category = FILE
        +MAX_LINE_LENGTH = 2000
        +DEFAULT_LIMIT = 2000
        #_execute(context, **kwargs) ToolResult
        -_read_text(path, offset, limit) ToolResult
        -_read_image(path, mime_type) ToolResult
        -_read_pdf(path) ToolResult
        -_read_notebook(path) ToolResult
    }

    class WriteTool {
        +name = "Write"
        +category = FILE
        #_execute(context, **kwargs) ToolResult
    }

    class EditTool {
        +name = "Edit"
        +category = FILE
        #_execute(context, **kwargs) ToolResult
    }

    class GlobTool {
        +name = "Glob"
        +category = FILE
        +DEFAULT_EXCLUDES: Set~str~
        +MAX_RESULTS = 1000
        #_execute(context, **kwargs) ToolResult
        -_filter_excludes(files) List~str~
    }

    class GrepTool {
        +name = "Grep"
        +category = FILE
        +MAX_FILE_SIZE = 10MB
        +DEFAULT_HEAD_LIMIT = 100
        #_execute(context, **kwargs) ToolResult
        -_get_files(path, glob, type) List~str~
        -_is_text_file(path) bool
        -_search_file(path, regex, ...) List~dict~
        -_format_output(results, mode) str
    }

    BaseTool <|-- ReadTool
    BaseTool <|-- WriteTool
    BaseTool <|-- EditTool
    BaseTool <|-- GlobTool
    BaseTool <|-- GrepTool
```

---

## 2. Class Diagram - ReadTool Details

```mermaid
classDiagram
    class ReadTool {
        +name: str
        +description: str
        +category: ToolCategory
        +parameters: List~ToolParameter~
        +MAX_LINE_LENGTH: int = 2000
        +DEFAULT_LIMIT: int = 2000
        +MAX_LIMIT: int = 10000
        +execute(context, **kwargs) ToolResult
        #_execute(context, **kwargs) ToolResult
        -_read_text(path, offset, limit) ToolResult
        -_read_image(path, mime_type) ToolResult
        -_read_pdf(path) ToolResult
        -_read_notebook(path) ToolResult
    }

    class ReadToolParams {
        <<parameters>>
        +file_path: string [required]
        +offset: integer [optional, min=1]
        +limit: integer [optional, min=1, max=10000]
    }

    class ReadToolResult {
        <<result variants>>
        +TextResult: lines with numbers
        +ImageResult: base64 + metadata
        +PDFResult: extracted text + pages
        +NotebookResult: formatted cells
        +ErrorResult: descriptive message
    }

    ReadTool --> ReadToolParams : validates
    ReadTool --> ReadToolResult : returns
```

---

## 3. Class Diagram - GrepTool Details

```mermaid
classDiagram
    class GrepTool {
        +name: str
        +description: str
        +category: ToolCategory
        +parameters: List~ToolParameter~
        +MAX_FILE_SIZE: int
        +DEFAULT_HEAD_LIMIT: int
    }

    class GrepParams {
        <<parameters>>
        +pattern: string [required]
        +path: string [optional]
        +glob: string [optional]
        +type: string [optional]
        +output_mode: enum [optional]
        +-i: boolean [optional]
        +-n: boolean [optional]
        +-A: integer [optional]
        +-B: integer [optional]
        +-C: integer [optional]
        +multiline: boolean [optional]
        +head_limit: integer [optional]
        +offset: integer [optional]
    }

    class OutputMode {
        <<enumeration>>
        content
        files_with_matches
        count
    }

    class TypeFilter {
        <<file types>>
        py: *.py
        js: *.js, *.jsx
        ts: *.ts, *.tsx
        rust: *.rs
        go: *.go
        java: *.java
        c: *.c, *.h
        cpp: *.cpp, *.hpp
        md: *.md
        json: *.json
        yaml: *.yaml, *.yml
    }

    GrepTool --> GrepParams : accepts
    GrepParams --> OutputMode : uses
    GrepParams --> TypeFilter : uses
```

---

## 4. Sequence Diagram - Read File Flow

```mermaid
sequenceDiagram
    participant Agent
    participant Executor as ToolExecutor
    participant Read as ReadTool
    participant FS as FileSystem
    participant MIME as mimetypes

    Agent->>Executor: execute("Read", ctx, file_path="/foo/bar.py")
    Executor->>Read: execute(ctx, file_path="/foo/bar.py")

    Read->>Read: validate_params()
    Read->>Read: check path is absolute

    Read->>FS: os.path.exists("/foo/bar.py")
    FS-->>Read: True

    Read->>FS: os.path.isdir("/foo/bar.py")
    FS-->>Read: False

    Read->>MIME: guess_type("/foo/bar.py")
    MIME-->>Read: ("text/x-python", None)

    Read->>Read: _read_text(path, offset=1, limit=2000)

    Read->>FS: open(file_path, "r")
    FS-->>Read: file handle

    loop For each line
        Read->>Read: format with line number
        Read->>Read: truncate if > 2000 chars
    end

    Read-->>Executor: ToolResult.ok(content, lines_read=150)
    Executor-->>Agent: ToolResult
```

---

## 5. Sequence Diagram - Edit File Flow

```mermaid
sequenceDiagram
    participant Agent
    participant Executor as ToolExecutor
    participant Edit as EditTool
    participant FS as FileSystem

    Agent->>Executor: execute("Edit", ctx, file_path, old_string, new_string)
    Executor->>Edit: execute(ctx, ...)

    Edit->>Edit: validate_params()
    Edit->>Edit: check old_string != new_string

    Edit->>FS: os.path.exists(file_path)
    FS-->>Edit: True

    Edit->>FS: open(file_path, "r")
    FS-->>Edit: content

    Edit->>Edit: count occurrences

    alt No occurrences
        Edit-->>Executor: ToolResult.fail("not found")
    else Multiple occurrences, no replace_all
        Edit-->>Executor: ToolResult.fail("not unique")
    else Valid replacement
        Edit->>Edit: content.replace(old, new)

        alt Dry run mode
            Edit-->>Executor: ToolResult.ok("[Dry Run]...")
        else Normal mode
            Edit->>FS: open(file_path, "w")
            Edit->>FS: write(new_content)
            Edit-->>Executor: ToolResult.ok("Replaced N occurrence(s)")
        end
    end

    Executor-->>Agent: ToolResult
```

---

## 6. Sequence Diagram - Grep Search Flow

```mermaid
sequenceDiagram
    participant Agent
    participant Executor as ToolExecutor
    participant Grep as GrepTool
    participant FS as FileSystem

    Agent->>Executor: execute("Grep", ctx, pattern="TODO", path="src/")
    Executor->>Grep: execute(ctx, ...)

    Grep->>Grep: compile regex pattern
    Grep->>Grep: _get_files(path, glob_filter, type_filter)

    Grep->>FS: os.walk("src/")
    FS-->>Grep: file list

    loop For each file
        Grep->>Grep: _is_text_file(file)

        alt Is text file
            Grep->>FS: open(file, "r")
            FS-->>Grep: content

            Grep->>Grep: _search_file(file, regex, mode, ...)

            loop For each line
                Grep->>Grep: regex.search(line)
                alt Match found
                    Grep->>Grep: collect result with context
                end
            end
        end
    end

    Grep->>Grep: apply offset and head_limit
    Grep->>Grep: _format_output(results, mode)

    Grep-->>Executor: ToolResult.ok(output, total_matches=N)
    Executor-->>Agent: ToolResult
```

---

## 7. Sequence Diagram - Glob Search Flow

```mermaid
sequenceDiagram
    participant Agent
    participant Executor as ToolExecutor
    participant Glob as GlobTool
    participant FS as FileSystem
    participant GlobLib as glob module

    Agent->>Executor: execute("Glob", ctx, pattern="**/*.py")
    Executor->>Glob: execute(ctx, pattern="**/*.py")

    Glob->>Glob: validate_params()
    Glob->>Glob: build full pattern

    Glob->>GlobLib: glob(pattern, recursive=True)
    GlobLib->>FS: filesystem traversal
    FS-->>GlobLib: matching paths
    GlobLib-->>Glob: list of paths

    Glob->>Glob: filter to files only
    Glob->>Glob: _filter_excludes(files)

    Note over Glob: Excludes .git, node_modules,<br/>__pycache__, etc.

    Glob->>Glob: sort by mtime (newest first)
    Glob->>Glob: limit to MAX_RESULTS

    Glob-->>Executor: ToolResult.ok(paths, count=N)
    Executor-->>Agent: ToolResult
```

---

## 8. State Diagram - File Read States

```mermaid
stateDiagram-v2
    [*] --> ValidatingPath: file_path provided

    ValidatingPath --> PathInvalid: not absolute
    ValidatingPath --> CheckingExists: path is absolute

    PathInvalid --> [*]: Return error

    CheckingExists --> FileNotFound: doesn't exist
    CheckingExists --> IsDirectory: is directory
    CheckingExists --> DetectingType: is file

    FileNotFound --> [*]: Return error
    IsDirectory --> [*]: Return error

    DetectingType --> ReadImage: image/*
    DetectingType --> ReadPDF: application/pdf
    DetectingType --> ReadNotebook: .ipynb
    DetectingType --> ReadText: other/text

    ReadImage --> [*]: Return base64 + metadata
    ReadPDF --> [*]: Return extracted text
    ReadNotebook --> [*]: Return formatted cells
    ReadText --> [*]: Return numbered lines
```

---

## 9. State Diagram - Edit Operation States

```mermaid
stateDiagram-v2
    [*] --> ValidatingParams: Parameters provided

    ValidatingParams --> InvalidPath: path not absolute
    ValidatingParams --> SameStrings: old == new
    ValidatingParams --> CheckingFile: params valid

    InvalidPath --> [*]: Return error
    SameStrings --> [*]: Return error

    CheckingFile --> FileNotFound: file doesn't exist
    CheckingFile --> ReadingContent: file exists

    FileNotFound --> [*]: Return error

    ReadingContent --> CountingOccurrences: content loaded
    ReadingContent --> ReadError: permission denied

    ReadError --> [*]: Return error

    CountingOccurrences --> NotFound: count == 0
    CountingOccurrences --> NotUnique: count > 1 && !replace_all
    CountingOccurrences --> Replacing: valid to replace

    NotFound --> [*]: Return error
    NotUnique --> [*]: Return error

    Replacing --> DryRunResult: dry_run == true
    Replacing --> WritingFile: dry_run == false

    DryRunResult --> [*]: Return preview
    WritingFile --> WriteError: write failed
    WritingFile --> Success: write succeeded

    WriteError --> [*]: Return error
    Success --> [*]: Return success
```

---

## 10. Component Diagram - File Tools

```mermaid
flowchart TB
    subgraph FileTools["File Tools Package"]
        READ[ReadTool]
        WRITE[WriteTool]
        EDIT[EditTool]
        GLOB[GlobTool]
        GREP[GrepTool]
    end

    subgraph Core["Core (Phase 2.1)"]
        BASE[BaseTool]
        PARAM[ToolParameter]
        RESULT[ToolResult]
        CTX[ExecutionContext]
        REG[ToolRegistry]
    end

    subgraph External["External Dependencies"]
        PYPDF[pypdf]
        MIME[mimetypes]
        RE[re module]
        GLOBLIB[glob module]
        OS[os/pathlib]
    end

    READ --> BASE
    WRITE --> BASE
    EDIT --> BASE
    GLOB --> BASE
    GREP --> BASE

    BASE --> PARAM
    BASE --> RESULT
    BASE --> CTX

    READ --> PYPDF
    READ --> MIME
    WRITE --> OS
    EDIT --> OS
    GLOB --> GLOBLIB
    GLOB --> OS
    GREP --> RE
    GREP --> GLOBLIB
    GREP --> OS

    REG --> READ
    REG --> WRITE
    REG --> EDIT
    REG --> GLOB
    REG --> GREP
```

---

## 11. Activity Diagram - Grep File Search

```mermaid
flowchart TD
    START([execute]) --> COMPILE{Compile regex}

    COMPILE -->|Invalid| REGEX_ERR[Return regex error]
    COMPILE -->|Valid| GET_FILES[Get files to search]

    GET_FILES --> FILE_LOOP{More files?}

    FILE_LOOP -->|Yes| CHECK_TEXT{Is text file?}
    FILE_LOOP -->|No| PAGINATE[Apply offset/limit]

    CHECK_TEXT -->|No| FILE_LOOP
    CHECK_TEXT -->|Yes| OPEN_FILE[Open file]

    OPEN_FILE --> LINE_LOOP{More lines?}

    LINE_LOOP -->|Yes| SEARCH[Search line with regex]
    LINE_LOOP -->|No| FILE_LOOP

    SEARCH --> MATCH{Match found?}

    MATCH -->|No| LINE_LOOP
    MATCH -->|Yes| MODE{Output mode?}

    MODE -->|files_with_matches| ADD_FILE[Add file to results]
    MODE -->|count| INC_COUNT[Increment count]
    MODE -->|content| GET_CTX[Get context lines]

    ADD_FILE --> FILE_LOOP
    INC_COUNT --> LINE_LOOP
    GET_CTX --> ADD_RESULT[Add to results]
    ADD_RESULT --> LINE_LOOP

    PAGINATE --> FORMAT[Format output]
    FORMAT --> RETURN([Return ToolResult])
    REGEX_ERR --> RETURN
```

---

## 12. Package Structure Diagram

```mermaid
flowchart TD
    subgraph opencode_tools["src/opencode/tools/"]
        INIT["__init__.py"]
        BASE["base.py"]
        REG["registry.py"]
        EXEC["executor.py"]

        subgraph file_pkg["file/"]
            FILE_INIT["__init__.py"]
            READ_PY["read.py"]
            WRITE_PY["write.py"]
            EDIT_PY["edit.py"]
            GLOB_PY["glob.py"]
            GREP_PY["grep.py"]
        end
    end

    subgraph tests_tools["tests/unit/tools/"]
        TEST_BASE["test_base.py"]
        TEST_REG["test_registry.py"]
        TEST_EXEC["test_executor.py"]

        subgraph test_file["file/"]
            TEST_READ["test_read.py"]
            TEST_WRITE["test_write.py"]
            TEST_EDIT["test_edit.py"]
            TEST_GLOB["test_glob.py"]
            TEST_GREP["test_grep.py"]
        end
    end

    INIT --> BASE
    INIT --> REG
    INIT --> EXEC
    INIT --> FILE_INIT

    FILE_INIT --> READ_PY
    FILE_INIT --> WRITE_PY
    FILE_INIT --> EDIT_PY
    FILE_INIT --> GLOB_PY
    FILE_INIT --> GREP_PY

    TEST_READ --> READ_PY
    TEST_WRITE --> WRITE_PY
    TEST_EDIT --> EDIT_PY
    TEST_GLOB --> GLOB_PY
    TEST_GREP --> GREP_PY
```

---

## 13. Tool Parameter Schemas

### ReadTool Parameters
```json
{
  "type": "object",
  "properties": {
    "file_path": {
      "type": "string",
      "description": "The absolute path to the file to read",
      "minLength": 1
    },
    "offset": {
      "type": "integer",
      "description": "Line number to start reading from",
      "minimum": 1
    },
    "limit": {
      "type": "integer",
      "description": "Maximum number of lines to read",
      "minimum": 1,
      "maximum": 10000
    }
  },
  "required": ["file_path"]
}
```

### EditTool Parameters
```json
{
  "type": "object",
  "properties": {
    "file_path": {
      "type": "string",
      "description": "The absolute path to the file to modify"
    },
    "old_string": {
      "type": "string",
      "description": "The text to replace"
    },
    "new_string": {
      "type": "string",
      "description": "The text to replace it with"
    },
    "replace_all": {
      "type": "boolean",
      "description": "Replace all occurrences",
      "default": false
    }
  },
  "required": ["file_path", "old_string", "new_string"]
}
```

### GrepTool Parameters
```json
{
  "type": "object",
  "properties": {
    "pattern": {
      "type": "string",
      "description": "Regular expression pattern"
    },
    "path": {
      "type": "string",
      "description": "File or directory to search"
    },
    "glob": {
      "type": "string",
      "description": "Glob pattern to filter files"
    },
    "output_mode": {
      "type": "string",
      "enum": ["content", "files_with_matches", "count"],
      "default": "files_with_matches"
    },
    "-i": {
      "type": "boolean",
      "description": "Case insensitive",
      "default": false
    },
    "-A": {
      "type": "integer",
      "description": "Lines after match",
      "minimum": 0
    },
    "-B": {
      "type": "integer",
      "description": "Lines before match",
      "minimum": 0
    }
  },
  "required": ["pattern"]
}
```

---

## Notes

- All file tools inherit from BaseTool (Phase 2.1)
- ReadTool handles multiple file types (text, image, PDF, notebook)
- EditTool requires the file to be read first (enforced by workflow)
- GlobTool and GrepTool exclude common directories by default
- All tools support dry_run mode through ExecutionContext
- Security validations prevent path traversal attacks
