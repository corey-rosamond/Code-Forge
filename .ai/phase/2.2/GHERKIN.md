# Phase 2.2: File Tools - Gherkin Specifications

**Phase:** 2.2
**Name:** File Tools
**Dependencies:** Phase 2.1 (Tool System Foundation)

---

## Feature: Read Tool

### Scenario: Read entire text file
```gherkin
Given a text file exists at "/home/user/test.txt"
And the file contains:
  """
  Line 1
  Line 2
  Line 3
  """
When I execute ReadTool with file_path="/home/user/test.txt"
Then the result should be successful
And the output should contain line numbers
And the output should be:
  """
       1	Line 1
       2	Line 2
       3	Line 3
  """
And metadata should contain lines_read=3
```

### Scenario: Read file with offset and limit
```gherkin
Given a text file exists at "/home/user/large.txt"
And the file contains 1000 lines
When I execute ReadTool with:
  | file_path | /home/user/large.txt |
  | offset    | 100                  |
  | limit     | 50                   |
Then the result should be successful
And the output should start at line 100
And the output should contain 50 lines
And metadata should contain:
  | lines_read | 50   |
  | offset     | 100  |
  | limit      | 50   |
  | truncated  | true |
```

### Scenario: Read non-existent file
```gherkin
Given no file exists at "/home/user/missing.txt"
When I execute ReadTool with file_path="/home/user/missing.txt"
Then the result should be failed
And the error should be "File not found: /home/user/missing.txt"
```

### Scenario: Read directory instead of file
```gherkin
Given a directory exists at "/home/user/mydir"
When I execute ReadTool with file_path="/home/user/mydir"
Then the result should be failed
And the error should contain "Cannot read directory"
```

### Scenario: Read file with relative path
```gherkin
Given a text file exists at "/home/user/test.txt"
When I execute ReadTool with file_path="test.txt"
Then the result should be failed
And the error should contain "must be an absolute path"
```

### Scenario: Read file with long lines
```gherkin
Given a text file exists with a line of 3000 characters
When I execute ReadTool with file_path="/home/user/long.txt"
Then the result should be successful
And lines longer than 2000 characters should be truncated
And truncated lines should end with "..."
```

### Scenario: Read binary file
```gherkin
Given a binary file exists at "/home/user/binary.exe"
When I execute ReadTool with file_path="/home/user/binary.exe"
Then the result should be failed
And the error should contain "binary file"
```

### Scenario: Read image file
```gherkin
Given an image file exists at "/home/user/photo.png"
When I execute ReadTool with file_path="/home/user/photo.png"
Then the result should be successful
And metadata should contain is_image=true
And metadata should contain base64_data
And metadata should contain mime_type="image/png"
```

### Scenario: Read PDF file
```gherkin
Given a PDF file exists at "/home/user/document.pdf"
And the PDF has 3 pages
When I execute ReadTool with file_path="/home/user/document.pdf"
Then the result should be successful
And the output should contain "--- Page 1 ---"
And the output should contain "--- Page 2 ---"
And the output should contain "--- Page 3 ---"
And metadata should contain is_pdf=true
And metadata should contain page_count=3
```

### Scenario: Read Jupyter notebook
```gherkin
Given a Jupyter notebook exists at "/home/user/analysis.ipynb"
And the notebook has 5 cells
When I execute ReadTool with file_path="/home/user/analysis.ipynb"
Then the result should be successful
And the output should contain "--- Cell 1"
And the output should contain cell types (code/markdown)
And the output should contain cell outputs
And metadata should contain is_notebook=true
And metadata should contain cell_count=5
```

### Scenario: Read file with permission denied
```gherkin
Given a file exists at "/etc/shadow"
And the file is not readable by current user
When I execute ReadTool with file_path="/etc/shadow"
Then the result should be failed
And the error should be "Permission denied: /etc/shadow"
```

### Scenario: Read file with encoding issues
```gherkin
Given a file exists with mixed encodings
When I execute ReadTool with file_path="/home/user/mixed.txt"
Then the result should be successful
And encoding errors should be replaced with fallback characters
```

---

## Feature: Write Tool

