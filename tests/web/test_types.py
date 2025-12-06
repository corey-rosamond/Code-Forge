"""Tests for web types."""

import pytest

from opencode.web.types import (
    FetchOptions,
    FetchResponse,
    ParsedContent,
    SearchResponse,
    SearchResult,
)


class TestSearchResult:
    """Tests for SearchResult."""

    def test_basic_creation(self) -> None:
        """Test creating a basic search result."""
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet",
        )
        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.snippet == "Test snippet"
        assert result.date is None
        assert result.source is None
        assert result.metadata == {}

    def test_full_creation(self) -> None:
        """Test creating a search result with all fields."""
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet",
            date="2024-01-01",
            source="example.com",
            metadata={"key": "value"},
        )
        assert result.date == "2024-01-01"
        assert result.source == "example.com"
        assert result.metadata == {"key": "value"}

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        result = SearchResult(
            title="Test",
            url="https://example.com",
            snippet="Snippet",
            date="2024-01-01",
            source="example.com",
        )
        d = result.to_dict()
        assert d["title"] == "Test"
        assert d["url"] == "https://example.com"
        assert d["snippet"] == "Snippet"
        assert d["date"] == "2024-01-01"
        assert d["source"] == "example.com"

    def test_to_markdown(self) -> None:
        """Test converting to markdown."""
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet",
        )
        md = result.to_markdown()
        assert "**[Test Title](https://example.com)**" in md
        assert "Test snippet" in md

    def test_to_markdown_with_date(self) -> None:
        """Test markdown includes date if present."""
        result = SearchResult(
            title="Test",
            url="https://example.com",
            snippet="Snippet",
            date="2024-01-01",
        )
        md = result.to_markdown()
        assert "*2024-01-01*" in md


class TestSearchResponse:
    """Tests for SearchResponse."""

    def test_basic_creation(self) -> None:
        """Test creating a basic search response."""
        response = SearchResponse(
            query="test query",
            results=[],
            provider="test",
        )
        assert response.query == "test query"
        assert response.results == []
        assert response.provider == "test"
        assert response.total_results is None
        assert response.search_time is None

    def test_with_results(self) -> None:
        """Test search response with results."""
        results = [
            SearchResult(title="R1", url="https://a.com", snippet="S1"),
            SearchResult(title="R2", url="https://b.com", snippet="S2"),
        ]
        response = SearchResponse(
            query="test",
            results=results,
            provider="test",
            total_results=2,
            search_time=0.5,
        )
        assert len(response.results) == 2
        assert response.total_results == 2
        assert response.search_time == 0.5

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        results = [SearchResult(title="T", url="https://x.com", snippet="S")]
        response = SearchResponse(
            query="q",
            results=results,
            provider="p",
            total_results=1,
        )
        d = response.to_dict()
        assert d["query"] == "q"
        assert d["provider"] == "p"
        assert len(d["results"]) == 1
        assert d["total_results"] == 1

    def test_to_markdown(self) -> None:
        """Test converting to markdown."""
        results = [
            SearchResult(title="Result 1", url="https://a.com", snippet="Snippet 1"),
            SearchResult(title="Result 2", url="https://b.com", snippet="Snippet 2"),
        ]
        response = SearchResponse(
            query="test query",
            results=results,
            provider="test",
        )
        md = response.to_markdown()
        assert "## Search Results for: test query" in md
        assert "### 1. [Result 1](https://a.com)" in md
        assert "### 2. [Result 2](https://b.com)" in md


class TestFetchResponse:
    """Tests for FetchResponse."""

    def test_basic_creation(self) -> None:
        """Test creating a basic fetch response."""
        response = FetchResponse(
            url="https://example.com",
            final_url="https://example.com",
            status_code=200,
            content_type="text/html",
            content="<html></html>",
            headers={},
            encoding="utf-8",
            fetch_time=0.1,
        )
        assert response.url == "https://example.com"
        assert response.status_code == 200
        assert response.from_cache is False

    def test_is_html(self) -> None:
        """Test is_html property."""
        html_response = FetchResponse(
            url="https://example.com",
            final_url="https://example.com",
            status_code=200,
            content_type="text/html; charset=utf-8",
            content="<html></html>",
            headers={},
            encoding="utf-8",
            fetch_time=0.1,
        )
        assert html_response.is_html is True

        json_response = FetchResponse(
            url="https://example.com",
            final_url="https://example.com",
            status_code=200,
            content_type="application/json",
            content="{}",
            headers={},
            encoding="utf-8",
            fetch_time=0.1,
        )
        assert json_response.is_html is False

    def test_is_text(self) -> None:
        """Test is_text property."""
        text_response = FetchResponse(
            url="https://example.com",
            final_url="https://example.com",
            status_code=200,
            content_type="text/plain",
            content="text",
            headers={},
            encoding="utf-8",
            fetch_time=0.1,
        )
        assert text_response.is_text is True

        json_response = FetchResponse(
            url="https://example.com",
            final_url="https://example.com",
            status_code=200,
            content_type="application/json",
            content="{}",
            headers={},
            encoding="utf-8",
            fetch_time=0.1,
        )
        assert json_response.is_text is True

        binary_response = FetchResponse(
            url="https://example.com",
            final_url="https://example.com",
            status_code=200,
            content_type="image/png",
            content=b"\x89PNG",
            headers={},
            encoding="utf-8",
            fetch_time=0.1,
        )
        assert binary_response.is_text is False

    def test_from_cache(self) -> None:
        """Test from_cache flag."""
        response = FetchResponse(
            url="https://example.com",
            final_url="https://example.com",
            status_code=200,
            content_type="text/html",
            content="<html></html>",
            headers={},
            encoding="utf-8",
            fetch_time=0.1,
            from_cache=True,
        )
        assert response.from_cache is True


class TestFetchOptions:
    """Tests for FetchOptions."""

    def test_defaults(self) -> None:
        """Test default values."""
        options = FetchOptions()
        assert options.timeout == 30
        assert options.max_size == 5 * 1024 * 1024
        assert options.follow_redirects is True
        assert options.max_redirects == 5
        assert options.verify_ssl is True
        assert options.headers == {}

    def test_custom_values(self) -> None:
        """Test custom values."""
        options = FetchOptions(
            timeout=60,
            max_size=1024,
            user_agent="Custom Agent",
            follow_redirects=False,
            max_redirects=3,
            headers={"X-Custom": "value"},
            verify_ssl=False,
        )
        assert options.timeout == 60
        assert options.max_size == 1024
        assert options.user_agent == "Custom Agent"
        assert options.follow_redirects is False
        assert options.max_redirects == 3
        assert options.headers == {"X-Custom": "value"}
        assert options.verify_ssl is False


class TestParsedContent:
    """Tests for ParsedContent."""

    def test_basic_creation(self) -> None:
        """Test creating parsed content."""
        content = ParsedContent(
            title="Test Title",
            text="Test text",
            markdown="# Test",
        )
        assert content.title == "Test Title"
        assert content.text == "Test text"
        assert content.markdown == "# Test"
        assert content.links == []
        assert content.images == []
        assert content.metadata == {}

    def test_full_creation(self) -> None:
        """Test with all fields."""
        content = ParsedContent(
            title="Title",
            text="Text",
            markdown="MD",
            links=[{"text": "Link", "url": "https://example.com"}],
            images=[{"alt": "Image", "src": "https://example.com/img.png"}],
            metadata={"description": "Test"},
        )
        assert len(content.links) == 1
        assert len(content.images) == 1
        assert content.metadata["description"] == "Test"
