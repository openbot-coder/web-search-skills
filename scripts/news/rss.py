"""RSS news aggregation engine."""
from __future__ import annotations
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse
import httpx
from scripts.core.base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)

RSS_FEEDS = {
    "BBC World": {"url": "https://feeds.bbci.co.uk/news/world/rss.xml", "category": "news", "lang": "en"},
    "BBC Top Stories": {"url": "https://feeds.bbci.co.uk/news/rss.xml", "category": "news", "lang": "en"},
    "BBC Business": {"url": "https://feeds.bbci.co.uk/news/business/rss.xml", "category": "business", "lang": "en"},
    "BBC Technology": {"url": "https://feeds.bbci.co.uk/news/technology/rss.xml", "category": "technology", "lang": "en"},
    "Reuters": {"url": "https://www.reutersagency.com/feed/?best-regions=world&post_type=best", "category": "news", "lang": "en"},
    "NPR": {"url": "https://feeds.npr.org/1001/rss.xml", "category": "news", "lang": "en"},
    "Al Jazeera": {"url": "https://www.aljazeera.com/xml/rss/all.xml", "category": "news", "lang": "en"},
}

class RSSNewsEngine(SearchEngine):
    def __init__(self, config: Optional[dict] = None):
        super().__init__("RSS News", config)
        timeout = (config or {}).get("timeout", 30)
        self._client = httpx.AsyncClient(timeout=timeout, headers={"User-Agent": (config or {}).get("user_agent", "Mozilla/5.0"), "Accept": "application/rss+xml,application/xml"}, follow_redirects=True)

    async def search(self, query: str, max_results: int = 10, **kwargs) -> list[SearchResult]:
        feeds = RSS_FEEDS
        if kwargs.get("category"):
            feeds = {k:v for k,v in RSS_FEEDS.items() if v.get("category") == kwargs["category"]}
        results = []
        for name, info in feeds.items():
            try:
                r = await self._client.get(info["url"]); r.raise_for_status()
                root = ET.fromstring(r.text)
                items = root.findall(".//item") if root.tag == "rss" else root.findall("{http://www.w3.org/2005/Atom}entry")
                for i, item in enumerate(items):
                    if root.tag == "rss":
                        title = item.findtext("title", "")
                        link = item.findtext("link", "")
                        desc = item.findtext("description", "")
                    else:
                        title = item.findtext("{http://www.w3.org/2005/Atom}title", "")
                        link_el = item.find("{http://www.w3.org/2005/Atom}link")
                        link = link_el.get("href", "") if link_el is not None else ""
                        desc = item.findtext("{http://www.w3.org/2005/Atom}summary", "") or item.findtext("{http://www.w3.org/2005/Atom}content", "")
                    import re
                    snippet = re.sub(r"<[^>]+>", "", desc).strip()[:300]
                    if query and query.lower() not in title.lower() and query.lower() not in snippet.lower():
                        continue
                    results.append(SearchResult(title=title, url=link, snippet=snippet, source=name, rank=i+1, category=info.get("category","news"), extra={"feed_name": name}))
            except Exception as e:
                logger.debug(f"RSS {name} failed: {e}")
                continue
        results.sort(key=lambda r: r.rank)
        return results[:max_results * max(1, len(feeds))]

    async def close(self):
        await self._client.aclose()
