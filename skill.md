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

## 概述

Multi-source web search CLI and library supporting 20+ search engines, including web search, news (财联社, 华尔街见闻), WeChat articles, academic papers (ArXiv), social media (Twitter/X), and RSS feeds.

## 触发词 Triggers

中文触发词：
- "搜索微信公众号..."
- "搜一下微信公众号..."
- "查一下新闻..."
- "搜索新闻关于..."
- "搜论文..."
- "查学术资料..."
- "搜索一下..."

English Triggers:
- "search the web for..."
- "find information about..."
- "look up..."
- "search WeChat for..."
- "search news about..."
- Any query requiring real-time web data

## 安装 Installation

```bash
cd web-search-skills
uv tool install -e .
```

安装后 `web-search` 命令全局可用。

## 命令 Commands

| 命令 Commands | 说明 Description |
|---------------|------------------|
| `web-search search <query>` | 全源搜索 Search all sources |
| `web-search web <query>` | 网页搜索 Web search engines |
| `web-search news <query>` | 新闻搜索 News (财联社, 华尔街见闻) |
| `web-search wechat <query>` | 微信公众号搜索 WeChat articles |
| `web-search academic <query>` | 学术搜索 Academic papers (ArXiv) |
| `web-search social <query>` | 社交搜索 Social media (Twitter/X) |
| `web-search rss <query>` | RSS 源搜索 RSS feeds |
| `web-search sources` | 列出所有搜索源 List all sources |
| `web-search urls <query>` | 只生成搜索链接 Search URLs only |

### 通用选项 Options

| 选项 | 说明 |
|------|------|
| `-n N` | 每源最大结果数 (默认: 10) |
| `-j` | JSON 格式输出 |
| `-o FILE` | 保存结果到 JSON 文件 |
| `-s NAME` | 指定来源名称 |
| `-r cn/global` | 区域过滤 (web 搜索) |
| `-v` | 调试日志 |

## 项目结构 Structure

```
web-search-skills/
├── scripts/              # Python 脚本目录
│   ├── cli.py              # CLI 入口
│   ├── unified_search.py   # 统一搜索编排器
│   ├── core/
│   │   ├── base.py         # SearchResult & SearchEngine 基类
│   │   └── config_loader.py# 从 JSON 加载搜索引擎配置
│   ├── engines/
│   │   ├── url_engine.py   # URL 模板搜索引擎
│   │   └── parser_engines.py# HTML 解析搜索 (DuckDuckGo)
│   ├── news/
│   │   ├── cls.py          # 财联社新闻引擎
│   │   ├── wallstreetcn.py # 华尔街见闻引擎
│   │   └── rss.py          # RSS 聚合引擎
│   ├── academic/
│   │   └── arxiv.py        # ArXiv 学术论文引擎
│   ├── wechat/
│   │   └── sogou_weixin.py # 搜狗微信搜索引擎
│   └── social/
│       └── twitter.py      # Twitter/X 搜索引擎
├── config/
│   └── engines.json        # 搜索引擎定义配置
├── ws.py                   # 本地运行入口
├── pyproject.toml           # 包构建配置
├── SKILL.md                 # 本技能定义文件
├── LICENSE                  # MIT 许可证
└── README.md                # 项目文档
```

## 配置 Configuration

所有搜索引擎定义在 `config/engines.json` 中，支持 6 类源：

| 类别 | 数量 |
|------|------|
| Web 搜索引擎 | 14 个 (Baidu, Google, DuckDuckGo 等) |
| 新闻源 | 2 个 (财联社, 华尔街见闻) |
| 学术源 | 1 个 (ArXiv) |
| 微信源 | 1 个 (搜狗微信) |
| 社交源 | 2 个 (Twitter, Twitter Latest) |
| 特殊源 | 1 个 (WolframAlpha) |

每个引擎定义格式：
```json
{"name": "Baidu", "url": "https://www.baidu.com/s?wd={keyword}", "region": "cn", "type": "url"}
```

- `{keyword}` 会被替换为搜索关键词
- `type: url` 表示只生成 URL，`type: parser` 表示会解析 HTML 提取结果

## Python API

也可在代码中直接调用：

```python
from scripts.unified_search import UnifiedSearch

async def main():
    us = UnifiedSearch()
    results = await us.search("量子计算", sources=["web", "news"], max_results=5)
    for r in results:
        print(f"[{r.rank}] {r.title}: {r.url}")
    await us.close()
```

## 注意事项 Notes

- 搜狗微信搜索有反爬限制，可能返回空结果
- 财联社和华尔街见闻需要 JavaScript 渲染，`UnifiedSearch` 返回搜索页面链接
- RSS 源需要稳定的网络连接
