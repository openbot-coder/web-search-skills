"""
Basic usage example for Web Search Skills.

Run:
    python examples/basic_search.py
"""

import asyncio

from src.web_search import WebSearch


async def main():
    async with WebSearch() as searcher:
        results = await searcher.search(
            "Python web scraping best practices 2026",
            max_results=5,
        )

        print(f"Found {len(results)} results:\n")
        for result in results:
            print(f"[{result.rank}] {result.title}")
            print(f"    URL: {result.url}")
            print(f"    {result.snippet[:120]}...")
            print()

        if results:
            content = await searcher.extract_content(results[0].url)
            if content:
                print(f"--- Content from {results[0].url} ---")
                print(content[:300])
                print("...")


if __name__ == "__main__":
    asyncio.run(main())
