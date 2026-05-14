"""
Parsing-based search engines (e.g. DuckDuckGo HTML scraper).
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from scripts.core.base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)


class DuckDuckGoEngine(SearchEngine):
    """DuckDuckGo HTML search engine (no API key required)."""

    SEARCH_URL = "https://html.duckduckgo.com/html/"

    def __init__(self, config: Optional[dict] = None):
        super().__init__("DuckDuckGo", config)
        timeout = (config or {}).get("timeout", 15)
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "User-Agent": (config or {}).get(
                    "user_agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36",
                ),
            },
            follow_redirects=True,
        )

    def build_url(self, query: str, **kwargs) -> str:
        """Build DuckDuckGo search URL."""
        from urllib.parse import quote_plus
        return f"https://duckduckgo.com/?q={quote_plus(query)}"

    async def search(
        self, query: str, max_results: int = 10, **kwargs
    ) -> list[SearchResult]:
        """Search DuckDuckGo and parse HTML results."""
        params = {"q": query}
        try:
            response = await self._client.post(self.SEARCH_URL, data=params)
            response.raise_for_status()
            return self._parse_results(response.text, max_results)
        except httpx.HTTPError as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []

    def _parse_results(self, html: str, max_results: int) -> list[SearchResult]:
        """Parse DuckDuckGo HTML search results."""
        soup = BeautifulSoup(html, "lxml")
        results = []

        for i, result in enumerate(soup.select(".result")[:max_results]):
            title_el = result.select_one(".result__title a")
            snippet_el = result.select_one(".result__snippet")
            if title_el:
                results.append(
                    SearchResult(
                        title=title_el.get_text(strip=True),
                        url=title_el.get("href", ""),
                        snippet=snippet_el.get_text(strip=True)
                        if snippet_el else "",
                        source=self.name,
                        rank=i + 1,
                        category="web",
                    )
                )
        return results

    async def close(self):
        await self._client.aclose()
