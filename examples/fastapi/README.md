# FastAPI + NATS example

Tiny FastAPI application that wires the `unimessaging.send_message` facade into an HTTP endpoint and uses the NATS gateway to publish notifications.

## Prerequisites

- A running NATS server (e.g. `docker run -p 4222:4222 nats:latest`). If you skip this, the app falls back to the in-memory gateway.
- Python dependencies: `fastapi`, `uvicorn`, and the optional NATS extras (`pip install unimessaging[nats]`).

## Run locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install fastapi uvicorn
pip install -e ../..[nats]  # install unimessaging + optional NATS deps
export NATS_URL="nats://127.0.0.1:4222"        # optional, defaults shown
export NATS_SUBJECT="notifications.demo"
uvicorn app:app --reload

# (If you skipped installing the NATS extras, the server will warn and continue using the in-memory gateway.)
```

Send a request:

```bash
curl -X POST http://127.0.0.1:8000/notifications \
     -H "Content-Type: application/json" \
     -d '{"message": "hello", "recipient": "team"}'
```

Expected response:

```json
{"status": "sent", "payload": {"message": "hello", "to": "team", "subject": "notifications.demo"}}
```

Verify that the listener consumed the message (only when NATS is enabled):

```bash
curl http://127.0.0.1:8000/notifications/received
```

Sample output:

```json
{"count":1,"items":[{"message":"hello","to":"team","subject":"notifications.demo"}]}
```
