"""Synchronous event bus for Django services.

Reuses the serialization helpers from the generic ``outbox.event_bus`` module
so event conversion logic is never duplicated::

    from django.db import transaction
    from unimessaging.outbox_django import DjangoOutboxRepository, DjangoOutboxEventBus

    repo = DjangoOutboxRepository()
    bus = DjangoOutboxEventBus(repo)

    with transaction.atomic():
        reservation.save()
        bus.publish(ReservationCreated(...))
"""

from __future__ import annotations

from typing import Sequence

from ..outbox.event_bus import _serialize
from .repository import DjangoOutboxRepository


class DjangoOutboxEventBus:
    """Writes domain events to the outbox table via the Django repository.

    Parameters
    ----------
    outbox_repo:
        A ``DjangoOutboxRepository`` instance.
    """

    def __init__(self, outbox_repo: DjangoOutboxRepository) -> None:
        self._outbox = outbox_repo

    def publish(self, event) -> None:
        """Serialize a single dataclass event and write it to the outbox."""
        payload = _serialize(event)
        self._outbox.add(
            aggregate_type=event.aggregate_type,
            aggregate_id=str(event.aggregate_id) if event.aggregate_id else "",
            event_type=type(event).__name__,
            payload=payload,
            headers={"event_id": str(event.event_id)},
            occurred_at=event.occurred_at,
        )

    def publish_many(self, events: Sequence) -> None:
        """Serialize and write multiple events."""
        for event in events:
            self.publish(event)