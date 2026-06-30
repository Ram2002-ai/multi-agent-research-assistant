"""Persistent pub/sub event stream shared by SSE and WebSocket clients."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from app.database.repository import Repository


class EventBroker:
    def __init__(self, repository: Repository):
        self.repository = repository
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)
        self._publish_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._lock = asyncio.Lock()

    async def publish(self, job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with self._publish_locks[job_id]:
            event = await asyncio.to_thread(self.repository.add_event, job_id, payload)
            async with self._lock:
                queues = list(self._subscribers.get(job_id, set()))
            for queue in queues:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    _ = queue.get_nowait()
                    queue.put_nowait(event)
            return event

    async def subscribe(self, job_id: str) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=500)
        async with self._lock:
            self._subscribers[job_id].add(queue)
        return queue

    async def unsubscribe(
        self, job_id: str, queue: asyncio.Queue[dict[str, Any]]
    ) -> None:
        async with self._lock:
            self._subscribers[job_id].discard(queue)
            if not self._subscribers[job_id]:
                self._subscribers.pop(job_id, None)
