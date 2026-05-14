"""
Tech & social news aggregation engines.

Implements non-Playwright news sources inspired by news-aggregator-skill:
- Hacker News (via Algolia API)
- GitHub Trending (HTML scrape)
- 36氪 (HTML scrape)
- 微博热搜 (Ajax API)
- V2EX (Public API)
- 腾讯新闻 (API)
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from scripts.core.base import SearchEngine, SearchResult
from scripts.core.thread_utils import run_in_thread

logger = logging.getLogger(__name__)

# Shared HTTP client settings
_DEFAULT_TIMEOUT = 15
_COMMON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


# ---------------------------------------------------------------------------
# Hacker News (via Algolia API)
# ---------------------------------------------------------------------------

class HackerNewsEngine(SearchEngine):
    """Hacker News search via Algolia public API."""

    SEARCH_URL = "https://hn.algolia.com/api/v1/search"

    def __init__(self, config: Optional[dict] = None):
        super().__init__("Hacker News", config)
        self._client = httpx.AsyncClient(
            timeout=_DEFAULT_TIMEOUT,
            headers={"User-Agent": _COMMON_HEADERS["User-Agent"]},
            follow_redirects=True,
        )

    async def search(self, query: str, max_results: int = 10, **kwargs) -> list[SearchResult]:
        try:
            params = {
                "query": query,
                "hitsPerPage": max_results,
                "tags": "story",
            }
            response = await self._client.get(self.SEARCH_URL, params=params)
            response.raise_for_status()
            data = response.json()
            return self._parse_results(data, max_results)
        except Exception as e:
            logger.error(f"Hacker News search failed: {e}")
            return []

    def _parse_results(self, data: dict, max_results: int) -> list[SearchResult]:
        results = []
        hits = data.get("hits", [])[:max_results]
        for i, hit in enumerate(hits):
            title = hit.get("title", "")
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
            snippet = hit.get("story_text", "") or ""
            # Clean HTML from snippet
            snippet = re.sub(r"<[^>]+>", "", snippet)[:200]
            points = hit.get("points", 0)
            author = hit.get("author", "")
            created_at = hit.get("created_at", "")

            results.append(SearchResult(
                title=title,
                url=url,
                snippet=snippet or f"[{points} points] by {author}",
                source=self.name,
                rank=i + 1,
                category="news",
                extra={
                    "points": points,
                    "author": author,
                    "time": created_at,
                    "heat": f"{points} points",
                },
            ))
        return results

    async def close(self):
        await self._client.aclose()


# ---------------------------------------------------------------------------
# GitHub Trending
# ---------------------------------------------------------------------------

class GitHubTrendingEngine(SearchEngine):
    """GitHub Trending repositories."""

    TRENDING_URL = "https://github.com/trending"

    def __init__(self, config: Optional[dict] = None):
        super().__init__("GitHub Trending", config)
        self._client = httpx.AsyncClient(
            timeout=_DEFAULT_TIMEOUT,
            headers=_COMMON_HEADERS,
            follow_redirects=True,
        )

    async def search(self, query: str = "", max_results: int = 10, **kwargs) -> list[SearchResult]:
        """GitHub Trending doesn't support keyword search; returns top trending repos."""
        url = self.TRENDING_URL
        if query:
            url += f"?spoken_language_code=&q={quote_plus(query)}"
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            return await run_in_thread(self._parse_html, response.text, max_results)
        except Exception as e:
            logger.error(f"GitHub Trending failed: {e}")
            return []

    def _parse_html(self, html: str, max_results: int) -> list[SearchResult]:
        soup = BeautifulSoup(html, "lxml")
        results = []
        articles = soup.select("article.Box-row")[:max_results]
        for i, article in enumerate(articles):
            h2 = article.select_one("h2")
            if not h2:
                continue
            repo_path = h2.get_text(strip=True).replace(" ", "")
            repo_url = f"https://github.com/{repo_path}"

            desc_el = article.select_one("p")
            description = desc_el.get_text(strip=True) if desc_el else ""

            # Language
            lang_el = article.select_one("[itemprop='programmingLanguage']")
            language = lang_el.get_text(strip=True) if lang_el else ""

            # Stars today
            stars_el = article.select_one(".float-sm-right")
            stars_today = stars_el.get_text(strip=True) if stars_el else ""

            results.append(SearchResult(
                title=repo_path,
                url=repo_url,
                snippet=description[:200] if description else language,
                source=self.name,
                rank=i + 1,
                category="news",
                extra={
                    "language": language,
                    "heat": stars_today,
                    "time": "",
                },
            ))
        return results

    async def close(self):
        await self._client.aclose()


