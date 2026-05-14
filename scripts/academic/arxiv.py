"""ArXiv academic paper search engine."""
from __future__ import annotations
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote_plus
import httpx
from scripts.core.base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)

class ArXivEngine(SearchEngine):
    API_URL = "https://export.arxiv.org/api/query"

    def __init__(self, config: Optional[dict] = None):
        super().__init__("ArXiv", config)
        timeout = (config or {}).get("timeout", 30)
        self._client = httpx.AsyncClient(timeout=timeout, headers={"User-Agent": (config or {}).get("user_agent", "ArXivSearchSkill/1.0"), "Accept": "application/atom+xml"}, follow_redirects=True)

    def build_url(self, query: str, max_results: int = 10, **kwargs) -> str:
        sf = kwargs.get("search_field", "all")
        return f"{self.API_URL}?search_query={sf}:{quote_plus(query)}&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"

    async def search(self, query: str, max_results: int = 10, **kwargs) -> list[SearchResult]:
        url = self.build_url(query, max_results=max_results, **kwargs)
        try:
            r = await self._client.get(url); r.raise_for_status()
            ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
            root = ET.fromstring(r.text)
            results = []
            for i, entry in enumerate(root.findall("atom:entry", ns)[:max_results]):
                title = entry.findtext("atom:title", "", ns).replace("\n", " ").strip()
                summary = entry.findtext("atom:summary", "", ns).replace("\n", " ").strip()[:300]
                link_el = entry.find("atom:link", ns)
                link = link_el.get("href", "") if link_el is not None else ""
                authors = [a.findtext("atom:name", "", ns) for a in entry.findall("atom:author", ns)]
                published = entry.findtext("atom:published", "", ns)
                results.append(SearchResult(title=title or summary[:60], url=link, snippet=summary or "No abstract", source=self.name, rank=i+1, category="academic", extra={"published": published, "authors": ", ".join(authors)}))
            return results
        except Exception as e:
            logger.error(f"ArXiv search failed: {e}")
            return []

    async def close(self):
        await self._client.aclose()
