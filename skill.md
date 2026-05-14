---
name: web-search-skills
description: "Multi-source web search skill for AI agents. Supports 16+ search engines (Google, DuckDuckGo, Baidu, Bing, etc.), Chinese financial news (财联社, 华尔街见闻), ArXiv academic papers, and WeChat public accounts. Use when the agent needs real-time web data, news, research papers, or WeChat articles."
version: 2.0.0
license: MIT
metadata:
  author: openbot-coder
  category: search
  tags: [web-search, news, academic, wechat, multi-engine]
  engines: 19
---

# Web Search Skills

Multi-source web search toolkit. Provides a unified interface to search across search engines, news sources, academic databases, and WeChat public accounts.

## Overview

- **16+ Search Engines**: Baidu, Google, DuckDuckGo, Bing CN/INT, 360, Sogou, Yahoo, Startpage, Brave, Ecosia, Qwant, Shenma
- **News Sources**: 财联社 (cls.cn), 华尔街见闻 (wallstreetcn.com)
- **Academic Papers**: ArXiv (all scientific categories)
- **WeChat Articles**: 搜狗微信 (wx.sogou.com)
- **Knowledge Computing**: WolframAlpha
- **No API Keys Required**: Most sources work via URL generation or HTML scraping

## Available Sources

### Web Search Engines (14)

| Engine | URL Template | Region |
|--------|-------------|--------|
| **Baidu** | `https://www.baidu.com/s?wd={keyword}` | CN |
| **Bing CN** | `https://cn.bing.com/search?q={keyword}&ensearch=0` | CN |
| **Bing INT** | `https://cn.bing.com/search?q={keyword}&ensearch=1` | CN |
| **360** | `https://www.so.com/s?q={keyword}` | CN |
| **Sogou** | `https://sogou.com/web?query={keyword}` | CN |
| **Shenma** | `https://m.sm.cn/s?q={keyword}` | CN |
| **Google** | `https://www.google.com/search?q={keyword}` | Global |
| **Google HK** | `https://www.google.com.hk/search?q={keyword}` | Global |
| **DuckDuckGo** | `https://duckduckgo.com/html/?q={keyword}` | Global |
| **Yahoo** | `https://search.yahoo.com/search?p={keyword}` | Global |
| **Startpage** | `https://www.startpage.com/sp/search?query={keyword}` | Global |
| **Brave** | `https://search.brave.com/search?q={keyword}` | Global |
| **Ecosia** | `https://www.ecosia.org/search?q={keyword}` | Global |
| **Qwant** | `https://www.qwant.com/?q={keyword}` | Global |

### News Sources (2)
| Source | Endpoint | Description |
|--------|----------|-------------|
| **财联社** | `cls.cn/searchPage?keyword={keyword}` | Financial news |
| **华尔街见闻** | `wallstreetcn.com/search?q={keyword}` | Global financial news |

### Academic (1)
| Source | Endpoint | Description |
|--------|----------|-------------|
| **ArXiv** | `export.arxiv.org/api/query` | Scientific papers |

### WeChat (1)
| Source | Endpoint | Description |
|--------|----------|-------------|
| **微信公众号** | `wx.sogou.com/weixin?type=2&query={keyword}` | WeChat articles |

### Special (1)
| Source | URL | Description |
|--------|-----|-------------|
| **WolframAlpha** | `https://www.wolframalpha.com/input?i={keyword}` | Knowledge computation |
