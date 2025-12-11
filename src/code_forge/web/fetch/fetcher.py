"""URL fetcher implementation."""

import asyncio
import logging
import time

import aiohttp

from ..types import FetchOptions, FetchResponse

logger = logging.getLogger(__name__)


class FetchError(Exception):
    """URL fetch error."""

    pass


class URLFetcher:
    """Fetches content from URLs."""

    def __init__(self, options: FetchOptions | None = None):
        """Initialize fetcher.

        Args:
            options: Default fetch options
        """
        self.default_options = options or FetchOptions()

    async def fetch(
        self,
        url: str,
        options: FetchOptions | None = None,
    ) -> FetchResponse:
        """Fetch URL content.

        Args:
            url: URL to fetch
            options: Override options for this request

        Returns:
            FetchResponse with content
        """
        opts = options or self.default_options
        start_time = time.time()

        # Upgrade HTTP to HTTPS
        if url.startswith("http://"):
            url = "https://" + url[7:]

        headers = {
            "User-Agent": opts.user_agent,
            **opts.headers,
        }

        timeout = aiohttp.ClientTimeout(total=opts.timeout)

        try:
            connector = aiohttp.TCPConnector(ssl=opts.verify_ssl)
            async with aiohttp.ClientSession(
                timeout=timeout,
                headers=headers,
                connector=connector,
            ) as session, session.get(
                url,
                allow_redirects=opts.follow_redirects,
                max_redirects=opts.max_redirects,
            ) as resp:
                # Check content size from headers
                content_length = resp.headers.get("Content-Length")
                if content_length and int(content_length) > opts.max_size:
                    raise FetchError(
                        f"Content too large: {content_length} bytes "
                        f"(max: {opts.max_size})"
                    )

                # Read content with size limit
                content = await self._read_content(resp, opts.max_size)

                # Determine encoding
                encoding = resp.charset or "utf-8"

                # Decode if text
                content_type = resp.content_type or ""
                decoded_content: str | bytes
                if "text" in content_type or "json" in content_type:
                    try:
                        decoded_content = content.decode(encoding)
                    except UnicodeDecodeError:
                        decoded_content = content.decode("utf-8", errors="replace")
                else:
                    decoded_content = content

                fetch_time = time.time() - start_time

                return FetchResponse(
                    url=url,
                    final_url=str(resp.url),
                    status_code=resp.status,
                    content_type=content_type,
                    content=decoded_content,
                    headers=dict(resp.headers),
                    encoding=encoding,
                    fetch_time=fetch_time,
                )

        except aiohttp.TooManyRedirects as e:
            raise FetchError(f"Too many redirects: {e}") from e
        except aiohttp.ClientError as e:
            raise FetchError(f"Network error: {e}") from e
        except TimeoutError as e:
            raise FetchError(f"Timeout fetching {url}") from e

    async def _read_content(
        self,
        response: aiohttp.ClientResponse,
        max_size: int,
    ) -> bytes:
        """Read response content with size limit."""
        chunks: list[bytes] = []
        total_size = 0

        async for chunk in response.content.iter_chunked(8192):
            total_size += len(chunk)
            if total_size > max_size:
                raise FetchError(f"Content exceeds max size: {max_size} bytes")
            chunks.append(chunk)

        return b"".join(chunks)

    async def fetch_multiple(
        self,
        urls: list[str],
        options: FetchOptions | None = None,
        concurrency: int = 5,
    ) -> list[FetchResponse | FetchError]:
        """Fetch multiple URLs concurrently.

        Args:
            urls: URLs to fetch
            options: Fetch options
            concurrency: Max concurrent requests

        Returns:
            List of responses or errors
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def fetch_one(url: str) -> FetchResponse | FetchError:
            async with semaphore:
                try:
                    return await self.fetch(url, options)
                except FetchError as e:
                    return e

        tasks = [fetch_one(url) for url in urls]
        return await asyncio.gather(*tasks)
