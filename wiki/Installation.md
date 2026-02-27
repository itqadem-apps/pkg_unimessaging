# Installation

## Basic Install

Install the core package (includes the `InMemoryNotificationGateway`):

```bash
pip install unimessaging
```

Or install from source in the monorepo:

```bash
pip install -e packages/pkg_unimessaging
```

## With NATS Support

To use the `NATSNotificationGateway`, install with the `nats` extra:

```bash
pip install unimessaging[nats]
```

This pulls in [`nats-py`](https://github.com/nats-io/nats.py) >= 2.11.0.

## Development Install

For development (adds `pytest` and `mypy`):

```bash
pip install -e "packages/pkg_unimessaging[dev]"
```

Or with all extras:

```bash
pip install -e "packages/pkg_unimessaging[dev,nats]"
```

## Requirements

- **Python** >= 3.12
- **No runtime dependencies** for the core package
- **nats-py** >= 2.11.0 (optional, for NATS transport)

## Verify Installation

```python
import unimessaging
print(unimessaging.__version__)
# 0.0.2
```

```python
from unimessaging import send_message
result = send_message("ping", "test-user")
print(result["status"])
# sent
```
