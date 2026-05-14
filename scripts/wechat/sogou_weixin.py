"""Sogou WeChat (搜狗微信) search engine."""
from __future__ import annotations
import asyncio
import logging
import random
import re
from typing import Optional
from urllib.parse import quote_plus
import httpx
from bs4 import BeautifulSoup
from scripts.core.base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
]

class SogouWeChatEngine(SearchEngine):
    SEARCH_URL = "https://weixin.sogou.com/weixin"
    COOKIE_URL = "https://v.sogou.com"

    def __init__(self, config: Optional[dict] = None):
        super().__init__("weixin", config)
        timeout = (config or {}).get("timeout", 15)
        self._ua = random.choice(USER_AGENTS)
        self._cookies: dict[str, str] = {}
        self._client = httpx.AsyncClient(timeout=timeout, headers={"User-Agent": self._ua, "Accept": "text/html", "Accept-Language": "zh-CN,zh;q=0.9", "Referer": "https://weixin.sogou.com/"}, follow_redirects=False)

    def build_url(self, query: str, search_type: int = 2, page: int = 1, **kwargs) -> str:
        return f"{self.SEARCH_URL}?query={quote_plus(query)}&s_from=input&_sug_=n&type={search_type}&page={page}&ie=utf8"

    async def _get_cookie(self) -> dict:
        try:
            r = await self._client.get(self.COOKIE_URL, headers={"User-Agent": self._ua})
            cookies = {}
            for c in r.cookies.jar:
                if isinstance(c, tuple): cookies[c[0]] = c[1]
                else: cookies[c.name] = c.value
            return cookies
        except Exception:
            return {}

    async def search(self, query: str, max_results: int = 10, **kwargs) -> list[SearchResult]:
        if not self._cookies:
            self._cookies = await self._get_cookie()
            await asyncio.sleep(random.uniform(0.5, 1.5))
        all_results = []
        for page in range(1, min(5, (max_results+9)//10) + 1):
            url = self.build_url(query, page=page, **kwargs)
            for attempt in range(3):
                try:
                    if attempt > 0:
                        self._ua = random.choice(USER_AGENTS)
                        self._client.headers.update({"User-Agent": self._ua})
                    r = await self._client.get(url, cookies=self._cookies, follow_redirects=False)
                    if r.status_code == 302:
                        self._cookies = await self._get_cookie()
                        await asyncio.sleep(random.uniform(1,2))
                        continue
                    if r.status_code != 200:
                        await asyncio.sleep(random.uniform(0.5,1.5))
                        continue
                    html = r.text
                    if "请输入验证码" in html or "访问频率过高" in html:
                        await asyncio.sleep(random.uniform(2,4))
                        self._cookies = await self._get_cookie()
                        continue
                    soup = BeautifulSoup(html, "lxml")
                    items = soup.select("ul.news-list > li") or soup.select(".news-list2 li, .wx-rb-item, .results .result, .item")
                    for i, item in enumerate(items[:max_results]):
                        te = item.select_one("h3 a") or item.select_one(".tit a, .title a, h3")
                        if not te: continue
                        title = te.get_text(strip=True)
                        link = te.get("href", "") if hasattr(te, "get") else ""
                        if link and not link.startswith("http"): link = f"https://weixin.sogou.com{link}"
                        se = item.select_one(".all-time-y2 a.account, a.account, .account, .source")
                        account = se.get_text(strip=True) if se else ""
                        snip = (item.select_one("p.txt-info, .txt-info, .summary") or item).get_text(strip=True)[:200]
                        all_results.append(SearchResult(title=title, url=link, snippet=snip, source=self.name, rank=len(all_results)+1, category="wechat", extra={"account": account, "time": "", "search_url": self.build_url(query)}))
                    break
                except httpx.HTTPError:
                    await asyncio.sleep(random.uniform(0.5,1.5))
                    continue
            if len(all_results) >= max_results:
                break
            await asyncio.sleep(random.uniform(0.5, 1.5))
        if not all_results:
            u = self.build_url(query)
            all_results.append(SearchResult(title=f"微信搜索: {query}", url=u, snippet=f"Search WeChat for '{query}'", source=self.name, rank=1, category="wechat", extra={"search_url": u}))
        return all_results[:max_results]

    async def close(self):
        await self._client.aclose()
