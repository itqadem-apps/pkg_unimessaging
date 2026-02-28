from __future__ import annotations

import json
import logging
from typing import Callable, List, Optional

from .client import UnifiedMessaging
from .registry import HandlerRegistry, _default_registry
from .utils import create_messaging_client

logger = logging.getLogger(__name__)


class UnifiedMessageBroker:
    """Transport-agnostic messaging broker facade.

    Manages client lifecycle, subscribes to subjects, and dispatches
    incoming messages to registered handlers via a ``HandlerRegistry``.

    Unlike the original itq_articles implementation this class is **not**
    a singleton — the caller controls instantiation and lifetime.
    """

    def __init__(
        self,
        *,
        subjects: Optional[List[str]] = None,
        service_name: str = "service",
        url: str = "nats://localhost:4222",
        enable_durable: bool = False,
        registry: Optional[HandlerRegistry] = None,
        client: Optional[UnifiedMessaging] = None,
    ) -> None:
        self.subjects = [s.strip() for s in (subjects or []) if s and s.strip()] or [
            "notifications.>"
        ]
        self.service_name = service_name
        self.registry = registry or _default_registry
        self.client = client or create_messaging_client(
            service_name, url=url, enable_durable=enable_durable
        )
        self._started = False

    async def start(self) -> None:
        if self._started:
            logger.info("Broker already running; skip start.")
            return
        if not self.subjects:
            logger.info("No subjects configured; listener disabled.")
            self._started = True
            return

        await self.client.start()
        for subject in self.subjects:
            await self.client.subscribe(subject, self._on_message)
            logger.info("Subscribed to '%s'", subject)
        self._started = True

    async def stop(self) -> None:
        if not self._started:
            logger.info("Broker not running; skip stop.")
            return
        await self.client.stop()
        self._started = False

    async def publish(self, subject: str, message: dict) -> None:
        if not self._started:
            raise RuntimeError("Broker.publish called before start().")
        logger.debug("Publish -> %s: %s", subject, message)
        await self.client.publish(subject, message)

    async def reply(self, subject: str, handler: Callable) -> None:
        async def _on_req(data: bytes, meta: dict) -> None:
            try:
                payload = json.loads(data.decode()) if data else None
            except Exception:
                payload = data
            return await handler(payload, meta)

        await self.client.reply(subject, _on_req)

    async def _on_message(self, data: bytes, meta: dict) -> None:
        subject = meta.get("subject", "")
        if not data:
            logger.debug("Skip empty payload on %s", subject)
            return
        try:
            text = data.decode()
        except UnicodeDecodeError:
            logger.error("Non-UTF8 payload on %s; dropping.", subject)
            return
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            logger.error("Invalid JSON on %s: %s", subject, text)
            return

        handler = self.registry.resolve_handler(subject)
        if handler is None:
            logger.debug("No handler for subject %s; ignoring.", subject)
            return
        try:
            result = handler(payload, subject)
            if callable(getattr(result, "__await__", None)):
                await result
        except Exception as exc:
            logger.error("Handler error for %s: %s", subject, exc)
