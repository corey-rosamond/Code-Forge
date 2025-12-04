# Phase 10.1: Plugin System - Gherkin Specifications

**Phase:** 10.1
**Name:** Plugin System
**Dependencies:** Phase 2.1 (Tool System), Phase 4.2 (Hooks System), Phase 6.1 (Slash Commands)

---

## Feature: Plugin Discovery

### Scenario: Discover plugins in user directory
```gherkin
Given a plugin in ~/.src/opencode/plugins/my-plugin/
And plugin has valid plugin.yaml manifest
When plugin discovery runs
Then plugin should be discovered
And source should be "user"
```

### Scenario: Discover plugins in project directory
```gherkin
Given a plugin in .src/opencode/plugins/project-plugin/
And plugin has valid plugin.yaml manifest
When plugin discovery runs
Then plugin should be discovered
And source should be "project"
```

### Scenario: Discover plugins from installed packages
```gherkin
Given a Python package with opencode.plugins entry point
When plugin discovery runs
Then plugin should be discovered
And source should be "package"
```

### Scenario: Skip plugins with invalid manifest
```gherkin
Given a plugin with invalid plugin.yaml
When plugin discovery runs
Then plugin should not be discovered
And warning should be logged
```

### Scenario: Skip directories without manifest
```gherkin
Given a directory in ~/.src/opencode/plugins/ without manifest
When plugin discovery runs
Then directory should be skipped
```

### Scenario: Discover multiple plugins
```gherkin
Given 3 plugins in user directory
And 2 plugins in project directory
When plugin discovery runs
Then 5 plugins should be discovered
```

---

## Feature: Manifest Parsing

### Scenario: Parse YAML manifest
```gherkin
Given a file plugin.yaml with valid content
When manifest is parsed
Then PluginManifest should be created
And name should match manifest
And version should match manifest
And entry_point should be parsed
```

### Scenario: Parse pyproject.toml manifest
```gherkin
Given a pyproject.toml with [tool.opencode.plugin] section
When manifest is parsed
Then PluginManifest should be created
And all fields should be extracted
```

### Scenario: Validate required fields
```gherkin
Given a manifest missing "name" field
When manifest is validated
Then validation should return errors
And error should mention "name is required"
```

### Scenario: Validate version format
```gherkin
Given a manifest with version "invalid"
When manifest is validated
Then validation should return error
And error should mention "Invalid version format"
```

### Scenario: Validate entry point format
```gherkin
Given a manifest with entry_point "invalid_format"
When manifest is validated
Then validation should return error
And error should mention "module:class format"
```

### Scenario: Parse capabilities
```gherkin
Given a manifest with capabilities section
And tools: true
And commands: false
When manifest is parsed
Then capabilities.tools should be True
And capabilities.commands should be False
```

---

## Feature: Plugin Loading

### Scenario: Load plugin successfully
```gherkin
Given a discovered plugin with valid manifest
And entry_point "my_plugin:MyPlugin"
When plugin is loaded
Then LoadedPlugin should be created
And instance should be Plugin subclass
And context should be set
```

### Scenario: Load plugin adds path to sys.path
```gherkin
Given a plugin in ~/.src/opencode/plugins/my-plugin/
When plugin is loaded
Then plugin path should be in sys.path
And import should work
```

### Scenario: Load plugin calls on_load
```gherkin
Given a plugin with on_load method
When plugin is loaded
Then on_load should be called
```

### Scenario: Load plugin creates context
```gherkin
Given a plugin being loaded
When context is created
Then context.plugin_id should be set
And context.data_dir should exist
And context.logger should be configured
```

### Scenario: Load disabled plugin
```gherkin
Given a plugin in disabled_plugins list
When plugin is loaded
Then LoadedPlugin.enabled should be False
And plugin should not be activated
```

### Scenario: Load plugin with import error
```gherkin
Given a plugin with invalid entry_point module
When plugin loading is attempted
Then PluginLoadError should be raised
And error should mention import failure
```

### Scenario: Load plugin with non-Plugin class
```gherkin
Given a plugin where entry_point class is not Plugin subclass
When plugin loading is attempted
Then PluginLoadError should be raised
And error should mention "not a Plugin subclass"
```

---

## Feature: Plugin Lifecycle

### Scenario: Plugin lifecycle hooks called in order
```gherkin
Given a plugin with all lifecycle hooks
When plugin is loaded and activated
Then on_load should be called first
And on_activate should be called second
```

### Scenario: Plugin deactivation
```gherkin
Given an active plugin
When plugin is disabled
Then on_deactivate should be called
And plugin.active should be False
```

### Scenario: Plugin unload
```gherkin
Given a loaded plugin
When plugin is unloaded
Then on_unload should be called
And plugin resources should be cleaned up
```

### Scenario: Plugin reload
```gherkin
Given an active plugin
When plugin is reloaded
Then old instance should be unloaded
And new instance should be loaded
And contributions should be re-registered
```

### Scenario: Lifecycle error handling
```gherkin
Given a plugin where on_activate raises exception
When plugin activation is attempted
Then error should be logged
And plugin system should continue
```

---

## Feature: Plugin Registration

### Scenario: Register plugin tools
```gherkin
Given a plugin with capabilities.tools = true
And register_tools returns [MyTool]
When plugin is activated
Then tool should be registered in registry
And tool name should be prefixed with plugin ID
```

