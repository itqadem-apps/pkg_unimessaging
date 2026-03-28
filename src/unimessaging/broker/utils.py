from __future__ import annotations

import os
import uuid
from typing import Dict, List, Optional

from .config import JetStreamConsumer, MessagingConfig


def create_messaging_client(
    service_name: str,
    *,
    url: Optional[str] = None,
    enable_durable: bool = False,
    stream_name: Optional[str] = None,
    stream_subjects: Optional[List[str]] = None,
    consumers: Optional[List[JetStreamConsumer]] = None,
    pull_batch: int = 10,
    pull_timeout: float = 1.0,
) -> "UnifiedMessaging":
    from .client import UnifiedMessaging

    cfg = MessagingConfig(
        backend="nats",
        url=url or os.getenv("NATS_URL", "nats://localhost:4222"),
        name=service_name,
        enable_durable=enable_durable,
        stream_name=stream_name,
        stream_subjects=list(stream_subjects or []),
        consumers=consumers or [],
        pull_batch=pull_batch,
        pull_timeout=pull_timeout,
        default_headers={"service": service_name},
    )
    return UnifiedMessaging(cfg)


def prepare_notification_payload(event_type: str, payload: dict) -> dict:
    return {"event": event_type, "payload": payload}


def build_notification_headers(service_name: str) -> Dict[str, str]:
    return {"trace_id": str(uuid.uuid4()), "service": service_name}