# Architecture

**unimessaging** follows a clean-architecture layout aligned with other packages in the monorepo (e.g., `pkg_auth`). Each layer has a single responsibility and dependencies point inward toward the domain.

## Directory Layout

```
src/unimessaging/
├── __init__.py                     # Public API: re-exports all symbols, __version__, __all__
├── domain/                         # Layer 1: Pure business rules
│   ├── __init__.py                 # Empty (no re-exports)
│   ├── entities.py                 # Message value object
│   ├── exceptions.py               # InvalidMessageError
│   └── ports.py                    # NotificationGateway, AsyncMessagingPort protocols
├── application/                    # Layer 2: Use cases and DTOs
│   ├── __init__.py                 # Empty (no re-exports)
│   ├── dto.py                      # SendMessageRequest, SendMessageResponse
│   └── use_cases/
│       ├── __init__.py             # Exports SendMessageUseCase via __all__
│       └── send_message.py         # SendMessageUseCase implementation
├── adapters/                       # Layer 3: Infrastructure implementations
│   ├── __init__.py                 # Re-exports all adapter classes
│   ├── in_memory/
│   │   ├── __init__.py
│   │   └── gateway.py             # InMemoryNotificationGateway
│   ├── in_memory_broker.py         # InMemoryBrokerAdapter (testing)
│   └── nats/
│       ├── __init__.py
│       ├── async_adapter.py        # NATSAdapter (async pub/sub)
│       └── gateway.py              # NATSNotificationGateway, NATSConfig
├── broker/                         # Transport-agnostic pub/sub infrastructure
│   ├── __init__.py                 # Re-exports broker symbols
│   ├── broker.py                   # UnifiedMessageBroker
│   ├── client.py                   # UnifiedMessaging facade
│   ├── config.py                   # MessagingConfig
│   ├── registry.py                 # HandlerRegistry + module-level helpers
│   └── utils.py                    # Client factory + payload helpers
├── outbox/                         # Transactional outbox (requires sqlalchemy)
│   ├── __init__.py                 # Exports all outbox components
│   ├── models.py                   # OutboxMixin + OutboxStatus (table schema)
│   ├── repository.py               # OutboxRepository (write rows in caller's txn)
│   ├── event_bus.py                # OutboxEventBus (generic dataclass serializer)
│   └── relay.py                    # OutboxRelay + relay_loop (background publisher)
├── outbox_django/                  # Django transactional outbox (requires django)
│   ├── __init__.py                 # Exports all Django outbox components
│   ├── models.py                   # OutboxRecord Django model + OutboxStatus
│   ├── repository.py               # DjangoOutboxRepository (sync, Django ORM)
│   ├── event_bus.py                # DjangoOutboxEventBus (sync, reuses serialization)
│   └── relay.py                    # DjangoOutboxRelay (sync DB + async publish bridge)
└── integrations/                   # Layer 4: Facade / entrypoints
    ├── __init__.py
    ├── common/
    │   ├── __init__.py             # Exports send_message
    │   └── facade.py               # send_message() function
    ├── fastapi/
    │   ├── __init__.py             # Exports start_messaging, stop_messaging
    │   └── startup.py              # FastAPI lifespan helpers
    └── django/
        ├── __init__.py             # Exports start_messaging, stop_messaging, get_messaging, get_broker
        ├── startup.py              # Django messaging helpers (module-level state)
        └── management/
            └── commands/
                └── outbox_relay.py # manage.py outbox_relay command
```

## Layer Responsibilities

### Domain (`domain/`)

The innermost layer. Contains pure business logic with zero external dependencies.

- **entities.py** -- `Message` value object with self-validation
- **exceptions.py** -- `InvalidMessageError` for domain rule violations
- **ports.py** -- `NotificationGateway` protocol defining the contract adapters must satisfy

The domain layer never imports from application, adapters, or integrations.

### Application (`application/`)

Orchestrates domain objects through use cases. Depends only on the domain layer.

- **dto.py** -- `SendMessageRequest` and `SendMessageResponse` data transfer objects
- **use_cases/send_message.py** -- `SendMessageUseCase` accepts a gateway and a request DTO, constructs a `Message`, calls `gateway.deliver()`, and returns a response DTO

