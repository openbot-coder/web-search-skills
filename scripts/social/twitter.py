"""
Twitter/X search module.
Generates search URLs and supports advanced search operators.
"""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from scripts.core.base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)


class TwitterSearchEngine(SearchEngine):
    """Twitter/X search engine."""

    SEARCH_URL = "https://twitter.com/search"
    BASE_URL = "https://twitter.com"

    def __init__(self, config: Optional[dict] = None):
        super().__init__("Twitter", config)
        timeout = (config or {}).get("timeout", 15)
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                     "Accept-Language": "en-US,en;q=0.5"},
            follow_redirects=True,
        )

    def build_url(self, query: str, search_type: str = "top", **kwargs) -> str:
        encoded_query = quote_plus(query)
        url = f"{self.SEARCH_URL}?q={encoded_query}&src=typed_query"
        type_map = {"latest": "live", "people": "user", "photos": "image", "videos": "video"}
        if search_type in type_map:
            url += f"&f={type_map[search_type]}"
        if kwargs.get("lang"): url += f"&l={kwargs['lang']}"
        if kwargs.get("until"): url += f"&until={kwargs['until']}"
        if kwargs.get("since"): url += f"&since={kwargs['since']}"
        return url

    def build_advanced_url(self, **params) -> str:
        parts = []
        if params.get("from_user"): parts.append(f"from:{params['from_user']}")
        if params.get("to_user"): parts.append(f"to:{params['to_user']}")
        if params.get("hashtag"): parts.append(f"#{params['hashtag']}")
        if params.get("keyword"): parts.append(params["keyword"])
        if params.get("min_retweets"): parts.append(f"min_retweets:{params['min_retweets']}")
        if params.get("min_faves"): parts.append(f"min_faves:{params['min_faves']}")
        if params.get("lang"): parts.append(f"lang:{params['lang']}")
        if params.get("filter"): parts.append(f"filter:{params['filter']}")
        return self.build_url(" ".join(parts), search_type=params.get("search_type", "top"))

    async def search(self, query: str, max_results: int = 10, search_type: str = "top", **kwargs) -> list[SearchResult]:
        url = self.build_url(query, search_type=search_type, **kwargs)
        try:
            response = await self._client.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                results = self._parse_page(soup, max_results)
                if results:
                    return results
        except Exception as e:
            logger.debug(f"Twitter scrape expected: {e}")
        desc = {"top": "Top tweets", "latest": "Latest tweets", "people": "People",
                "photos": "Photos", "videos": "Videos"}.get(search_type, "Tweets")
        return [SearchResult(title=f"Twitter: {query} ({desc})", url=url,
                             snippet=f"Search Twitter/X for '{query}'. Note: Twitter may require login.",
                             source=self.name, rank=1, category="social",
                             extra={"search_type": search_type, "twitter_url": url})]

    def _parse_page(self, soup, max_results: int) -> list[SearchResult]:
        results = []
        tweets = soup.select("article[data-testid='tweet'], div.tweet, .content")
        for i, tweet in enumerate(tweets[:max_results]):
            text_el = tweet.select_one("[data-testid='tweetText'], .tweet-text, p[lang]")
            link_el = tweet.select_one("a[href*='/status/'], time")
            user_el = tweet.select_one("[data-testid='User-Name'], .username, .fullname")
            text = text_el.get_text(strip=True) if text_el else ""
            user = user_el.get_text(strip=True) if user_el else ""
            tweet_url = ""
            if link_el:
                href = link_el.get("href", "")
                tweet_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href
            if text:
                results.append(SearchResult(title=f"@{user}: {text[:80]}...", url=tweet_url or self.build_url(text[:30]),
                                            snippet=text, source=self.name, rank=i+1, category="social",
                                            extra={"user": user} if user else {}))
        return results

    async def close(self):
        await self._client.aclose()
