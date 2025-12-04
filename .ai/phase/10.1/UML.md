# Phase 10.1: Plugin System - UML Diagrams

**Phase:** 10.1
**Name:** Plugin System
**Dependencies:** Phase 2.1 (Tool System), Phase 4.2 (Hooks System), Phase 6.1 (Slash Commands)

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Plugin System                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────┐       ┌─────────────────────────────────────┐
│          <<dataclass>>              │       │          <<dataclass>>              │
│         PluginMetadata              │       │       PluginCapabilities            │
├─────────────────────────────────────┤       ├─────────────────────────────────────┤
│ + name: str                         │       │ + tools: bool                       │
│ + version: str                      │       │ + commands: bool                    │
│ + description: str                  │       │ + hooks: bool                       │
│ + author: str | None                │       │ + subagents: bool                   │
│ + email: str | None                 │       │ + skills: bool                      │
│ + license: str | None               │       │ + system_access: bool               │
│ + homepage: str | None              │       ├─────────────────────────────────────┤
│ + repository: str | None            │       │ + to_dict(): dict                   │
│ + keywords: list[str]               │       └─────────────────────────────────────┘
│ + opencode_version: str | None      │
├─────────────────────────────────────┤
│ + to_dict(): dict                   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│          <<dataclass>>              │
│         PluginContext               │
├─────────────────────────────────────┤
│ + plugin_id: str                    │
│ + data_dir: Path                    │
│ + config: dict                      │
│ + logger: Logger                    │
├─────────────────────────────────────┤
│ + get_config(key, default): Any     │
│ + ensure_data_dir(): Path           │
└─────────────────────────────────────┘

                              ┌─────────────────────────────────────┐
                              │        <<abstract>>                 │
                              │           Plugin                    │
                              ├─────────────────────────────────────┤
                              │ - _context: PluginContext | None    │
                              ├─────────────────────────────────────┤
                              │ + metadata: PluginMetadata          │
                              │ + capabilities: PluginCapabilities  │
                              │ + context: PluginContext            │
                              │ + set_context(ctx): None            │
                              │ + on_load(): None                   │
                              │ + on_activate(): None               │
                              │ + on_deactivate(): None             │
                              │ + on_unload(): None                 │
                              │ + register_tools(): list[Tool]      │
                              │ + register_commands(): list[Command]│
                              │ + register_hooks(): dict            │
                              │ + get_config_schema(): dict | None  │
                              └──────────────────┬──────────────────┘
                                                 │
                                                 │ implements
                                                 │
                              ┌──────────────────┴──────────────────┐
                              │         <<concrete>>                │
                              │        MyPlugin                     │
                              ├─────────────────────────────────────┤
                              │ + metadata: PluginMetadata          │
                              │ + capabilities: PluginCapabilities  │
                              │ + register_tools(): list[Tool]      │
                              └─────────────────────────────────────┘


┌─────────────────────────────────────┐       ┌─────────────────────────────────────┐
│          <<dataclass>>              │       │          <<dataclass>>              │
│        PluginManifest               │       │       DiscoveredPlugin              │
├─────────────────────────────────────┤       ├─────────────────────────────────────┤
│ + name: str                         │       │ + path: Path | None                 │
│ + version: str                      │◄──────│ + manifest: PluginManifest          │
│ + description: str                  │       │ + source: str                       │
│ + entry_point: str                  │       ├─────────────────────────────────────┤
│ + metadata: PluginMetadata          │       │ + id: str                           │
│ + capabilities: PluginCapabilities  │       └─────────────────────────────────────┘
│ + dependencies: list[str]           │
│ + config_schema: dict | None        │
│ + path: Path | None                 │
├─────────────────────────────────────┤
│ + from_yaml(path): PluginManifest   │
│ + from_pyproject(path): Manifest    │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐       ┌─────────────────────────────────────┐
│          <<dataclass>>              │       │          <<dataclass>>              │
│         LoadedPlugin                │       │         PluginConfig                │
├─────────────────────────────────────┤       ├─────────────────────────────────────┤
│ + id: str                           │       │ + enabled: bool                     │
│ + manifest: PluginManifest          │       │ + user_dir: Path | None             │
│ + instance: Plugin                  │       │ + project_dir: Path | None          │
│ + context: PluginContext            │       │ + disabled_plugins: list[str]       │
│ + source: str                       │       │ + plugin_configs: dict              │
│ + enabled: bool                     │       ├─────────────────────────────────────┤
│ + active: bool                      │       │ + from_dict(data): PluginConfig     │
└─────────────────────────────────────┘       │ + to_dict(): dict                   │
                                              └─────────────────────────────────────┘
