from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SendMessageRequest:
    message: str
    recipient: str


@dataclass(frozen=True)
class SendMessageResponse:
    status: str
    payload: dict
