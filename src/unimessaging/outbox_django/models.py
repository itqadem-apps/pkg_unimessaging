"""Django ORM model for the outbox table.

Services add ``"unimessaging.outbox_django"`` to ``INSTALLED_APPS`` and
run ``manage.py migrate`` to create the table::

    INSTALLED_APPS = [
        ...,
        "unimessaging.outbox_django",
    ]
"""

from __future__ import annotations

import uuid

try:
    from django.db import models
except ImportError as _exc:  # pragma: no cover
    raise ImportError(
        "Django is required for the outbox_django module. "
        "Install it with: pip install unimessaging[django]"
    ) from _exc


class OutboxStatus(models.TextChoices):
    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class OutboxRecord(models.Model):
    """Outbox row — same schema as the SQLAlchemy ``OutboxMixin``."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    aggregate_type = models.TextField()
    aggregate_id = models.TextField()
    event_type = models.TextField()
    payload = models.JSONField()
    headers = models.JSONField(default=dict)
    status = models.TextField(default=OutboxStatus.PENDING, db_index=True)
    retries = models.IntegerField(default=0)
    available_at = models.DateTimeField(auto_now_add=True)
    occurred_at = models.DateTimeField()
    published_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(null=True, blank=True)

    class Meta:
        app_label = "unimessaging"
        db_table = "outbox"
        indexes = [
            models.Index(
                fields=["available_at"],
                condition=models.Q(status="PENDING"),
                name="idx_outbox_pending",
            ),
        ]