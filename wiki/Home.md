# unimessaging

**unimessaging** is a lightweight, clean-architecture messaging package for Python. It provides a simple public API for dispatching messages through pluggable transport gateways.

**Current version:** `0.0.2`
**License:** MIT
**Python:** >= 3.12
**Author:** Fritill

---

## Quick Start

```python
from unimessaging import send_message

result = send_message("hello world", "alice@example.com")
print(result)
# {'status': 'sent', 'payload': {'message': 'hello world', 'to': 'alice@example.com'}}
```

That single function call wires up the entire use case, domain validation, and gateway delivery behind the scenes.

---

## Wiki Pages

| Page | Description |
|------|-------------|
| [Installation](Installation) | How to install the package and optional dependencies |
| [Architecture](Architecture) | Clean-architecture layers, directory layout, and design rationale |
| [Getting Started](Getting-Started) | Basic usage, sending messages, and handling errors |
| [Domain Layer](Domain-Layer) | `Message` entity, `InvalidMessageError`, and `NotificationGateway` port |
| [Application Layer](Application-Layer) | DTOs, `SendMessageUseCase`, and request/response flow |
| [Adapters](Adapters) | Built-in gateways: InMemory and NATS |
| [Custom Adapters](Custom-Adapters) | How to implement your own `NotificationGateway` |
| [Integrations](Integrations) | The `send_message` facade and how wiring works |
| [NATS Gateway](NATS-Gateway) | Detailed guide for the NATS adapter, configuration, and async behavior |
| [FastAPI Example](FastAPI-Example) | Full walkthrough of the included FastAPI demo app |
| [Testing](Testing) | Running the test suite and writing tests for your adapters |
| [API Reference](API-Reference) | Complete reference for every public symbol |
| [Contributing](Contributing) | Development setup, extending the package, and conventions |
