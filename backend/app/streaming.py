"""Per-user streaming delivery for SSE endpoints.

Messages are delivered directly to the local asyncio queue for low latency and
published to Redis so a worker handling the research task can stream to a
worker holding the client's SSE connection. Redis is optional; local delivery
continues to work when it is unavailable.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from collections import deque
from typing import Any, Deque, Dict, Optional, Set

try:
    from redis import asyncio as redis_asyncio
except ImportError:  # pragma: no cover - exercised only in minimal local installs
    redis_asyncio = None

from loguru import logger


class ConnectionManager:
    def __init__(self):
        queue_size = int(os.getenv("TEKK_STREAM_QUEUE_SIZE", "1000"))
        self.active_connections: Dict[str, asyncio.Queue] = {}
        self._queue_size = max(1, queue_size)
        self._listener_tasks: Dict[str, asyncio.Task] = {}
        self._recent_message_ids: Dict[str, Set[str]] = {}
        self._recent_message_order: Dict[str, Deque[str]] = {}
        self._redis = None
        self._redis_disabled_until = 0.0
        self._redis_enabled = os.getenv(
            "TEKK_REDIS_STREAM_ENABLED", "true"
        ).lower() not in {"0", "false", "no", "off"}
        self._redis_url = os.getenv(
            "REDIS_URL", "redis://localhost:6379/0"
        )

    @staticmethod
    def _channel(client_id: str) -> str:
        return f"tekkscope:stream:{client_id}"

    async def _get_redis(self):
        if not self._redis_enabled or redis_asyncio is None:
            return None
        if time.monotonic() < self._redis_disabled_until:
            return None
        if self._redis is not None:
            return self._redis

        client = None
        try:
            client = redis_asyncio.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=0.5,
                socket_timeout=2.0,
            )
            await asyncio.wait_for(client.ping(), timeout=0.75)
            self._redis = client
            logger.info("Redis-backed SSE streaming enabled")
            return client
        except Exception as error:  # noqa: BLE001 - local fallback is intentional
            self._redis_disabled_until = time.monotonic() + 5.0
            logger.warning("Redis SSE transport unavailable; using local queues: {}", error)
            try:
                close = getattr(client, "aclose", None)
                if close:
                    await close()
            except Exception:
                pass
            return None

    async def redis_available(self) -> bool:
        """Return whether the configured Redis transport is reachable."""

        return await self._get_redis() is not None

    def _remember_message(self, client_id: str, message_id: str) -> None:
        seen = self._recent_message_ids.setdefault(client_id, set())
        order = self._recent_message_order.setdefault(client_id, deque())
        if message_id in seen:
            return
        seen.add(message_id)
        order.append(message_id)
        while len(order) > 4096:
            expired = order.popleft()
            seen.discard(expired)

    def _has_seen_message(self, client_id: str, message_id: str) -> bool:
        return message_id in self._recent_message_ids.get(client_id, set())

    @staticmethod
    def _put_nowait_bounded(queue: asyncio.Queue, message: Any) -> None:
        try:
            queue.put_nowait(message)
            return
        except asyncio.QueueFull:
            # Progress messages are transient. Drop the oldest item so a slow
            # client cannot block the research worker indefinitely.
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                logger.warning("Dropping SSE message because the client queue is full")

    async def _redis_listener(self, client_id: str, queue: asyncio.Queue) -> None:
        channel = self._channel(client_id)
        while self.active_connections.get(client_id) is queue:
            client = await self._get_redis()
            if client is None:
                await asyncio.sleep(1.0)
                continue

            pubsub = client.pubsub()
            try:
                await pubsub.subscribe(channel)
                while self.active_connections.get(client_id) is queue:
                    payload = await pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0,
                    )
                    if not payload or payload.get("type") != "message":
                        continue
                    raw_data = payload.get("data")
                    if isinstance(raw_data, bytes):
                        raw_data = raw_data.decode("utf-8")
                    try:
                        envelope = json.loads(raw_data)
                        message_id = str(envelope["id"])
                        message = envelope["message"]
                    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                        logger.warning("Ignoring malformed Redis SSE message")
                        continue

                    if self._has_seen_message(client_id, message_id):
                        continue
                    self._remember_message(client_id, message_id)
                    self._put_nowait_bounded(queue, message)
            except asyncio.CancelledError:
                raise
            except Exception as error:  # noqa: BLE001 - local queue remains available
                logger.warning("Redis SSE listener stopped for {}: {}", client_id, error)
                self._redis = None
                self._redis_disabled_until = time.monotonic() + 1.0
            finally:
                try:
                    await pubsub.unsubscribe(channel)
                    close = getattr(pubsub, "aclose", None)
                    if close:
                        await close()
                except Exception:
                    pass

            if self.active_connections.get(client_id) is queue:
                await asyncio.sleep(1.0)

    async def connect(self, client_id: str):
        existing = self.active_connections.get(client_id)
        if existing is not None:
            self.disconnect(client_id, existing)

        queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=self._queue_size)
        self.active_connections[client_id] = queue
        self._recent_message_ids[client_id] = set()
        self._recent_message_order[client_id] = deque()
        if self._redis_enabled and redis_asyncio is not None:
            self._listener_tasks[client_id] = asyncio.create_task(
                self._redis_listener(client_id, queue)
            )
        return queue

    def disconnect(self, client_id: str, queue: Optional[asyncio.Queue] = None):
        current_queue = self.active_connections.get(client_id)
        if current_queue is None or (queue is not None and current_queue is not queue):
            return

        del self.active_connections[client_id]
        task = self._listener_tasks.pop(client_id, None)
        if task:
            task.cancel()
        self._recent_message_ids.pop(client_id, None)
        self._recent_message_order.pop(client_id, None)

    async def _publish(self, client_id: str, message_id: str, message: Any) -> None:
        client = await self._get_redis()
        if client is None:
            return
        envelope = json.dumps(
            {"id": message_id, "message": message},
            default=str,
        )
        try:
            await client.publish(self._channel(client_id), envelope)
        except Exception as error:  # noqa: BLE001 - local delivery still succeeds
            logger.warning("Failed to publish SSE message to Redis: {}", error)
            self._redis = None
            self._redis_disabled_until = time.monotonic() + 5.0

    async def broadcast(self, message: Any):
        for client_id in tuple(self.active_connections):
            await self.send_to_client(client_id, message)

    async def send_to_client(self, client_id: str, message: Any):
        message_id = uuid.uuid4().hex
        queue = self.active_connections.get(client_id)
        if queue is not None:
            self._remember_message(client_id, message_id)
            self._put_nowait_bounded(queue, message)

        # Publish even when this process does not own the SSE connection; the
        # worker owning it can receive the event through Redis.
        await self._publish(client_id, message_id, message)


manager = ConnectionManager()
