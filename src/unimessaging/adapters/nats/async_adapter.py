from __future__ import annotations

import asyncio
import json
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

MessageHandler = Callable[[bytes, Dict[str, Any]], Awaitable[None]]


class NATSAdapter:
    """Full async NATS adapter with persistent connection for pub/sub."""

    def __init__(self, cfg: MessagingConfig) -> None:
        if NATS is None:
            raise RuntimeError(
                "nats-py is required. Install via: pip install unimessaging[nats]"
            ) from _IMPORT_ERROR
        self.cfg = cfg
        self.nc: Optional[NATS] = None
        self.js: Any = None
        self._subs: List[Any] = []

    async def start(self) -> None:
        self.nc = NATS()
        await self.nc.connect(self.cfg.url, name=self.cfg.name)
        if self.cfg.enable_durable:
            self.js = self.nc.jetstream()
            if self.cfg.stream_name and self.cfg.stream_subjects:
                try:
                    await self.js.add_stream(
                        name=self.cfg.stream_name,
                        subjects=list(self.cfg.stream_subjects),
                    )
                except Exception:
                    pass

    async def stop(self) -> None:
        if self.nc:
            await self.nc.drain()

    async def publish(
        self, subject: str, data: Any = None, headers: Optional[Dict[str, str]] = None
    ) -> None:
        payload = self._to_bytes(data)
        hdrs = self._headers(headers)
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
            await handler(msg.data, meta)

        sid = await self.nc.subscribe(subject, queue=queue, cb=_on_msg)
        self._subs.append(sid)
        return sid

    async def request(
        self,
        subject: str,
        data: Any = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        try:
            msg = await self.nc.request(
                subject,
                self._to_bytes(data),
                timeout or self.cfg.request_timeout,
                headers=self._headers(headers),
            )
            return {
                "data": msg.data,
                "headers": dict(msg.headers or {}),
                "subject": msg.subject,
            }
        except NATSTimeout as e:
            raise TimeoutError(str(e)) from e

    async def reply(
        self, subject: str, fn: Callable, queue: Optional[str] = None
    ) -> Any:
        async def _on_req(msg: Any) -> None:
            try:
                res = await fn(msg.data, {"subject": msg.subject})
                if msg.reply:
                    await self.nc.publish(msg.reply, self._to_bytes(res))
            except Exception:
                pass

        sid = await self.nc.subscribe(subject, queue=queue, cb=_on_req)
        self._subs.append(sid)
        return sid

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
        await self.nc.publish(
            subject, self._to_bytes(data), reply=inbox, headers=self._headers(headers)
        )
        try:
            await asyncio.wait_for(done.wait(), timeout=window)
        except asyncio.TimeoutError:
            pass
        await self.nc.unsubscribe(sid)
        return results

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
        sub = await self.js.pull_subscribe(subject, durable=durable)
        while True:
            try:
                msgs = await sub.fetch(batch, timeout=timeout)
            except NATSTimeout:
                msgs = []
            for m in msgs:
                try:
                    await handler(m.data, {"subject": m.subject})
                    await m.ack()
                except Exception:
                    await m.nak()

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