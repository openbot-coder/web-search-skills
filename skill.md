---
name: web-search-skills
description: "Multi-source web search skill for AI agents. Supports 16+ search engines (Google, DuckDuckGo, Baidu, Bing, etc.), Chinese financial news (财联社, 华尔街见闻), international RSS news (BBC, Reuters, NPR, Al Jazeera), ArXiv academic papers, WeChat public accounts, and Twitter/X search. Use when the agent needs real-time web data, news, research papers, WeChat articles, or social media content."
version: 2.1.0
license: MIT
metadata:
  author: openbot-coder
  category: search
  tags: [web-search, news, academic, wechat, social, twitter, rss, multi-engine]
  engines: 26
---

# Web Search Skills

Multi-source web search toolkit. Provides a unified interface to search across search engines, news sources, academic databases, social media, and WeChat public accounts.

## Overview

| Category | Sources | Count |
|----------|---------|:-----:|
| Web Search | Baidu, Google, DuckDuckGo, Bing CN/INT, 360, Sogou, Shenma, Yahoo, Startpage, Brave, Ecosia, Qwant | 14 |
| CN News | 财联社, 华尔街见闻 | 2 |
| RSS News | BBC (World/Business/Tech), Reuters, NPR, Al Jazeera | 6 |
| Academic | ArXiv | 1 |
| WeChat | 搜狗微信 | 1 |
| Social | Twitter/X (top/latest/people/photos) | 1 |
| Special | WolframAlpha | 1 |
| **Total** | | **26** |

## Quick Start

### Python API
```python
from scripts.unified_search import UnifiedSearch

async with UnifiedSearch() as searcher:
    tweets = await searcher.search_social("Python")
    tweet_url = await searcher.get_twitter_search_url("Python", search_type="latest")
    headlines = await searcher.search_rss(max_results=20)
    tech_news = await searcher.search_rss("AI", feeds=["BBC Technology"])
```

### URL Generation
```javascript
web_fetch({"url": "https://twitter.com/search?q=AI&f=live&src=typed_query"})
web_fetch({"url": "https://feeds.bbci.co.uk/news/technology/rss.xml"})
web_fetch({"url": "https://www.aljazeera.com/xml/rss/all.xml"})
```

## Available Sources

### Twitter/X Search
| Type | URL |
|------|-----|
| Top | `https://twitter.com/search?q={keyword}&src=typed_query` |
| Latest | `...&f=live&src=typed_query` |
| People | `...&f=user&src=typed_query` |
| Photos | `...&f=image&src=typed_query` |

**Advanced operators**: `from:user`, `to:user`, `#hashtag`, `filter:links`, `min_retweets:N`, `min_faves:N`

### RSS News Feeds
| Source | Category |
|--------|----------|
| BBC World | News |
| BBC Top Stories | News |
| BBC Business | Business |
| BBC Technology | Technology |
| Reuters | News |
| NPR | News |
| Al Jazeera | News |

## References
- `references/search-operators.md`
- `config/engines.json`
- `scripts/unified_search.py`
