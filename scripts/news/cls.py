"""财联社 (cls.cn) news search."""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from scripts.core.base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)


class CLSNewsEngine(SearchEngine):
    """财联社 financial news search engine."""

    SEARCH_URL = "https://www.cls.cn/searchPage"

    def __init__(self, config: Optional[dict] = None):
        super().__init__("财联社", config)
        timeout = (config or {}).get("timeout", 15)
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://www.cls.cn/",
            },
            follow_redirects=True,
        )

    def build_url(self, query: str, **kwargs) -> str:
        return f"{self.SEARCH_URL}?keyword={quote_plus(query)}&type=all"

    async def search(self, query: str, max_results: int = 10, **kwargs) -> list[SearchResult]:
        try:
            url = self.build_url(query)
            response = await self._client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            results = []
            articles = soup.select(".search-item, .article-item, .news-item") or soup.select("a[href*='/detail/']")
            for i, article in enumerate(articles[:max_results]):
                title_el = article.select_one("h3, h4, .title, a[href*='/detail/']")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                href = title_el.get("href", "")
                if href and not href.startswith("http"):
                    href = f"https://www.cls.cn{href}"
                snippet_el = article.select_one(".summary, .desc, p, .snippet")
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                results.append(SearchResult(title=title, url=href, snippet=snippet, source="财联社", rank=i + 1, category="news"))
            if not results:
                results.append(SearchResult(title=f"财联社: {query}", url=url, snippet="Search 财联社 financial news", source="财联社", rank=1, category="news"))
            return results
        except httpx.HTTPError as e:
            logger.error(f"财联社 search failed: {e}")
            return [SearchResult(title=f"财联社: {query}", url=self.build_url(query), snippet=f"Search via 财联社 (connection issue)", source="财联社", rank=1, category="news")]

    async def close(self):
        await self._client.aclose()
