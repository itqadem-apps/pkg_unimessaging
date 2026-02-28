from __future__ import annotations

import os
import uuid
from typing import Dict, Optional

from .config import MessagingConfig


def create_messaging_client(
    service_name: str,
    *,
    url: Optional[str] = None,
    enable_durable: bool = False,
) -> "UnifiedMessaging":
    from .client import UnifiedMessaging

    cfg = MessagingConfig(
        backend="nats",
        url=url or os.getenv("NATS_URL", "nats://localhost:4222"),
        name=service_name,
        enable_durable=enable_durable,
        default_headers={"service": service_name},
    )
    return UnifiedMessaging(cfg)


def prepare_notification_payload(event_type: str, payload: dict) -> dict:
    return {"event": event_type, "payload": payload}


def build_notification_headers(service_name: str) -> Dict[str, str]:
    return {"trace_id": str(uuid.uuid4()), "service": service_name}