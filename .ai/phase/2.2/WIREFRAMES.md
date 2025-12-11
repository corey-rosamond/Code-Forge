# Phase 2.2: File Tools - Wireframes

**Phase:** 2.2
**Name:** File Tools
**Dependencies:** Phase 2.1 (Tool System Foundation)

---

## Overview

This document shows the expected output formats and user-visible results from the file tools. These wireframes demonstrate how tool results will appear in the REPL and logs.

---

## 1. Read Tool Output

### Text File with Line Numbers
```
┌─────────────────────────────────────────────────────────────────────┐
│ Read: /home/user/project/src/main.py                                │
├─────────────────────────────────────────────────────────────────────┤
│      1	#!/usr/bin/env python3                                       │
│      2	"""Main module for the application."""                       │
│      3	                                                              │
│      4	import sys                                                    │
│      5	from pathlib import Path                                      │
│      6	                                                              │
│      7	from forge.cli import main                                 │
│      8	                                                              │
│      9	                                                              │
│     10	if __name__ == "__main__":                                    │
│     11	    sys.exit(main())                                          │
├─────────────────────────────────────────────────────────────────────┤
│ Lines: 11 | File: 245 bytes                                         │
└─────────────────────────────────────────────────────────────────────┘
```

### Truncated Output (Large File)
```
┌─────────────────────────────────────────────────────────────────────┐
│ Read: /home/user/project/data/large.txt (showing lines 100-199)     │
├─────────────────────────────────────────────────────────────────────┤
│    100	Data line 100                                                 │
│    101	Data line 101                                                 │
│    ...                                                               │
│    198	Data line 198                                                 │
│    199	Data line 199                                                 │
├─────────────────────────────────────────────────────────────────────┤
│ Showing 100 of 5000 lines | Use offset/limit to see more            │
└─────────────────────────────────────────────────────────────────────┘
```

### Long Line Truncation
```
│    42	def very_long_function_name_that_takes_many_parameters(param_...│
│         ↑ Line truncated (2543 chars, showing 2000)                  │
```

### Image File Result
```
┌─────────────────────────────────────────────────────────────────────┐
│ Read: /home/user/project/assets/logo.png                            │
├─────────────────────────────────────────────────────────────────────┤
│ [Image: image/png]                                                  │
│                                                                     │
│ Dimensions: 512x512                                                 │
│ Size: 24,576 bytes                                                  │
│                                                                     │
│ Base64: iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hA...           │
│         (truncated, full data in metadata)                          │
└─────────────────────────────────────────────────────────────────────┘
```

### PDF File Result
```
┌─────────────────────────────────────────────────────────────────────┐
│ Read: /home/user/documents/report.pdf                               │
├─────────────────────────────────────────────────────────────────────┤
│ --- Page 1 ---                                                      │
│ Annual Report 2024                                                  │
│                                                                     │
│ Executive Summary                                                   │
│ This report covers the fiscal year...                               │
│                                                                     │
│ --- Page 2 ---                                                      │
│ Financial Overview                                                  │
│ Revenue increased by 15% compared to...                             │
│                                                                     │
│ --- Page 3 ---                                                      │
│ ...                                                                 │
├─────────────────────────────────────────────────────────────────────┤
│ Pages: 3 | PDF version: 1.7                                         │
└─────────────────────────────────────────────────────────────────────┘
```

