"""财联社 (cls.cn) news search engine."""
from __future__ import annotations
import logging
from typing import Optional
from urllib.parse import quote_plus
import httpx
from bs4 import BeautifulSoup
from scripts.core.base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)

class CLSNewsEngine(SearchEngine):
    SEARCH_URL = "https://www.cls.cn/searchPage"

    def __init__(self, config: Optional[dict] = None):
        super().__init__("cls", config)
        timeout = (config or {}).get("timeout", 15)
        self._client = httpx.AsyncClient(timeout=timeout, headers={"User-Agent": (config or {}).get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"), "Referer": "https://www.cls.cn/"}, follow_redirects=True)

    def build_url(self, query: str, **kwargs) -> str:
        return f"{self.SEARCH_URL}?keyword={quote_plus(query)}&type=all"

    async def search(self, query: str, max_results: int = 10, **kwargs) -> list[SearchResult]:
        url = self.build_url(query)
        try:
            r = await self._client.get(url); r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")
            results = []
            for i, a in enumerate(soup.select("a[href*='/detail'], .news-item, .search-result-item, article")[:max_results]):
                t = (a.select_one("h3, h4, .title, .news-title") or a).get_text(strip=True)
                link = a.get("href", "")
                snip = (a.select_one(".summary, .desc, .abstract, p") or a).get_text(strip=True) if a.select_one(".summary, .desc, .abstract, p") else ""
                if t:
                    full = link if link.startswith("http") else f"https://www.cls.cn{link}"
                    results.append(SearchResult(title=t, url=full, snippet=snip, source=self.name, rank=i+1, category="news", extra={"region":"cn"}))
            if not results:
                u = self.build_url(query)
                results.append(SearchResult(title=f"财联社: {query}", url=u, snippet=f"Search 财联社 for '{query}' (JS required)", source=self.name, rank=1, category="news", extra={"search_url":u, "note":"JS-rendered"}))
            return results
        except httpx.HTTPError as e:
            logger.error(f"财联社 search failed: {e}"); return []

    async def close(self):
        await self._client.aclose()
