import pytest

from app.streaming import ConnectionManager


@pytest.mark.asyncio
async def test_streaming_keeps_local_delivery_when_redis_is_disabled(monkeypatch):
    monkeypatch.setenv("TEKK_REDIS_STREAM_ENABLED", "false")
    manager = ConnectionManager()
    queue = await manager.connect("test-user")

    assert await manager.redis_available() is False
    await manager.send_to_client("test-user", {"type": "progress", "value": 1})
    assert await queue.get() == {"type": "progress", "value": 1}

    manager.disconnect("test-user", queue)
    assert "test-user" not in manager.active_connections
