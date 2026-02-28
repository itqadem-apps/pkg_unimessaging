from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional


@dataclass
class MessagingConfig:
    backend: str = "nats"
    url: str = "nats://localhost:4222"
    name: Optional[str] = None
    enable_durable: bool = False
    stream_name: Optional[str] = None
    stream_subjects: Iterable[str] = field(default_factory=list)
    request_timeout: float = 2.0
    max_inflight: int = 64
    default_headers: Dict[str, str] = field(default_factory=dict)