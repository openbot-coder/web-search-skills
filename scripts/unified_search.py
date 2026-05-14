"""Unified search entry point."""
from __future__ import annotations
import asyncio
import logging
from typing import Any, Optional
from scripts.core.base import SearchResult
from scripts.core.config_loader import get_search_engines, get_news_sources, get_academic_sources, get_wechat_sources, get_special_engines, get_social_sources, get_all_sources, get_engine
from scripts.engines.url_engine import UrlSearchEngine
from scripts.engines.parser_engines import DuckDuckGoEngine
from scripts.news.cls import CLSNewsEngine
from scripts.news.wallstreetcn import WallStreetCNEngine
from scripts.news.rss import RSSNewsEngine
from scripts.academic.arxiv import ArXivEngine
from scripts.wechat.sogou_weixin import SogouWeChatEngine
from scripts.social.twitter import TwitterSearchEngine

logger = logging.getLogger(__name__)
SOURCE_CATEGORIES = {"web": get_search_engines, "news": get_news_sources, "academic": get_academic_sources, "wechat": get_wechat_sources, "social": get_social_sources, "special": get_special_engines}

class UnifiedSearch:
    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self._cache: dict[str, list[SearchResult]] = {}
        self._engines: dict[str, Any] = {}

    async def __aenter__(self): return self
    async def __aexit__(self, *args): await self.close()

    async def search(self, query: str, sources: Optional[list[str]] = None, max_results: int = 10, force_refresh: bool = False, **kwargs) -> list[SearchResult]:
        if not sources or "all" in sources: sources = list(SOURCE_CATEGORIES.keys())
        tasks = []
        for spec in sources:
            if spec in SOURCE_CATEGORIES:
                for ed in SOURCE_CATEGORIES[spec]():
                    e = self._get_engine(ed)
                    if e: tasks.append(self._safe_search(e, query, max_results, **kwargs))
            else:
                ed = get_engine(spec)
                if ed:
                    e = self._get_engine(ed)
                    if e: tasks.append(self._safe_search(e, query, max_results, **kwargs))
        if not tasks: return []
        lists = await asyncio.gather(*tasks, return_exceptions=True)
        all_results = []
        for r in lists:
            if isinstance(r, Exception):
                logger.error(f"Search failed: {r}"); continue
            all_results.extend(r)
        return all_results

    def _get_engine(self, ed: dict):
        name = ed.get("name", "")
        if name in self._engines: return self._engines[name]
        if name == "DuckDuckGo": e = DuckDuckGoEngine(self.config)
        elif "cls" in name.lower(): e = CLSNewsEngine(self.config)
        elif "wallstreet" in name.lower() or "华尔街" in name: e = WallStreetCNEngine(self.config)
        elif name == "ArXiv" or ed.get("type") == "api": e = ArXivEngine(self.config)
        elif "微信" in name or "wechat" in name.lower() or "weixin" in name.lower(): e = SogouWeChatEngine(self.config)
        elif "twitter" in name.lower(): e = TwitterSearchEngine(self.config)
        elif ed.get("type") == "news" and name not in ("cls","wallstreetcn"): e = RSSNewsEngine(self.config)
        else: e = UrlSearchEngine(name, ed)
        self._engines[name] = e; return e

    async def _safe_search(self, engine, query, max_results, **kw):
        try: return await engine.search(query, max_results=max_results, **kw)
        except Exception as e:
            logger.error(f"Engine {engine.name} failed: {e}")
            return []

    async def search_engines(self, query, region=None, max_results=10):
        engines = get_search_engines()
        if region: engines = [e for e in engines if e.get("region") == region]
        return await self.search(query, sources=[e["name"] for e in engines], max_results=max_results)

    async def search_news(self, query, max_results=10, **kw):
        return await self.search(query, sources=["news"], max_results=max_results, **kw)

    async def search_academic(self, query, max_results=10, **kw):
        return await self.search(query, sources=["academic"], max_results=max_results, **kw)

    async def search_wechat(self, query, max_results=10):
        return await self.search(query, sources=["wechat"], max_results=max_results)

    async def search_social(self, query, max_results=10, **kw):
        return await self.search(query, sources=["social"], max_results=max_results, **kw)

    async def search_rss(self, query="", max_results=10, **kw):
        e = RSSNewsEngine(self.config)
        return await e.search(query, max_results=max_results, **kw)

    async def get_search_urls(self, query, sources=None):
        if not sources: sources = [e["name"] for e in get_search_engines()]
        return {name: UrlSearchEngine(name, get_engine(name)).build_url(query) for name in sources if get_engine(name)}

    async def close(self):
        for e in self._engines.values():
            try: await e.close()
            except Exception: pass
