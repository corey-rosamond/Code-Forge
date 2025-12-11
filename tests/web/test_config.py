"""Tests for web configuration."""

import os
from unittest.mock import patch

import pytest

from code_forge.web.config import (
    CacheConfig,
    FetchConfig,
    SearchConfig,
    SearchProviderConfig,
    WebConfig,
)


class TestSearchProviderConfig:
    """Tests for SearchProviderConfig."""

    def test_basic_creation(self) -> None:
        """Test creating a basic provider config."""
        config = SearchProviderConfig(name="test")
        assert config.name == "test"
        assert config.api_key is None
        assert config.endpoint is None
        assert config.extra == {}

    def test_full_creation(self) -> None:
        """Test creating with all fields."""
        config = SearchProviderConfig(
            name="google",
            api_key="test-key",
            endpoint="https://api.example.com",
            extra={"cx": "search-engine-id"},
        )
        assert config.name == "google"
        assert config.api_key == "test-key"
        assert config.endpoint == "https://api.example.com"
        assert config.extra["cx"] == "search-engine-id"


class TestSearchConfig:
    """Tests for SearchConfig."""

    def test_defaults(self) -> None:
        """Test default values."""
        config = SearchConfig()
        assert config.default_provider == "duckduckgo"
        assert config.default_results == 10
        assert config.timeout == 10
        assert config.providers == {}

    def test_custom_values(self) -> None:
        """Test custom values."""
        providers = {"google": SearchProviderConfig(name="google", api_key="key")}
        config = SearchConfig(
            default_provider="google",
            default_results=5,
            timeout=30,
            providers=providers,
        )
        assert config.default_provider == "google"
        assert config.default_results == 5
        assert config.timeout == 30
        assert "google" in config.providers


class TestFetchConfig:
    """Tests for FetchConfig."""

    def test_defaults(self) -> None:
        """Test default values."""
        config = FetchConfig()
        assert config.timeout == 30
        assert config.max_size == 5 * 1024 * 1024
        assert config.follow_redirects is True
        assert config.max_redirects == 5

    def test_custom_values(self) -> None:
        """Test custom values."""
        config = FetchConfig(
            timeout=60,
            max_size=1024,
            user_agent="Custom",
            follow_redirects=False,
            max_redirects=3,
        )
        assert config.timeout == 60
        assert config.max_size == 1024
        assert config.user_agent == "Custom"


class TestCacheConfig:
    """Tests for CacheConfig."""

    def test_defaults(self) -> None:
        """Test default values."""
        config = CacheConfig()
        assert config.enabled is True
        assert config.ttl == 900
        assert config.max_size == 100 * 1024 * 1024
        assert config.directory is None

    def test_custom_values(self) -> None:
        """Test custom values."""
        config = CacheConfig(
            enabled=False,
            ttl=60,
            max_size=1024,
            directory="/tmp/cache",
        )
        assert config.enabled is False
        assert config.ttl == 60
        assert config.directory == "/tmp/cache"


class TestWebConfig:
    """Tests for WebConfig."""

    def test_defaults(self) -> None:
        """Test default values."""
        config = WebConfig()
        assert config.search.default_provider == "duckduckgo"
        assert config.fetch.timeout == 30
        assert config.cache.enabled is True

    def test_from_dict_empty(self) -> None:
        """Test from_dict with empty dict."""
        config = WebConfig.from_dict({})
        assert config.search.default_provider == "duckduckgo"
        assert config.fetch.timeout == 30
        assert config.cache.enabled is True

    def test_from_dict_full(self) -> None:
        """Test from_dict with full config."""
        data = {
            "search": {
                "default_provider": "google",
                "default_results": 5,
                "timeout": 15,
                "providers": {
                    "google": {
                        "api_key": "test-key",
                        "endpoint": "https://api.example.com",
                        "cx": "search-id",
                    },
                },
            },
            "fetch": {
                "timeout": 60,
                "max_size": 1024,
                "user_agent": "Test Agent",
                "follow_redirects": False,
                "max_redirects": 3,
            },
            "cache": {
                "enabled": False,
                "ttl": 60,
                "max_size": 1024,
                "directory": "/tmp/cache",
            },
        }
        config = WebConfig.from_dict(data)

        assert config.search.default_provider == "google"
        assert config.search.default_results == 5
        assert "google" in config.search.providers
        assert config.search.providers["google"].api_key == "test-key"
        assert config.search.providers["google"].extra["cx"] == "search-id"

        assert config.fetch.timeout == 60
        assert config.fetch.max_size == 1024
        assert config.fetch.follow_redirects is False

        assert config.cache.enabled is False
        assert config.cache.ttl == 60
        assert config.cache.directory == "/tmp/cache"

    def test_from_dict_env_var_expansion(self) -> None:
        """Test environment variable expansion in api_key."""
        with patch.dict(os.environ, {"TEST_API_KEY": "secret-key"}):
            data = {
                "search": {
                    "providers": {
                        "google": {
                            "api_key": "${TEST_API_KEY}",
                        },
                    },
                },
            }
            config = WebConfig.from_dict(data)
            assert config.search.providers["google"].api_key == "secret-key"

    def test_from_dict_empty_api_key(self) -> None:
        """Test empty api_key becomes None."""
        data = {
            "search": {
                "providers": {
                    "google": {
                        "api_key": "",
                    },
                },
            },
        }
        config = WebConfig.from_dict(data)
        assert config.search.providers["google"].api_key is None

    def test_to_dict(self) -> None:
        """Test converting config to dict."""
        config = WebConfig()
        d = config.to_dict()

        assert "search" in d
        assert "fetch" in d
        assert "cache" in d
        assert d["search"]["default_provider"] == "duckduckgo"
        assert d["fetch"]["timeout"] == 30
        assert d["cache"]["enabled"] is True

    def test_to_dict_with_providers(self) -> None:
        """Test to_dict includes provider config."""
        providers = {
            "google": SearchProviderConfig(
                name="google",
                api_key="key",
                endpoint="https://api.example.com",
                extra={"cx": "search-id"},
            ),
        }
        config = WebConfig(
            search=SearchConfig(providers=providers),
        )
        d = config.to_dict()

        assert "google" in d["search"]["providers"]
        assert d["search"]["providers"]["google"]["api_key"] == "key"
        assert d["search"]["providers"]["google"]["cx"] == "search-id"
