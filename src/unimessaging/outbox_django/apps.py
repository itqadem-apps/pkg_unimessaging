"""Django AppConfig for the outbox_django module."""

from django.apps import AppConfig


class OutboxDjangoConfig(AppConfig):
    name = "unimessaging.outbox_django"
    label = "unimessaging"
    verbose_name = "Unimessaging Outbox"
    default_auto_field = "django.db.models.BigAutoField"
