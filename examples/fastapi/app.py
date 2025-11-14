"""Minimal FastAPI project demonstrating how to use unimessaging."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import warnings

from fastapi import FastAPI
from pydantic import BaseModel

# Allow running the example without installing the package beforehand.
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from unimessaging import send_message
from unimessaging.infrastructure import (
    InMemoryNotificationGateway,
    NATSConfig,
    NATSNotificationGateway,
)


app = FastAPI(title="Unimessaging Demo")

# try:
gateway = NATSNotificationGateway(
    NATSConfig(
        url=os.getenv("NATS_URL", "nats://localhost:4222"),
        subject=os.getenv("NATS_SUBJECT", "notifications.demo"),
        client_name=os.getenv("SERVICE_NAME", "unimessaging-fastapi"),
    )
)
# except RuntimeError as exc:
#     warnings.warn(
#         "Falling back to InMemoryNotificationGateway because NATS is unavailable. "
#         "Install unimessaging[nats] and ensure a NATS server is running to enable real publishing. "
#         f"Original error: {exc}",
#         RuntimeWarning,
#     )
#     gateway = InMemoryNotificationGateway()


class NotificationPayload(BaseModel):
    message: str
    recipient: str


@app.get("/health")
async def healthcheck():
    return {"status": "ok"}


@app.post("/notifications")
def create_notification(payload: NotificationPayload):
    """Invoke the clean-architecture use case via the public facade."""

    return send_message(payload.message, payload.recipient, gateway=gateway)