# ---------------------------------------------------------------------------
# 36氪 (36kr.com)
# ---------------------------------------------------------------------------

class Kr36Engine(SearchEngine):
    """36氪 tech news search."""

    SEARCH_URL = "https://36kr.com/search/articles/{keyword}"

    def __init__(self, config: Optional[dict] = None):
        super().__init__("36氪", config)
        self._client = httpx.AsyncClient(
            timeout=_DEFAULT_TIMEOUT,
            headers={**_COMMON_HEADERS, "Referer": "https://36kr.com/"},
            follow_redirects=True,
        )

    async def search(self, query: str, max_results: int = 10, **kwargs) -> list[SearchResult]:
        url = self.SEARCH_URL.format(keyword=quote_plus(query))
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            return await run_in_thread(self._parse_html, response.text, query, max_results)
        except Exception as e:
            logger.error(f"36氪 search failed: {e}")
            return []

    def _parse_html(self, html: str, query: str, max_results: int) -> list[SearchResult]:
        soup = BeautifulSoup(html, "lxml")
        results = []

        # Look for article cards
        for i, item in enumerate(soup.select("a[href*='/p/'], .article-item, .search-result-item, [class*='article']")[:max_results]):
            title_el = item.select_one("h3, h4, .title, [class*='title']")
            link = item.get("href", "")
            snippet_el = item.select_one(".abstract, .summary, .desc, p, [class*='desc']")

            title = title_el.get_text(strip=True) if title_el else ""
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""

            if not title and not link:
                continue

            full_url = link if link.startswith("http") else f"https://36kr.com{link}"

            results.append(SearchResult(
                title=title or f"36氪: {query}",
                url=full_url,
                snippet=snippet[:200] if snippet else "",
                source=self.name,
                rank=i + 1,
                category="news",
                extra={"region": "cn"},
            ))

        if not results:
            search_url = f"https://36kr.com/search/articles/{quote_plus(query)}"
            results.append(SearchResult(
                title=f"36氪: {query}",
                url=search_url,
                snippet="Search 36氪 (site may require JS)",
                source=self.name,
                rank=1,
                category="news",
                extra={"search_url": search_url, "note": "JS-rendered page"},
            ))

        return results

    async def close(self):
        await self._client.aclose()


# ---------------------------------------------------------------------------
# 微博热搜 (Weibo Trending)
# ---------------------------------------------------------------------------

class WeiboEngine(SearchEngine):
    """微博热搜 trending topics."""

    HOT_URL = "https://weibo.com/ajax/side/hotSearch"

    def __init__(self, config: Optional[dict] = None):
        super().__init__("微博热搜", config)
        self._client = httpx.AsyncClient(
            timeout=_DEFAULT_TIMEOUT,
            headers={**_COMMON_HEADERS, "Referer": "https://weibo.com/"},
            follow_redirects=True,
        )

    async def search(self, query: str = "", max_results: int = 10, **kwargs) -> list[SearchResult]:
        try:
            response = await self._client.get(self.HOT_URL)
            response.raise_for_status()
            data = response.json()
            return self._parse_results(data, query, max_results)
        except Exception as e:
            logger.error(f"微博热搜 failed: {e}")
            return []

    def _parse_results(self, data: dict, query: str, max_results: int) -> list[SearchResult]:
        results = []
        realtime = data.get("data", {}).get("realtime", [])[:max_results]
        for i, item in enumerate(realtime):
            word = item.get("word", "")
            raw_hot = item.get("raw_hot", 0)
            url = f"https://s.weibo.com/weibo?q={quote_plus(word)}"

            # Filter by keyword if query provided
            if query and query.lower() not in word.lower():
                continue

            results.append(SearchResult(
                title=f"#{word}#",
                url=url,
                snippet=f"热度: {raw_hot:,}" if raw_hot else "",
                source=self.name,
                rank=i + 1,
                category="news",
                extra={
                    "heat": f"{raw_hot:,}" if raw_hot else "",
                    "region": "cn",
                },
            ))

        return results

    async def close(self):
        await self._client.aclose()


# ---------------------------------------------------------------------------
# V2EX (via public API)
# ---------------------------------------------------------------------------

