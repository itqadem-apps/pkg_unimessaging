"""Outbox repository — writes event rows within the caller's transaction.

The repository receives the SQLAlchemy session from the service's Unit of Work
so the outbox INSERT shares the same transaction as the domain write::

    from unimessaging.outbox import OutboxRepository

    outbox_repo = OutboxRepository(session, OutboxORM)
    await outbox_repo.add(
        aggregate_type="event",
        aggregate_id="...",
        event_type="EventCreated",
        payload={...},
        headers={},
        occurred_at=datetime.now(timezone.utc),
    )
"""

from __future__ import annotations

from datetime import datetime

try:
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError as _exc:  # pragma: no cover
    raise ImportError(
        "SQLAlchemy is required for the outbox repository. "
        "Install it with: pip install unimessaging[outbox]"
    ) from _exc


class OutboxRepository:
    """Writes outbox rows using the provided session and ORM model class.

    Parameters
    ----------
    session:
        The async SQLAlchemy session (shared with the service's UoW).
    model_class:
        The concrete ORM class inheriting from ``OutboxMixin`` + ``Base``.
    """

    def __init__(self, session: AsyncSession, model_class) -> None:
        self._session = session
        self._model = model_class

    async def add(
        self,
        *,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict,
        headers: dict | None = None,
        occurred_at: datetime,
    ) -> None:
        self._session.add(
            self._model(
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                event_type=event_type,
                payload=payload,
                headers=headers or {},
                occurred_at=occurred_at,
            )
        )
        await self._session.flush()