### Jupyter Notebook Result
```
┌─────────────────────────────────────────────────────────────────────┐
│ Read: /home/user/notebooks/analysis.ipynb                           │
├─────────────────────────────────────────────────────────────────────┤
│ --- Cell 1 (markdown) ---                                           │
│ # Data Analysis Notebook                                            │
│ This notebook analyzes sales data from Q4.                          │
│                                                                     │
│ --- Cell 2 (code) ---                                               │
│ import pandas as pd                                                 │
│ import matplotlib.pyplot as plt                                     │
│                                                                     │
│ --- Cell 3 (code) ---                                               │
│ df = pd.read_csv('sales.csv')                                       │
│ df.head()                                                           │
│                                                                     │
│ Output:                                                             │
│    date       product  quantity  revenue                            │
│ 0  2024-01-01 Widget A      100    1500.00                          │
│ 1  2024-01-02 Widget B       75    1125.00                          │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ Cells: 3 | Kernel: Python 3                                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Write Tool Output

### New File Created
```
┌─────────────────────────────────────────────────────────────────────┐
│ Write: /home/user/project/src/new_module.py                         │
├─────────────────────────────────────────────────────────────────────┤
│ ✓ Created /home/user/project/src/new_module.py                      │
│   Bytes written: 1,234                                              │
└─────────────────────────────────────────────────────────────────────┘
```

### Existing File Updated
```
┌─────────────────────────────────────────────────────────────────────┐
│ Write: /home/user/project/src/existing.py                           │
├─────────────────────────────────────────────────────────────────────┤
│ ✓ Updated /home/user/project/src/existing.py                        │
│   Bytes written: 2,456                                              │
└─────────────────────────────────────────────────────────────────────┘
```

### Dry Run Mode
```
┌─────────────────────────────────────────────────────────────────────┐
│ Write: /home/user/project/src/new_module.py [DRY RUN]               │
├─────────────────────────────────────────────────────────────────────┤
│ [Dry Run] Would create /home/user/project/src/new_module.py         │
│   Bytes: 1,234                                                      │
│   No changes made                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Directory Created
```
┌─────────────────────────────────────────────────────────────────────┐
│ Write: /home/user/project/new/path/file.py                          │
├─────────────────────────────────────────────────────────────────────┤
│ ✓ Created directory: /home/user/project/new/path/                   │
│ ✓ Created /home/user/project/new/path/file.py                       │
│   Bytes written: 567                                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Edit Tool Output

### Single Replacement
```
┌─────────────────────────────────────────────────────────────────────┐
│ Edit: /home/user/project/src/config.py                              │
├─────────────────────────────────────────────────────────────────────┤
│ Replaced 1 occurrence in /home/user/project/src/config.py           │
│                                                                     │
│ Line 15:                                                            │
│ - DEBUG = True                                                      │
│ + DEBUG = False                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Multiple Replacements
```
┌─────────────────────────────────────────────────────────────────────┐
│ Edit: /home/user/project/src/utils.py                               │
├─────────────────────────────────────────────────────────────────────┤
│ Replaced 5 occurrences in /home/user/project/src/utils.py           │
│                                                                     │
│ Lines: 12, 28, 45, 67, 89                                           │
│ - old_function_name                                                 │
│ + new_function_name                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Dry Run Mode
```
┌─────────────────────────────────────────────────────────────────────┐
│ Edit: /home/user/project/src/config.py [DRY RUN]                    │
├─────────────────────────────────────────────────────────────────────┤
│ [Dry Run] Would replace 1 occurrence                                │
│                                                                     │
│ Line 15:                                                            │
│ - DEBUG = True                                                      │
│ + DEBUG = False                                                     │
│                                                                     │
│ No changes made                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Edit Tool Error Messages

### String Not Found
```
┌─────────────────────────────────────────────────────────────────────┐
│ Edit Error                                                          │
├─────────────────────────────────────────────────────────────────────┤
│ old_string not found in /home/user/project/src/config.py            │
│                                                                     │
│ Searched for:                                                       │
│   "DEBUG = true"                                                    │
│                                                                     │
│ Tips:                                                               │
│ • Make sure you've read the file first                              │
│ • Check for exact whitespace and indentation                        │
│ • The match must be exact (case-sensitive)                          │
└─────────────────────────────────────────────────────────────────────┘
```