```

---

## Service Classes Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Plugin System Services                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────┐
│         ManifestParser              │
├─────────────────────────────────────┤
│ + MANIFEST_FILES: list[str]         │
├─────────────────────────────────────┤
│ + find_manifest(dir): Path | None   │
│ + parse(path): PluginManifest       │
│ + validate(manifest): list[str]     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         PluginDiscovery             │
├─────────────────────────────────────┤
│ + USER_PLUGIN_DIR: Path             │
│ + PROJECT_PLUGIN_DIR: Path          │
│ + ENTRY_POINT_GROUP: str            │
│ - parser: ManifestParser            │
├─────────────────────────────────────┤
│ + discover(): list[DiscoveredPlugin]│
│ + discover_user_plugins(): list     │
│ + discover_project_plugins(): list  │
│ + discover_extra_plugins(): list    │
│ + discover_package_plugins(): list  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│        PluginConfigManager          │
├─────────────────────────────────────┤
│ - base_config: PluginConfig         │
│ - data_dir: Path                    │
├─────────────────────────────────────┤
│ + get_plugin_config(id, schema): dict│
│ + set_plugin_config(id, config): None│
│ + get_plugin_data_dir(id): Path     │
│ + validate_config(config, schema)   │
│ + is_plugin_disabled(id): bool      │
│ + disable_plugin(id): None          │
│ + enable_plugin(id): None           │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│          PluginLoader               │
├─────────────────────────────────────┤
│ - config_manager: PluginConfigManager│
│ - logger: Logger                    │
├─────────────────────────────────────┤
│ + load(discovered): LoadedPlugin    │
│ + create_context(id, manifest): Ctx │
│ + unload(plugin): None              │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         PluginRegistry              │
├─────────────────────────────────────┤
│ - _tools: dict                      │
│ - _commands: dict                   │
│ - _hooks: dict                      │
│ - _subagents: dict                  │
│ - _skills: dict                     │
├─────────────────────────────────────┤
│ + register_tool(plugin_id, tool)    │
│ + register_command(plugin_id, cmd)  │
│ + register_hook(plugin_id, event, h)│
│ + register_subagent(id, type, cls)  │
│ + register_skill(plugin_id, skill)  │
│ + unregister_plugin(plugin_id)      │
│ + get_tools(): dict                 │
│ + get_commands(): dict              │
│ + get_hooks(event): list[Callable]  │
│ + get_subagents(): dict             │
│ + get_skills(): dict                │
│ + list_plugins_contributions(id)    │
└─────────────────────────────────────┘

                              ┌─────────────────────────────────────┐
                              │          PluginManager              │
                              ├─────────────────────────────────────┤
                              │ - config: PluginConfig              │
                              │ - registry: PluginRegistry          │
                              │ - config_manager: ConfigManager     │
                              │ - discovery: PluginDiscovery        │
                              │ - loader: PluginLoader              │
                              │ - _plugins: dict[str, LoadedPlugin] │
                              │ - _load_errors: dict[str, str]      │
                              ├─────────────────────────────────────┤
                              │ + plugins: dict[str, LoadedPlugin]  │
                              │ + discover_and_load(): None         │
                              │ + get_plugin(id): LoadedPlugin|None │
                              │ + enable(plugin_id): None           │
                              │ + disable(plugin_id): None          │
                              │ + reload(plugin_id): None           │
                              │ + list_plugins(): list[LoadedPlugin]│
                              │ + get_load_errors(): dict           │
                              │ + shutdown(): None                  │
                              └─────────────────────────────────────┘
```

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Plugin System                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │    base      │     │   manifest   │     │  discovery   │                │
│  │    .py       │     │     .py      │     │     .py      │                │
│  │              │     │              │     │              │                │
│  │   Plugin     │◄────│PluginManifest│◄────│PluginDiscovery│               │
│  │PluginMetadata│     │ManifestParser│     │DiscoveredPlugin│              │
│  │PluginContext │     └──────────────┘     └──────────────┘                │
│  │PluginCaps    │                                                          │
│  └──────────────┘                                                          │
│         ▲                                                                   │
│         │                                                                   │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │   loader     │     │   config     │     │   registry   │                │
│  │    .py       │────▶│     .py      │     │     .py      │                │
│  │              │     │              │     │              │                │
│  │PluginLoader  │     │PluginConfig  │     │PluginRegistry│                │
│  │LoadedPlugin  │     │ConfigManager │     │              │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
│         │                    │                    │                        │
│         └────────────────────┼────────────────────┘                        │
│                              │                                              │
│                              ▼                                              │
│                       ┌──────────────┐                                     │
│                       │   manager    │                                     │
│                       │     .py      │                                     │
│                       │              │                                     │
│                       │PluginManager │                                     │
│                       └──────────────┘                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   User Plugins   │     │ Project Plugins  │     │ Package Plugins  │
│  ~/.src/opencode/    │     │   .src/opencode/     │     │  (entry points)  │
│    plugins/      │     │    plugins/      │     │                  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

