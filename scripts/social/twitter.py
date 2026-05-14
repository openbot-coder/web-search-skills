"""Twitter/X search module."""
from __future__ import annotations
import logging
from typing import Optional
from urllib.parse import quote_plus
import httpx
from bs4 import BeautifulSoup
from scripts.core.base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)

class TwitterSearchEngine(SearchEngine):
    SEARCH_URL = "https://twitter.com/search"
    BASE_URL = "https://twitter.com"

    def __init__(self, config: Optional[dict] = None):
        super().__init__("Twitter", config)
        timeout = (config or {}).get("timeout", 15)
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": (config or {}).get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")},
            follow_redirects=True,
        )

    def build_url(self, query: str, search_type: str = "top", **kwargs) -> str:
        encoded_query = quote_plus(query)
        url = f"{self.SEARCH_URL}?q={encoded_query}&src=typed_query"
        if search_type == "latest":
            url += "&f=live"
        elif search_type == "people":
            url += "&f=user"
        elif search_type == "photos":
            url += "&f=image"
        elif search_type == "videos":
            url += "&f=video"
        if kwargs.get("lang"):
            url += f"&l={kwargs['lang']}"
        if kwargs.get("until"):
            url += f"&until={kwargs['until']}"
        if kwargs.get("since"):
            url += f"&since={kwargs['since']}"
        return url

    async def search(self, query: str, max_results: int = 10, search_type: str = "top", **kwargs) -> list[SearchResult]:
        url = self.build_url(query, search_type=search_type, **kwargs)
        try:
            response = await self._client.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                results = []
                tweets = soup.select("article[data-testid='tweet'], div.tweet, .content")
                for i, tweet in enumerate(tweets[:max_results]):
                    text_el = tweet.select_one("[data-testid='tweetText'], .tweet-text, p[lang]")
                    if text_el:
                        text = text_el.get_text(strip=True)
                        results.append(SearchResult(title=text[:80], url=url, snippet=text, source=self.name, rank=i+1, category="social"))
                if results:
                    return results
        except Exception:
            pass
        return [SearchResult(title=f"Twitter: {query}", url=url, snippet=f"Search Twitter/X for '{query}'", source=self.name, rank=1, category="social", extra={"search_type": search_type})]

    async def close(self):
        await self._client.aclose()
