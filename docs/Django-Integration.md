# Django Integration

**unimessaging** provides Django-native support for the transactional outbox pattern and messaging broker integration. All Django components are synchronous, bridging to async NATS publishing where needed.

## Installation

```bash
pip install unimessaging[django]
```

This adds `django>=4.2` as a dependency.

## Components

| Module | Component | Description |
|--------|-----------|-------------|
| `outbox_django` | `OutboxRecord` | Django model for the outbox table |
| `outbox_django` | `DjangoOutboxRepository` | Writes outbox rows within `transaction.atomic()` |
| `outbox_django` | `DjangoOutboxEventBus` | Sync event bus — serializes dataclass events |
| `outbox_django` | `DjangoOutboxRelay` | Polls DB and publishes to NATS |
| `integrations.django` | `start_messaging()` | Start the NATS broker (async) |
| `integrations.django` | `stop_messaging()` | Stop the broker (async) |
| `integrations.django` | `get_messaging()` | Access the messaging client (sync) |
| `integrations.django` | `get_broker()` | Access the broker instance (sync) |

## Setup Guide

### 1. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "unimessaging.outbox_django",
]
```

Then create and run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

This creates the `outbox` table with the same schema as the SQLAlchemy `OutboxMixin`.

### 2. Wire the Event Bus

```python
from django.db import transaction
from unimessaging.outbox_django import DjangoOutboxRepository, DjangoOutboxEventBus

repo = DjangoOutboxRepository()
bus = DjangoOutboxEventBus(repo)

with transaction.atomic():
    reservation.save()
    bus.publish(ReservationCreated(
        aggregate_type="reservation",
        aggregate_id=reservation.id,
        event_id=uuid4(),
        occurred_at=datetime.now(timezone.utc),
        ...
    ))
    # Both writes happen in the same transaction
```

The `DjangoOutboxEventBus` satisfies any `EventBus` protocol with `publish(event)` and `publish_many(events)` via structural (duck) typing. It reuses the same serialization helpers as the async `OutboxEventBus` — no code duplication.

### 3. Run the Outbox Relay

Start as a separate process via the management command:

```bash
python manage.py outbox_relay --subject-prefix reservations
```

Full options:

```bash
python manage.py outbox_relay \
    --subject-prefix reservations \
    --nats-url nats://nats:4222 \
    --service-name reservations-service \
    --poll-interval 1.0 \
    --batch-size 100
```

| Argument | Default | Description |
|---|---|---|
| `--subject-prefix` | *required* | Prefix for NATS subjects (e.g. `"reservations"` -> `"reservations.slot"`) |
| `--nats-url` | `nats://localhost:4222` | NATS server URL |
| `--service-name` | `django-service` | Service name for the messaging broker |
| `--poll-interval` | `0.5` | Seconds to sleep when no pending rows found |
| `--batch-size` | `50` | Max rows to process per batch |

The command handles `SIGINT` and `SIGTERM` for graceful shutdown.

## Messaging Integration

For services that also need to subscribe to NATS messages (not just publish via outbox), use the Django integration helpers:

### Starting the Broker

```python
# In AppConfig.ready() or a management command
import asyncio
from unimessaging.integrations.django import start_messaging, get_messaging
from unimessaging.broker.registry import register_handler

# Register handlers before starting
register_handler("payments.*", handle_payment_event)

loop = asyncio.new_event_loop()
loop.run_until_complete(start_messaging(
    subjects=["payments.>"],
    service_name="reservations-service",
    url="nats://localhost:4222",
))

# Access the client anywhere:
messaging = get_messaging()
```

### Differences from FastAPI

| Aspect | FastAPI | Django |
|--------|---------|--------|
| State storage | `app.state.messaging` | Module-level via `get_messaging()` |
| First argument | `app: FastAPI` | None |
| Access pattern | `request.app.state.messaging` | `get_messaging()` |
| Lifecycle | Async lifespan context manager | Manual `start_messaging()` / `stop_messaging()` |
| Event bus | `OutboxEventBus` (async) | `DjangoOutboxEventBus` (sync) |
| Relay | `relay_loop()` as asyncio task | `manage.py outbox_relay` command |

## Architecture

```
Django Service
│
├── views / use cases
│   └── with transaction.atomic():
│       ├── model.save()
│       └── bus.publish(event)          # sync → outbox table
│
├── outbox_relay (management command)
│   ├── polls outbox table (sync SQL)
│   └── publishes to NATS (async bridge)
│
└── messaging handlers (optional)
    └── subscribe to external NATS events
```

The key design decision is **sync Django ORM + async NATS**:
1. **DB operations** are sync — Django ORM with `transaction.atomic()` and `select_for_update()`
2. **NATS publishing** is async — bridged via `asyncio.get_event_loop().run_until_complete()`
3. The management command creates its own event loop for the broker lifecycle

## Outbox Table Schema

The `OutboxRecord` model creates this table (identical to the SQLAlchemy version):

```sql
CREATE TABLE outbox (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type  TEXT NOT NULL,
    aggregate_id    TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    payload         JSONB NOT NULL,
    headers         JSONB NOT NULL DEFAULT '{}',
    status          TEXT NOT NULL DEFAULT 'PENDING',
    retries         INTEGER NOT NULL DEFAULT 0,
    available_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    occurred_at     TIMESTAMPTZ NOT NULL,
    published_at    TIMESTAMPTZ,
    last_error      TEXT
);

CREATE INDEX idx_outbox_pending ON outbox (available_at)
    WHERE status = 'PENDING';
```

## Complete Example

```python
# settings.py
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    ...,
    "unimessaging.outbox_django",
    "reservations",
]

# reservations/services.py
from django.db import transaction
from unimessaging.outbox_django import DjangoOutboxRepository, DjangoOutboxEventBus
from .models import Reservation
from .events import ReservationCreated

def create_reservation(data):
    repo = DjangoOutboxRepository()
    bus = DjangoOutboxEventBus(repo)

    with transaction.atomic():
        reservation = Reservation.objects.create(**data)
        bus.publish(ReservationCreated(
            aggregate_type="reservation",
            aggregate_id=reservation.id,
            event_id=uuid4(),
            occurred_at=timezone.now(),
            reservation_data=data,
        ))
    return reservation
```

Then run the relay:

```bash
python manage.py outbox_relay --subject-prefix reservations --nats-url nats://localhost:4222
```