### Scenario: Write new file
```gherkin
Given no file exists at "/home/user/new.txt"
When I execute WriteTool with:
  | file_path | /home/user/new.txt |
  | content   | Hello, World!      |
Then the result should be successful
And the file "/home/user/new.txt" should exist
And the file should contain "Hello, World!"
And the output should contain "Created"
And metadata should contain bytes_written=13
And metadata should contain created=true
```

### Scenario: Overwrite existing file
```gherkin
Given a file exists at "/home/user/existing.txt"
And the file contains "Old content"
When I execute WriteTool with:
  | file_path | /home/user/existing.txt |
  | content   | New content             |
Then the result should be successful
And the file should contain "New content"
And the output should contain "Updated"
And metadata should contain created=false
```

### Scenario: Write file creates parent directories
```gherkin
Given no directory exists at "/home/user/new/nested/dir"
When I execute WriteTool with:
  | file_path | /home/user/new/nested/dir/file.txt |
  | content   | Content here                        |
Then the result should be successful
And the directory "/home/user/new/nested/dir" should exist
And the file should exist
```

### Scenario: Write file with relative path
```gherkin
When I execute WriteTool with:
  | file_path | relative/path.txt |
  | content   | Content           |
Then the result should be failed
And the error should contain "must be an absolute path"
```

### Scenario: Write file in dry run mode
```gherkin
Given no file exists at "/home/user/dryrun.txt"
And the execution context has dry_run=true
When I execute WriteTool with:
  | file_path | /home/user/dryrun.txt |
  | content   | Test content          |
Then the result should be successful
And the output should contain "[Dry Run]"
And the file "/home/user/dryrun.txt" should NOT exist
And metadata should contain dry_run=true
```

### Scenario: Write file with permission denied
```gherkin
Given a directory exists at "/root/protected"
And the directory is not writable
When I execute WriteTool with:
  | file_path | /root/protected/file.txt |
  | content   | Content                   |
Then the result should be failed
And the error should contain "Permission denied"
```

### Scenario: Write empty content
```gherkin
When I execute WriteTool with:
  | file_path | /home/user/empty.txt |
  | content   |                      |
Then the result should be successful
And the file should exist
And the file should be empty
And metadata should contain bytes_written=0
```

---

## Feature: Edit Tool

### Scenario: Replace single occurrence
```gherkin
Given a file exists at "/home/user/code.py"
And the file contains:
  """
  def hello():
      print("Hello")
  """
When I execute EditTool with:
  | file_path  | /home/user/code.py  |
  | old_string | "Hello"             |
  | new_string | "Hi"                |
Then the result should be successful
And the file should contain:
  """
  def hello():
      print("Hi")
  """
And metadata should contain replacements=1
```

### Scenario: Replace all occurrences
```gherkin
Given a file exists at "/home/user/code.py"
And the file contains "foo" 5 times
When I execute EditTool with:
  | file_path   | /home/user/code.py |
  | old_string  | foo                |
  | new_string  | bar                |
  | replace_all | true               |
Then the result should be successful
And the file should contain "bar" 5 times
And the file should not contain "foo"
And metadata should contain replacements=5
```

### Scenario: String not found
```gherkin
Given a file exists at "/home/user/code.py"
And the file does not contain "nonexistent"
When I execute EditTool with:
  | file_path  | /home/user/code.py |
  | old_string | nonexistent        |
  | new_string | replacement        |
Then the result should be failed
And the error should contain "not found"
```

### Scenario: Non-unique string without replace_all
```gherkin
Given a file exists at "/home/user/code.py"
And the file contains "print" on lines 5, 10, and 15
When I execute EditTool with:
  | file_path  | /home/user/code.py |
  | old_string | print              |
  | new_string | log                |
Then the result should be failed
And the error should contain "found 3 times"
And the error should contain "lines: [5, 10, 15]"
And the error should suggest using replace_all or more context
```

### Scenario: Same old and new string
```gherkin
Given a file exists at "/home/user/code.py"
When I execute EditTool with:
  | file_path  | /home/user/code.py |
  | old_string | same               |
  | new_string | same               |
Then the result should be failed
And the error should contain "must be different"
```

