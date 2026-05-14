"""Generic URL-based search engine."""
from __future__ import annotations
import logging
from typing import Any, Optional
from urllib.parse import quote_plus
from scripts.core.base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)

class UrlSearchEngine(SearchEngine):
    def __init__(self, name: str, engine_def: dict[str, Any]):
        super().__init__(name, engine_def.get("config", {}))
        self.url_template = engine_def.get("url", "")
        self.region = engine_def.get("region", "global")

    def build_url(self, query: str, **kwargs) -> str:
        if not self.url_template:
            return ""
        encoded = quote_plus(query)
        return self.url_template.replace("{keyword}", encoded)

    async def search(self, query: str, max_results: int = 10, **kwargs) -> list[SearchResult]:
        url = self.build_url(query, **kwargs)
        if not url:
            return []
        return [SearchResult(
            title=f"{self.name}: {query}",
            url=url,
            snippet=f"Search {self.name} for '{query}'",
            source=self.name,
            rank=1,
            category="web",
            extra={"url": url, "region": self.region},
        )]

    async def close(self):
        pass
