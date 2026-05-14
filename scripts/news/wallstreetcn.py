"""华尔街见闻 (wallstreetcn.com) news search."""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from scripts.core.base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)


class WallStreetCNEngine(SearchEngine):
    """华尔街见闻 financial news search engine."""

    SEARCH_URL = "https://wallstreetcn.com/search"

    def __init__(self, config: Optional[dict] = None):
        super().__init__("华尔街见闻", config)
        timeout = (config or {}).get("timeout", 15)
        self._client = httpx.AsyncClient(timeout=timeout, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://wallstreetcn.com/"}, follow_redirects=True)

    def build_url(self, query: str, **kwargs) -> str:
        return f"{self.SEARCH_URL}?q={quote_plus(query)}"

    async def search(self, query: str, max_results: int = 10, **kwargs) -> list[SearchResult]:
        try:
            url = self.build_url(query)
            response = await self._client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            results = []
            articles = soup.select("a[href*='/article/'], a[href*='/news/'], .article-item")
            for i, article in enumerate(articles[:max_results]):
                title = article.get_text(strip=True) or article.get("title", "")
                href = article.get("href", "")
                if href and not href.startswith("http"):
                    href = f"https://wallstreetcn.com{href}"
                if title:
                    results.append(SearchResult(title=title[:200], url=href, snippet="", source="华尔街见闻", rank=i + 1, category="news"))
            if not results:
                results.append(SearchResult(title=f"华尔街见闻: {query}", url=url, snippet="Search 华尔街见闻", source="华尔街见闻", rank=1, category="news"))
            return results
        except httpx.HTTPError as e:
            logger.error(f"华尔街见闻 search failed: {e}")
            return [SearchResult(title=f"华尔街见闻: {query}", url=self.build_url(query), snippet="Connection issue", source="华尔街见闻", rank=1, category="news")]

    async def close(self):
        await self._client.aclose()
