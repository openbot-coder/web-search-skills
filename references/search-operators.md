# Advanced Search Operators Guide

---

## Google

| Operator | Example | Description |
|----------|---------|-------------|
| `""` | `"machine learning"` | Exact phrase match |
| `-` | `python -snake` | Exclude term |
| `OR` | `cat OR dog` | Either term |
| `site:` | `site:github.com python` | Search within site |
| `filetype:` | `filetype:pdf report` | File type filter |
| `intitle:` | `intitle:test` | Title contains |
| `inurl:` | `inurl:login` | URL contains term |
| `related:` | `related:github.com` | Find similar sites |

### Time Filters

| Parameter | Description |
|-----------|-------------|
| `tbs=qdr:h` | Past hour |
| `tbs=qdr:d` | Past 24 hours |
| `tbs=qdr:w` | Past week |
| `tbs=qdr:m` | Past month |
| `tbs=qdr:y` | Past year |

### Special Search Types

| Type | URL |
|------|-----|
| Images | `?q={keyword}&tbm=isch` |
| News | `?q={keyword}&tbm=nws` |
| Scholar | `scholar.google.com/scholar?q={keyword}` |

---

## DuckDuckGo

### Bangs

| Bang | Destination |
|------|-------------|
| `!g` | Google |
| `!gh` | GitHub |
| `!so` | Stack Overflow |
| `!w` | Wikipedia |
| `!yt` | YouTube |
| `!a` | Amazon |
| `!m` | Google Maps |

### Region & Safety

| Parameter | Description |
|-----------|-------------|
| `kl=cn` | Chinese region |
| `kl=us-en` | US English |
| `kp=1` | Strict safe search |
| `kp=-1` | Off safe search |

---

## Baidu (百度)

| Feature | URL |
|---------|-----|
| Basic search | `https://www.baidu.com/s?wd={keyword}` |
| Academic | `https://xueshu.baidu.com/s?wd={keyword}` |

Supports: `site:`, `filetype:`, `""`, `-`

---

## Bing

| Feature | URL |
|---------|-----|
| CN search | `https://cn.bing.com/search?q={keyword}&ensearch=0` |
| INT search | `https://cn.bing.com/search?q={keyword}&ensearch=1` |
| Academic | `https://cn.bing.com/academic/search?q={keyword}` |

---

## Brave Search

| Feature | URL |
|---------|-----|
| News (week) | `...&source=news&tf=pw` |
| News (month) | `...&source=news&tf=pm` |
| Images | `...&source=images` |

---

## WolframAlpha (Knowledge)

| Type | Example |
|------|---------|
| Math | `integrate x^2 dx` |
| Currency | `100 USD to CNY` |
| Stocks | `AAPL stock` |
| Weather | `weather in Beijing` |

---

## Search Strategy

| Goal | Engine | Why |
|------|--------|-----|
| Chinese content | Baidu / Bing CN | Best CN index |
| WeChat articles | 搜狗微信 | Only channel |
| Academic | Google Scholar / ArXiv | Best index |
| Programming | Google + DDG Bangs | Strong tech docs |
| Privacy | DuckDuckGo / Startpage | No tracking |
| Financial news | 财联社 / 华尔街见闻 | CN financial |
| Knowledge | WolframAlpha | Structured data |
