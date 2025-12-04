# Phase 10.1: Plugin System - Wireframes & Usage Examples

**Phase:** 10.1
**Name:** Plugin System
**Dependencies:** Phase 2.1 (Tool System), Phase 4.2 (Hooks System), Phase 6.1 (Slash Commands)

---

## 1. Plugin List Display

### List All Plugins

```
You: /plugins

Installed Plugins
═══════════════════════════════════════════

Active:
  ● code-review (1.2.0)
    Code review assistance with AI feedback
    Tools: analyze, suggest-fixes
    By: Example Author

  ● jira-integration (2.0.1)
    Connect to Jira for issue tracking
    Tools: jira-search, jira-create
    By: Integration Inc

  ● sql-assistant (1.0.0)
    SQL query generation and optimization
    Tools: generate-sql, optimize-query
    Commands: /sql

Disabled:
  ○ experimental-feature (0.5.0)
    Experimental features in development

3 active, 1 disabled plugins
```

### No Plugins Installed

```
You: /plugins

Installed Plugins
═══════════════════════════════════════════

No plugins installed.

To install plugins:
  1. Download plugin to ~/.src/opencode/plugins/
  2. Restart OpenCode or run /plugin reload

Example plugin structure:
  ~/.src/opencode/plugins/my-plugin/
  ├── plugin.yaml
  └── my_plugin.py
```

---

## 2. Plugin Details

### Plugin Info

```
You: /plugin info code-review

Plugin: code-review
═══════════════════════════════════════════

Version: 1.2.0
Status: Active ●
Author: Example Author <author@example.com>
License: MIT
Homepage: https://github.com/example/code-review

Description:
  Code review assistance with AI-powered feedback.
  Analyzes code for issues, suggests improvements,
  and helps maintain code quality.

Capabilities:
  ✓ Tools
  ✓ Commands
  ✗ Hooks
  ✗ Subagents

Registered Tools (2):
  • code-review__analyze
    Analyze code for issues
  • code-review__suggest-fixes
    Suggest fixes for code issues

Registered Commands (1):
  • /code-review:review
    Start a code review session

Configuration:
  strictness: high
  include_style: true
  max_issues: 20
```

### Plugin with Errors

```
You: /plugin info broken-plugin

Plugin: broken-plugin
═══════════════════════════════════════════

Version: 1.0.0
Status: Failed ✗

Error loading plugin:
  ImportError: No module named 'missing_dependency'

The plugin could not be loaded due to a missing
dependency. Check the plugin requirements.

Suggested actions:
  1. Install missing dependency: pip install missing_dependency
  2. Check plugin documentation for requirements
  3. Contact plugin author for support
```

---

## 3. Plugin Operations

### Enable Plugin

```
You: /plugin enable experimental-feature

Enabling plugin: experimental-feature

✓ Plugin activated successfully

Registered:
  • 2 tools
  • 1 command
  • 3 hooks

experimental-feature is now active.
```

### Disable Plugin

```
You: /plugin disable jira-integration

Disabling plugin: jira-integration

Unregistering contributions:
  • Removed 2 tools
  • Removed 0 commands
  • Removed 1 hook

✓ Plugin disabled

jira-integration is now inactive.
```

### Reload Plugin

```
You: /plugin reload code-review

Reloading plugin: code-review

Deactivating...
  ○ Unregistered contributions

Reloading module...
  ✓ Module reloaded

Activating...
  ✓ Registered 2 tools
  ✓ Registered 1 command

code-review v1.2.0 reloaded successfully.
```

---

## 4. Plugin Tools Usage

### Using Plugin Tools

```
You: Analyze my authentication code

I'll use the code-review plugin to analyze your code.

[Calling code-review__analyze: path="src/auth.py"]

Code Analysis Results
═══════════════════════════════════════════

File: src/auth.py

Issues Found (3):

1. Security Warning (Line 45)
   Password stored in plain text
   Recommendation: Use password hashing

2. Code Quality (Line 78)
   Function exceeds 50 lines
   Recommendation: Extract helper functions

3. Best Practice (Line 92)
   Missing input validation
   Recommendation: Validate user input

Overall: 1 critical, 2 moderate issues

Would you like me to suggest fixes for these issues?
```

### Plugin Command Usage

