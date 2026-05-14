"""
Thread pool utilities for CPU-bound operations.

BeautifulSoup/HTML parsing is CPU-bound and can block the async event loop.
Use this shared thread pool to offload parsing work to background threads.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Shared thread pool - max_workers=4 balances parallelism with overhead
_PARSE_POOL: ThreadPoolExecutor | None = None
_MAX_WORKERS = 4


def get_parse_pool() -> ThreadPoolExecutor:
    """Get the shared thread pool for parsing operations."""
    global _PARSE_POOL
    if _PARSE_POOL is None:
        _PARSE_POOL = ThreadPoolExecutor(
            max_workers=_MAX_WORKERS,
            thread_name_prefix="parse",
        )
    return _PARSE_POOL


async def run_in_thread(func: Callable[..., T], *args, **kwargs) -> T:
    """
    Run a CPU-bound function in a thread pool to avoid blocking the event loop.

    Usage:
        soup = await run_in_thread(BeautifulSoup, html, "lxml")
        results = await run_in_thread(parse_func, html, max_results)
    """
    import asyncio
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(get_parse_pool(), func, *args, **kwargs)


def shutdown_pool():
    """Clean up the thread pool (call during application shutdown)."""
    global _PARSE_POOL
    if _PARSE_POOL:
        _PARSE_POOL.shutdown(wait=True)
        _PARSE_POOL = None
