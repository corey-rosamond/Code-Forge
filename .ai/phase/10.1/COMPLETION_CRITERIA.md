# Phase 10.1: Plugin System - Completion Criteria

**Phase:** 10.1
**Name:** Plugin System
**Dependencies:** Phase 2.1 (Tool System), Phase 4.2 (Hooks System), Phase 6.1 (Slash Commands)

---

## Completion Checklist

### 1. Plugin Base Types (base.py)

- [ ] `PluginMetadata` dataclass implemented
  - [ ] `name: str`
  - [ ] `version: str`
  - [ ] `description: str`
  - [ ] `author: str | None`
  - [ ] `email: str | None`
  - [ ] `license: str | None`
  - [ ] `homepage: str | None`
  - [ ] `repository: str | None`
  - [ ] `keywords: list[str]`
  - [ ] `forge_version: str | None`
  - [ ] `to_dict()` method

- [ ] `PluginCapabilities` dataclass implemented
  - [ ] `tools: bool`
  - [ ] `commands: bool`
  - [ ] `hooks: bool`
  - [ ] `subagents: bool`
  - [ ] `skills: bool`
  - [ ] `system_access: bool`
  - [ ] `to_dict()` method

- [ ] `PluginContext` dataclass implemented
  - [ ] `plugin_id: str`
  - [ ] `data_dir: Path`
  - [ ] `config: dict`
  - [ ] `logger: Logger`
  - [ ] `get_config()` method
  - [ ] `ensure_data_dir()` method

- [ ] `Plugin` abstract base class implemented
  - [ ] `metadata` abstract property
  - [ ] `capabilities` property
  - [ ] `context` property
  - [ ] `set_context()` method
  - [ ] `on_load()` lifecycle hook
  - [ ] `on_activate()` lifecycle hook
  - [ ] `on_deactivate()` lifecycle hook
  - [ ] `on_unload()` lifecycle hook
  - [ ] `register_tools()` method
  - [ ] `register_commands()` method
  - [ ] `register_hooks()` method
  - [ ] `get_config_schema()` method

### 2. Manifest Parsing (manifest.py)

- [ ] `PluginManifest` dataclass implemented
  - [ ] All required fields
  - [ ] `from_yaml()` class method
  - [ ] `from_pyproject()` class method

- [ ] `ManifestParser` class implemented
  - [ ] `find_manifest()` method
  - [ ] `parse()` method
  - [ ] `validate()` method

- [ ] Manifest validation
  - [ ] Required fields checked
  - [ ] Version format validated
  - [ ] Entry point format validated

### 3. Plugin Discovery (discovery.py)

- [ ] `DiscoveredPlugin` dataclass implemented
  - [ ] `path: Path | None`
  - [ ] `manifest: PluginManifest`
  - [ ] `source: str`
  - [ ] `id` property

- [ ] `PluginDiscovery` class implemented
  - [ ] `discover()` method
  - [ ] `discover_user_plugins()` method
  - [ ] `discover_project_plugins()` method
  - [ ] `discover_extra_plugins()` method
  - [ ] `discover_package_plugins()` method

- [ ] Discovery features
  - [ ] User plugin directory support
  - [ ] Project plugin directory support
  - [ ] Python entry points support
  - [ ] Invalid manifest handling

### 4. Plugin Configuration (config.py)

- [ ] `PluginConfig` dataclass implemented
  - [ ] `enabled: bool`
  - [ ] `user_dir: Path | None`
  - [ ] `project_dir: Path | None`
  - [ ] `disabled_plugins: list[str]`
  - [ ] `plugin_configs: dict`
  - [ ] `from_dict()` class method
  - [ ] `to_dict()` method

- [ ] `PluginConfigManager` class implemented
  - [ ] `get_plugin_config()` method
  - [ ] `set_plugin_config()` method
  - [ ] `get_plugin_data_dir()` method
  - [ ] `validate_config()` method
  - [ ] `is_plugin_disabled()` method
  - [ ] `disable_plugin()` method
  - [ ] `enable_plugin()` method

- [ ] Config features
  - [ ] Schema defaults application
  - [ ] JSON schema validation
  - [ ] Data directory creation

### 5. Plugin Loader (loader.py)

- [ ] `LoadedPlugin` dataclass implemented
  - [ ] `id: str`
  - [ ] `manifest: PluginManifest`
  - [ ] `instance: Plugin`
  - [ ] `context: PluginContext`
  - [ ] `source: str`
  - [ ] `enabled: bool`
  - [ ] `active: bool`

- [ ] `PluginLoader` class implemented
  - [ ] `load()` method
  - [ ] `create_context()` method
  - [ ] `unload()` method