class V2EXEngine(SearchEngine):
    """V2EX tech community hot topics."""

    HOT_API = "https://www.v2ex.com/api/v2/topics/hot"
    # Fallback to older API if v2 needs auth
    HOT_API_FALLBACK = "https://www.v2ex.com/api/topics/hot.json"

    def __init__(self, config: Optional[dict] = None):
        super().__init__("V2EX", config)
        self._client = httpx.AsyncClient(
            timeout=_DEFAULT_TIMEOUT,
            headers=_COMMON_HEADERS,
            follow_redirects=True,
        )

    async def search(self, query: str = "", max_results: int = 10, **kwargs) -> list[SearchResult]:
        # Try v2 API first, fallback to old API
        for api_url in [self.HOT_API, self.HOT_API_FALLBACK]:
            try:
                response = await self._client.get(api_url)
                if response.status_code == 200:
                    data = response.json()
                    # v2 API returns list directly; old API also returns list
                    topics = data if isinstance(data, list) else data.get("data", [])
                    return self._parse_results(topics, query, max_results)
            except Exception:
                continue
        logger.error("V2EX API failed (both v2 and fallback)")
        return []

    def _parse_results(self, topics: list, query: str, max_results: int) -> list[SearchResult]:
        results = []
        for i, topic in enumerate(topics[:max_results]):
            title = topic.get("title", "")
            node_name = ""
            if "node" in topic and isinstance(topic["node"], dict):
                node_name = topic["node"].get("title", "")
            topic_id = topic.get("id", "")
            url = f"https://www.v2ex.com/t/{topic_id}"
            replies = topic.get("replies", 0)
            created = topic.get("created", "")
            member = ""
            if "member" in topic and isinstance(topic["member"], dict):
                member = topic["member"].get("username", "")

            # Filter by keyword
            if query and query.lower() not in title.lower():
                continue

            # Format time
            time_str = ""
            if created:
                try:
                    dt = datetime.fromtimestamp(int(created), tz=timezone.utc)
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                except (ValueError, OSError):
                    time_str = str(created)

            results.append(SearchResult(
                title=title,
                url=url,
                snippet=f"[{node_name}] by {member}" if node_name and member else f"by {member}" if member else "",
                source=self.name,
                rank=i + 1,
                category="news",
                extra={
                    "heat": f"{replies} replies",
                    "author": member,
                    "time": time_str,
                    "region": "cn",
                },
            ))

        return results

    async def close(self):
        await self._client.aclose()


# ---------------------------------------------------------------------------
# 腾讯新闻 (news.qq.com)
# ---------------------------------------------------------------------------

class TencentNewsEngine(SearchEngine):
    """腾讯新闻 search."""

    SEARCH_URL = "https://news.qq.com/search"

    def __init__(self, config: Optional[dict] = None):
        super().__init__("腾讯新闻", config)
        self._client = httpx.AsyncClient(
            timeout=_DEFAULT_TIMEOUT,
            headers={**_COMMON_HEADERS, "Referer": "https://news.qq.com/"},
            follow_redirects=True,
        )

    async def search(self, query: str, max_results: int = 10, **kwargs) -> list[SearchResult]:
        url = f"{self.SEARCH_URL}?q={quote_plus(query)}"
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            return await run_in_thread(self._parse_html, response.text, query, max_results)
        except Exception as e:
            logger.error(f"腾讯新闻 search failed: {e}")
            return []

    def _parse_html(self, html: str, query: str, max_results: int) -> list[SearchResult]:
        soup = BeautifulSoup(html, "lxml")
        results = []

        for i, item in enumerate(soup.select("a[href*='news.qq.com'], .list-item, [class*='result'], article")[:max_results]):
            title_el = item.select_one("h3, h4, .title, a")
            link = item.get("href", "") or (title_el.get("href", "") if title_el else "")
            snippet_el = item.select_one(".summary, .desc, .abstract, p, .text")

            title = title_el.get_text(strip=True) if title_el else ""
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""

            if not title:
                continue

            full_url = link if link.startswith("http") else f"https:{link}" if link.startswith("//") else link

            results.append(SearchResult(
                title=title,
                url=full_url,
                snippet=snippet[:200] if snippet else "",
                source=self.name,
                rank=i + 1,
                category="news",
                extra={"region": "cn"},
            ))

        if not results:
            search_url = f"{self.SEARCH_URL}?q={quote_plus(query)}"
            results.append(SearchResult(
                title=f"腾讯新闻: {query}",
                url=search_url,
                snippet=f"Search Tencent News for '{query}'",
                source=self.name,
                rank=1,
                category="news",
                extra={"search_url": search_url, "note": "JS-rendered page"},
            ))

        return results

    async def close(self):
        await self._client.aclose()
