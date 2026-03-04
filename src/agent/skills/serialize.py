from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

_queues: dict[str, asyncio.Future[object]] = {}


async def serialize_by_key(key: str, task: Callable[[], Awaitable[object]]) -> object:
    prev = _queues.get(key)
    if prev is None:
        prev = asyncio.get_running_loop().create_future()
        prev.set_result(None)

    async def run() -> object:
        try:
            await prev
        except Exception:
            pass
        return await task()

    next_future = asyncio.create_task(run())
    _queues[key] = next_future
    try:
        return await next_future
    finally:
        if _queues.get(key) is next_future:
            _queues.pop(key, None)
