"""
财联社 (cls.cn) news search engine.

Scrapes cls.cn search results for financial news.
"""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from scripts.core.base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)


class CLSNewsEngine(SearchEngine):
    """财联社 (cls.cn) news search engine."""

    SEARCH_URL = "https://www.cls.cn/searchPage"

    def __init__(self, config: Optional[dict] = None):
        super().__init__("cls", config)
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
                "Referer": "https://www.cls.cn/",
            },
            follow_redirects=True,
        )

    def build_url(self, query: str, **kwargs) -> str:
        return f"{self.SEARCH_URL}?keyword={quote_plus(query)}&type=all"

    async def search(
        self, query: str, max_results: int = 10, **kwargs
    ) -> list[SearchResult]:
        """Search 财联社 and parse results."""
        url = self.build_url(query)
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            return self._parse_results(response.text, query, max_results)
        except httpx.HTTPError as e:
            logger.error(f"财联社 search failed: {e}")
            return []

    def _parse_results(
        self, html: str, query: str, max_results: int
    ) -> list[SearchResult]:
        """Parse 财联社 search page."""
        soup = BeautifulSoup(html, "lxml")
        results = []

        # cls.cn typically uses dynamic rendering, so parsing may be limited
        articles = soup.select(
            "a[href*='/detail'], .news-item, .search-result-item, article"
        )
        for i, article in enumerate(articles[:max_results]):
            title_el = article.select_one("h3, h4, .title, .news-title")
            link = article.get("href", "")
            snippet_el = article.select_one(
                ".summary, .desc, .abstract, p"
            )

            title = title_el.get_text(strip=True) if title_el else ""
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""

            if not title and not link:
                continue

            full_url = link if link.startswith("http") else f"https://www.cls.cn{link}"

            results.append(
                SearchResult(
                    title=title or f"财联社: {query}",
                    url=full_url,
                    snippet=snippet or f"Search result from 财联社",
                    source=self.name,
                    rank=i + 1,
                    category="news",
                    extra={"region": "cn"},
                )
            )

        if not results:
            # Fallback: return URL for manual browsing
            search_url = self.build_url(query)
            results.append(
                SearchResult(
                    title=f"财联社: {query}",
                    url=search_url,
                    snippet=f"Search 财联社 for '{query}' (site requires JS)",
                    source=self.name,
                    rank=1,
                    category="news",
                    extra={"search_url": search_url, "note": "JS-rendered page"},
                )
            )

        return results

    async def close(self):
        await self._client.aclose()
