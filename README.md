# unimessaging

Small reference project that demonstrates a clean-architecture approach for a messaging package. The public API is intentionally tiny — `unimessaging.send_message` — while the internals are layered so you can swap gateways, add use cases, or plug the domain into other applications without rewriting business logic.

## Architecture overview

```
src/unimessaging/
├── domain/                # Entities, exceptions, and port protocols (pure business rules)
├── application/           # DTOs and use cases
├── adapters/              # Gateway implementations (in-memory, NATS, …)
│   ├── in_memory/
│   └── nats/
├── broker/                # Transport-agnostic pub/sub infrastructure
├── outbox/                # Transactional outbox relay (requires sqlalchemy)
└── integrations/          # Framework integrations (FastAPI, facade)
```

- **Domain** defines a `Message` value object, validates invariants up front, and declares the `NotificationGateway` port protocol.
- **Application** holds the `SendMessageUseCase`, plus request/response DTOs so the use case is transport-agnostic.
- **Adapters** contain concrete gateways. The package ships with `InMemoryNotificationGateway` and `NATSNotificationGateway`. You can implement your own adapter that satisfies the same protocol.
- **Integrations** exposes a simple function (`send_message`) that orchestrates dependency wiring and input validation.

## Installation

Install from the latest [GitHub Release](https://github.com/fritill-team/pkg_unimessaging/releases) wheel:

```bash
# core (in-memory gateway only)
pip install "https://github.com/fritill-team/pkg_unimessaging/releases/latest/download/unimessaging-0.0.2-py3-none-any.whl"
```

Or install from a specific release tag:

```bash
pip install "git+https://github.com/fritill-team/pkg_unimessaging.git@pkg_unimessaging-v0.0.2"
```

Then install optional extras as needed:

```bash
pip install nats-py>=2.11.0   # for NATS transport support
```

## Usage

```python
from unimessaging import send_message

payload = send_message("hello world", "alice@example.com")
print(payload)
# {'status': 'sent', 'payload': {'message': 'hello world', 'to': 'alice@example.com'}}
```

To plug in your own gateway, pass an implementation of `NotificationGateway`:

```python
from unimessaging import send_message
from unimessaging.domain.ports import NotificationGateway
from unimessaging.domain.entities import Message

class ConsoleGateway(NotificationGateway):
    def deliver(self, message: Message) -> dict:
        print(f"Dispatching {message}")
        return message.to_dict()

send_message("ping", "logger", gateway=ConsoleGateway())
```

To use the NATS transport:

```python
from unimessaging import send_message
from unimessaging.adapters import NATSNotificationGateway, NATSConfig

gateway = NATSNotificationGateway(NATSConfig(
    url="nats://localhost:4222",
    subject="notifications.orders",
))
send_message("Order confirmed", "user-42", gateway=gateway)
```

## Outbox Relay

The package includes a transactional outbox relay for publishing domain events through NATS. It polls a PostgreSQL `outbox` table and publishes pending rows to messaging subjects with automatic retries and exponential back-off.

```bash
pip install -e ".[outbox]"   # adds sqlalchemy[asyncio]
```

```python
from unimessaging.outbox import OutboxRelay, relay_loop

relay = OutboxRelay(
    session_factory=async_sessionmaker,
    messaging=unified_messaging,
    subject_prefix="articles",       # → "articles.event", "articles.therapy_session", ...
)

# Run as a background asyncio task
task = asyncio.create_task(relay_loop(relay))
```

See [Outbox Relay](../../wiki/Outbox-Relay) for the full guide.

## Development

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev,nats]"
```

Run the test suite:

```bash
pytest -q
```

## Extending

1. Add new domain entities or rules under `src/unimessaging/domain/`.
2. Define a use case (or DTO) in `src/unimessaging/application/`.
3. Implement the required gateway port inside `src/unimessaging/adapters/<your_transport>/gateway.py`.
4. Expose the functionality through `src/unimessaging/integrations/common/` or another entrypoint (CLI, API, etc.).

Following this workflow keeps transport details isolated and ensures your business logic remains testable and framework-agnostic.

## Examples

- `examples/fastapi/` shows how to mount the facade inside a FastAPI service with `/notifications` (publish) and `/notifications/received` (listener inspection) endpoints. The example uses the `NATSNotificationGateway`, so you'll need a running NATS server plus the optional `nats-py` dependency.

## Documentation

Full documentation is available in the [GitHub Wiki](../../wiki).
