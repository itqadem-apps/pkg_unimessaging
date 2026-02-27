# Adapters

Adapters are concrete implementations of the `NotificationGateway` port. They live under `src/unimessaging/adapters/`, each in its own sub-package.

## Importing Adapters

```python
from unimessaging.adapters import (
    InMemoryNotificationGateway,
    NATSNotificationGateway,
    NATSConfig,
)
```

`InMemoryNotificationGateway` is always available. `NATSNotificationGateway` and `NATSConfig` are `None` if `nats-py` is not installed.

---

## InMemoryNotificationGateway

**Module:** `unimessaging.adapters.in_memory.gateway`

A simple gateway that echoes the message payload back as a dictionary. No external dependencies.

### Usage

```python
from unimessaging.adapters import InMemoryNotificationGateway
from unimessaging.domain.entities import Message

gateway = InMemoryNotificationGateway()
msg = Message("hello", "alice")

result = gateway.deliver(msg)
# {"message": "hello", "to": "alice"}
```

### When to Use

- **Tests** -- predictable output, no side effects
- **Local development** -- quick iteration without a running message broker
- **Demos** -- shows the architecture without infrastructure setup
- **Default gateway** -- the `send_message` facade uses this when no gateway is provided

---

## NATSNotificationGateway

**Module:** `unimessaging.adapters.nats.gateway`

A gateway that publishes messages to a [NATS](https://nats.io/) subject. Requires the `nats-py` package.

See [NATS Gateway](NATS-Gateway) for the full detailed guide.

### Quick Usage

```python
from unimessaging.adapters import NATSNotificationGateway, NATSConfig

config = NATSConfig(
    url="nats://localhost:4222",
    subject="notifications.orders",
)

gateway = NATSNotificationGateway(config)
```

### Installation

After installing the core package, add the NATS dependency:

```bash
pip install nats-py>=2.11.0
```

---

## Adapter Summary

| Adapter | Transport | Dependencies | Sync/Async |
|---------|-----------|-------------|------------|
| `InMemoryNotificationGateway` | None (echo) | None | Sync |
| `NATSNotificationGateway` | NATS | `nats-py` | Sync wrapper over async |
