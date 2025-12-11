# Phase 1.2: Configuration System - UML Diagrams

**Phase:** 1.2
**Name:** Configuration System
**Dependencies:** Phase 1.1

---

## 1. Class Diagram - Configuration Models

```mermaid
classDiagram
    class Code-ForgeConfig {
        <<Aggregate Root>>
        +model: ModelConfig
        +permissions: PermissionConfig
        +hooks: HooksConfig
        +mcp_servers: Dict~str,MCPServerConfig~
        +display: DisplayConfig
        +session: SessionConfig
        +api_key: SecretStr?
    }

    class ModelConfig {
        +default: str
        +fallback: List~str~
        +max_tokens: int
        +temperature: float
        +routing_variant: RoutingVariant?
    }

    class PermissionConfig {
        +allow: List~str~
        +ask: List~str~
        +deny: List~str~
    }

    class HooksConfig {
        +pre_tool_use: List~HookConfig~
        +post_tool_use: List~HookConfig~
        +user_prompt_submit: List~HookConfig~
        +stop: List~HookConfig~
        +subagent_stop: List~HookConfig~
        +notification: List~HookConfig~
    }

    class HookConfig {
        +type: HookType
        +matcher: str?
        +command: str?
        +prompt: str?
        +timeout: int
    }

    class MCPServerConfig {
        +transport: TransportType
        +command: str?
        +args: List~str~
        +url: str?
        +env: Dict~str,str~
        +oauth_client_id: str?
    }

    class DisplayConfig {
        +theme: str
        +show_tokens: bool
        +show_cost: bool
        +streaming: bool
        +vim_mode: bool
        +status_line: bool
    }

    class SessionConfig {
        +auto_save: bool
        +save_interval: int
        +max_history: int
        +session_dir: Path?
        +compress_after: int
    }

    class RoutingVariant {
        <<enumeration>>
        NITRO
        FLOOR
        EXACTO
        THINKING
        ONLINE
    }

    class TransportType {
        <<enumeration>>
        STDIO
        STREAMABLE_HTTP
    }

    class HookType {
        <<enumeration>>
        COMMAND
        PROMPT
    }

    Code-ForgeConfig --> ModelConfig
    Code-ForgeConfig --> PermissionConfig
    Code-ForgeConfig --> HooksConfig
    Code-ForgeConfig --> MCPServerConfig
    Code-ForgeConfig --> DisplayConfig
    Code-ForgeConfig --> SessionConfig
    ModelConfig --> RoutingVariant
    HooksConfig --> HookConfig
    HookConfig --> HookType
    MCPServerConfig --> TransportType
```

---

## 2. Class Diagram - Configuration Loading

```mermaid
classDiagram
    class IConfigLoader {
        <<interface>>
        +load(path) Dict
        +merge(base, override) Dict
        +validate(config) tuple
    }

    class IConfigSource {
        <<interface>>
        +load() Dict
        +exists() bool
    }

    class ConfigLoader {
        -_user_dir: Path
        -_project_dir: Path
        -_config: Code-ForgeConfig?
        -_observers: List~Callable~
        -_file_watcher: Observer?
        +config: Code-ForgeConfig
        +load_all() Code-ForgeConfig
        +load(path) Dict
        +merge(base, override) Dict
        +validate(config) tuple
        +reload() void
        +watch() void
        +stop_watching() void
        +add_observer(callback) void
        +remove_observer(callback) void
    }

    class JsonFileSource {
        -_path: Path
        +load() Dict
        +exists() bool
    }

    class YamlFileSource {
        -_path: Path
        +load() Dict
        +exists() bool
    }

    class EnvironmentSource {
        +PREFIX: str
        +load() Dict
        +exists() bool
    }

    IConfigLoader <|.. ConfigLoader
    IConfigSource <|.. JsonFileSource
    IConfigSource <|.. YamlFileSource
    IConfigSource <|.. EnvironmentSource
    ConfigLoader --> IConfigSource : uses
    ConfigLoader --> Code-ForgeConfig : produces
```

---

## 3. Sequence Diagram - Configuration Loading

```mermaid
sequenceDiagram
    participant App as Application
    participant CL as ConfigLoader
    participant JSON as JsonFileSource
    participant YAML as YamlFileSource
    participant ENV as EnvironmentSource
    participant Model as Code-ForgeConfig

    App->>CL: load_all()
    CL->>CL: Create default config

    Note over CL: Load Enterprise
    CL->>JSON: load("/etc/src/forge/settings.json")
    JSON-->>CL: enterprise config or {}

    Note over CL: Load User
    CL->>JSON: load("~/.src/forge/settings.json")
    alt JSON exists
        JSON-->>CL: user config
    else Try YAML
        CL->>YAML: load("~/.src/forge/settings.yaml")
        YAML-->>CL: user config or {}
    end

    Note over CL: Load Project
    CL->>JSON: load(".src/forge/settings.json")
    JSON-->>CL: project config or {}

    Note over CL: Load Local
    CL->>JSON: load(".src/forge/settings.local.json")
    JSON-->>CL: local config or {}

    Note over CL: Load Environment
    CL->>ENV: load()
    ENV-->>CL: env config

    CL->>CL: merge all configs
    CL->>Model: validate(merged)
    Model-->>CL: Code-ForgeConfig instance

    CL-->>App: Code-ForgeConfig
```

