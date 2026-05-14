# Web Search Skill

## Description

Provides web search capabilities for AI agents, supporting multiple search engines, intelligent result processing, and customizable search parameters.

## Triggers

- "search the web for..."
- "find information about..."
- "look up..."
- Any query requiring real-time web data

## Configuration

```yaml
search:
  default_engine: duckduckgo
  max_results: 10
  timeout: 15
  user_agent: "WebSearchSkill/1.0"
```

## Actions

- `web_search(query, engine=None, max_results=10)` - Perform a web search
- `search_news(query, max_results=5)` - Search news sources
- `search_images(query, max_results=10)` - Search for images
- `extract_content(url)` - Extract readable content from a URL

## Notes

- Respects robots.txt for web scraping
- Implements rate limiting to avoid API bans
- Caches results for repeated queries within the same session
