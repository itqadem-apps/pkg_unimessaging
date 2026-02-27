from __future__ import annotations

from unimessaging.domain.entities import Message
from unimessaging.domain.ports import NotificationGateway


class InMemoryNotificationGateway(NotificationGateway):
    """Simple gateway that echoes payload (useful for tests or demos)."""

    def deliver(self, message: Message) -> dict:
        return message.to_dict()
