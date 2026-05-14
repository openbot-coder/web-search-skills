---
name: web-search-skills
description: "多源搜索 CLI 工具，支持 20+ 搜索引擎。搜索微信公众号文章、新闻资讯、学术论文、社交媒体的综合搜索技能。当用户需要搜索网络信息、查找微信公众号文章、搜索财经新闻、查询学术论文时使用。"
version: 2.1.0
license: MIT
compatibility: Requires Python 3.8+, httpx, beautifulsoup4, lxml
metadata:
  author: openbot-coder
  category: development
  tags: [search, web, wechat, news, academic, cli]
---

# Web Search Skills

## Overview

Multi-source web search CLI and library supporting 20+ search engines.

## Triggers

Chinese: "搜索微信公众号...", "搜一下微信公众号...", "查一下新闻...", "搜索新闻关于...", "搜论文...", "查学术资料...", "搜索一下..."
English: "search the web for...", "find information about...", "look up...", "search WeChat for...", "search news about..."

## Installation

```bash
cd web-search-skills
uv tool install -e .
```

## Commands

| Command | Description |
|---------|-------------|
| `web-search search <query>` | Search all sources |
| `web-search web <query>` | Web search engines |
| `web-search news <query>` | News (CLS, WallStreetCN) |
| `web-search wechat <query>` | WeChat articles |
| `web-search academic <query>` | Academic papers (ArXiv) |
| `web-search social <query>` | Social media (Twitter/X) |
| `web-search rss <query>` | RSS feeds |
| `web-search sources` | List all sources |
| `web-search urls <query>` | Get search URLs only |

## Configuration

Engines defined in `config/engines.json`. Supports 6 categories with 21 sources.
