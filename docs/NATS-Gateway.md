# NATS Gateway

The `NATSNotificationGateway` publishes messages to a [NATS](https://nats.io/) subject. It's an optional adapter that requires `nats-py`.

## Installation

After installing the core package (see [Installation](Installation)), add the NATS dependency:

```bash
pip install nats-py>=2.11.0
```

## NATSConfig

**Module:** `unimessaging.adapters.nats.gateway`

A frozen dataclass for NATS connection settings.

```python
from unimessaging.adapters import NATSConfig

config = NATSConfig(
    url="nats://localhost:4222",
    subject="notifications.default",
    client_name="unimessaging",
    flush_timeout=2.0,
)
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `url` | `str` | `"nats://localhost:4222"` | NATS server URL |
| `subject` | `str` | `"notifications.default"` | NATS subject to publish to |
| `client_name` | `str` | `"unimessaging"` | Client identifier for the connection |
| `flush_timeout` | `float` | `2.0` | Seconds to wait for flush before timeout |

## NATSNotificationGateway

### Constructor

```python
from unimessaging.adapters import NATSNotificationGateway, NATSConfig

gateway = NATSNotificationGateway(config=NATSConfig(
    url="nats://my-nats-server:4222",
    subject="notifications.orders",
))
```

If `config` is `None`, defaults to `NATSConfig()` with all default values.

Raises `RuntimeError` if `nats-py` is not installed.

### deliver()

```python
result = gateway.deliver(message)
```

Publishes the message as JSON to the configured NATS subject. Returns an enriched payload dict:

```python
{
    "message": "hello",
    "to": "alice",
    "subject": "notifications.orders"
}
```

### Sync/Async Behavior

The `deliver()` method has a **synchronous** signature but uses `asyncio.run()` internally to perform the async NATS publish. This means:

- **From sync code** (scripts, sync endpoints): works out of the box
- **From async code** (inside a running event loop): raises `RuntimeError`

If you need to call it from inside an async context (e.g., a FastAPI async endpoint), use `asyncio.to_thread`:

```python
import asyncio
from unimessaging import send_message

result = await asyncio.to_thread(send_message, "hello", "alice", gateway=gateway)
```

Or use a sync FastAPI endpoint (the example app does this):

```python
@app.post("/notifications")
def create_notification(payload: NotificationPayload):  # sync, not async
    return send_message(payload.message, payload.recipient, gateway=gateway)
```

### Connection Lifecycle

Each `deliver()` call:
1. Opens a new NATS connection
2. Publishes the message
3. Flushes the buffer
4. Closes the connection

This is simple but not optimal for high-throughput scenarios. For production use at scale, consider implementing a persistent-connection adapter.

### Logging

The gateway logs at two levels:

| Level | Messages |
|-------|----------|
| `DEBUG` | Connection initialization, connecting to NATS |
| `INFO` | Publishing message (includes subject and recipient) |

Logger name: `unimessaging.adapters.nats.gateway`

### Environment Variables (Example App)

The FastAPI example uses environment variables for configuration:

| Variable | Default | Description |
|----------|---------|-------------|
| `NATS_URL` | `nats://localhost:4222` | NATS server URL |
| `NATS_SUBJECT` | `notifications.demo` | NATS subject |
| `SERVICE_NAME` | `unimessaging-fastapi` | Client name |

### Graceful Degradation

If `nats-py` is not installed, importing `NATSNotificationGateway` from `unimessaging.adapters` returns `None` instead of raising:

```python
from unimessaging.adapters import NATSNotificationGateway

if NATSNotificationGateway is None:
    print("NATS support not available, install nats-py")
```

Attempting to instantiate the class directly when `nats-py` is missing raises `RuntimeError`.