---

## Sequence Diagram: Plugin Discovery and Loading

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│OpenCode │     │PluginManager │     │PluginDiscovery│    │ PluginLoader │     │PluginRegistry│
└────┬────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
     │                 │                    │                    │                    │
     │ discover_and_   │                    │                    │                    │
     │ load()          │                    │                    │                    │
     │────────────────▶│                    │                    │                    │
     │                 │                    │                    │                    │
     │                 │   discover()       │                    │                    │
     │                 │───────────────────▶│                    │                    │
     │                 │                    │                    │                    │
     │                 │                    │ [Scan user dir]    │                    │
     │                 │                    │ [Scan project dir] │                    │
     │                 │                    │ [Scan entry points]│                    │
     │                 │                    │                    │                    │
     │                 │ list[Discovered]   │                    │                    │
     │                 │◀───────────────────│                    │                    │
     │                 │                    │                    │                    │
     │                 │ [For each discovered plugin]            │                    │
     │                 │────────────────────────────────────────▶│                    │
     │                 │                    │                    │                    │
     │                 │   load(discovered) │                    │                    │
     │                 │───────────────────────────────────────▶ │                    │
     │                 │                    │                    │                    │
     │                 │                    │                    │ [Import module]    │
     │                 │                    │                    │ [Instantiate class]│
     │                 │                    │                    │ [Create context]   │
     │                 │                    │                    │                    │
     │                 │   LoadedPlugin     │                    │                    │
     │                 │◀──────────────────────────────────────── │                    │
     │                 │                    │                    │                    │
     │                 │ [Call on_load()]   │                    │                    │
     │                 │                    │                    │                    │
     │                 │ [If enabled, activate]                  │                    │
     │                 │                    │                    │                    │
     │                 │                    │                    │ register_tool()    │
     │                 │─────────────────────────────────────────────────────────────▶│
     │                 │                    │                    │                    │
     │                 │                    │                    │ register_command() │
     │                 │─────────────────────────────────────────────────────────────▶│
     │                 │                    │                    │                    │
     │                 │ [Call on_activate()]                    │                    │
     │                 │                    │                    │                    │
     │  complete       │                    │                    │                    │
     │◀────────────────│                    │                    │                    │
     │                 │                    │                    │                    │
```

---

## Sequence Diagram: Plugin Enable/Disable

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User   │     │PluginManager │     │ LoadedPlugin │     │PluginRegistry│
└────┬────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
     │                 │                    │                    │
     │ disable("my-    │                    │                    │
     │  plugin")       │                    │                    │
     │────────────────▶│                    │                    │
     │                 │                    │                    │
     │                 │ [Get LoadedPlugin] │                    │
     │                 │                    │                    │
     │                 │                    │                    │
     │                 │ unregister_plugin  │                    │
     │                 │ ("my-plugin")      │                    │
     │                 │─────────────────────────────────────────▶│
     │                 │                    │                    │
     │                 │                    │                    │ [Remove tools,
     │                 │                    │                    │  commands, hooks]
     │                 │                    │                    │
     │                 │  on_deactivate()   │                    │
     │                 │───────────────────▶│                    │
     │                 │                    │                    │
     │                 │ [Update config]    │                    │
     │                 │ plugin.enabled=False                    │
     │                 │                    │                    │
     │  success        │                    │                    │
     │◀────────────────│                    │                    │
     │                 │                    │                    │
```

---

## Sequence Diagram: Plugin Tool Registration

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Plugin │     │PluginManager │     │PluginRegistry│     │ ToolRegistry │
└────┬────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
     │                 │                    │                    │
     │ [Plugin loaded  │                    │                    │
     │  and activated] │                    │                    │
     │                 │                    │                    │
     │ register_tools()│                    │                    │
     │◀────────────────│                    │                    │
     │                 │                    │                    │
     │ [MyTool1,       │                    │                    │
     │  MyTool2]       │                    │                    │
     │────────────────▶│                    │                    │
     │                 │                    │                    │
     │                 │ register_tool(     │                    │
     │                 │  "my-plugin",      │                    │
     │                 │   MyTool1)         │                    │
     │                 │───────────────────▶│                    │
     │                 │                    │                    │
     │                 │                    │ [Store with prefix │
     │                 │                    │  "my-plugin__tool1"]│
     │                 │                    │                    │
     │                 │ "my-plugin__tool1" │                    │
     │                 │◀───────────────────│                    │
     │                 │                    │                    │
     │                 │                    │ register(prefixed, │
     │                 │                    │  tool)             │
     │                 │                    │───────────────────▶│
     │                 │                    │                    │
     │                 │ [Repeat for other  │                    │
     │                 │  tools]            │                    │
     │                 │                    │                    │
