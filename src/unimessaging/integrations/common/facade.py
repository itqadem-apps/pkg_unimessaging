from __future__ import annotations

from functools import lru_cache
from typing import Optional

from unimessaging.application.dto import SendMessageRequest
from unimessaging.application.use_cases import SendMessageUseCase
from unimessaging.domain.ports import NotificationGateway
from unimessaging.adapters import InMemoryNotificationGateway


def _build_use_case(gateway: Optional[NotificationGateway] = None) -> SendMessageUseCase:
    return SendMessageUseCase(gateway or InMemoryNotificationGateway())


@lru_cache(maxsize=1)
def _default_use_case() -> SendMessageUseCase:
    return _build_use_case()


def send_message(message: str, recipient: Optional[str] = None, *, gateway: Optional[NotificationGateway] = None) -> dict:
    """Public API used by tests; orchestrates the send message use case."""

    if recipient is None:
        raise ValueError("recipient is required")

    use_case = _build_use_case(gateway) if gateway else _default_use_case()
    response = use_case.execute(SendMessageRequest(message=message, recipient=recipient))
    return {"status": response.status, "payload": response.payload}