### Non-Unique String
```
┌─────────────────────────────────────────────────────────────────────┐
│ Edit Error                                                          │
├─────────────────────────────────────────────────────────────────────┤
│ old_string found 3 times (lines: [15, 42, 78])                      │
│                                                                     │
│ Searched for:                                                       │
│   "return None"                                                     │
│                                                                     │
│ Options:                                                            │
│ 1. Provide more surrounding context to make it unique               │
│ 2. Use replace_all=true to replace all occurrences                  │
│                                                                     │
│ Example with more context:                                          │
│   old_string: "def process():\n    return None"                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Glob Tool Output

### Files Found
```
┌─────────────────────────────────────────────────────────────────────┐
│ Glob: **/*.py in /home/user/project                                 │
├─────────────────────────────────────────────────────────────────────┤
│ /home/user/project/src/main.py                                      │
│ /home/user/project/src/config.py                                    │
│ /home/user/project/src/utils/helpers.py                             │
│ /home/user/project/src/utils/formatters.py                          │
│ /home/user/project/tests/test_main.py                               │
│ /home/user/project/tests/test_config.py                             │
├─────────────────────────────────────────────────────────────────────┤
│ Found: 6 files (sorted by modification time)                        │
└─────────────────────────────────────────────────────────────────────┘
```

### No Files Found
```
┌─────────────────────────────────────────────────────────────────────┐
│ Glob: **/*.xyz in /home/user/project                                │
├─────────────────────────────────────────────────────────────────────┤
│ No files matching pattern "**/*.xyz"                                │
└─────────────────────────────────────────────────────────────────────┘
```

### Results Truncated
```
┌─────────────────────────────────────────────────────────────────────┐
│ Glob: **/*.js in /home/user/large-project                           │
├─────────────────────────────────────────────────────────────────────┤
│ /home/user/large-project/src/index.js                               │
│ /home/user/large-project/src/app.js                                 │
│ ... (showing first 1000 of 2543 files)                              │
├─────────────────────────────────────────────────────────────────────┤
│ Found: 2543 files (showing 1000, truncated)                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Grep Tool Output

### Content Mode (Default)
```
┌─────────────────────────────────────────────────────────────────────┐
│ Grep: "TODO" in /home/user/project                                  │
├─────────────────────────────────────────────────────────────────────┤
│ /home/user/project/src/main.py:42                                   │
│ >42:    # TODO: Implement error handling                            │
│                                                                     │
│ /home/user/project/src/utils.py:15                                  │
│ >15:    # TODO: Add caching                                         │
│                                                                     │
│ /home/user/project/src/utils.py:78                                  │
│ >78:    # TODO: Optimize this loop                                  │
├─────────────────────────────────────────────────────────────────────┤
│ Matches: 3 in 2 files                                               │
└─────────────────────────────────────────────────────────────────────┘
```

### Content Mode with Context
```
┌─────────────────────────────────────────────────────────────────────┐
│ Grep: "class.*Error" with -B 1 -A 2                                 │
├─────────────────────────────────────────────────────────────────────┤
│ /home/user/project/src/errors.py:10                                 │
│  9:                                                                 │
│ >10:class ValidationError(Exception):                               │
│  11:    """Raised when validation fails."""                         │
│  12:    pass                                                        │
│                                                                     │
│ /home/user/project/src/errors.py:15                                 │
│  14:                                                                │
│ >15:class ConfigError(Exception):                                   │
│  16:    """Raised when configuration is invalid."""                 │
│  17:    pass                                                        │
├─────────────────────────────────────────────────────────────────────┤
│ Matches: 2 in 1 file                                                │
└─────────────────────────────────────────────────────────────────────┘
```

### Files With Matches Mode
```
┌─────────────────────────────────────────────────────────────────────┐
│ Grep: "import asyncio" (files_with_matches)                         │
├─────────────────────────────────────────────────────────────────────┤
│ /home/user/project/src/async_utils.py                               │
│ /home/user/project/src/server.py                                    │
│ /home/user/project/src/client.py                                    │
│ /home/user/project/tests/test_async.py                              │
├─────────────────────────────────────────────────────────────────────┤
│ Files: 4                                                            │
└─────────────────────────────────────────────────────────────────────┘
```

### Count Mode
```
┌─────────────────────────────────────────────────────────────────────┐
│ Grep: "print" (count mode)                                          │
├─────────────────────────────────────────────────────────────────────┤
│ /home/user/project/src/main.py: 5                                   │
│ /home/user/project/src/debug.py: 23                                 │
│ /home/user/project/tests/test_main.py: 8                            │
├─────────────────────────────────────────────────────────────────────┤
│ Total: 36 matches in 3 files                                        │
└─────────────────────────────────────────────────────────────────────┘
```

### No Matches
```
┌─────────────────────────────────────────────────────────────────────┐
│ Grep: "xyznonexistent" in /home/user/project                        │
├─────────────────────────────────────────────────────────────────────┤
│ No matches found                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Paginated Results
```
┌─────────────────────────────────────────────────────────────────────┐
│ Grep: "function" (offset=20, limit=10)                              │
├─────────────────────────────────────────────────────────────────────┤
│ /home/user/project/src/utils.js:145                                 │
│ >145:function validateInput(data) {                                 │
│ ... (8 more results)                                                │
├─────────────────────────────────────────────────────────────────────┤
│ Showing: 21-30 of 156 matches                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. Error Messages

### File Not Found
```
┌─────────────────────────────────────────────────────────────────────┐
│ Error: File not found                                               │
├─────────────────────────────────────────────────────────────────────┤
│ File not found: /home/user/project/missing.py                       │
│                                                                     │
│ Did you mean one of these?                                          │
│ • /home/user/project/main.py                                        │
│ • /home/user/project/module.py                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Permission Denied
```
┌─────────────────────────────────────────────────────────────────────┐
│ Error: Permission denied                                            │
├─────────────────────────────────────────────────────────────────────┤
│ Permission denied: /etc/shadow                                      │
│                                                                     │
│ The current user does not have permission to access this file.      │
└─────────────────────────────────────────────────────────────────────┘
```

### Invalid Path
```
┌─────────────────────────────────────────────────────────────────────┐
│ Error: Invalid path                                                 │
├─────────────────────────────────────────────────────────────────────┤
│ file_path must be an absolute path                                  │
│                                                                     │
│ Received: relative/path/file.py                                     │
│ Expected: /absolute/path/file.py                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Binary File
```
┌─────────────────────────────────────────────────────────────────────┐
│ Error: Binary file                                                  │
├─────────────────────────────────────────────────────────────────────┤
│ Cannot read binary file: /home/user/project/data.bin                │
│                                                                     │
│ This file appears to be binary (contains null bytes).               │
│ Use a hex editor or specialized tool to view binary files.          │
└─────────────────────────────────────────────────────────────────────┘
```

### Invalid Regex
```
┌─────────────────────────────────────────────────────────────────────┐
│ Error: Invalid regex                                                │
├─────────────────────────────────────────────────────────────────────┤
│ Invalid regex pattern: [unclosed bracket                            │
│                                                                     │
│ Error details: unterminated character set at position 0             │
│                                                                     │
│ Tips:                                                               │
│ • Use \[ to match a literal bracket                                 │
│ • Make sure all brackets are properly closed                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Tool Schema Display

### Read Tool Schema (OpenAI Format)
```json
{
  "type": "function",
  "function": {
    "name": "Read",
    "description": "Reads a file from the local filesystem...",
    "parameters": {
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
  }
}
```

---

## 9. Log Output Examples

### Info Level
```
2024-01-15 10:30:45.123 INFO  [tools.file] Executing Read: /home/user/test.py
2024-01-15 10:30:45.135 INFO  [tools.file] Read succeeded: 150 lines
```

### Debug Level
```
2024-01-15 10:30:45.123 DEBUG [tools.file] Read params: file_path=/home/user/test.py, offset=1, limit=2000
2024-01-15 10:30:45.124 DEBUG [tools.file] File type detected: text/x-python
2024-01-15 10:30:45.135 DEBUG [tools.file] Read complete: 150 lines, 4567 bytes
```

### Warning Level
```
2024-01-15 10:30:45.135 WARN  [tools.file] Edit failed: old_string not found in /home/user/test.py
```

---

## Notes

- All output uses Rich library for formatting in the actual REPL
- Line numbers use tab-alignment for readability
- Metadata is included in ToolResult but may not be displayed to user
- Error messages provide actionable suggestions where possible
- Long outputs are truncated with indicators