### Scenario: Edit file in dry run mode
```gherkin
Given a file exists at "/home/user/code.py"
And the file contains "original"
And the execution context has dry_run=true
When I execute EditTool with:
  | file_path  | /home/user/code.py |
  | old_string | original           |
  | new_string | modified           |
Then the result should be successful
And the output should contain "[Dry Run]"
And the file should still contain "original"
And metadata should contain dry_run=true
```

### Scenario: Edit non-existent file
```gherkin
Given no file exists at "/home/user/missing.py"
When I execute EditTool with:
  | file_path  | /home/user/missing.py |
  | old_string | foo                   |
  | new_string | bar                   |
Then the result should be failed
And the error should contain "File not found"
```

### Scenario: Edit with whitespace preservation
```gherkin
Given a file exists with specific indentation
When I execute EditTool with old_string including whitespace
Then the replacement should preserve surrounding whitespace
And the file should maintain its original line endings
```

---

## Feature: Glob Tool

### Scenario: Find Python files recursively
```gherkin
Given a project directory at "/home/user/project"
And the directory contains:
  | src/main.py           |
  | src/utils/helpers.py  |
  | tests/test_main.py    |
  | README.md             |
When I execute GlobTool with:
  | pattern | **/*.py                |
  | path    | /home/user/project     |
Then the result should be successful
And the output should contain "src/main.py"
And the output should contain "src/utils/helpers.py"
And the output should contain "tests/test_main.py"
And the output should NOT contain "README.md"
And metadata should contain count=3
```

### Scenario: Find files with specific pattern
```gherkin
Given a project directory with multiple file types
When I execute GlobTool with pattern="src/**/*.tsx"
Then the result should contain only .tsx files in src/
And files should be sorted by modification time (newest first)
```

### Scenario: Glob excludes common directories
```gherkin
Given a project directory with:
  | src/app.py                    |
  | .git/objects/abc123           |
  | node_modules/package/index.js |
  | __pycache__/module.cpython    |
When I execute GlobTool with pattern="**/*"
Then the output should contain "src/app.py"
And the output should NOT contain ".git"
And the output should NOT contain "node_modules"
And the output should NOT contain "__pycache__"
```

### Scenario: Glob with no matches
```gherkin
Given a project directory with no .xyz files
When I execute GlobTool with pattern="**/*.xyz"
Then the result should be successful
And the output should be empty
And metadata should contain count=0
```

### Scenario: Glob limits results
```gherkin
Given a project with 2000 Python files
When I execute GlobTool with pattern="**/*.py"
Then the result should contain at most 1000 files
And metadata should contain truncated=true
```

### Scenario: Glob with default path
```gherkin
Given the execution context has working_dir="/home/user/project"
When I execute GlobTool with pattern="*.py" and no path
Then the search should be performed in "/home/user/project"
```

### Scenario: Glob directory not found
```gherkin
Given no directory exists at "/nonexistent/path"
When I execute GlobTool with:
  | pattern | **/*.py            |
  | path    | /nonexistent/path  |
Then the result should be failed
And the error should contain "Directory not found"
```

---

## Feature: Grep Tool

### Scenario: Search with simple pattern
```gherkin
Given a file exists at "/home/user/code.py"
And the file contains "TODO: fix this bug" on line 42
When I execute GrepTool with:
  | pattern     | TODO                       |
  | path        | /home/user/code.py         |
  | output_mode | content                    |
Then the result should be successful
And the output should contain "code.py:42"
And the output should contain "TODO: fix this bug"
```

### Scenario: Search case-insensitive
```gherkin
Given files containing "Error", "ERROR", and "error"
When I execute GrepTool with:
  | pattern | error |
  | -i      | true  |
Then all variations should be matched
```

### Scenario: Search with context lines
```gherkin
Given a file with a match at line 10
When I execute GrepTool with:
  | pattern | match_text |
  | -B      | 2          |
  | -A      | 2          |
Then the output should include lines 8-12
And the matching line should be marked with ">"
And context lines should be marked with " "
```

