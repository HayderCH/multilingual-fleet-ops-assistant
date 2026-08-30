from __future__ import annotations

import json
import time
from typing import Protocol

from redis.asyncio import Redis

from .models import SessionState


class SessionStore(Protocol):
    async def get(self, conversation_id: str) -> SessionState: ...

    async def set(self, conversation_id: str, state: SessionState) -> None: ...

    async def delete(self, conversation_id: str) -> None: ...


class MemorySessionStore:
    def __init__(self, ttl_seconds: int = 1800) -> None:
        self.ttl_seconds = ttl_seconds
        self._values: dict[str, tuple[float, SessionState]] = {}

    async def get(self, conversation_id: str) -> SessionState:
        value = self._values.get(conversation_id)
        if not value or value[0] < time.monotonic():
            self._values.pop(conversation_id, None)
            return SessionState()
        return value[1].model_copy(deep=True)

    async def set(self, conversation_id: str, state: SessionState) -> None:
        self._values[conversation_id] = (
            time.monotonic() + self.ttl_seconds,
            state.model_copy(deep=True),
        )

    async def delete(self, conversation_id: str) -> None:
        self._values.pop(conversation_id, None)


class RedisSessionStore:
    def __init__(self, url: str, ttl_seconds: int = 1800) -> None:
        self.redis = Redis.from_url(url, decode_responses=True)
        self.ttl_seconds = ttl_seconds

    def _key(self, conversation_id: str) -> str:
        return f"fleet-assistant:session:{conversation_id}"

    async def get(self, conversation_id: str) -> SessionState:
        raw = await self.redis.get(self._key(conversation_id))
        return SessionState.model_validate_json(raw) if raw else SessionState()

    async def set(self, conversation_id: str, state: SessionState) -> None:
        await self.redis.set(
            self._key(conversation_id),
            json.dumps(state.model_dump()),
            ex=self.ttl_seconds,
        )

    async def delete(self, conversation_id: str) -> None:
        await self.redis.delete(self._key(conversation_id))
