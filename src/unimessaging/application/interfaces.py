from __future__ import annotations

from typing import Protocol

from unimessaging.domain import Message


class NotificationGateway(Protocol):
    """Gateway abstraction implemented by infrastructure adapters."""

    def deliver(self, message: Message) -> dict:
        """Send the message to the infrastructure channel and return payload metadata."""
        raise NotImplementedError
