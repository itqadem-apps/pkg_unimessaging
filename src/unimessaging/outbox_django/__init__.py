"""Django transactional outbox for reliable domain event publishing.

Provides Django-native equivalents of the SQLAlchemy outbox infrastructure:

- ``OutboxRecord`` / ``OutboxStatus`` — Django model for the outbox table
- ``DjangoOutboxRepository`` — writes rows within the caller's transaction
- ``DjangoOutboxEventBus`` — sync event bus that serializes dataclass events
- ``DjangoOutboxRelay`` — polls and publishes to messaging (sync DB + async publish)
"""

from .models import OutboxRecord, OutboxStatus
from .repository import DjangoOutboxRepository
from .event_bus import DjangoOutboxEventBus
from .relay import DjangoOutboxRelay

__all__ = [
    "OutboxRecord",
    "OutboxStatus",
    "DjangoOutboxRepository",
    "DjangoOutboxEventBus",
    "DjangoOutboxRelay",
]