- [ ] Loader features
  - [ ] Module import handling
  - [ ] sys.path management
  - [ ] Context creation
  - [ ] Error handling

### 6. Plugin Registry (registry.py)

- [ ] `PluginRegistry` class implemented
  - [ ] `register_tool()` method
  - [ ] `register_command()` method
  - [ ] `register_hook()` method
  - [ ] `register_subagent()` method
  - [ ] `register_skill()` method
  - [ ] `unregister_plugin()` method
  - [ ] `get_tools()` method
  - [ ] `get_tool()` method
  - [ ] `get_commands()` method
  - [ ] `get_command()` method
  - [ ] `get_hooks()` method
  - [ ] `get_subagents()` method
  - [ ] `get_skills()` method
  - [ ] `list_plugins_contributions()` method

- [ ] Registry features
  - [ ] Name prefixing for tools
  - [ ] Name prefixing for commands
  - [ ] Hook priority ordering
  - [ ] Complete unregistration

### 7. Plugin Manager (manager.py)

- [ ] `PluginManager` class implemented
  - [ ] `plugins` property
  - [ ] `discover_and_load()` method
  - [ ] `get_plugin()` method
  - [ ] `enable()` method
  - [ ] `disable()` method
  - [ ] `reload()` method
  - [ ] `list_plugins()` method
  - [ ] `get_load_errors()` method
  - [ ] `shutdown()` method

- [ ] Manager features
  - [ ] Lifecycle hook calling
  - [ ] Error isolation
  - [ ] Enable/disable at runtime
  - [ ] Plugin reload support

### 8. Exceptions (exceptions.py)

- [ ] `PluginError` base exception
- [ ] `PluginNotFoundError`
- [ ] `PluginLoadError`
- [ ] `PluginManifestError`
- [ ] `PluginDependencyError`
- [ ] `PluginConfigError`
- [ ] `PluginLifecycleError`

### 9. Package Exports (__init__.py)

- [ ] All base types exported
- [ ] All service classes exported
- [ ] All exceptions exported
- [ ] `__all__` list complete

### 10. Slash Commands

- [ ] `/plugins` command implemented
- [ ] `/plugin info <name>` command implemented
- [ ] `/plugin enable <name>` command implemented
- [ ] `/plugin disable <name>` command implemented
- [ ] `/plugin reload <name>` command implemented

### 11. Testing

- [ ] Unit tests for Plugin base class
- [ ] Unit tests for ManifestParser
- [ ] Unit tests for PluginDiscovery
- [ ] Unit tests for PluginConfigManager
- [ ] Unit tests for PluginLoader
- [ ] Unit tests for PluginRegistry
- [ ] Unit tests for PluginManager
- [ ] Integration tests with sample plugins
- [ ] Test coverage >= 90%

### 12. Code Quality

- [ ] McCabe complexity <= 10 for all functions
- [ ] Type hints on all public methods
- [ ] Docstrings on all public classes/methods
- [ ] No circular imports
- [ ] Follows project code style

---

## Verification Commands

```bash
# Run unit tests
pytest tests/plugins/ -v

# Run with coverage
pytest tests/plugins/ --cov=src/forge/plugins --cov-report=term-missing

# Check coverage threshold
pytest tests/plugins/ --cov=src/forge/plugins --cov-fail-under=90

# Type checking
mypy src/forge/plugins/

# Complexity check
flake8 src/forge/plugins/ --max-complexity=10
```

---

## Test Scenarios

### Plugin Discovery Tests

```python
def test_discover_user_plugins(tmp_path, monkeypatch):
    # Create plugin directory
    plugin_dir = tmp_path / "plugins" / "test-plugin"
    plugin_dir.mkdir(parents=True)

    # Create manifest
    manifest = plugin_dir / "plugin.yaml"
    manifest.write_text("""
name: test-plugin
version: 1.0.0
description: Test plugin
entry_point: test_plugin:TestPlugin
""")

    discovery = PluginDiscovery(user_dir=tmp_path / "plugins")
    plugins = discovery.discover_user_plugins()

    assert len(plugins) == 1
    assert plugins[0].id == "test-plugin"
    assert plugins[0].source == "user"


def test_skip_invalid_manifest(tmp_path):
    plugin_dir = tmp_path / "plugins" / "bad-plugin"
    plugin_dir.mkdir(parents=True)

    manifest = plugin_dir / "plugin.yaml"
    manifest.write_text("invalid: yaml: content")

    discovery = PluginDiscovery(user_dir=tmp_path / "plugins")
    plugins = discovery.discover_user_plugins()

    assert len(plugins) == 0
```

### Plugin Loading Tests

