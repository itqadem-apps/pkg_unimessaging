"""Transactional outbox for reliable domain event publishing.

Provides the full outbox infrastructure:

- ``OutboxMixin`` / ``OutboxStatus`` — table schema (mixin for your Base)
- ``OutboxRepository`` — writes rows within the caller's transaction
- ``OutboxEventBus`` — serializes dataclass events into outbox rows
- ``OutboxRelay`` / ``relay_loop`` — polls and publishes to messaging
"""

from .models import OutboxMixin, OutboxStatus
from .repository import OutboxRepository
from .event_bus import OutboxEventBus
from .relay import OutboxRelay, relay_loop

__all__ = [
    "OutboxMixin",
    "OutboxStatus",
    "OutboxRepository",
    "OutboxEventBus",
    "OutboxRelay",
    "relay_loop",
]
