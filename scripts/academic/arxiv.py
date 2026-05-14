"""ArXiv academic paper search using the official API (no API key required)."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from typing import Optional
from urllib.parse import quote_plus

import httpx

from scripts.core.base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)


class ArXivEngine(SearchEngine):
    """ArXiv academic paper search engine."""

    API_URL = "https://export.arxiv.org/api/query"

    SEARCH_PARAMS = {
        "all": "search_query=all:{keyword}",
        "title": "search_query=ti:{keyword}",
        "author": "search_query=au:{keyword}",
        "abstract": "search_query=abs:{keyword}",
    }

    def __init__(self, config: Optional[dict] = None):
        super().__init__("ArXiv", config)
        timeout = (config or {}).get("timeout", 30)
        self._client = httpx.AsyncClient(timeout=timeout, headers={"User-Agent": "WebSearchSkill/1.0"}, follow_redirects=True)

    def build_url(self, query: str, field: str = "all", max_results: int = 10, **kwargs) -> str:
        query_template = self.SEARCH_PARAMS.get(field, self.SEARCH_PARAMS["all"])
        query_part = query_template.replace("{keyword}", quote_plus(query))
        return f"{self.API_URL}?{query_part}&max_results={max_results}&sortBy=relevance&sortOrder=descending"

    async def search(self, query: str, max_results: int = 10, field: str = "all", **kwargs) -> list[SearchResult]:
        try:
            url = self.build_url(query, field=field, max_results=max_results)
            response = await self._client.get(url)
            response.raise_for_status()
            return self._parse_response(response.text, max_results)
        except httpx.HTTPError as e:
            logger.error(f"ArXiv search failed: {e}")
            return []

    def _parse_response(self, xml_data: str, max_results: int) -> list[SearchResult]:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(xml_data)
        results = []
        for i, entry in enumerate(root.findall("a:entry", ns)[:max_results]):
            title = entry.find("a:title", ns)
            summary = entry.find("a:summary", ns)
            published = entry.find("a:published", ns)
            authors = entry.findall("a:author/a:name", ns)
            title_text = title.text.strip().replace("\n", " ") if title is not None and title.text else ""
            summary_text = summary.text.strip().replace("\n", " ") if summary is not None and summary.text else ""
            snippet = summary_text[:300] + "..." if len(summary_text) > 300 else summary_text
            links = entry.findall("a:link", ns)
            page_url = ""
            for link in links:
                if link.get("title") == "pdf":
                    page_url = link.get("href", "").replace("/pdf/", "/abs/")
                    break
            if not page_url:
                for link in links:
                    if link.get("rel") == "alternate":
                        page_url = link.get("href", "")
                        break
            author_list = [a.text for a in authors if a.text]
            author_str = ", ".join(author_list[:3])
            if len(author_list) > 3:
                author_str += " et al."
            pub_date = published.text[:10] if published is not None and published.text else ""
            results.append(SearchResult(title=title_text, url=page_url, snippet=snippet, source="ArXiv", rank=i + 1, category="academic", extra={"authors": author_str, "published": pub_date, "arxiv_id": page_url.split("/")[-1] if page_url else ""}))
        return results

    async def close(self):
        await self._client.aclose()
