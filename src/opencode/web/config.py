"""Web tools configuration."""

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchProviderConfig:
    """Configuration for a search provider."""

    name: str
    api_key: str | None = None
    endpoint: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchConfig:
    """Search configuration."""

    default_provider: str = "duckduckgo"
    default_results: int = 10
    timeout: int = 10
    providers: dict[str, SearchProviderConfig] = field(default_factory=dict)


@dataclass
class FetchConfig:
    """Fetch configuration."""

    timeout: int = 30
    max_size: int = 5 * 1024 * 1024
    user_agent: str = "opencode/1.0 (AI Assistant)"
    follow_redirects: bool = True
    max_redirects: int = 5


@dataclass
class CacheConfig:
    """Cache configuration."""

    enabled: bool = True
    ttl: int = 900  # 15 minutes
    max_size: int = 100 * 1024 * 1024  # 100MB
    directory: str | None = None


@dataclass
class WebConfig:
    """Complete web tools configuration."""

    search: SearchConfig = field(default_factory=SearchConfig)
    fetch: FetchConfig = field(default_factory=FetchConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WebConfig":
        """Create from dictionary."""
        search_data = data.get("search", {})
        fetch_data = data.get("fetch", {})
        cache_data = data.get("cache", {})

        # Parse provider configs
        providers: dict[str, SearchProviderConfig] = {}
        for name, pdata in search_data.get("providers", {}).items():
            api_key_raw = pdata.get("api_key", "")
            api_key = os.path.expandvars(api_key_raw) if api_key_raw else None
            providers[name] = SearchProviderConfig(
                name=name,
                api_key=api_key,
                endpoint=pdata.get("endpoint"),
                extra={
                    k: v for k, v in pdata.items() if k not in ("api_key", "endpoint")
                },
            )

        search_config = SearchConfig(
            default_provider=search_data.get("default_provider", "duckduckgo"),
            default_results=search_data.get("default_results", 10),
            timeout=search_data.get("timeout", 10),
            providers=providers,
        )

        fetch_config = FetchConfig(
            timeout=fetch_data.get("timeout", 30),
            max_size=fetch_data.get("max_size", 5 * 1024 * 1024),
            user_agent=fetch_data.get("user_agent", "opencode/1.0 (AI Assistant)"),
            follow_redirects=fetch_data.get("follow_redirects", True),
            max_redirects=fetch_data.get("max_redirects", 5),
        )

        cache_config = CacheConfig(
            enabled=cache_data.get("enabled", True),
            ttl=cache_data.get("ttl", 900),
            max_size=cache_data.get("max_size", 100 * 1024 * 1024),
            directory=cache_data.get("directory"),
        )

        return cls(
            search=search_config,
            fetch=fetch_config,
            cache=cache_config,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        providers_dict: dict[str, dict[str, Any]] = {}
        for name, provider in self.search.providers.items():
            providers_dict[name] = {
                "api_key": provider.api_key,
                "endpoint": provider.endpoint,
                **provider.extra,
            }

        return {
            "search": {
                "default_provider": self.search.default_provider,
                "default_results": self.search.default_results,
                "timeout": self.search.timeout,
                "providers": providers_dict,
            },
            "fetch": {
                "timeout": self.fetch.timeout,
                "max_size": self.fetch.max_size,
                "user_agent": self.fetch.user_agent,
                "follow_redirects": self.fetch.follow_redirects,
                "max_redirects": self.fetch.max_redirects,
            },
            "cache": {
                "enabled": self.cache.enabled,
                "ttl": self.cache.ttl,
                "max_size": self.cache.max_size,
                "directory": self.cache.directory,
            },
        }
