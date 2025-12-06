"""Tests for search providers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opencode.web.search.base import SearchError, SearchProvider
from opencode.web.search.brave import BraveSearchProvider
from opencode.web.search.duckduckgo import DuckDuckGoProvider
from opencode.web.search.google import GoogleSearchProvider
from opencode.web.types import SearchResponse, SearchResult


class TestSearchProvider:
    """Tests for SearchProvider base class."""

    def test_filter_results_no_filters(self) -> None:
        """Test filter_results with no filters returns same response."""

        class TestProvider(SearchProvider):
            @property
            def name(self) -> str:
                return "test"

            async def search(self, query: str, num_results: int = 10, **kwargs):
                return SearchResponse(query=query, results=[], provider=self.name)

        provider = TestProvider()
        response = SearchResponse(
            query="test",
            results=[
                SearchResult(title="T1", url="https://a.com", snippet="S1"),
                SearchResult(title="T2", url="https://b.com", snippet="S2"),
            ],
            provider="test",
        )

        filtered = provider.filter_results(response)
        assert len(filtered.results) == 2

    def test_filter_results_allowed_domains(self) -> None:
        """Test filtering by allowed domains."""

        class TestProvider(SearchProvider):
            @property
            def name(self) -> str:
                return "test"

            async def search(self, query: str, num_results: int = 10, **kwargs):
                return SearchResponse(query=query, results=[], provider=self.name)

        provider = TestProvider()
        response = SearchResponse(
            query="test",
            results=[
                SearchResult(title="T1", url="https://example.com/page", snippet="S1"),
                SearchResult(title="T2", url="https://other.com/page", snippet="S2"),
                SearchResult(title="T3", url="https://example.com/other", snippet="S3"),
            ],
            provider="test",
        )

        filtered = provider.filter_results(response, allowed_domains=["example.com"])
        assert len(filtered.results) == 2
        assert all("example.com" in r.url for r in filtered.results)

    def test_filter_results_blocked_domains(self) -> None:
        """Test filtering by blocked domains."""

        class TestProvider(SearchProvider):
            @property
            def name(self) -> str:
                return "test"

            async def search(self, query: str, num_results: int = 10, **kwargs):
                return SearchResponse(query=query, results=[], provider=self.name)

        provider = TestProvider()
        response = SearchResponse(
            query="test",
            results=[
                SearchResult(title="T1", url="https://example.com/page", snippet="S1"),
                SearchResult(title="T2", url="https://blocked.com/page", snippet="S2"),
                SearchResult(title="T3", url="https://other.com/page", snippet="S3"),
            ],
            provider="test",
        )

        filtered = provider.filter_results(response, blocked_domains=["blocked.com"])
        assert len(filtered.results) == 2
        assert all("blocked.com" not in r.url for r in filtered.results)

    def test_filter_results_combined(self) -> None:
        """Test with both allowed and blocked domains."""

        class TestProvider(SearchProvider):
            @property
            def name(self) -> str:
                return "test"

            async def search(self, query: str, num_results: int = 10, **kwargs):
                return SearchResponse(query=query, results=[], provider=self.name)

        provider = TestProvider()
        response = SearchResponse(
            query="test",
            results=[
                SearchResult(title="T1", url="https://docs.example.com", snippet="S1"),
                SearchResult(title="T2", url="https://bad.example.com", snippet="S2"),
                SearchResult(title="T3", url="https://other.com", snippet="S3"),
            ],
            provider="test",
        )

        filtered = provider.filter_results(
            response,
            allowed_domains=["example.com"],
            blocked_domains=["bad.example.com"],
        )
        assert len(filtered.results) == 1
        assert "docs.example.com" in filtered.results[0].url


class TestDuckDuckGoProvider:
    """Tests for DuckDuckGoProvider."""

    def test_name(self) -> None:
        """Test provider name."""
        provider = DuckDuckGoProvider()
        assert provider.name == "duckduckgo"

    def test_requires_api_key(self) -> None:
        """Test requires_api_key is False."""
        provider = DuckDuckGoProvider()
        assert provider.requires_api_key is False

    @pytest.mark.asyncio
    async def test_search_import_error(self) -> None:
        """Test search handles ImportError."""
        provider = DuckDuckGoProvider()

        with patch.dict("sys.modules", {"duckduckgo_search": None}):
            with patch(
                "opencode.web.search.duckduckgo.DuckDuckGoProvider.search",
                side_effect=SearchError("duckduckgo-search package not installed"),
            ):
                with pytest.raises(SearchError, match="not installed"):
                    await provider.search("test")

    @pytest.mark.asyncio
    async def test_search_success(self) -> None:
        """Test successful search."""
        provider = DuckDuckGoProvider()

        mock_results = [
            {"title": "Result 1", "href": "https://a.com", "body": "Snippet 1"},
            {"title": "Result 2", "href": "https://b.com", "body": "Snippet 2"},
        ]

        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text = MagicMock(return_value=mock_results)

        with patch("duckduckgo_search.DDGS", return_value=mock_ddgs):
            response = await provider.search("test query", num_results=5)

        assert response.query == "test query"
        assert response.provider == "duckduckgo"
        assert len(response.results) == 2
        assert response.results[0].title == "Result 1"
        assert response.results[0].url == "https://a.com"

    @pytest.mark.asyncio
    async def test_search_error(self) -> None:
        """Test search handles errors."""
        provider = DuckDuckGoProvider()

        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text = MagicMock(side_effect=Exception("API Error"))

        with patch("duckduckgo_search.DDGS", return_value=mock_ddgs):
            with pytest.raises(SearchError, match="Search failed"):
                await provider.search("test")


class TestGoogleSearchProvider:
    """Tests for GoogleSearchProvider."""

    def test_initialization(self) -> None:
        """Test provider initialization."""
        provider = GoogleSearchProvider(api_key="test-key", cx="test-cx")
        assert provider.api_key == "test-key"
        assert provider.cx == "test-cx"

    def test_name(self) -> None:
        """Test provider name."""
        provider = GoogleSearchProvider(api_key="key", cx="cx")
        assert provider.name == "google"

    def test_requires_api_key(self) -> None:
        """Test requires_api_key is True."""
        provider = GoogleSearchProvider(api_key="key", cx="cx")
        assert provider.requires_api_key is True

    @pytest.mark.asyncio
    async def test_search_no_api_key(self) -> None:
        """Test search without API key raises error."""
        provider = GoogleSearchProvider(api_key="", cx="cx")
        with pytest.raises(SearchError, match="API key not configured"):
            await provider.search("test")

    @pytest.mark.asyncio
    async def test_search_success(self) -> None:
        """Test successful search."""
        provider = GoogleSearchProvider(api_key="key", cx="cx")

        mock_response = {
            "items": [
                {
                    "title": "Result 1",
                    "link": "https://a.com",
                    "snippet": "Snippet 1",
                    "displayLink": "a.com",
                },
            ],
            "searchInformation": {"totalResults": "100"},
        }

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=mock_response)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_resp))
        )
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with patch("aiohttp.ClientSession", return_value=mock_session):
            response = await provider.search("test query")

        assert response.query == "test query"
        assert response.provider == "google"
        assert response.total_results == 100

    @pytest.mark.asyncio
    async def test_search_api_error(self) -> None:
        """Test search handles API errors."""
        provider = GoogleSearchProvider(api_key="key", cx="cx")

        mock_resp = AsyncMock()
        mock_resp.status = 400
        mock_resp.text = AsyncMock(return_value="Bad Request")

        # Create a proper context manager mock for both levels
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_cm.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_cm)

        mock_session_cm = MagicMock()
        mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cm.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session_cm):
            with pytest.raises(SearchError, match="Google API error"):
                await provider.search("test")


class TestBraveSearchProvider:
    """Tests for BraveSearchProvider."""

    def test_initialization(self) -> None:
        """Test provider initialization."""
        provider = BraveSearchProvider(api_key="test-key")
        assert provider.api_key == "test-key"

    def test_name(self) -> None:
        """Test provider name."""
        provider = BraveSearchProvider(api_key="key")
        assert provider.name == "brave"

    def test_requires_api_key(self) -> None:
        """Test requires_api_key is True."""
        provider = BraveSearchProvider(api_key="key")
        assert provider.requires_api_key is True

    @pytest.mark.asyncio
    async def test_search_no_api_key(self) -> None:
        """Test search without API key raises error."""
        provider = BraveSearchProvider(api_key="")
        with pytest.raises(SearchError, match="API key not configured"):
            await provider.search("test")

    @pytest.mark.asyncio
    async def test_search_success(self) -> None:
        """Test successful search."""
        provider = BraveSearchProvider(api_key="key")

        mock_response = {
            "web": {
                "results": [
                    {
                        "title": "Result 1",
                        "url": "https://a.com",
                        "description": "Snippet 1",
                        "page_age": "2024-01-01",
                    },
                ],
            },
        }

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=mock_response)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_resp))
        )
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with patch("aiohttp.ClientSession", return_value=mock_session):
            response = await provider.search("test query")

        assert response.query == "test query"
        assert response.provider == "brave"
        assert len(response.results) == 1
        assert response.results[0].date == "2024-01-01"

    @pytest.mark.asyncio
    async def test_search_api_error(self) -> None:
        """Test search handles API errors."""
        provider = BraveSearchProvider(api_key="key")

        mock_resp = AsyncMock()
        mock_resp.status = 401
        mock_resp.text = AsyncMock(return_value="Unauthorized")

        # Create a proper context manager mock for both levels
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_cm.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_cm)

        mock_session_cm = MagicMock()
        mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cm.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session_cm):
            with pytest.raises(SearchError, match="Brave API error"):
                await provider.search("test")
