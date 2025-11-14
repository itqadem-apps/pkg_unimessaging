"""FastAPI demo wiring unimessaging to NATS with a simple listener."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import warnings
from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("unimessaging.examples.fastapi")

# Allow running the example without installing the package beforehand.
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from unimessaging import send_message
from unimessaging.infrastructure import (  # noqa: E402
    InMemoryNotificationGateway,
    NATSConfig,
    NATSNotificationGateway,
)

app = FastAPI(title="Unimessaging Demo")
app.state.received_messages: List[Dict[str, Any]] = []

gateway_config: Optional[NATSConfig] = NATSConfig(
    url=os.getenv("NATS_URL", "nats://localhost:4222"),
    subject=os.getenv("NATS_SUBJECT", "notifications.demo"),
    client_name=os.getenv("SERVICE_NAME", "unimessaging-fastapi"),
    flush_timeout=2.0,
)

try:
    gateway = NATSNotificationGateway(gateway_config)
    USING_NATS = True
except RuntimeError as exc:
    warnings.warn(
        "Falling back to InMemoryNotificationGateway because NATS is unavailable. "
        "Install unimessaging[nats] and ensure a NATS server is running to enable real publishing. "
        f"Original error: {exc}",
        RuntimeWarning,
    )
    gateway = InMemoryNotificationGateway()
    gateway_config = None
    USING_NATS = False


class NotificationPayload(BaseModel):
    message: str
    recipient: str


@app.get("/health")
async def healthcheck():
    return {"status": "ok"}


@app.post("/notifications")
def create_notification(payload: NotificationPayload):
    """Invoke the clean-architecture use case via the public facade."""

    result = send_message(payload.message, payload.recipient, gateway=gateway)
    return result


@app.get("/notifications/received")
def received_notifications():
    """Return messages captured by the NATS listener (if enabled)."""

    return {
        "count": len(app.state.received_messages),
        "items": app.state.received_messages,
    }


@app.on_event("startup")
async def start_listener():
    if not USING_NATS or gateway_config is None:
        logger.warning("Listener disabled: running without NATS gateway.")
        return
    stop_event = asyncio.Event()
    task = asyncio.create_task(_listen_for_notifications(stop_event, gateway_config))
    app.state.listener_stop_event = stop_event
    app.state.listener_task = task
    logger.info("NATS listener started for subject %s", gateway_config.subject)


@app.on_event("shutdown")
async def stop_listener():
    stop_event = getattr(app.state, "listener_stop_event", None)
    task = getattr(app.state, "listener_task", None)
    if stop_event and not stop_event.is_set():
        stop_event.set()
    if task:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        logger.info("NATS listener stopped")


async def _listen_for_notifications(stop_event: asyncio.Event, config: NATSConfig):
    from nats.aio.client import Client as NATS  # Imported lazily

    nc = NATS()
    await nc.connect(config.url, name=f"{config.client_name}-listener")

    async def _on_msg(msg):
        try:
            payload = json.loads(msg.data.decode("utf-8"))
        except json.JSONDecodeError:
            payload = {"raw": msg.data.decode("utf-8", errors="ignore")}
        payload["subject"] = msg.subject
        app.state.received_messages.append(payload)
        logger.info("Listener received message on %s: %s", msg.subject, payload)

    sid = await nc.subscribe(config.subject, cb=_on_msg)
    try:
        await stop_event.wait()
    finally:
        await nc.unsubscribe(sid)
        await nc.drain()
        await nc.close()
