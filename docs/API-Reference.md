# API Reference

All public symbols are exported from the top-level `unimessaging` package.

```python
import unimessaging
print(unimessaging.__version__)  # "0.0.2"
print(unimessaging.__all__)
```

---

## Top-Level Exports

| Symbol | Type | Module |
|--------|------|--------|
| `send_message` | function | `unimessaging.integrations.common.facade` |
| `Message` | class | `unimessaging.domain.entities` |
| `InvalidMessageError` | exception | `unimessaging.domain.exceptions` |
| `NotificationGateway` | protocol | `unimessaging.domain.ports` |
| `SendMessageRequest` | dataclass | `unimessaging.application.dto` |
| `SendMessageResponse` | dataclass | `unimessaging.application.dto` |
| `SendMessageUseCase` | class | `unimessaging.application.use_cases` |
| `InMemoryNotificationGateway` | class | `unimessaging.adapters.in_memory.gateway` |

---

## `send_message(message, recipient, *, gateway=None)`

The primary facade function.

```python
send_message(message: str, recipient: str | None = None, *, gateway: NotificationGateway | None = None) -> dict
```

**Parameters:**
- `message` (str) -- Message content. Must not be empty.
- `recipient` (str | None) -- Target recipient. Required.
- `gateway` (NotificationGateway | None) -- Custom gateway. Defaults to `InMemoryNotificationGateway`.

**Returns:** `dict` with keys `"status"` and `"payload"`.

**Raises:**
- `ValueError` -- if `recipient` is `None`
- `InvalidMessageError` -- if `message` or `recipient` is empty/whitespace

---

## `Message(content, recipient)`

Domain value object.

```python
Message(content: str, recipient: str)
```

**Fields:**
- `content` (str) -- Stripped on creation. Must not be empty.
- `recipient` (str) -- Stripped on creation. Must not be empty.

**Methods:**
- `to_dict() -> dict` -- Returns `{"message": content, "to": recipient}`

**Raises:** `InvalidMessageError` on construction if validation fails.

---

## `InvalidMessageError(detail)`

Domain exception. Subclass of `ValueError`.

```python
InvalidMessageError(detail: str)
```

**Attributes:**
- `detail` (str) -- Human-readable error description.

---

## `NotificationGateway` (Protocol)

Port contract for transport adapters.

**Required method:**
```python
def deliver(self, message: Message) -> dict
```

---

## `SendMessageRequest(message, recipient)`

Application-layer input DTO. Frozen dataclass.

**Fields:**
- `message` (str)
- `recipient` (str)

---

## `SendMessageResponse(status, payload)`

Application-layer output DTO. Frozen dataclass.

**Fields:**
- `status` (str)
- `payload` (dict)

---

## `SendMessageUseCase(gateway)`

Application-layer use case.

**Constructor:**
- `gateway` (NotificationGateway) -- The transport adapter.

**Methods:**
- `execute(request: SendMessageRequest) -> SendMessageResponse`

---

## `InMemoryNotificationGateway()`

Echo adapter. Returns `message.to_dict()` from `deliver()`. No dependencies.

**Methods:**
- `deliver(message: Message) -> dict`

---

## `NATSNotificationGateway(config=None)`

**Module:** `unimessaging.adapters.nats.gateway`
**Import:** `from unimessaging.adapters import NATSNotificationGateway`

NATS transport adapter. Requires `nats-py`.

**Constructor:**
- `config` (NATSConfig | None) -- Connection settings. Defaults to `NATSConfig()`.

**Methods:**
- `deliver(message: Message) -> dict` -- Publishes to NATS. Returns payload enriched with `"subject"` key.

**Raises:**
- `RuntimeError` -- if `nats-py` not installed, or if called from within an active event loop.

---

## `NATSConfig(url, subject, client_name, flush_timeout)`

**Module:** `unimessaging.adapters.nats.gateway`
**Import:** `from unimessaging.adapters import NATSConfig`

Frozen dataclass for NATS connection settings.

| Field | Type | Default |
|-------|------|---------|
| `url` | `str` | `"nats://localhost:4222"` |
| `subject` | `str` | `"notifications.default"` |
| `client_name` | `str` | `"unimessaging"` |
| `flush_timeout` | `float` | `2.0` |
