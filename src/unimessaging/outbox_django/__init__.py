"""Django transactional outbox for reliable domain event publishing.

Provides Django-native equivalents of the SQLAlchemy outbox infrastructure:

- ``OutboxRecord`` / ``OutboxStatus`` — Django model for the outbox table
- ``DjangoOutboxRepository`` — writes rows within the caller's transaction
- ``DjangoOutboxEventBus`` — sync event bus that serializes dataclass events
- ``DjangoOutboxRelay`` — polls and publishes to messaging (sync DB + async publish)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

default_app_config = "unimessaging.outbox_django.apps.OutboxDjangoConfig"

if TYPE_CHECKING:
    from .event_bus import DjangoOutboxEventBus
    from .models import OutboxRecord, OutboxStatus
    from .relay import DjangoOutboxRelay
    from .repository import DjangoOutboxRepository

__all__ = [
    "OutboxRecord",
    "OutboxStatus",
    "DjangoOutboxRepository",
    "DjangoOutboxEventBus",
    "DjangoOutboxRelay",
]


def __getattr__(name: str):
    if name in ("OutboxRecord", "OutboxStatus"):
        from .models import OutboxRecord, OutboxStatus

        return OutboxRecord if name == "OutboxRecord" else OutboxStatus
    if name == "DjangoOutboxRepository":
        from .repository import DjangoOutboxRepository

        return DjangoOutboxRepository
    if name == "DjangoOutboxEventBus":
        from .event_bus import DjangoOutboxEventBus

        return DjangoOutboxEventBus
    if name == "DjangoOutboxRelay":
        from .relay import DjangoOutboxRelay

        return DjangoOutboxRelay
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
