"""Management command that runs the outbox relay as a long-lived process.

Usage::

    python manage.py outbox_relay --subject-prefix reservations
    python manage.py outbox_relay --subject-prefix reservations --nats-url nats://nats:4222 --poll-interval 1.0
"""

from __future__ import annotations

import asyncio
import signal
import time

from django.core.management.base import BaseCommand

from unimessaging.integrations.django import get_messaging, start_messaging, stop_messaging
from unimessaging.outbox_django import DjangoOutboxRelay


class Command(BaseCommand):
    help = "Run the outbox relay (polls outbox table and publishes to NATS)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--subject-prefix",
            required=True,
            help='Prefix for NATS subjects (e.g. "reservations" -> "reservations.slot")',
        )
        parser.add_argument(
            "--nats-url",
            default="nats://localhost:4222",
            help="NATS server URL (default: nats://localhost:4222)",
        )
        parser.add_argument(
            "--service-name",
            default="django-service",
            help="Service name for the messaging broker (default: django-service)",
        )
        parser.add_argument(
            "--poll-interval",
            type=float,
            default=0.5,
            help="Seconds to sleep when no pending rows found (default: 0.5)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Max rows to process per batch (default: 50)",
        )

    def handle(self, **options):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(
            start_messaging(
                subjects=[],
                service_name=options["service_name"],
                url=options["nats_url"],
            )
        )

        messaging = get_messaging()
        relay = DjangoOutboxRelay(
            messaging,
            subject_prefix=options["subject_prefix"],
        )

        running = True

        def _stop(sig, frame):
            nonlocal running
            running = False

        signal.signal(signal.SIGINT, _stop)
        signal.signal(signal.SIGTERM, _stop)

        self.stdout.write(
            self.style.SUCCESS(
                f"Outbox relay started (prefix={options['subject_prefix']})"
            )
        )

        while running:
            try:
                count = relay.process_batch(options["batch_size"])
                if count == 0:
                    time.sleep(options["poll_interval"])
            except Exception as ex:
                self.stderr.write(self.style.ERROR(f"Relay error: {ex}"))
                time.sleep(options["poll_interval"])

        loop.run_until_complete(stop_messaging())
        loop.close()
        self.stdout.write(self.style.SUCCESS("Outbox relay stopped"))