```
You: /code-review:review src/utils.py

Starting code review for: src/utils.py
═══════════════════════════════════════════

Analyzing file...

Summary:
  Lines of code: 234
  Functions: 12
  Complexity: Medium

Issues:
  ● 2 potential bugs
  ● 4 code style issues
  ● 1 documentation gap

Detailed findings:

Bug #1 (Line 45):
  Possible null pointer access
  ```python
  user.name.lower()  # user could be None
  ```

Bug #2 (Line 89):
  Resource not closed
  ```python
  f = open(path)  # Should use with statement
  ```

Continue with style issues? [y/n]
```

---

## 5. Plugin Configuration

### View Plugin Config

```
You: /plugin config code-review

Configuration: code-review
═══════════════════════════════════════════

Current settings:

  strictness: high
    Type: string
    Options: low, medium, high
    Description: How strict the code review should be

  include_style: true
    Type: boolean
    Description: Include code style checks

  max_issues: 20
    Type: integer
    Range: 1-100
    Description: Maximum issues to report

  ignored_rules: []
    Type: array
    Description: Rules to ignore

To change a setting, edit your config file:
  ~/.src/opencode/config.yaml

  plugins:
    code-review:
      strictness: medium
      max_issues: 50
```

### Plugin Config Schema Display

```
You: /plugin config sql-assistant --schema

Configuration Schema: sql-assistant
═══════════════════════════════════════════

{
  "type": "object",
  "properties": {
    "database_type": {
      "type": "string",
      "enum": ["postgresql", "mysql", "sqlite"],
      "default": "postgresql",
      "description": "Target database type"
    },
    "optimize_queries": {
      "type": "boolean",
      "default": true,
      "description": "Automatically optimize generated queries"
    },
    "max_results": {
      "type": "integer",
      "default": 100,
      "minimum": 1,
      "maximum": 1000,
      "description": "Default LIMIT for queries"
    }
  },
  "required": ["database_type"]
}
```

---

## 6. Plugin Discovery

### Discover New Plugins

```
You: /plugin discover

Scanning for plugins...
═══════════════════════════════════════════

User plugins (~/.src/opencode/plugins/):
  ✓ code-review (loaded)
  ✓ sql-assistant (loaded)
  ● new-plugin (discovered)

Project plugins (.src/opencode/plugins/):
  ✓ project-helper (loaded)

Package plugins:
  ✓ jira-integration (loaded)

New plugins found:
  • new-plugin (1.0.0)
    A newly installed plugin
    Load now? [y/n]
```

### Load New Plugin

```
You: Yes, load the new plugin

Loading: new-plugin
═══════════════════════════════════════════

Parsing manifest... ✓
Importing module... ✓
Creating instance... ✓
Setting up context... ✓
Calling on_load... ✓

Capabilities:
  ✓ Tools (1)
  ✗ Commands
  ✗ Hooks

Activating plugin...
  Registering: new-plugin__my-tool

✓ new-plugin is now active!

Use 'new-plugin__my-tool' to access the plugin's tool.
```

---

## 7. Error Handling

### Plugin Load Error

```
You: /plugins

Installed Plugins
═══════════════════════════════════════════

Active:
  ● code-review (1.2.0)

Failed to Load:
  ✗ broken-plugin
    Error: ModuleNotFoundError: No module named 'requests'

  ✗ invalid-plugin
    Error: Invalid manifest: missing 'name' field

Use '/plugin info <name>' for details.
```

### Plugin Execution Error

```
You: Analyze my code with code-review

[Calling code-review__analyze: path="src/app.py"]

Plugin Error
═══════════════════════════════════════════

The code-review plugin encountered an error:

  TimeoutError: Analysis took too long

The plugin did not complete successfully.
This has been logged for debugging.

Would you like to:
1. Try again with a smaller file
2. Disable this plugin
3. Report this issue
```

### Plugin Conflict

```
You: /plugin enable conflicting-plugin

⚠️ Plugin Conflict Detected
═══════════════════════════════════════════

conflicting-plugin registers tool "search"
which conflicts with:
  • existing-plugin__search (from existing-plugin)

Options:
1. Enable anyway (tools will be prefixed)
2. Cancel and keep current configuration
3. Disable existing-plugin first

Choose [1/2/3]:
```

---

