"""Generic outbox event bus — serializes dataclass events into outbox rows.

Works with any dataclass event that has these attributes:

- ``aggregate_type`` (str)
- ``aggregate_id`` (UUID | None)
- ``event_id`` (UUID)
- ``occurred_at`` (datetime)

The bus satisfies service-specific ``EventBus`` protocols via structural
(duck) typing — no domain imports required::

    from unimessaging.outbox import OutboxEventBus, OutboxRepository

    outbox_repo = OutboxRepository(session, OutboxORM)
    bus = OutboxEventBus(outbox_repo)
    await bus.publish(MyDomainEvent(...))
"""

from __future__ import annotations

import dataclasses
from datetime import datetime
from enum import Enum
from typing import Any, Sequence
from uuid import UUID

from .repository import OutboxRepository


class OutboxEventBus:
    """Writes domain events to the outbox table via the repository.

    Parameters
    ----------
    outbox_repo:
        An ``OutboxRepository`` instance sharing the UoW's session.
    """

    def __init__(self, outbox_repo: OutboxRepository) -> None:
        self._outbox = outbox_repo

    async def publish(self, event) -> None:
        """Serialize a single dataclass event and write it to the outbox."""
        payload = _serialize(event)
        await self._outbox.add(
            aggregate_type=event.aggregate_type,
            aggregate_id=str(event.aggregate_id) if event.aggregate_id else "",
            event_type=type(event).__name__,
            payload=payload,
            headers={"event_id": str(event.event_id)},
            occurred_at=event.occurred_at,
        )

    async def publish_many(self, events: Sequence) -> None:
        """Serialize and write multiple events."""
        for event in events:
            await self.publish(event)


# ── Serialization helpers ────────────────────────────────────────────


def _serialize(event) -> dict[str, Any]:
    """Convert a dataclass event to a JSON-safe dict."""
    raw = dataclasses.asdict(event)
    return _convert_values(raw)


def _convert_values(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _convert_values(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_convert_values(item) for item in obj]
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    return obj
