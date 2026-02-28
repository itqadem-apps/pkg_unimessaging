from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional, Tuple

from unimessaging.broker.config import MessagingConfig


class InMemoryBrokerAdapter:
    """In-memory async broker adapter for testing.

    Stores published messages and dispatches to subscribers synchronously
    within ``publish()`` for deterministic integration tests.
    """

    def __init__(self, cfg: Optional[MessagingConfig] = None) -> None:
        self.cfg = cfg or MessagingConfig(backend="memory")
        self._subscribers: List[Tuple[str, Callable]] = []
        self._published: List[Tuple[str, bytes, Dict[str, str]]] = []
        self._started = False

    async def start(self) -> None:
        self._started = True

    async def stop(self) -> None:
        self._started = False
        self._subscribers.clear()

    async def publish(
        self, subject: str, data: Any = None, headers: Optional[Dict[str, str]] = None
    ) -> None:
        payload = data if isinstance(data, bytes) else (b"" if data is None else __import__("json").dumps(data).encode())
        hdrs = dict(self.cfg.default_headers)
        if headers:
            hdrs.update(headers)
        self._published.append((subject, payload, hdrs))
        for pattern, handler in self._subscribers:
            if self._match(pattern, subject):
                meta = {"subject": subject, "headers": hdrs}
                await handler(payload, meta)

    async def subscribe(
        self,
        subject: str,
        handler: Callable,
        queue: Optional[str] = None,
    ) -> int:
        self._subscribers.append((subject, handler))
        return len(self._subscribers) - 1

    async def request(
        self,
        subject: str,
        data: Any = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("request() not supported in InMemoryBrokerAdapter")

    async def reply(
        self, subject: str, fn: Callable, queue: Optional[str] = None
    ) -> int:
        raise NotImplementedError("reply() not supported in InMemoryBrokerAdapter")

    @staticmethod
    def _match(pattern: str, subject: str) -> bool:
        """NATS-style wildcard matching: ``*`` = one token, ``>`` = one or more tokens."""
        pat_parts = pattern.split(".")
        sub_parts = subject.split(".")
        for i, p in enumerate(pat_parts):
            if p == ">":
                return i < len(sub_parts)
            if i >= len(sub_parts):
                return False
            if p != "*" and p != sub_parts[i]:
                return False
        return len(pat_parts) == len(sub_parts)