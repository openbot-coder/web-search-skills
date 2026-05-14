"""
Unified search entry point.

Provides a single interface to search across all configured sources.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from scripts.core.base import SearchResult
from scripts.core.config_loader import (
    get_search_engines, get_news_sources, get_academic_sources,
    get_wechat_sources, get_api_engines, get_special_engines,
    get_social_sources, get_all_sources, get_engine,
)
from scripts.engines.url_engine import UrlSearchEngine
from scripts.engines.parser_engines import DuckDuckGoEngine
from scripts.news.cls import CLSNewsEngine
from scripts.news.wallstreetcn import WallStreetCNEngine
from scripts.news.rss import RSSNewsEngine
from scripts.academic.arxiv import ArXivEngine
from scripts.wechat.sogou_weixin import SogouWeChatEngine
from scripts.social.twitter import TwitterSearchEngine
from scripts.engines.baidu_qianfan import BaiduQianFanEngine

logger = logging.getLogger(__name__)

# Default timeout per engine (seconds)
_DEFAULT_ENGINE_TIMEOUT = 15
# Max concurrent engine calls
_DEFAULT_MAX_CONCURRENT = 5

SOURCE_CATEGORIES = {
    "web": get_search_engines,
    "news": get_news_sources,
    "academic": get_academic_sources,
    "wechat": get_wechat_sources,
    "social": get_social_sources,
    "api": get_api_engines,
    "special": get_special_engines,
}


class UnifiedSearch:
    """Unified search client that aggregates results from multiple sources."""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self._cache: dict[str, list[SearchResult]] = {}
        self._engines: dict[str, Any] = {}
        self._timeout = self.config.get("engine_timeout", _DEFAULT_ENGINE_TIMEOUT)
        self._semaphore = asyncio.Semaphore(
            self.config.get("max_concurrent", _DEFAULT_MAX_CONCURRENT)
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def search(
        self, query: str, sources: Optional[list[str]] = None,
        max_results: int = 10, force_refresh: bool = False, **kwargs,
    ) -> list[SearchResult]:
        """Search across selected sources and aggregate results."""
        if not sources or "all" in sources:
            sources = list(SOURCE_CATEGORIES.keys())

        cache_key = f"{sorted(sources) if isinstance(sources, list) else sources}:{query}"
        if not force_refresh and cache_key in self._cache:
            return self._cache[cache_key]

        tasks = []
        for source_spec in sources:
            if source_spec in SOURCE_CATEGORIES:
                for engine_def in SOURCE_CATEGORIES[source_spec]():
                    engine = self._get_engine(engine_def)
                    if engine:
                        tasks.append(self._safe_search(engine, query, max_results, **kwargs))
            else:
                engine_def = get_engine(source_spec)
                if engine_def:
                    engine = self._get_engine(engine_def)
                    if engine:
                        tasks.append(self._safe_search(engine, query, max_results, **kwargs))

        if not tasks:
            return []

        # Run all engines with semaphore-based concurrency control
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        all_results: list[SearchResult] = []
        for results in results_lists:
            if isinstance(results, Exception):
                logger.error(f"Search task failed: {results}")
                continue
            all_results.extend(results)

        # Dedup by URL, keep first occurrence
        all_results = self._dedup_results(all_results)

        self._cache[cache_key] = all_results
        return all_results

    def _dedup_results(self, results: list[SearchResult]) -> list[SearchResult]:
        """Remove duplicates by URL, keeping first occurrence."""
        seen: set[str] = set()
        deduped = []
        for r in results:
            key = r.url.strip().rstrip("/")
            if key and key not in seen:
                seen.add(key)
                deduped.append(r)
        return deduped

    async def _safe_search(self, engine, query, max_results, **kwargs):
        async with self._semaphore:
            try:
                return await asyncio.wait_for(
                    engine.search(query, max_results=max_results, **kwargs),
                    timeout=self._timeout,
                )
            except asyncio.TimeoutError:
                logger.warning(f"Engine {engine.name} timed out after {self._timeout}s")
                return []
            except Exception as e:
                logger.error(f"Engine {engine.name} failed: {e}")
                return []

    async def search_health(self) -> list[dict[str, Any]]:
        """Check health of all configured engines."""
        statuses = []
        seen_names = set()
        for cat_key, cat_fn in SOURCE_CATEGORIES.items():
            for engine_def in cat_fn():
                name = engine_def.get("name", "?")
                if name in seen_names:
                    continue
                seen_names.add(name)
                engine = self._get_engine(engine_def)
                if engine is None:
                    statuses.append({"name": name, "status": "error", "detail": "engine_init_failed"})
                    continue
                try:
                    async with self._semaphore:
                        await asyncio.wait_for(
                            engine.search("health check", max_results=1),
                            timeout=8,
                        )
                    statuses.append({"name": name, "status": "ok"})
                except asyncio.TimeoutError:
                    statuses.append({"name": name, "status": "timeout"})
                except Exception as e:
                    statuses.append({"name": name, "status": "error", "detail": str(e)[:80]})
        return statuses

    def _get_engine(self, engine_def: dict[str, Any]):
        """Get or create an engine instance by definition."""
        name = engine_def.get("name", "")
        engine_type = engine_def.get("type", "url")

        if name in self._engines:
            return self._engines[name]

        if name == "DuckDuckGo":
            engine = DuckDuckGoEngine(self.config)
        elif engine_type == "baidu_qianfan" or "baidu qianfan" in name.lower():
            engine = BaiduQianFanEngine(self.config)
        elif "cls" in name.lower():
            engine = CLSNewsEngine(self.config)
        elif "wallstreet" in name.lower() or "华尔街" in name:
            engine = WallStreetCNEngine(self.config)
        elif name == "ArXiv" or engine_type == "api":
            engine = ArXivEngine(self.config)
        elif "微信" in name or "wechat" in name.lower() or "weixin" in name.lower():
            engine = SogouWeChatEngine(self.config)
        elif "twitter" in name.lower():
            engine = TwitterSearchEngine(self.config)
        elif engine_type == "news" and name not in ("cls", "wallstreetcn"):
            engine = RSSNewsEngine(self.config)
        elif engine_type == "social":
            engine = TwitterSearchEngine(self.config) if "twitter" in name.lower() else UrlSearchEngine(name, engine_def)
        else:
            engine = UrlSearchEngine(name, engine_def)

        self._engines[name] = engine
        return engine

    async def search_engines(self, query, region=None, max_results=10):
        """Quick search across web search engines."""
        engines = get_search_engines()
        if region:
            engines = [e for e in engines if e.get("region") == region]
        return await self.search(query, sources=[e["name"] for e in engines], max_results=max_results)

    async def search_news(self, query, max_results=10, **kwargs):
        """Quick search news sources (CN news + RSS feeds)."""
        return await self.search(query, sources=["news"], max_results=max_results, **kwargs)

    async def search_academic(self, query, max_results=10, **kwargs):
        """Quick search academic papers."""
        return await self.search(query, sources=["academic"], max_results=max_results, **kwargs)

    async def search_wechat(self, query, max_results=10):
        """Quick search WeChat articles."""
        return await self.search(query, sources=["wechat"], max_results=max_results)

    async def search_social(self, query, max_results=10, **kwargs):
        """Quick search social media (Twitter/X)."""
        return await self.search(query, sources=["social"], max_results=max_results, **kwargs)

    async def search_rss(self, query="", max_results=10, **kwargs):
        """Quick search RSS news feeds."""
        engine = RSSNewsEngine(self.config)
        return await engine.search(query, max_results=max_results, **kwargs)

    async def get_search_urls(self, query, sources=None):
        """Get search URLs without executing searches."""
        if not sources:
            sources = [e["name"] for e in get_search_engines()]

        urls = {}
        for name in sources:
            engine_def = get_engine(name)
            if engine_def:
                urls[name] = UrlSearchEngine(name, engine_def).build_url(query)

        return urls

    async def get_twitter_search_url(self, query, search_type="top"):
        """Get Twitter/X search URL for browser/web_fetch usage."""
        engine = TwitterSearchEngine(self.config)
        return engine.build_url(query, search_type=search_type)

    async def close(self):
        """Close all engine resources."""
        for engine in self._engines.values():
            try:
                await engine.close()
            except Exception:
                pass
