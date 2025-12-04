"""Configuration package for OpenCode.

This package provides hierarchical configuration loading with support for:
- JSON and YAML configuration files
- Environment variable overrides
- Live configuration reload
- Pydantic-based validation

Usage:
    from opencode.config import ConfigLoader, OpenCodeConfig

    loader = ConfigLoader()
    config = loader.config  # Loads and caches configuration

    # Access configuration values
    print(config.model.default)
    print(config.display.theme)

    # Watch for changes
    loader.watch()
    loader.add_observer(lambda c: print("Config changed!"))
"""

from opencode.config.loader import ConfigLoader
from opencode.config.models import (
    DisplayConfig,
    HookConfig,
    HooksConfig,
    HookType,
    MCPServerConfig,
    ModelConfig,
    OpenCodeConfig,
    PermissionConfig,
    RoutingVariant,
    SessionConfig,
    TransportType,
)
from opencode.config.sources import (
    EnvironmentSource,
    IConfigSource,
    JsonFileSource,
    YamlFileSource,
)

__all__ = [
    "ConfigLoader",
    "DisplayConfig",
    "EnvironmentSource",
    "HookConfig",
    "HookType",
    "HooksConfig",
    "IConfigSource",
    "JsonFileSource",
    "MCPServerConfig",
    "ModelConfig",
    "OpenCodeConfig",
    "PermissionConfig",
    "RoutingVariant",
    "SessionConfig",
    "TransportType",
    "YamlFileSource",
]