```python
def test_load_plugin(tmp_path):
    # Create plugin
    plugin_dir = tmp_path / "test-plugin"
    plugin_dir.mkdir()

    (plugin_dir / "plugin.yaml").write_text("""
name: test-plugin
version: 1.0.0
description: Test
entry_point: test_plugin:TestPlugin
""")

    (plugin_dir / "test_plugin.py").write_text("""
from forge.plugins import Plugin, PluginMetadata

class TestPlugin(Plugin):
    @property
    def metadata(self):
        return PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            description="Test"
        )
""")

    discovered = DiscoveredPlugin(
        path=plugin_dir,
        manifest=PluginManifest.from_yaml(plugin_dir / "plugin.yaml"),
        source="test"
    )

    config_manager = PluginConfigManager(PluginConfig())
    loader = PluginLoader(config_manager)
    loaded = loader.load(discovered)

    assert loaded.id == "test-plugin"
    assert isinstance(loaded.instance, Plugin)


def test_load_plugin_creates_context(tmp_path):
    # ... setup ...
    loaded = loader.load(discovered)

    assert loaded.context.plugin_id == "test-plugin"
    assert loaded.context.data_dir.exists()
```

### Plugin Registry Tests

```python
def test_register_tool():
    registry = PluginRegistry()
    tool = MockTool(name="search")

    name = registry.register_tool("my-plugin", tool)

    assert name == "my-plugin__search"
    assert "my-plugin__search" in registry.get_tools()


def test_unregister_plugin():
    registry = PluginRegistry()
    registry.register_tool("plugin-a", MockTool(name="tool1"))
    registry.register_tool("plugin-a", MockTool(name="tool2"))
    registry.register_tool("plugin-b", MockTool(name="tool3"))

    registry.unregister_plugin("plugin-a")

    tools = registry.get_tools()
    assert "plugin-a__tool1" not in tools
    assert "plugin-a__tool2" not in tools
    assert "plugin-b__tool3" in tools
```

### Plugin Manager Tests

```python
async def test_discover_and_load(tmp_path):
    # Create plugins
    # ...

    manager = PluginManager(config=PluginConfig(
        user_dir=tmp_path / "plugins"
    ))
    manager.discover_and_load()

    assert len(manager.plugins) > 0


async def test_enable_disable_plugin():
    manager = PluginManager()
    manager.discover_and_load()

    # Disable
    manager.disable("my-plugin")
    plugin = manager.get_plugin("my-plugin")
    assert plugin.enabled is False
    assert plugin.active is False

    # Enable
    manager.enable("my-plugin")
    plugin = manager.get_plugin("my-plugin")
    assert plugin.enabled is True
    assert plugin.active is True
```

---

## Definition of Done

Phase 10.1 is complete when:

1. All checklist items are checked off
2. All unit tests pass
3. Test coverage is >= 90%
4. Code complexity is <= 10
5. Type checking passes with no errors
6. Plugins can be discovered from all sources
7. Plugin manifests are parsed and validated
8. Plugins load correctly with context
9. Plugin lifecycle hooks are called
10. Plugin tools are registered correctly
11. Plugin commands are registered correctly
12. Plugin hooks are registered correctly
13. Plugins can be enabled/disabled at runtime
14. Plugins can be reloaded
15. Plugin errors don't crash the system
16. Plugin data is isolated
17. Slash commands work correctly
18. Sample plugin works end-to-end
19. Documentation is complete
20. Code review approved

---

## Dependencies Verification

Before starting Phase 10.1, verify:

- [ ] Phase 2.1 (Tool System) is complete
  - [ ] Tool interface available
  - [ ] Tool registration works

- [ ] Phase 4.2 (Hooks System) is complete
  - [ ] Hook registration works
  - [ ] Event system functional

- [ ] Phase 6.1 (Slash Commands) is complete
  - [ ] Command registration works
  - [ ] Commands can be added dynamically

---

## Plugin Directory Structure

```
~/.src/forge/
├── plugins/                  # User plugins
│   └── my-plugin/
│       ├── plugin.yaml       # Manifest
│       ├── __init__.py
│       └── my_plugin.py
│
├── plugin_data/              # Plugin data directories
│   └── my-plugin/
│       └── ...
│
└── config.yaml               # May include plugin configs

.src/forge/                    # Project level
└── plugins/
    └── project-plugin/
        └── ...
```

---

## Performance Requirements

| Operation | Max Time |
|-----------|----------|
| Plugin discovery | 500ms |
| Single plugin load | 100ms |
| Total startup (10 plugins) | 2s |
| Plugin enable/disable | 50ms |
| Plugin reload | 200ms |

---

## Notes

- Plugin system is optional (can be disabled)
- Core functionality works without plugins
- Plugin errors are isolated
- Plugins have namespaced contributions
- Configuration supports schema validation
- Data directories are per-plugin
