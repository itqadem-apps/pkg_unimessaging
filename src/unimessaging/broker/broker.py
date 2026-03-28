from __future__ import annotations

import asyncio
import inspect
import json
import logging
from typing import Callable, List, Optional

from .client import UnifiedMessaging
from .config import JetStreamConsumer
from .registry import HandlerRegistry, _default_registry
from .utils import create_messaging_client

logger = logging.getLogger(__name__)


class UnifiedMessageBroker:
    """Transport-agnostic messaging broker facade.

    Manages client lifecycle, subscribes to subjects, dispatches
    incoming messages to registered handlers via a ``HandlerRegistry``,
    and optionally runs JetStream durable pull consumers.
    """

    def __init__(
        self,
        *,
        subjects: Optional[List[str]] = None,
        service_name: str = "service",
        url: str = "nats://localhost:4222",
        enable_durable: bool = False,
        stream_name: Optional[str] = None,
        stream_subjects: Optional[List[str]] = None,
        consumers: Optional[List[JetStreamConsumer]] = None,
        pull_batch: int = 10,
        pull_timeout: float = 1.0,
        registry: Optional[HandlerRegistry] = None,
        client: Optional[UnifiedMessaging] = None,
    ) -> None:
        self.subjects = [s.strip() for s in (subjects or []) if s and s.strip()] or [
            "notifications.>"
        ]
        self.service_name = service_name
        self.registry = registry or _default_registry
        self._consumers = consumers or []
        self._pull_batch = pull_batch
        self._pull_timeout = pull_timeout
        self._consumer_tasks: List[asyncio.Task] = []
        self.client = client or create_messaging_client(
            service_name,
            url=url,
            enable_durable=enable_durable,
            stream_name=stream_name,
            stream_subjects=stream_subjects,
            consumers=self._consumers,
            pull_batch=pull_batch,
            pull_timeout=pull_timeout,
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

        # Start JetStream durable consumers
        for consumer in self._consumers:
            task = asyncio.create_task(self._run_consumer(consumer))
            self._consumer_tasks.append(task)
            logger.info(
                "JetStream %s consumer started (subject=%s, durable=%s)",
                consumer.label,
                consumer.subject,
                consumer.durable,
            )

        self._started = True

    async def stop(self) -> None:
        if not self._started:
            logger.info("Broker not running; skip stop.")
            return

        # Cancel consumer tasks first
        for task in self._consumer_tasks:
            task.cancel()
        for task in self._consumer_tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        if self._consumer_tasks:
            logger.info("JetStream consumers stopped")
        self._consumer_tasks.clear()

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

    # ── JetStream Consumer Runner ────────────────────────────────────

    async def _run_consumer(self, consumer: JetStreamConsumer) -> None:
        """Run a durable pull consumer with handler dispatch."""

        async def _on_message(data: bytes, meta: dict) -> None:
            subject = meta.get("subject", "")
            if not data:
                return
            try:
                payload = json.loads(data.decode())
            except Exception:
                logger.error(
                    "Invalid JSON on JetStream %s; dropping", subject
                )
                return
            handler = self.registry.resolve_handler(subject)
            if handler is None:
                logger.warning(
                    "No handler for JetStream subject %s", subject
                )
                return
            result = handler(payload, subject)
            if inspect.isawaitable(result):
                await result

        try:
            await self.client.pull_consume(
                subject=consumer.subject,
                durable=consumer.durable,
                handler=_on_message,
                batch=self._pull_batch,
                timeout=self._pull_timeout,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            message = str(exc).lower()
            if "stream" in message and (
                "not found" in message or "no response" in message
            ):
                logger.warning(
                    "JetStream %s consumer skipped; stream unavailable: %s",
                    consumer.label,
                    exc,
                )
                return
            raise

    # ── Core Message Handler ─────────────────────────────────────────

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