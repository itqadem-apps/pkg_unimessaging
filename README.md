# unimessaging

Small reference project that demonstrates a clean-architecture approach for a messaging package. The public API is intentionally tiny—`unimessaging.send_message`—while the internals are layered so you can swap gateways, add use cases, or plug the domain into other applications without rewriting business logic.

## Architecture overview

```
src/unimessaging/
├── domain/           # Entities and domain errors (pure business rules)
├── application/      # DTOs, interfaces, and use cases
├── infrastructure/   # Gateways that talk to real transports (in-memory stub here)
└── interfaces/       # Facade exposed to package consumers
```

- **Domain** defines a `Message` value object and validates invariants up front.
- **Application** holds the `SendMessageUseCase`, plus request/response DTOs and gateway protocols so the use case is persistence-agnostic.
- **Infrastructure** contains concrete gateways. The project ships with an `InMemoryNotificationGateway`, but you can implement another adapter (e.g., NATS, RabbitMQ) that satisfies the same protocol.
- **Interfaces** exposes a simple function (`send_message`) that orchestrates dependency wiring and input validation.

## Usage

```python
from unimessaging import send_message

payload = send_message("hello world", recipient="alice@example.com")
print(payload)
# {'status': 'sent', 'payload': {'message': 'hello world', 'to': 'alice@example.com'}}
```

To plug in your own gateway, pass an implementation of `NotificationGateway`:

```python
from unimessaging import send_message
from unimessaging.application.interfaces import NotificationGateway
from unimessaging.domain import Message

class ConsoleGateway(NotificationGateway):
    def deliver(self, message: Message) -> dict:
        print(f"Dispatching {message}")
        return message.to_dict()

send_message("ping", "logger", gateway=ConsoleGateway())
```

## Development

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .[nats]  # installs optional NATS gateway dependencies
```

Run the test suite:

```bash
pytest -q
```

## Extending

1. Add new domain entities or rules under `src/unimessaging/domain`.
2. Define a use case (or DTO) in `src/unimessaging/application`.
3. Implement the required gateway interface inside `src/unimessaging/infrastructure`.
4. Expose the functionality through `src/unimessaging/interfaces` or another adapter (CLI, API, etc.).

Following this workflow keeps infrastructure details isolated and ensures your business logic remains testable and framework-agnostic.

## Examples

- `examples/fastapi` shows how to mount the facade inside a FastAPI service with `/notifications` (publish) and `/notifications/received` (listener inspection) endpoints. The example uses the `NATSNotificationGateway`, so you'll need a running NATS server plus the optional `nats-py` dependency.
