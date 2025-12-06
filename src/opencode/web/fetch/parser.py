"""HTML parser and converter."""

import logging
import re
from urllib.parse import urljoin

import html2text
from bs4 import BeautifulSoup

from ..types import ParsedContent

logger = logging.getLogger(__name__)


class HTMLParser:
    """Parses and converts HTML content."""

    def __init__(self) -> None:
        """Initialize parser."""
        self._h2t = html2text.HTML2Text()
        self._h2t.ignore_links = False
        self._h2t.ignore_images = False
        self._h2t.body_width = 0  # Don't wrap lines

    def parse(
        self,
        html: str,
        base_url: str | None = None,
    ) -> ParsedContent:
        """Parse HTML to structured content.

        Args:
            html: HTML content
            base_url: Base URL for relative links

        Returns:
            ParsedContent with extracted data
        """
        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title: str | None = None
        if soup.title and soup.title.string:
            title = soup.title.string

        # Extract metadata
        metadata: dict[str, str] = {}
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")
            if name and content:
                metadata[str(name)] = str(content)

        # Extract links
        links: list[dict[str, str]] = []
        for a in soup.find_all("a", href=True):
            href = str(a["href"])
            if base_url:
                href = urljoin(base_url, href)
            links.append({
                "text": a.get_text(strip=True),
                "url": href,
            })

        # Extract images
        images: list[dict[str, str]] = []
        for img in soup.find_all("img", src=True):
            src = str(img["src"])
            if base_url:
                src = urljoin(base_url, src)
            images.append({
                "alt": img.get("alt", ""),
                "src": src,
            })

        # Convert to text and markdown
        text = self.to_text(html)
        markdown = self.to_markdown(html)

        return ParsedContent(
            title=title,
            text=text,
            markdown=markdown,
            links=links,
            images=images,
            metadata=metadata,
        )

    def to_text(self, html: str) -> str:
        """Convert HTML to plain text.

        Args:
            html: HTML content

        Returns:
            Plain text content
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style
        for element in soup(["script", "style", "nav", "footer", "aside"]):
            element.decompose()

        text = soup.get_text(separator="\n")

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines()]
        text = "\n".join(line for line in lines if line)

        # Collapse multiple newlines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def to_markdown(self, html: str) -> str:
        """Convert HTML to Markdown.

        Args:
            html: HTML content

        Returns:
            Markdown content
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "footer", "aside"]):
            element.decompose()

        # Convert using html2text
        markdown = self._h2t.handle(str(soup))

        # Clean up
        markdown = re.sub(r"\n{3,}", "\n\n", markdown)

        return markdown.strip()

    def extract_main_content(self, html: str) -> str:
        """Extract main content, removing boilerplate.

        Args:
            html: HTML content

        Returns:
            Main content HTML
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove unwanted elements
        for element in soup([
            "script", "style", "nav", "header", "footer",
            "aside", "form", "iframe", "noscript",
        ]):
            element.decompose()

        # Try to find main content area
        main = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", {"class": re.compile(r"content|main|article")})
            or soup.find("div", {"id": re.compile(r"content|main|article")})
            or soup.body
            or soup
        )

        return str(main)
