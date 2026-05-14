"""
Generic URL-based search engine. Generates search URLs from config definitions.
Inspired by the multi-search-engine skill's URL-based approach.
"""

from __future__ import annotations

from typing import Any, Optional
from urllib.parse import quote_plus

from scripts.core.base import SearchEngine, SearchResult


class UrlSearchEngine(SearchEngine):
    """Generic search engine that generates search URLs from config."""

    def __init__(self, name: str, engine_def: Optional[dict[str, Any]] = None, **kwargs):
        super().__init__(name)
        self.engine_def = engine_def or {}
        self.base_url = self.engine_def.get("url", "")
        self.region = self.engine_def.get("region", "global")

    def build_url(self, query: str, **kwargs) -> str:
        encoded_query = quote_plus(query)
        url = self.base_url.replace("{keyword}", encoded_query)
        if kwargs:
            from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
            parsed = urlparse(url)
            params = parse_qs(parsed.query, keep_blank_values=True)
            for k, v in kwargs.items():
                params[k] = [str(v)]
            url = urlunparse(parsed._replace(query=urlencode(params, doseq=True)))
        return url

    async def search(self, query: str, max_results: int = 10, **kwargs) -> list[SearchResult]:
        url = self.build_url(query, **kwargs)
        return [
            SearchResult(
                title=f"{self.name}: {query}",
                url=url,
                snippet=f"Search via {self.name}",
                source=self.name,
                rank=1,
                category=self._infer_category(),
            )
        ]

    def _infer_category(self) -> str:
        type_map = {"url": "web", "news": "news", "api": "academic"}
        return type_map.get(self.engine_def.get("type", "url"), "web")

    async def close(self):
        pass