## 8. Creating Plugins

### Plugin Template Generation

```
You: /plugin create my-new-plugin

Creating new plugin: my-new-plugin
═══════════════════════════════════════════

Directory: ~/.src/opencode/plugins/my-new-plugin/

Creating files:
  ✓ plugin.yaml
  ✓ __init__.py
  ✓ my_new_plugin.py
  ✓ README.md

Plugin created successfully!

Next steps:
1. Edit plugin.yaml to update metadata
2. Implement your plugin in my_new_plugin.py
3. Run '/plugin reload my-new-plugin' to test

See documentation: https://opencode.dev/plugins
```

### Plugin Template Files

```yaml
# ~/.src/opencode/plugins/my-new-plugin/plugin.yaml

name: my-new-plugin
version: 0.1.0
description: My custom OpenCode plugin

author: Your Name
email: your@email.com
license: MIT

entry_point: my_new_plugin:MyNewPlugin

capabilities:
  tools: true
  commands: false
  hooks: false
```

```python
# ~/.src/opencode/plugins/my-new-plugin/my_new_plugin.py

from opencode.plugins import Plugin, PluginMetadata, PluginCapabilities
from opencode.tools.base import Tool


class MyTool(Tool):
    name = "my-tool"
    description = "Does something useful"

    async def execute(self, input: str) -> str:
        # Implement your tool logic here
        return f"Processed: {input}"


class MyNewPlugin(Plugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my-new-plugin",
            version="0.1.0",
            description="My custom OpenCode plugin",
            author="Your Name",
        )

    @property
    def capabilities(self) -> PluginCapabilities:
        return PluginCapabilities(tools=True)

    def register_tools(self) -> list[Tool]:
        return [MyTool()]

    def on_load(self) -> None:
        self.context.logger.info("Plugin loaded!")

    def on_activate(self) -> None:
        self.context.logger.info("Plugin activated!")
```

---

## 9. Plugin Data and State

### Plugin Data Directory

```
You: Where does my plugin store data?

Plugin Data Locations
═══════════════════════════════════════════

Each plugin has an isolated data directory:

  ~/.src/opencode/plugin_data/<plugin-name>/

For your plugin "code-review":
  ~/.src/opencode/plugin_data/code-review/
  ├── cache/
  ├── config.json
  └── history.db

Access in your plugin:
  data_dir = self.context.data_dir
  cache_path = data_dir / "cache"
```

### View Plugin State

```
You: /plugin state code-review

Plugin State: code-review
═══════════════════════════════════════════

Status: Active
Loaded: 2024-01-15 09:30:00
Last activity: 2024-01-15 14:22:45

Data directory: ~/.src/opencode/plugin_data/code-review/
  Size: 2.3 MB
  Files: 15

Configuration:
  Source: ~/.src/opencode/config.yaml
  Last modified: 2024-01-10 08:00:00

Contributions:
  Tools registered: 2
  Commands registered: 1
  Hook handlers: 0

Usage this session:
  Tool calls: 15
  Command uses: 3
  Errors: 0
```

---

## 10. Plugin Dependencies

### Plugin with Dependencies

```
You: /plugin info complex-plugin

Plugin: complex-plugin
═══════════════════════════════════════════

Version: 1.0.0
Status: Active ●

Dependencies:
  ✓ requests >= 2.28.0 (installed: 2.31.0)
  ✓ beautifulsoup4 >= 4.12.0 (installed: 4.12.2)
  ✗ special-lib >= 1.0.0 (not installed)

Warning: Missing dependency 'special-lib'
Some features may not work correctly.

Install with: pip install special-lib>=1.0.0
```

### Dependency Installation Prompt

```
You: /plugin enable needs-deps

Plugin needs-deps requires dependencies:
═══════════════════════════════════════════

Missing packages:
  • pandas >= 2.0.0
  • numpy >= 1.24.0

Would you like to install them?

This will run:
  pip install 'pandas>=2.0.0' 'numpy>=1.24.0'

[yes/no/skip]:
```

---

## Notes

- Plugin names are prefixed to avoid conflicts
- Plugins have isolated data directories
- Configuration supports schema validation
- Lifecycle hooks allow proper initialization and cleanup
- Errors in plugins don't crash the main application
- Plugins can be enabled/disabled at runtime
