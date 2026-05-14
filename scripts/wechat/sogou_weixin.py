"""微信公众号文章搜索 (via 搜狗微信搜索)."""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from scripts.core.base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)


class SogouWeChatEngine(SearchEngine):
    """搜狗微信搜索 - WeChat public account article search."""

    SEARCH_URL = "https://wx.sogou.com/weixin"

    def __init__(self, config: Optional[dict] = None):
        super().__init__("微信公众号", config)
        timeout = (config or {}).get("timeout", 15)
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://wx.sogou.com/",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
            follow_redirects=True,
        )

    def build_url(self, query: str, **kwargs) -> str:
        return f"{self.SEARCH_URL}?type=2&query={quote_plus(query)}"

    async def search(self, query: str, max_results: int = 10, **kwargs) -> list[SearchResult]:
        try:
            url = self.build_url(query)
            response = await self._client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            results = []
            articles = soup.select(".news-list2 li, .wx-rb, .results .wx-rb")
            for i, article in enumerate(articles[:max_results]):
                link_el = article.select_one("a[href*='mp.weixin.qq.com'], h3 a, .tit a")
                if not link_el:
                    continue
                title = link_el.get_text(strip=True)
                href = link_el.get("href", "")
                account_el = article.select_one(".account, .source, .s-p")
                account = account_el.get_text(strip=True) if account_el else ""
                summary_el = article.select_one(".summary, .txt-info, p, .des")
                snippet = summary_el.get_text(strip=True) if summary_el else ""
                results.append(SearchResult(title=title[:200], url=href, snippet=snippet[:300], source="微信公众号", rank=i + 1, category="wechat", extra={"account": account} if account else {}))
            if not results:
                results.append(SearchResult(title=f"微信公众号: {query}", url=url, snippet="Search WeChat articles", source="微信公众号", rank=1, category="wechat"))
            return results
        except httpx.HTTPError as e:
            logger.error(f"搜狗微信 search failed: {e}")
            return [SearchResult(title=f"微信公众号: {query}", url=self.build_url(query), snippet=f"Connection issue. Note: 搜狗微信 may require browser cookies.", source="微信公众号", rank=1, category="wechat")]

    async def close(self):
        await self._client.aclose()
