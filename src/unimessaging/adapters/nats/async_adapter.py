from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional

from unimessaging.broker.config import MessagingConfig

try:
    from nats.aio.client import Client as NATS
    from nats.errors import TimeoutError as NATSTimeout
except ModuleNotFoundError as _exc:
    NATS = None  # type: ignore[assignment,misc]
    NATSTimeout = None  # type: ignore[assignment,misc]
    _IMPORT_ERROR = _exc
else:
    _IMPORT_ERROR = None

logger = logging.getLogger("unimessaging.nats")

MessageHandler = Callable[[bytes, Dict[str, Any]], Awaitable[None]]


class NATSAdapter:
    """Production-grade async NATS adapter with reconnection and JetStream."""

    def __init__(self, cfg: MessagingConfig) -> None:
        if NATS is None:
            raise RuntimeError(
                "nats-py is required. Install via: pip install unimessaging[nats]"
            ) from _IMPORT_ERROR
        self.cfg = cfg
        self.nc: Optional[NATS] = None
        self.js: Any = None
        self._subs: List[Any] = []

    # ── Lifecycle ────────────────────────────────────────────────────

    async def start(self) -> None:
        self.nc = NATS()
        logger.info(
            "NATS connecting: service=%s url=%s durable=%s "
            "max_reconnect=%s reconnect_wait=%s",
            self.cfg.name,
            self.cfg.url,
            self.cfg.enable_durable,
            self.cfg.max_reconnect_attempts,
            self.cfg.reconnect_time_wait,
        )
        await self.nc.connect(
            self.cfg.url,
            name=self.cfg.name,
            max_reconnect_attempts=self.cfg.max_reconnect_attempts,
            reconnect_time_wait=self.cfg.reconnect_time_wait,
            disconnected_cb=self._on_disconnected,
            reconnected_cb=self._on_reconnected,
            closed_cb=self._on_closed,
            error_cb=self._on_error,
        )
        if self.cfg.enable_durable:
            self.js = self.nc.jetstream()
            if self.cfg.stream_name and self.cfg.stream_subjects:
                try:
                    await self.js.add_stream(
                        name=self.cfg.stream_name,
                        subjects=list(self.cfg.stream_subjects),
                    )
                    logger.info(
                        "JetStream stream ensured: stream=%s subjects=%s",
                        self.cfg.stream_name,
                        list(self.cfg.stream_subjects),
                    )
                except Exception as exc:
                    logger.debug(
                        "JetStream stream ensure skipped: stream=%s err=%s",
                        self.cfg.stream_name,
                        exc,
                    )
        logger.info(
            "NATS connected: service=%s js=%s",
            self.cfg.name,
            bool(self.js),
        )

    async def stop(self) -> None:
        if self.nc:
            logger.info("NATS stopping: service=%s", self.cfg.name)
            await self.nc.drain()
            logger.info("NATS stopped: service=%s", self.cfg.name)

    # ── Pub/Sub ──────────────────────────────────────────────────────

    async def publish(
        self, subject: str, data: Any = None, headers: Optional[Dict[str, str]] = None
    ) -> None:
        payload = self._to_bytes(data)
        hdrs = self._headers(headers)
        logger.debug(
            "NATS publish: subject=%s bytes=%d js=%s",
            subject,
            len(payload),
            bool(self.js),
        )
        if self.js:
            await self.js.publish(subject, payload, headers=hdrs)
        else:
            await self.nc.publish(subject, payload, headers=hdrs)

    async def subscribe(
        self,
        subject: str,
        handler: MessageHandler,
        queue: Optional[str] = None,
    ) -> Any:
        async def _on_msg(msg: Any) -> None:
            meta = {"subject": msg.subject, "headers": dict(msg.headers or {})}
            logger.debug(
                "NATS recv: subject=%s bytes=%d",
                msg.subject,
                len(msg.data or b""),
            )
            await handler(msg.data, meta)

        sid = await self.nc.subscribe(subject, queue=queue, cb=_on_msg)
        self._subs.append(sid)
        logger.info("NATS subscribed: subject=%s queue=%s", subject, queue)
        return sid

    # ── Request / Reply ──────────────────────────────────────────────

    async def request(
        self,
        subject: str,
        data: Any = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        payload = self._to_bytes(data)
        wait_timeout = timeout or self.cfg.request_timeout
        logger.debug(
            "NATS request: subject=%s bytes=%d timeout=%s",
            subject,
            len(payload),
            wait_timeout,
        )
        try:
            msg = await self.nc.request(
                subject,
                payload,
                wait_timeout,
                headers=self._headers(headers),
            )
            logger.debug(
                "NATS reply: subject=%s bytes=%d",
                msg.subject,
                len(msg.data or b""),
            )
            return {
                "data": msg.data,
                "headers": dict(msg.headers or {}),
                "subject": msg.subject,
            }
        except NATSTimeout as exc:
            logger.warning("NATS request timeout: subject=%s err=%s", subject, exc)
            raise TimeoutError(str(exc)) from exc

    async def reply(
        self, subject: str, fn: Callable, queue: Optional[str] = None
    ) -> Any:
        async def _on_req(msg: Any) -> None:
            try:
                logger.debug(
                    "NATS serve: subject=%s bytes=%d",
                    msg.subject,
                    len(msg.data or b""),
                )
                res = await fn(msg.data, {"subject": msg.subject})
                if msg.reply:
                    out = self._to_bytes(res)
                    await self.nc.publish(msg.reply, out)
            except Exception as exc:
                logger.exception(
                    "NATS reply handler failed: subject=%s err=%s",
                    msg.subject,
                    exc,
                )

        sid = await self.nc.subscribe(subject, queue=queue, cb=_on_req)
        self._subs.append(sid)
        logger.info("NATS replier started: subject=%s queue=%s", subject, queue)
        return sid

    # ── Scatter / Gather ─────────────────────────────────────────────

    async def scatter_gather(
        self,
        subject: str,
        data: Any,
        window: float = 0.3,
        headers: Optional[Dict[str, str]] = None,
        max_msgs: Optional[int] = None,
    ) -> List[bytes]:
        inbox = await self.nc.new_inbox()
        results: List[bytes] = []
        done = asyncio.Event()

        async def on_reply(msg: Any) -> None:
            results.append(msg.data)
            if max_msgs and len(results) >= max_msgs:
                done.set()

        sid = await self.nc.subscribe(inbox, cb=on_reply)
        logger.debug(
            "NATS scatter: subject=%s window=%s max_msgs=%s",
            subject,
            window,
            max_msgs,
        )
        await self.nc.publish(
            subject, self._to_bytes(data), reply=inbox, headers=self._headers(headers)
        )
        try:
            await asyncio.wait_for(done.wait(), timeout=window)
        except asyncio.TimeoutError:
            pass
        await self.nc.unsubscribe(sid)
        logger.debug(
            "NATS scatter done: subject=%s replies=%d",
            subject,
            len(results),
        )
        return results

    # ── JetStream Pull Consumer ──────────────────────────────────────

    async def pull_consume(
        self,
        subject: str,
        durable: str,
        handler: MessageHandler,
        batch: int = 10,
        timeout: float = 1.0,
    ) -> None:
        if not self.js:
            raise RuntimeError("JetStream not enabled")
        while True:
            try:
                sub = await self.js.pull_subscribe(subject, durable=durable)
                logger.info(
                    "JetStream consumer bound: subject=%s durable=%s batch=%d",
                    subject,
                    durable,
                    batch,
                )
                while True:
                    try:
                        msgs = await sub.fetch(batch, timeout=timeout)
                    except NATSTimeout:
                        continue
                    for msg in msgs:
                        try:
                            logger.debug(
                                "JetStream recv: subject=%s durable=%s bytes=%d",
                                msg.subject,
                                durable,
                                len(msg.data or b""),
                            )
                            await handler(msg.data, {"subject": msg.subject})
                            await msg.ack()
                        except Exception:
                            logger.warning(
                                "JetStream nak: subject=%s durable=%s",
                                msg.subject,
                                durable,
                            )
                            await msg.nak()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning(
                    "JetStream consumer reset: subject=%s durable=%s err=%s",
                    subject,
                    durable,
                    exc,
                )
                await asyncio.sleep(self.cfg.pull_consumer_retry_delay)

    # ── Connection Lifecycle Callbacks ───────────────────────────────

    async def _on_disconnected(self) -> None:
        logger.warning("NATS disconnected: service=%s", self.cfg.name)

    async def _on_reconnected(self) -> None:
        logger.info("NATS reconnected: service=%s", self.cfg.name)

    async def _on_closed(self) -> None:
        logger.warning("NATS closed: service=%s", self.cfg.name)

    async def _on_error(self, exc: Exception) -> None:
        logger.warning("NATS error: service=%s err=%s", self.cfg.name, exc)

    # ── Helpers ──────────────────────────────────────────────────────

    def _to_bytes(self, data: Any) -> bytes:
        if data is None:
            return b""
        if isinstance(data, bytes):
            return data
        return json.dumps(data).encode()

    def _headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        out = dict(self.cfg.default_headers)
        if headers:
            out.update(headers)
        return out
