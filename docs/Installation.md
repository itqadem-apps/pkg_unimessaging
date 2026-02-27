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

## With NATS Support

After installing the core package, add the NATS transport dependency:

```bash
pip install nats-py>=2.11.0
```

This enables the `NATSNotificationGateway`. See [NATS Gateway](NATS-Gateway) for details.

## Development Install

For development (adds `pytest` and `mypy`):

```bash
pip install -e ".[dev]"
```

Or with all extras:

```bash
pip install -e ".[dev,nats]"
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
