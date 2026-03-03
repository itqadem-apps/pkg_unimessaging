"""Outbox table schema as a SQLAlchemy mixin.

Services create their own ORM class by inheriting from this mixin
and their declarative ``Base``::

    from unimessaging.outbox import OutboxMixin
    from .base import Base

    class OutboxORM(OutboxMixin, Base):
        pass

Alembic will then pick up the table via ``--autogenerate``.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

try:
    from sqlalchemy import text
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy.orm import Mapped, mapped_column
except ImportError as _exc:  # pragma: no cover
    raise ImportError(
        "SQLAlchemy is required for the outbox models. "
        "Install it with: pip install unimessaging[outbox]"
    ) from _exc


class OutboxStatus(str, Enum):
    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class OutboxMixin:
    """Mixin providing all outbox table columns.

    Inherit together with your project's declarative ``Base`` to create
    the concrete ORM model.
    """

    __tablename__ = "outbox"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    aggregate_type: Mapped[str]
    aggregate_id: Mapped[str]
    event_type: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSONB)
    headers: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(default=OutboxStatus.PENDING.value)
    retries: Mapped[int] = mapped_column(default=0)
    available_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    occurred_at: Mapped[datetime]
    published_at: Mapped[datetime | None]
    last_error: Mapped[str | None]