### Scenario: Search files_with_matches mode
```gherkin
Given multiple files containing "pattern"
When I execute GrepTool with:
  | pattern     | pattern            |
  | output_mode | files_with_matches |
Then the output should be a list of file paths
And each file should appear only once
```

### Scenario: Search count mode
```gherkin
Given files with varying match counts
When I execute GrepTool with:
  | pattern     | pattern |
  | output_mode | count   |
Then the output should show "filename: N" for each file
```

### Scenario: Search with file type filter
```gherkin
Given a project with .py, .js, and .ts files
When I execute GrepTool with:
  | pattern | function |
  | type    | py       |
Then only Python files should be searched
And results should not include .js or .ts files
```

### Scenario: Search with glob filter
```gherkin
Given a project with various file types
When I execute GrepTool with:
  | pattern | import |
  | glob    | *.tsx  |
Then only .tsx files should be searched
```

### Scenario: Search with regex pattern
```gherkin
Given files containing various function definitions
When I execute GrepTool with pattern="def \w+\([^)]*\):"
Then all Python function definitions should be matched
```

### Scenario: Search with invalid regex
```gherkin
When I execute GrepTool with pattern="[invalid(regex"
Then the result should be failed
And the error should contain "Invalid regex pattern"
```

### Scenario: Search with multiline mode
```gherkin
Given a file containing a multiline string
When I execute GrepTool with:
  | pattern   | start.*end |
  | multiline | true       |
Then patterns spanning multiple lines should be matched
```

### Scenario: Search with pagination
```gherkin
Given a codebase with 500 matches for "TODO"
When I execute GrepTool with:
  | pattern    | TODO |
  | head_limit | 20   |
  | offset     | 0    |
Then the result should contain 20 matches
And metadata should contain total_matches=500
And metadata should contain returned_matches=20
```

### Scenario: Search no matches found
```gherkin
Given a codebase with no matches for "xyznonexistent"
When I execute GrepTool with pattern="xyznonexistent"
Then the result should be successful
And the output should be "No matches found"
And metadata should contain total_matches=0
```

### Scenario: Search binary files skipped
```gherkin
Given a directory with text and binary files
When I execute GrepTool with pattern="pattern"
Then binary files should be skipped
And only text files should be searched
```

---

## Feature: File Tools Registration

### Scenario: All file tools are registered
```gherkin
Given the OpenCode application initializes
When I call register_file_tools(registry)
Then the registry should contain "Read" tool
And the registry should contain "Write" tool
And the registry should contain "Edit" tool
And the registry should contain "Glob" tool
And the registry should contain "Grep" tool
And all tools should have category=FILE
```

### Scenario: File tools generate valid schemas
```gherkin
Given all file tools are registered
When I call get_all_schemas("openai")
Then each tool should have a valid OpenAI function schema
And each schema should include all required parameters
And each schema should match the tool's parameter definitions
```

---

## Feature: Security

### Scenario: Path traversal prevention
```gherkin
Given the working directory is "/home/user/project"
When I execute ReadTool with file_path="/home/user/project/../../../etc/passwd"
Then appropriate security validation should be applied
And access outside allowed paths should be restricted
```

### Scenario: Symlink handling
```gherkin
Given a symlink at "/home/user/project/link" pointing to "/etc/passwd"
When I execute ReadTool with file_path="/home/user/project/link"
Then the tool should handle symlinks according to security policy
```

---

## Feature: Integration Tests

### Scenario: Read-Edit-Verify workflow
```gherkin
Given a file exists at "/home/user/test.py"
And the file contains "old_value = 1"
When I:
  1. Execute ReadTool to read the file
  2. Execute EditTool to change "old_value" to "new_value"
  3. Execute ReadTool to verify the change
Then the final read should show "new_value = 1"
```

### Scenario: Glob-Grep workflow
```gherkin
Given a project directory with Python files
When I:
  1. Execute GlobTool to find all .py files
  2. Execute GrepTool to search for "class" in found files
Then I should find all class definitions in Python files
```

### Scenario: Write-Read roundtrip
```gherkin
Given no file exists at "/home/user/roundtrip.txt"
When I:
  1. Execute WriteTool to create file with specific content
  2. Execute ReadTool to read the file back
Then the read content should exactly match written content
```
