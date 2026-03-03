# Outbox Relay

The outbox relay provides reliable, at-least-once event publishing through the [transactional outbox pattern](https://microservices.io/patterns/data/transactional-outbox.html). Domain events are written to an `outbox` table within the same database transaction as the business data, then a background relay process picks them up and publishes to NATS.

## Installation

```bash
pip install unimessaging[outbox]
```

This adds `sqlalchemy[asyncio]>=2.0` as a dependency.

## How It Works

```
Use Case ─── (same DB transaction) ──→ INSERT into outbox table
                                              │
                                       OutboxRelay (background task)
                                              │
                                       messaging.publish(subject, data)
                                              │
                                       NATS subject: "{prefix}.{aggregate_type}"
```

1. Your use case writes an event to the `outbox` table inside the same transaction as the domain write. This guarantees atomicity — if the transaction rolls back, the event is never published.
2. The `OutboxRelay` polls for `PENDING` rows with `FOR UPDATE SKIP LOCKED`, ensuring safe concurrent processing.
3. Each row is published to a NATS subject built from `subject_prefix` + `aggregate_type` (e.g. `"articles.event"`).
4. On success the row is marked `PUBLISHED`. On failure, retries increment with exponential back-off until `max_retries`, after which the row is marked `FAILED`.

## Usage

### Basic Setup

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from unimessaging.outbox import OutboxRelay, relay_loop

engine = create_async_engine("postgresql+asyncpg://...")
session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

relay = OutboxRelay(
    session_factory=session_factory,
    messaging=unified_messaging,   # any object with async publish(subject, data)
    subject_prefix="articles",
)

# Run as a background task
task = asyncio.create_task(relay_loop(relay))
```

### FastAPI Lifespan

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from unimessaging.outbox import OutboxRelay, relay_loop
from unimessaging.integrations.fastapi import start_messaging, stop_messaging

@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_messaging(app, subjects=[...], service_name="my-service", url="nats://localhost:4222")

    messaging = app.state.messaging
    relay = OutboxRelay(session_factory, messaging, subject_prefix="my-service")
    relay_task = asyncio.create_task(relay_loop(relay))

    try:
        yield
    finally:
        relay_task.cancel()
        try:
            await relay_task
        except asyncio.CancelledError:
            pass
        await stop_messaging(app)
```

### Configuration

```python
relay = OutboxRelay(
    session_factory=session_factory,
    messaging=messaging,
    subject_prefix="articles",      # required — builds "articles.{aggregate_type}"
    table_name="outbox",            # default: "outbox"
    max_retries=10,                 # default: 10 — FAILED after this many attempts
    base_backoff=5,                 # default: 5 seconds — exponential: 5, 10, 20, 40, ...
)

# Poll interval is configured on the loop
task = asyncio.create_task(relay_loop(relay, poll_interval=0.5))
```

### Processing a Single Batch

For testing or one-off processing, call `process_batch()` directly:

```python
count = await relay.process_batch(batch_size=100)
print(f"Published {count} events")
```

## Subject Routing

The relay builds NATS subjects as `{subject_prefix}.{aggregate_type}`:

| `subject_prefix` | `aggregate_type` | NATS Subject |
|-------------------|------------------|--------------|
| `"articles"` | `"event"` | `articles.event` |
| `"articles"` | `"therapy_session"` | `articles.therapy_session` |
| `"articles"` | `"article"` | `articles.article` |
| `"reservations"` | `"slot"` | `reservations.slot` |

Subscribers use standard NATS wildcard patterns:

```python
# Subscribe to all article events
register_handler("articles.*", handle_article_event)

# Subscribe to a specific kind
register_handler("articles.event", handle_event_only)
```

## Outbox Table Schema

The relay expects a table with these columns:

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

## Retry Behavior

| Retry | Delay | Total Wait |
|-------|-------|------------|
| 1 | 5s | 5s |
| 2 | 10s | 15s |
| 3 | 20s | 35s |
| 4 | 40s | 75s |
| 5 | 80s | ~2.5min |
| 6 | 160s | ~5min |
| 7+ | 320s (capped) | ~10min+ |
| 10 | — | Marked `FAILED` |

## Logging

The relay uses Python's standard `logging` module under the logger name `unimessaging.outbox`. Configure it like any other logger:

```python
import logging
logging.getLogger("unimessaging.outbox").setLevel(logging.DEBUG)
```

## Architecture Notes

The outbox relay is **pure infrastructure** — it has no domain dependencies. It only knows about:

- SQL rows (generic columns: `aggregate_type`, `payload`, `status`)
- NATS subjects (strings)
- JSON bytes

Each service provides its own domain-aware `EventBus` implementation that serializes domain events into outbox rows. The relay simply reads those rows and publishes them. This separation means:

- The relay is reusable across all services in the monorepo
- Domain event structure is owned by each service
- The relay can be tested independently with an in-memory broker