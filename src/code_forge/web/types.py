"""Data types for web tools."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchResult:
    """Single search result."""

    title: str
    url: str
    snippet: str
    date: str | None = None
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "date": self.date,
            "source": self.source,
        }

    def to_markdown(self) -> str:
        """Format as Markdown."""
        md = f"**[{self.title}]({self.url})**\n"
        md += f"{self.snippet}\n"
        if self.date:
            md += f"*{self.date}*\n"
        return md


@dataclass
class SearchResponse:
    """Search response with multiple results."""

    query: str
    results: list[SearchResult]
    provider: str
    total_results: int | None = None
    search_time: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "provider": self.provider,
            "total_results": self.total_results,
            "search_time": self.search_time,
        }

    def to_markdown(self) -> str:
        """Format results as Markdown."""
        lines = [f"## Search Results for: {self.query}\n"]
        for i, result in enumerate(self.results, 1):
            lines.append(f"### {i}. [{result.title}]({result.url})")
            lines.append(f"{result.snippet}\n")
        return "\n".join(lines)


@dataclass
class FetchResponse:
    """Response from URL fetch."""

    url: str
    final_url: str
    status_code: int
    content_type: str
    content: str | bytes
    headers: dict[str, str]
    encoding: str
    fetch_time: float
    from_cache: bool = False

    @property
    def is_html(self) -> bool:
        """Check if content is HTML."""
        return "text/html" in self.content_type.lower()

    @property
    def is_text(self) -> bool:
        """Check if content is text."""
        ct = self.content_type.lower()
        return "text/" in ct or "json" in ct or "xml" in ct


@dataclass
class FetchOptions:
    """Options for URL fetching."""

    timeout: int = 30
    max_size: int = 5 * 1024 * 1024  # 5MB
    user_agent: str = "forge/1.0 (AI Assistant)"
    follow_redirects: bool = True
    max_redirects: int = 5
    headers: dict[str, str] = field(default_factory=dict)
    verify_ssl: bool = True


@dataclass
class ParsedContent:
    """Parsed HTML content."""

    title: str | None
    text: str
    markdown: str
    links: list[dict[str, str]] = field(default_factory=list)
    images: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
