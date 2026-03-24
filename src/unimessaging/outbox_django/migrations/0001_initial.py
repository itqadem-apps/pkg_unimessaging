import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="OutboxRecord",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("aggregate_type", models.TextField()),
                ("aggregate_id", models.TextField()),
                ("event_type", models.TextField()),
                ("payload", models.JSONField()),
                ("headers", models.JSONField(default=dict)),
                (
                    "status",
                    models.TextField(db_index=True, default="PENDING"),
                ),
                ("retries", models.IntegerField(default=0)),
                ("available_at", models.DateTimeField(auto_now_add=True)),
                ("occurred_at", models.DateTimeField()),
                (
                    "published_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                ("last_error", models.TextField(blank=True, null=True)),
            ],
            options={
                "db_table": "outbox",
            },
        ),
        migrations.AddIndex(
            model_name="outboxrecord",
            index=models.Index(
                condition=models.Q(("status", "PENDING")),
                fields=["available_at"],
                name="idx_outbox_pending",
            ),
        ),
    ]
