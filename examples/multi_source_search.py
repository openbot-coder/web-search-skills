"""Multi-source search example."""

import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.unified_search import UnifiedSearch


async def main():
    async with UnifiedSearch() as searcher:
        # 1. Search URLs (for browser / web_fetch)
        print("=== Search URLs ===")
        urls = await searcher.get_search_urls("machine learning", ["Google", "DuckDuckGo", "Baidu"])
        for name, url in urls.items():
            print(f"  [{name}] {url}")

        # 2. Parsed results (DuckDuckGo)
        print("\n=== DuckDuckGo Results ===")
        results = await searcher.search("Python asyncio", sources=["DuckDuckGo"], max_results=3)
        for r in results:
            print(f"  [{r.rank}] {r.title}")

        # 3. ArXiv papers
        print("\n=== ArXiv Papers ===")
        papers = await searcher.search_academic("transformer attention", max_results=2)
        for r in papers:
            authors = r.extra.get("authors", "")
            print(f"  [{r.rank}] {r.title}")
            print(f"       Authors: {authors}")

        # 4. News URLs
        print("\n=== News URLs ===")
        news_urls = await searcher.get_search_urls("A股 新能源", ["财联社", "华尔街见闻"])
        for name, url in news_urls.items():
            print(f"  [{name}] {url}")

        # 5. WeChat URL
        print("\n=== WeChat URL ===")
        wechat_urls = await searcher.get_search_urls("Python", ["微信公众号"])
        for name, url in wechat_urls.items():
            print(f"  [{name}] {url}")

    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
