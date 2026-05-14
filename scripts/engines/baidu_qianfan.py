"""
Baidu Qianfan AI Search API engine.

Uses the official Baidu Qianfan (千帆) AI Search API to get
structured search results. Requires BAIDU_API_KEY environment variable
or .env file in the project root.

API docs: https://console.bce.baidu.com/qianfan/ais/console/apiKey
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

import httpx

from scripts.core.base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)

API_URL = "https://qianfan.baidubce.com/v2/ai_search/web_search"
ENV_KEY = "BAIDU_API_KEY"


def _load_env_file() -> dict[str, str]:
    """Load .env file from project root (simple parser, no external deps)."""
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if not env_path.exists():
        return {}
    env_vars = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            env_vars[key.strip()] = val.strip().strip("\"'")
    return env_vars


def _get_api_key() -> str:
    """Get API key: env var > .env file > config."""
    key = os.getenv(ENV_KEY)
    if key:
        return key
    env_from_file = _load_env_file()
    return env_from_file.get(ENV_KEY, "")


class BaiduQianFanEngine(SearchEngine):
    """百度千帆 AI 搜索 API 引擎."""

    def __init__(self, config: Optional[dict] = None):
        super().__init__("Baidu Qianfan", config)
        self.api_key = (config or {}).get("api_key", "") or _get_api_key()
        if not self.api_key:
            logger.warning(
                f"BAIDU_API_KEY not set! Set it in .env file or as environment variable."
            )

        timeout = (config or {}).get("timeout", 30)
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "X-Appbuilder-From": "openclaw",
                "Content-Type": "application/json",
            },
            follow_redirects=True,
        )

    async def search(
        self, query: str, max_results: int = 10, **kwargs
    ) -> list[SearchResult]:
        """Search via Baidu Qianfan AI Search API.

        Args:
            query: Search keywords.
            max_results: Max results to return.
            **kwargs:
                site: Restrict search to a specific site (e.g. "mp.weixin.qq.com").
                recency: Time filter: "week", "month", "semiyear", "year" (default: "year").
                edition: "standard" (default) or "lite".
                safe_search: bool, default False.
        """
        if not self.api_key:
            return [
                SearchResult(
                    title="错误: BAIDU_API_KEY 未配置",
                    url="https://console.bce.baidu.com/qianfan/ais/console/apiKey",
                    snippet="请先设置 BAIDU_API_KEY 环境变量",
                    source=self.name,
                    rank=1,
                    category="web",
                    extra={"error": "missing_api_key"},
                )
            ]

        # Build resource_type_filter based on max_results
        top_k = min(max_results, 50)
        resource_type_filter = [
            {"type": "web", "top_k": top_k},
        ]

        # Build search_filter if site is specified
        search_filter = {}
        site = kwargs.get("site")
        if site:
            search_filter["match"] = {"site": [site]}

        request_body = {
            "messages": [{"content": query, "role": "user"}],
            "edition": kwargs.get("edition", "standard"),
            "search_source": "baidu_search_v2",
            "resource_type_filter": resource_type_filter,
            "search_recency_filter": kwargs.get("recency", "year"),
            "safe_search": kwargs.get("safe_search", False),
        }
        if search_filter:
            request_body["search_filter"] = search_filter
        if kwargs.get("block_websites"):
            request_body["block_websites"] = kwargs["block_websites"]

        try:
            response = await self._client.post(API_URL, json=request_body)
            response.raise_for_status()
            data = response.json()

            if "code" in data:
                logger.error(f"Baidu Qianfan API error: {data.get('message', '')}")
                return []

            references = data.get("references", [])
            results = []
            for i, ref in enumerate(references[:max_results]):
                results.append(
                    SearchResult(
                        title=ref.get("title", ""),
                        url=ref.get("url", ""),
                        snippet=ref.get("snippet", ""),
                        source=self.name,
                        rank=i + 1,
                        category="web",
                        extra={
                            k: ref[k]
                            for k in ("site", "date", "type", "source")
                            if k in ref
                        },
                    )
                )
            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"Baidu Qianfan API HTTP error: {e.response.status_code}")
            if e.response.status_code == 401:
                logger.error("API Key 无效或未授权，请检查 BAIDU_API_KEY")
            elif e.response.status_code == 429:
                logger.error("API 配额不足")
            return []
        except httpx.RequestError as e:
            logger.error(f"Baidu Qianfan API request failed: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Baidu Qianfan API response parse failed: {e}")
            return []

    async def close(self):
        await self._client.aclose()