### Adapters (`adapters/`)

Concrete implementations of domain ports. Each adapter lives in its own sub-package.

- **in_memory/** -- `InMemoryNotificationGateway` echoes the message payload (useful for tests and demos)
- **nats/** -- `NATSNotificationGateway` publishes messages to a NATS subject (requires `nats-py`)

### Broker (`broker/`)

Transport-agnostic pub/sub infrastructure. Provides a unified interface for publishing and subscribing to messages regardless of the underlying transport (NATS, in-memory, etc.).

- **broker.py** -- `UnifiedMessageBroker` manages client lifecycle, subscriptions, and message dispatch
- **client.py** -- `UnifiedMessaging` thin facade delegating to async adapters
- **config.py** -- `MessagingConfig` dataclass for connection settings
- **registry.py** -- `HandlerRegistry` for pattern-based message routing
- **utils.py** -- Factory functions and payload helpers

### Outbox (`outbox/`)

Complete transactional outbox infrastructure for reliable event publishing. Requires `sqlalchemy[asyncio]` (install via `pip install unimessaging[outbox]`).

- **models.py** -- `OutboxMixin` table schema mixin and `OutboxStatus` enum. Services inherit with their `Base` to create the concrete ORM class.
- **repository.py** -- `OutboxRepository` writes outbox rows within the caller's DB transaction (shared session).
- **event_bus.py** -- `OutboxEventBus` serializes any dataclass event into outbox rows via duck typing. No domain imports needed.
- **relay.py** -- `OutboxRelay` polls pending rows and publishes them via messaging. `relay_loop` wraps it in an infinite async task.

This module is pure infrastructure with no domain dependencies. Each service provides its own domain events and `subject_prefix` to build NATS subjects (e.g. `"articles"` → `"articles.event"`).

### Django Outbox (`outbox_django/`)

Django-native equivalent of the SQLAlchemy outbox module. Requires `django>=4.2` (install via `pip install unimessaging[django]`).

- **models.py** -- `OutboxRecord` Django model with the same schema as `OutboxMixin`. Uses `app_label = "unimessaging"` so services add `"unimessaging.outbox_django"` to `INSTALLED_APPS`.
- **repository.py** -- `DjangoOutboxRepository` writes outbox rows using Django ORM within `transaction.atomic()`.
- **event_bus.py** -- `DjangoOutboxEventBus` is a sync event bus that reuses the serialization helpers from `outbox/event_bus.py`. No code duplication.
- **relay.py** -- `DjangoOutboxRelay` uses raw SQL with `FOR UPDATE SKIP LOCKED` for DB polling and bridges to async NATS publishing.

### Integrations (`integrations/`)

Wiring layer that assembles use cases with adapters and exposes a simple public API.

- **common/facade.py** -- The `send_message()` function that consumers call. Handles dependency construction and caching.
- **fastapi/startup.py** -- `start_messaging()` and `stop_messaging()` for FastAPI lifespan integration. Stores the broker on `app.state`.
- **django/startup.py** -- `start_messaging()`, `stop_messaging()`, `get_messaging()`, and `get_broker()` for Django. Uses module-level state instead of `app.state` since Django has no equivalent.
- **django/management/commands/outbox_relay.py** -- `manage.py outbox_relay` management command that runs the outbox relay as a long-lived process with signal handling for graceful shutdown.

## Dependency Flow

```
integrations/common/  -->  application/  -->  domain/
                                ^
                                |
        adapters/  -------------+
```

- Integrations depend on application + adapters
- Application depends on domain (ports, entities)
- Adapters depend on domain (ports, entities)
- Domain depends on nothing

## Conventions (Monorepo Alignment)

| Convention | Description |
|------------|-------------|
| `domain/ports.py` | Port protocols live in the domain layer, not application |
| `adapters/<name>/gateway.py` | Each adapter gets its own sub-package |
| `integrations/common/` | Facade/entrypoint code lives here |
| Empty `__init__.py` | `domain/__init__.py` and `application/__init__.py` are empty |
| Top-level exports | `src/unimessaging/__init__.py` exports all public symbols with `__all__` and `__version__` |
| `pyproject.toml` | Uses `[tool.setuptools.packages.find]` with `where = ["src"]` |