### Scenario: Register plugin commands
```gherkin
Given a plugin with capabilities.commands = true
And register_commands returns [MyCommand]
When plugin is activated
Then command should be registered
And command name should be prefixed
```

### Scenario: Register plugin hooks
```gherkin
Given a plugin with capabilities.hooks = true
And register_hooks returns {"event": [handler]}
When plugin is activated
Then handler should be registered for event
```

### Scenario: Tool name prefixing
```gherkin
Given a plugin "my-plugin" registering tool "search"
When tool is registered
Then registered name should be "my-plugin__search"
```

### Scenario: Command name prefixing
```gherkin
Given a plugin "my-plugin" registering command "run"
When command is registered
Then registered name should be "my-plugin:run"
```

### Scenario: Unregister all on disable
```gherkin
Given an active plugin with registered tools and commands
When plugin is disabled
Then all tools should be unregistered
And all commands should be unregistered
And all hooks should be unregistered
```

---

## Feature: Plugin Configuration

### Scenario: Load plugin configuration
```gherkin
Given a plugin "my-plugin"
And config file has my-plugin config section
When plugin config is requested
Then config values should be returned
```

### Scenario: Apply config schema defaults
```gherkin
Given a plugin with config schema
And schema has default values
And user config is missing some values
When plugin config is requested
Then missing values should have defaults
```

### Scenario: Validate config against schema
```gherkin
Given a plugin with config schema
And user config has invalid values
When config is validated
Then validation errors should be returned
```

### Scenario: Get plugin data directory
```gherkin
Given a plugin "my-plugin"
When data directory is requested
Then path should be ~/.src/opencode/plugin_data/my-plugin/
And directory should be created if needed
```

### Scenario: Disable plugin via config
```gherkin
Given "my-plugin" in disabled_plugins list
When plugins are loaded
Then my-plugin should be loaded but not activated
```

---

## Feature: Plugin Manager

### Scenario: Discover and load all plugins
```gherkin
Given plugins in user and project directories
When discover_and_load is called
Then all valid plugins should be discovered
And all enabled plugins should be loaded and activated
```

### Scenario: Get plugin by ID
```gherkin
Given a loaded plugin "my-plugin"
When get_plugin("my-plugin") is called
Then LoadedPlugin should be returned
```

### Scenario: Enable disabled plugin
```gherkin
Given a disabled plugin "my-plugin"
When enable("my-plugin") is called
Then plugin should be activated
And contributions should be registered
```

### Scenario: Disable active plugin
```gherkin
Given an active plugin "my-plugin"
When disable("my-plugin") is called
Then plugin should be deactivated
And contributions should be unregistered
```

### Scenario: List all plugins
```gherkin
Given 3 loaded plugins
When list_plugins is called
Then list should contain 3 LoadedPlugin items
```

### Scenario: Get load errors
```gherkin
Given a plugin that failed to load
When get_load_errors is called
Then errors dict should contain plugin ID
And value should be error message
```

### Scenario: Shutdown plugin system
```gherkin
Given multiple active plugins
When shutdown is called
Then all plugins should be deactivated
And all plugins should be unloaded
```

---

## Feature: Plugin Registry

### Scenario: Get all registered tools
```gherkin
Given plugins have registered tools
When get_tools is called
Then dict of all tools should be returned
And keys should be prefixed names
```

### Scenario: Get hooks for event
```gherkin
Given plugins have registered hooks for "before_execute"
When get_hooks("before_execute") is called
Then list of handlers should be returned
And handlers should be sorted by priority
```

### Scenario: List plugin contributions
```gherkin
Given a plugin with tools, commands, and hooks
When list_plugins_contributions is called
Then dict should show all registered items
```

---

## Feature: Error Handling

### Scenario: Continue on plugin load failure
```gherkin
Given 3 plugins and 1 has import error
When plugins are loaded
Then 2 plugins should load successfully
And 1 error should be recorded
```

### Scenario: Isolate plugin errors
```gherkin
Given a plugin that throws in on_activate
When plugin system runs
Then error should be logged
And other plugins should continue working
```

### Scenario: Handle missing plugin
```gherkin
Given plugin "nonexistent" is not loaded
When enable("nonexistent") is called
Then PluginNotFoundError should be raised
```

---

## Feature: Plugin Slash Commands

### Scenario: List plugins command
```gherkin
Given 3 loaded plugins
When user runs /plugins
Then list of plugins should be shown
And each should show name, version, status
```

### Scenario: Plugin info command
```gherkin
Given a loaded plugin "my-plugin"
When user runs /plugin info my-plugin
Then plugin details should be shown
And should include capabilities
And should include registered tools
```

### Scenario: Enable plugin command
```gherkin
Given a disabled plugin "my-plugin"
When user runs /plugin enable my-plugin
Then plugin should be enabled
And success message should be shown
```

### Scenario: Disable plugin command
```gherkin
Given an active plugin "my-plugin"
When user runs /plugin disable my-plugin
Then plugin should be disabled
And success message should be shown
```

### Scenario: Reload plugin command
```gherkin
Given a loaded plugin "my-plugin"
When user runs /plugin reload my-plugin
Then plugin should be reloaded
And success message should be shown
```
