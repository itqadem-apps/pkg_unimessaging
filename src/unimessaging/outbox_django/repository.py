"""Django outbox repository — writes event rows within the caller's transaction.

The repository is used inside ``transaction.atomic()`` so the outbox INSERT
shares the same transaction as the domain write::

    from django.db import transaction
    from unimessaging.outbox_django import DjangoOutboxRepository

    repo = DjangoOutboxRepository()
    with transaction.atomic():
        my_model.save()
        repo.add(
            aggregate_type="reservation",
            aggregate_id="...",
            event_type="ReservationCreated",
            payload={...},
            occurred_at=datetime.now(timezone.utc),
        )
"""

from __future__ import annotations

from datetime import datetime

from .models import OutboxRecord


class DjangoOutboxRepository:
    """Writes outbox rows using Django ORM within the caller's transaction."""

    def add(
        self,
        *,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict,
        headers: dict | None = None,
        occurred_at: datetime,
    ) -> None:
        OutboxRecord.objects.create(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=payload,
            headers=headers or {},
            occurred_at=occurred_at,
        )