```

---

## State Diagram: Plugin Lifecycle

```
                              ┌─────────────────┐
                              │                 │
                              │   Discovered    │
                              │                 │
                              └────────┬────────┘
                                       │
                                  Load Plugin
                                       │
                                       ▼
                              ┌─────────────────┐
                              │                 │
                              │     Loaded      │──────────────────────┐
                              │   (on_load)     │                      │
                              │                 │                      │
                              └────────┬────────┘                      │
                                       │                               │
                               Plugin Enabled?                         │
                                       │                               │
                    ┌──────────────────┴──────────────────┐            │
                    │ Yes                                 │ No         │
                    ▼                                     ▼            │
           ┌─────────────────┐                   ┌─────────────────┐   │
           │                 │                   │                 │   │
           │     Active      │                   │    Disabled     │   │
           │ (on_activate)   │                   │   (inactive)    │   │
           │                 │                   │                 │   │
           └────────┬────────┘                   └────────┬────────┘   │
                    │                                     │            │
                    │◀──── enable() ──────────────────────┘            │
                    │                                                  │
                    │────── disable() ───────────────────▶             │
                    │                                                  │
                    │                                                  │
                    │        reload()                                  │
                    │───────────────────────────────────────────▶      │
                    │                                            │     │
                    │                                            │     │
                    │                              ┌─────────────┘     │
                    │                              │                   │
                    │                              ▼                   │
                    │                     ┌─────────────────┐          │
                    │                     │                 │          │
                    │─────────────────────│   Unloading     │◀─────────┘
                    │                     │  (on_unload)    │
                    │                     │                 │
                    │                     └────────┬────────┘
                    │                              │
                    │                              ▼
                    │                     ┌─────────────────┐
                    │                     │                 │
                    └────────────────────▶│   Unloaded      │
                          shutdown()      │                 │
                                          └─────────────────┘
```

---

## Activity Diagram: Plugin Registration Flow

```
                        ┌─────────────────┐
                        │   Plugin Load   │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   on_load()     │
                        │   callback      │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ Check if        │
                        │ enabled?        │
                        └────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    │ No                      │ Yes
                    ▼                         ▼
           ┌────────────────┐        ┌────────────────┐
           │  Store as      │        │  Check         │
           │  disabled      │        │  capabilities  │
           └────────────────┘        └───────┬────────┘
                                             │
                              ┌──────────────┼──────────────┐
                              │              │              │
                              ▼              ▼              ▼
                    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
                    │ has tools?   │ │has commands? │ │ has hooks?   │
                    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
                           │                │                │
                           ▼                ▼                ▼
                    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
                    │register_tools│ │register_cmds │ │register_hooks│
                    │ -> registry  │ │ -> registry  │ │ -> registry  │
                    └──────────────┘ └──────────────┘ └──────────────┘
                           │                │                │
                           └────────────────┼────────────────┘
                                            │
                                            ▼
                                   ┌────────────────┐
                                   │ on_activate()  │
                                   │   callback     │
                                   └────────┬───────┘
                                            │
                                            ▼
                                   ┌────────────────┐
                                   │ Plugin Active  │
                                   └────────────────┘
```

---

## Plugin Directory Structure

```
~/.src/opencode/
├── plugins/                      # User plugins directory
│   ├── my-plugin/
│   │   ├── plugin.yaml          # Plugin manifest
│   │   ├── __init__.py          # Plugin entry point
│   │   ├── my_plugin.py         # Main plugin class
│   │   ├── tools/               # Plugin tools
│   │   │   └── my_tool.py
│   │   ├── commands/            # Plugin commands
│   │   │   └── my_command.md
│   │   └── config.schema.yaml   # Config schema
│   │
│   └── another-plugin/
│       └── ...
│
└── plugin_data/                  # Plugin data directories
    ├── my-plugin/
    │   └── ...
    └── another-plugin/
        └── ...


.src/opencode/                        # Project-level
├── plugins/                      # Project plugins
│   └── project-plugin/
│       └── ...
└── config.yaml                   # May include plugin config
```

---

## Notes

- Plugins are namespaced to avoid conflicts
- Tools and commands are prefixed with plugin ID
- Lifecycle hooks allow plugins to initialize and cleanup
- Configuration supports JSON schema validation
- Discovery supports multiple sources (user, project, packages)
- Plugin errors are isolated from core functionality