---

## 4. Sequence Diagram - Live Reload

```mermaid
sequenceDiagram
    participant FS as File System
    participant W as FileWatcher
    participant CL as ConfigLoader
    participant O1 as Observer 1
    participant O2 as Observer 2

    Note over W: Watching config directories

    FS->>W: File modified event
    W->>CL: on_modified(event)
    CL->>CL: Check file is config file

    alt Is config file
        CL->>CL: load_all()
        CL->>CL: validate new config

        alt Valid config
            CL->>CL: _config = new_config
            CL->>O1: callback(new_config)
            O1-->>CL: done
            CL->>O2: callback(new_config)
            O2-->>CL: done
        else Invalid config
            CL->>CL: Log error
            Note over CL: Keep old config
        end
    end
```

---

## 5. State Diagram - Configuration State

```mermaid
stateDiagram-v2
    [*] --> Unloaded: Initialize

    Unloaded --> Loading: load_all() called
    Loading --> Loaded: Validation success
    Loading --> Error: Validation failed

    Error --> Loaded: Use defaults
    Error --> Loading: Retry with fixes

    Loaded --> Reloading: File changed
    Reloading --> Loaded: Success
    Reloading --> Loaded: Failed (keep old)

    Loaded --> Watching: watch() called
    Watching --> Loaded: stop_watching()

    state Watching {
        [*] --> Idle
        Idle --> Processing: File event
        Processing --> Idle: Reload complete
    }
```

---

## 6. Component Diagram

```mermaid
flowchart TB
    subgraph External["External Sources"]
        ENT["/etc/src/forge/settings.json"]
        USER["~/.src/forge/settings.json"]
        PROJ[".src/forge/settings.json"]
        LOCAL[".src/forge/settings.local.json"]
        ENV["Environment Variables"]
    end

    subgraph ConfigSystem["Configuration System"]
        LOADER[ConfigLoader]
        SOURCES[Config Sources]
        MODELS[Config Models]
        WATCHER[File Watcher]
    end

    subgraph Consumers["Configuration Consumers"]
        CLI[CLI]
        AGENT[Agent]
        TOOLS[Tools]
        PERMS[Permissions]
    end

    ENT --> SOURCES
    USER --> SOURCES
    PROJ --> SOURCES
    LOCAL --> SOURCES
    ENV --> SOURCES

    SOURCES --> LOADER
    LOADER --> MODELS
    WATCHER --> LOADER

    MODELS --> CLI
    MODELS --> AGENT
    MODELS --> TOOLS
    MODELS --> PERMS
```

---

## 7. Activity Diagram - Merge Algorithm

```mermaid
flowchart TD
    START([Start Merge]) --> INPUT[/base, override/]
    INPUT --> COPY[result = copy of base]

    COPY --> LOOP{For each key in override}

    LOOP -->|Has key| CHECK{Key exists in result?}
    LOOP -->|Done| RETURN[/Return result/]

    CHECK -->|Yes| BOTH_DICT{Both values are dicts?}
    CHECK -->|No| SET[result[key] = override[key]]

    BOTH_DICT -->|Yes| RECURSE[result[key] = merge recursive]
    BOTH_DICT -->|No| OVERRIDE[result[key] = override[key]]

    SET --> LOOP
    RECURSE --> LOOP
    OVERRIDE --> LOOP

    RETURN --> END([End])
```

---

## 8. Package Diagram

```mermaid
flowchart TB
    subgraph config["forge.config"]
        INIT["__init__.py"]
        MODELS["models.py"]
        SOURCES["sources.py"]
        LOADER["loader.py"]
    end

    subgraph core["forge.core (Phase 1.1)"]
        INTERFACES["interfaces.py"]
        ERRORS["errors.py"]
        LOGGING["logging.py"]
    end

    subgraph external["External Dependencies"]
        PYDANTIC["pydantic"]
        WATCHDOG["watchdog"]
        YAML["pyyaml"]
    end

    LOADER --> INTERFACES
    LOADER --> ERRORS
    LOADER --> LOGGING
    MODELS --> PYDANTIC
    LOADER --> WATCHDOG
    SOURCES --> YAML
    SOURCES --> PYDANTIC
```

---

## 9. File Hierarchy Diagram

```
Configuration Loading Order (Priority: Low → High)
═══════════════════════════════════════════════════

┌─────────────────────────────────────────────────┐
│  6. Environment Variables (FORGE_*)          │ ← Highest Priority
├─────────────────────────────────────────────────┤
│  5. Local Overrides                             │
│     .src/forge/settings.local.json               │
├─────────────────────────────────────────────────┤
│  4. Project Settings                            │
│     .src/forge/settings.json                     │
├─────────────────────────────────────────────────┤
│  3. User Settings                               │
│     ~/.src/forge/settings.json                   │
├─────────────────────────────────────────────────┤
│  2. Enterprise Settings                         │
│     /etc/src/forge/settings.json                 │
├─────────────────────────────────────────────────┤
│  1. Default Values (in code)                    │ ← Lowest Priority
└─────────────────────────────────────────────────┘
```

---

## Notes

- Configuration models use Pydantic v2 for validation
- `SecretStr` is used for API keys to prevent logging
- File watcher uses `watchdog` library
- Deep merge preserves nested structures
- Invalid configuration logs error but uses fallback
