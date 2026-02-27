# Contributing

## Development Setup

```bash
# Clone the repo
git clone git@github.com:fritill-team/pkg_unimessaging.git
cd pkg_unimessaging

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with all extras for development
pip install -e ".[dev,nats]"
```

## Running Tests

```bash
pytest tests/ -v
```

## Project Structure

See [Architecture](Architecture) for a detailed breakdown.

```
pkg_unimessaging/
├── src/unimessaging/          # Package source
│   ├── domain/                # Entities, exceptions, ports
│   ├── application/           # DTOs and use cases
│   ├── adapters/              # Gateway implementations
│   └── integrations/common/   # Facade / entrypoints
├── tests/                     # Test suite
├── examples/fastapi/          # FastAPI demo app
└── pyproject.toml             # Package metadata
```

## Conventions

These conventions are shared across the monorepo (aligned with `pkg_auth`):

### Layer Rules

- **Domain** has zero external dependencies. No imports from application, adapters, or integrations.
- **Application** depends only on domain.
- **Adapters** depend only on domain (ports and entities).
- **Integrations** wires application + adapters together.

### File Organization

- Port protocols go in `domain/ports.py`
- Each adapter gets its own sub-package: `adapters/<name>/gateway.py`
- Facade functions go in `integrations/common/facade.py`
- `domain/__init__.py` and `application/__init__.py` are **empty** (no re-exports)
- `application/use_cases/__init__.py` exports via `__all__`
- Top-level `__init__.py` exports all public symbols with `__all__` and `__version__`

### Naming

- Gateway classes: `<Transport>NotificationGateway` (e.g., `InMemoryNotificationGateway`, `NATSNotificationGateway`)
- Config classes: `<Transport>Config` (e.g., `NATSConfig`)
- Gateway files: `gateway.py` inside their sub-package

### Import Style

- Use absolute imports for cross-layer references: `from unimessaging.domain.entities import Message`
- Use relative imports only within the same layer: `from ..dto import SendMessageRequest`

## Adding a New Adapter

1. Create a sub-package under `adapters/`:

```
src/unimessaging/adapters/
└── my_transport/
    ├── __init__.py
    └── gateway.py
```

2. Implement the `NotificationGateway` protocol in `gateway.py`:

```python
from unimessaging.domain.entities import Message
from unimessaging.domain.ports import NotificationGateway


class MyTransportNotificationGateway(NotificationGateway):
    def deliver(self, message: Message) -> dict:
        payload = message.to_dict()
        # ... your transport logic ...
        return payload
```

3. Register in `adapters/__init__.py`:

```python
from .my_transport.gateway import MyTransportNotificationGateway
```

4. Add to top-level `__init__.py` if it should be a public export.

5. Write tests.

6. If it requires an optional dependency, follow the NATS pattern:

```python
try:
    from .my_transport.gateway import MyTransportNotificationGateway
except RuntimeError:
    MyTransportNotificationGateway = None
```

And add the dependency to `pyproject.toml`:

```toml
[project.optional-dependencies]
my_transport = ["my-transport-lib>=1.0"]
```

## Adding a New Use Case

1. Create `src/unimessaging/application/use_cases/your_use_case.py`
2. Define the DTO in `application/dto.py` (or a new DTO file)
3. Export from `application/use_cases/__init__.py`
4. Add a facade function in `integrations/common/facade.py` if needed
5. Export from top-level `__init__.py`

## Code Style

- Use `from __future__ import annotations` in all modules
- Use frozen dataclasses for value objects and DTOs
- Use `typing.Protocol` for port definitions
- Keep domain entities pure -- no framework or library imports
