"""Configuration package for Code-Forge.

This package provides hierarchical configuration loading with support for:
- JSON and YAML configuration files
- Environment variable overrides
- Live configuration reload
- Pydantic-based validation

Usage:
    from code_forge.config import ConfigLoader, CodeForgeConfig

    loader = ConfigLoader()
    config = loader.config  # Loads and caches configuration

    # Access configuration values
    print(config.model.default)
    print(config.display.theme)

    # Watch for changes
    loader.watch()
    loader.add_observer(lambda c: print("Config changed!"))
"""

from code_forge.config.loader import ConfigLoader
from code_forge.config.models import (
    DisplayConfig,
    HookConfig,
    HooksConfig,
    HookType,
    MCPServerConfig,
    ModelConfig,
    CodeForgeConfig,
    PermissionConfig,
    RoutingVariant,
    SessionConfig,
    TransportType,
)
from code_forge.config.sources import (
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
    "CodeForgeConfig",
    "PermissionConfig",
    "RoutingVariant",
    "SessionConfig",
    "TransportType",
    "YamlFileSource",
]
