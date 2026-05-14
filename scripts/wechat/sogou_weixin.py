"""
Sogou WeChat (搜狗微信) search engine.

Searches WeChat public account articles via weixin.sogou.com.

Anti-scraping strategy (inspired by Node.js wechat-article-search skill):
- Cookie pre-fetch from v.sogou.com to get SNUID
- User-Agent rotation with a pool of real browser UAs
- Random delays between requests (500-1500ms)
- Retry logic with exponential backoff
"""

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

# Real browser User-Agent pool for rotation
USER_AGENTS = [
    # Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]


class SogouWeChatEngine(SearchEngine):
    """搜狗微信搜索 - searches WeChat public account articles."""

    SEARCH_URL = "https://weixin.sogou.com/weixin"
    COOKIE_URL = "https://v.sogou.com"

    def __init__(self, config: Optional[dict] = None):
        super().__init__("weixin", config)
        timeout = (config or {}).get("timeout", 15)
        self._ua = random.choice(USER_AGENTS)
        self._cookies: dict[str, str] = {}
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers=self._build_headers(),
            follow_redirects=False,  # Don't auto-follow to detect anti-scraping
        )

    def _build_headers(self) -> dict[str, str]:
        return {
            "User-Agent": self._ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Referer": "https://weixin.sogou.com/",
            "DNT": "1",
            "Connection": "keep-alive",
        }

    def _random_delay(self):
        """Random delay between 500-1500ms to mimic human browsing."""
        delay = random.uniform(0.5, 1.5)
        return asyncio.sleep(delay)

    def _rotate_ua(self):
        """Rotate to a new random User-Agent."""
        self._ua = random.choice(USER_AGENTS)

    async def _get_cookie(self) -> dict[str, str]:
        """Pre-fetch cookie from v.sogou.com to get SNUID."""
        try:
            response = await self._client.get(
                self.COOKIE_URL,
                headers={
                    "User-Agent": self._ua,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                },
            )
            cookies = {}
            for cookie in response.cookies.jar:
                if isinstance(cookie, tuple):
                    # SimpleCookie format: (key, value)
                    cookies[cookie[0]] = cookie[1]
                else:
                    cookies[cookie.name] = cookie.value
            logger.debug(f"Got {len(cookies)} cookies from v.sogou.com")
            return cookies
        except Exception as e:
            logger.warning(f"Cookie pre-fetch failed: {e}")
            return {}

    def build_url(self, query: str, search_type: int = 2, page: int = 1, **kwargs) -> str:
        """
        Build Sogou WeChat search URL.

        Args:
            query: Search keyword.
            search_type: 2=articles, 1=accounts.
            page: Page number (starts at 1).
        """
        return (
            f"{self.SEARCH_URL}?query={quote_plus(query)}"
            f"&s_from=input&_sug_=n&type={search_type}"
            f"&page={page}&ie=utf8"
        )

    async def search(
        self, query: str, max_results: int = 10, **kwargs
    ) -> list[SearchResult]:
        """Search WeChat articles via Sogou and parse results."""
        # Step 1: Get cookie first
        if not self._cookies:
            self._cookies = await self._get_cookie()
            await self._random_delay()

        # Step 2: Search with retry
        max_pages = min(5, (max_results + 9) // 10)
        all_results = []

        for page in range(1, max_pages + 1):
            url = self.build_url(query, page=page, **kwargs)
            results = await self._search_page(url, query, max_results - len(all_results))
            all_results.extend(results)

            if len(all_results) >= max_results:
                break

            # Delay between pages
            await self._random_delay()

        if not all_results:
            # Fallback: try legacy wx.sogou.com
            return await self._legacy_search(query, max_results, **kwargs)

        return all_results[:max_results]

    async def _search_page(
        self, url: str, query: str, max_results: int
    ) -> list[SearchResult]:
        """Search a single page with retry logic."""
        for attempt in range(3):
            try:
                # Rotate UA on each retry
                if attempt > 0:
                    self._rotate_ua()
                    self._client.headers.update({"User-Agent": self._ua})
                    if self._cookies:
                        pass  # Keep existing cookies

                response = await self._client.get(
                    url,
                    cookies=self._cookies,
                    follow_redirects=False,
                )

                # Check for anti-scraping page
                if response.status_code == 302:
                    # Got redirected - likely hit anti-scraping
                    logger.warning(f"Sogou anti-scraping triggered (302), attempt {attempt + 1}")
                    # Try to get new cookie
                    self._cookies = await self._get_cookie()
                    await self._random_delay()
                    continue

                if response.status_code != 200:
                    logger.warning(f"Sogou returned {response.status_code}, attempt {attempt + 1}")
                    await self._random_delay()
                    continue

                html = response.text

                # Check for captcha/block page
                if "请输入验证码" in html or "访问频率过高" in html:
                    logger.warning(f"Sogou captcha triggered, attempt {attempt + 1}")
                    await asyncio.sleep(random.uniform(2, 4))
                    self._cookies = await self._get_cookie()
                    continue

                return self._parse_results(html, query, max_results)

            except (httpx.HTTPError, httpx.TimeoutException) as e:
                logger.warning(f"Sogou search attempt {attempt + 1} failed: {e}")
                await self._random_delay()
                continue

        return []

    async def _legacy_search(
        self, query: str, max_results: int, **kwargs
    ) -> list[SearchResult]:
        """Fallback: try the legacy wx.sogou.com domain."""
        legacy_url = f"https://wx.sogou.com/weixin?type=2&query={quote_plus(query)}"
        try:
            response = await self._client.get(
                legacy_url,
                cookies=self._cookies,
                follow_redirects=True,
            )
            if response.status_code == 200:
                return self._parse_results(response.text, query, max_results)
        except Exception:
            pass

        # Ultimate fallback
        search_url = self.build_url(query)
        return [
            SearchResult(
                title=f"微信搜索: {query}",
                url=search_url,
                snippet=f"Search WeChat for '{query}' via Sogou",
                source=self.name,
                rank=1,
                category="wechat",
                extra={"search_url": search_url},
            )
        ]

    def _parse_results(
        self, html: str, query: str, max_results: int
    ) -> list[SearchResult]:
        """Parse Sogou WeChat search results."""
        soup = BeautifulSoup(html, "lxml")
        results = []

        # Main selector: ul.news-list > li (standard Sogou WeChat structure)
        items = soup.select("ul.news-list > li")

        if not items:
            # Fallback selectors
            items = soup.select(
                ".news-list2 li, .wx-rb-item, .results .result, "
                ".item, .news-box .news-list li"
            )

        for i, item in enumerate(items[:max_results]):
            title_el = item.select_one("h3 a")
            if not title_el:
                title_el = item.select_one(".tit a, .title a, h3")

            snippet_el = item.select_one("p.txt-info, .txt-info, .summary, .des, p.info")
            source_el = item.select_one(
                ".all-time-y2 a.account, a.account, "
                ".account, .source, .s-p, .from"
            )

            title = title_el.get_text(strip=True) if title_el else ""
            link = title_el.get("href", "") if title_el and hasattr(title_el, "get") else ""
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            account = source_el.get_text(strip=True) if source_el else ""

            # Parse time from inline scripts or text
            time_text = self._parse_time(item)

            if not title:
                continue

            # Make sure URL is absolute
            if link and not link.startswith("http"):
                link = f"https://weixin.sogou.com{link}"

            results.append(
                SearchResult(
                    title=title,
                    url=link,
                    snippet=snippet or f"WeChat article from {account or 'unknown'}",
                    source=self.name,
                    rank=(i + 1),
                    category="wechat",
                    extra={
                        "account": account,
                        "time": time_text,
                        "search_url": self.build_url(query),
                    },
                )
            )

        return results

    def _parse_time(self, item) -> str:
        """Extract publish time from search result item."""
        # Try script tag with Unix timestamp (Sogou encodes dates in scripts)
        for script in item.select("script"):
            text = script.string or ""
            # Look for Unix timestamp pattern
            match = re.search(r'\d{10}', text)
            if match:
                import datetime
                ts = int(match.group())
                try:
                    dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone(datetime.timedelta(hours=8)))
                    return dt.strftime("%Y-%m-%d %H:%M")
                except (OSError, ValueError):
                    pass

        # Try inline text with relative time like "2小时前", "3天前"
        time_text = item.get_text()
        relative_match = re.search(r'(\d+)\s*(小时|分钟|天|周|月)前', time_text)
        if relative_match:
            return f"{relative_match.group(1)}{relative_match.group(2)}前"

        # Try standard date patterns
        date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', time_text)
        if date_match:
            return date_match.group(1)

        return ""

    async def close(self):
        await self._client.aclose()
