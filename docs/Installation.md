# Installation

## From GitHub Release (Recommended)

Install the latest wheel directly from [GitHub Releases](https://github.com/fritill-team/pkg_unimessaging/releases):

```bash
pip install "https://github.com/fritill-team/pkg_unimessaging/releases/latest/download/unimessaging-0.0.2-py3-none-any.whl"
```

## From Git Tag

Install from a specific release tag:

```bash
pip install "git+https://github.com/fritill-team/pkg_unimessaging.git@pkg_unimessaging-v0.0.2"
```

## From Source (Monorepo)

For local development in the monorepo:

```bash
pip install -e packages/pkg_unimessaging
```

## Optional Extras

### NATS Support

```bash
pip install -e ".[nats]"
```

Adds `nats-py>=2.11.0`. Enables the `NATSNotificationGateway` and `NATSAdapter`. See [NATS Gateway](NATS-Gateway) for details.

### Outbox Relay

```bash
pip install -e ".[outbox]"
```

Adds `sqlalchemy[asyncio]>=2.0`. Enables the transactional outbox relay for reliable event publishing. See [Outbox Relay](Outbox-Relay) for details.

### FastAPI Integration

```bash
pip install -e ".[fastapi]"
```

Adds `fastapi>=0.100`. Enables `start_messaging()` / `stop_messaging()` lifespan helpers.

### All Extras

```bash
pip install -e ".[all]"
```

Installs all optional dependencies (NATS, FastAPI, SQLAlchemy).

## Development Install

For development (adds `pytest` and `mypy`):

```bash
pip install -e ".[dev]"
```

Or with all extras:

```bash
pip install -e ".[dev,all]"
```

## Requirements

- **Python** >= 3.12
- **No runtime dependencies** for the core package
- **nats-py** >= 2.11.0 (optional, for NATS transport)
- **sqlalchemy[asyncio]** >= 2.0 (optional, for outbox relay)
- **fastapi** >= 0.100 (optional, for FastAPI integration)

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
