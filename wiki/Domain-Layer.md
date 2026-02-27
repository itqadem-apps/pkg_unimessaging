# Domain Layer

The domain layer contains pure business logic with no external dependencies. All domain types live under `src/unimessaging/domain/`.

## Message

**Module:** `unimessaging.domain.entities`

A frozen dataclass representing a message to be dispatched.

```python
from unimessaging.domain.entities import Message

msg = Message(content="Hello!", recipient="alice@example.com")
print(msg.content)    # "Hello!"
print(msg.recipient)  # "alice@example.com"
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `content` | `str` | The message body. Stripped of leading/trailing whitespace on creation. |
| `recipient` | `str` | The message target. Stripped of leading/trailing whitespace on creation. |

### Validation

`Message` validates its invariants at construction time via `__post_init__`:

- `content` must not be empty or whitespace-only
- `recipient` must not be empty or whitespace-only

Both raise `InvalidMessageError` if violated.

```python
Message(content="", recipient="alice")
# InvalidMessageError: message content cannot be empty

Message(content="hello", recipient="   ")
# InvalidMessageError: recipient cannot be empty
```

### Immutability

`Message` is a frozen dataclass. Attributes cannot be reassigned after creation:

```python
msg = Message("hello", "alice")
msg.content = "bye"  # FrozenInstanceError
```

### Methods

#### `to_dict() -> dict`

Returns a dictionary representation:

```python
msg = Message("hello", "alice")
msg.to_dict()
# {"message": "hello", "to": "alice"}
```

---

## InvalidMessageError

**Module:** `unimessaging.domain.exceptions`

Raised when a `Message` fails domain validation. Subclasses `ValueError`.

```python
from unimessaging.domain.exceptions import InvalidMessageError

try:
    Message(content="", recipient="alice")
except InvalidMessageError as e:
    print(e.detail)  # "message content cannot be empty"
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `detail` | `str` | A human-readable description of the validation failure |

---

## NotificationGateway

**Module:** `unimessaging.domain.ports`

A `typing.Protocol` that defines the contract every transport adapter must implement. This is the **port** in ports-and-adapters terminology.

```python
from unimessaging.domain.ports import NotificationGateway
```

### Protocol Definition

```python
class NotificationGateway(Protocol):
    def deliver(self, message: Message) -> dict:
        """Send the message and return payload metadata."""
        ...
```

### Implementing the Protocol

Any class with a matching `deliver` method satisfies the protocol (structural subtyping):

```python
from unimessaging.domain.entities import Message
from unimessaging.domain.ports import NotificationGateway

class MyGateway:
    def deliver(self, message: Message) -> dict:
        # your transport logic here
        return message.to_dict()
```

No inheritance is required -- Python's `Protocol` uses structural (duck) typing. However, the built-in adapters explicitly inherit from `NotificationGateway` for clarity.

See [Custom Adapters](Custom-Adapters) for a full guide on building your own gateway.
