# FastAPI Example

The package includes a complete FastAPI demo at `examples/fastapi/app.py` that shows how to wire **unimessaging** into a web service with NATS pub/sub.

## Prerequisites

```bash
pip install fastapi uvicorn
pip install unimessaging[nats]  # for NATS support
```

A running NATS server (optional -- falls back to in-memory without it):

```bash
# Using Docker
docker run -p 4222:4222 nats:latest

# Or using the NATS CLI
nats-server
```

## Running the Example

```bash
cd examples/fastapi
uvicorn app:app --reload
```

The app is available at `http://localhost:8000`.

## Endpoints

### `GET /health`

Health check endpoint.

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok"}
```

### `POST /notifications`

Send a notification through the `send_message` facade.

```bash
curl -X POST http://localhost:8000/notifications \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "recipient": "alice"}'
```

```json
{
  "status": "sent",
  "payload": {
    "message": "Hello!",
    "to": "alice",
    "subject": "notifications.demo"
  }
}
```

### `GET /notifications/received`

Returns messages captured by the built-in NATS listener.

```bash
curl http://localhost:8000/notifications/received
```

```json
{
  "count": 1,
  "items": [
    {
      "message": "Hello!",
      "to": "alice",
      "subject": "notifications.demo"
    }
  ]
}
```

## How It Works

### Gateway Selection

On startup, the app attempts to create a `NATSNotificationGateway`:

```python
try:
    gateway = NATSNotificationGateway(gateway_config)
    USING_NATS = True
except RuntimeError:
    gateway = InMemoryNotificationGateway()
    USING_NATS = False
```

If NATS is unavailable (package not installed or server not running), it falls back to `InMemoryNotificationGateway` with a warning.

### NATS Listener

When NATS is enabled, the app starts a background subscriber on the same subject it publishes to. This demonstrates the full pub/sub loop:

1. `POST /notifications` publishes a message via `send_message`
2. The listener receives it on the NATS subject
3. `GET /notifications/received` shows captured messages

The listener starts on `startup` and gracefully drains on `shutdown`.

### Configuration via Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `NATS_URL` | `nats://localhost:4222` | NATS server URL |
| `NATS_SUBJECT` | `notifications.demo` | Subject for pub/sub |
| `SERVICE_NAME` | `unimessaging-fastapi` | NATS client name |

Example:

```bash
NATS_URL=nats://prod-nats:4222 NATS_SUBJECT=notifications.orders uvicorn app:app
```

### Note on Sync Endpoints

The `POST /notifications` endpoint is defined as a **sync** function (`def`, not `async def`). This is intentional -- the `NATSNotificationGateway.deliver()` uses `asyncio.run()` internally, which cannot be called from within a running event loop. FastAPI runs sync endpoints in a thread pool, which avoids this conflict.
