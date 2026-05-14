"""Unified search entry point."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from scripts.core.base import SearchResult
from scripts.core.config_loader import (
    get_search_engines, get_news_sources, get_academic_sources,
    get_wechat_sources, get_special_engines, get_social_sources,
    get_engine,
)
from scripts.engines.url_engine import UrlSearchEngine
from scripts.engines.parser_engines import DuckDuckGoEngine
from scripts.news.cls import CLSNewsEngine
from scripts.news.wallstreetcn import WallStreetCNEngine
from scripts.news.rss import RSSNewsEngine
from scripts.academic.arxiv import ArXivEngine
from scripts.wechat.sogou_weixin import SogouWeChatEngine
from scripts.social.twitter import TwitterSearchEngine

logger = logging.getLogger(__name__)

SOURCE_CATEGORIES = {
    "web": get_search_engines,
    "news": get_news_sources,
    "academic": get_academic_sources,
    "wechat": get_wechat_sources,
    "social": get_social_sources,
    "special": get_special_engines,
}


class UnifiedSearch:
    """Unified search client."""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self._cache: dict[str, list[SearchResult]] = {}
        self._engines: dict[str, Any] = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def search(self, query: str, sources=None, max_results=10, force_refresh=False, **kwargs) -> list[SearchResult]:
        if not sources or "all" in sources:
            sources = list(SOURCE_CATEGORIES.keys())
        cache_key = f"{sorted(sources) if isinstance(sources, list) else sources}:{query}"
        if not force_refresh and cache_key in self._cache:
            return self._cache[cache_key]
        tasks = []
        for spec in sources:
            if spec in SOURCE_CATEGORIES:
                for ed in SOURCE_CATEGORIES[spec]():
                    eng = self._get_engine(ed)
                    if eng:
                        tasks.append(self._safe_search(eng, query, max_results, **kwargs))
            else:
                ed = get_engine(spec)
                if ed:
                    eng = self._get_engine(ed)
                    if eng:
                        tasks.append(self._safe_search(eng, query, max_results, **kwargs))
        if not tasks:
            return []
        lists = await asyncio.gather(*tasks, return_exceptions=True)
        all_r = []
        for r in lists:
            if isinstance(r, Exception):
                continue
            all_r.extend(r)
        self._cache[cache_key] = all_r
        return all_r

    def _get_engine(self, ed: dict):
        name = ed.get("name", "")
        t = ed.get("type", "url")
        if name in self._engines:
            return self._engines[name]
        if name == "DuckDuckGo":
            eng = DuckDuckGoEngine(self.config)
        elif "cls" in name.lower():
            eng = CLSNewsEngine(self.config)
        elif "wallstreet" in name.lower() or "华尔街" in name:
            eng = WallStreetCNEngine(self.config)
        elif name == "ArXiv" or t == "api":
            eng = ArXivEngine(self.config)
        elif "微信" in name or "wechat" in name.lower() or "weixin" in name.lower():
            eng = SogouWeChatEngine(self.config)
        elif "twitter" in name.lower():
            eng = TwitterSearchEngine(self.config)
        elif t in ("news",) and name not in ("cls", "wallstreetcn"):
            eng = RSSNewsEngine(self.config)
        else:
            eng = UrlSearchEngine(name, ed)
        self._engines[name] = eng
        return eng

    async def _safe_search(self, eng, query, max_results, **kwargs):
        try:
            return await eng.search(query, max_results=max_results, **kwargs)
        except Exception as e:
            logger.error(f"{eng.name} failed: {e}")
            return []

    async def search_engines(self, query, region=None, max_results=10):
        es = get_search_engines()
        if region:
            es = [e for e in es if e.get("region") == region]
        return await self.search(query, sources=[e["name"] for e in es], max_results=max_results)

    async def search_news(self, query, max_results=10, **kwargs):
        return await self.search(query, sources=["news"], max_results=max_results, **kwargs)

    async def search_academic(self, query, max_results=10, **kwargs):
        return await self.search(query, sources=["academic"], max_results=max_results, **kwargs)

    async def search_wechat(self, query, max_results=10):
        return await self.search(query, sources=["wechat"], max_results=max_results)

    async def search_social(self, query, max_results=10, **kwargs):
        return await self.search(query, sources=["social"], max_results=max_results, **kwargs)

    async def search_rss(self, query="", max_results=10, **kwargs):
        eng = RSSNewsEngine(self.config)
        return await eng.search(query, max_results=max_results, **kwargs)

    async def get_search_urls(self, query, sources=None):
        if not sources:
            sources = [e["name"] for e in get_search_engines()]
        urls = {}
        for name in sources:
            ed = get_engine(name)
            if ed:
                urls[name] = UrlSearchEngine(name, ed).build_url(query)
        return urls

    async def get_twitter_search_url(self, query, search_type="top"):
        return TwitterSearchEngine(self.config).build_url(query, search_type=search_type)

    async def close(self):
        for eng in self._engines.values():
            try:
                await eng.close()
            except Exception:
                pass
