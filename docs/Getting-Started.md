# Getting Started

## Sending a Message

The simplest way to use **unimessaging** is through the top-level `send_message` function:

```python
from unimessaging import send_message

result = send_message("Hello!", "alice@example.com")
```

The return value is a dictionary:

```python
{
    "status": "sent",
    "payload": {
        "message": "Hello!",
        "to": "alice@example.com"
    }
}
```

By default, `send_message` uses the `InMemoryNotificationGateway`, which echoes the message payload back. This is useful for development and testing.

## Using a Custom Gateway

Pass a `gateway` keyword argument to route messages through a different transport:

```python
from unimessaging import send_message
from unimessaging.adapters import NATSNotificationGateway, NATSConfig

gateway = NATSNotificationGateway(NATSConfig(
    url="nats://localhost:4222",
    subject="notifications.orders",
))

result = send_message("Order confirmed", "user-42", gateway=gateway)
```

## Handling Errors

### Missing Recipient

The `recipient` argument is required. Omitting it raises a `ValueError`:

```python
from unimessaging import send_message

send_message("hello")
# ValueError: recipient is required
```

### Invalid Message Content

Empty or whitespace-only content raises an `InvalidMessageError` (a subclass of `ValueError`):

```python
from unimessaging import send_message

send_message("", "alice")
# InvalidMessageError: message content cannot be empty

send_message("hello", "   ")
# InvalidMessageError: recipient cannot be empty
```

You can catch the specific exception:

```python
from unimessaging import send_message, InvalidMessageError

try:
    send_message("", "alice")
except InvalidMessageError as e:
    print(e.detail)  # "message content cannot be empty"
```

## Using the Use Case Directly

For more control, use the `SendMessageUseCase` class directly:

```python
from unimessaging import (
    SendMessageUseCase,
    SendMessageRequest,
    InMemoryNotificationGateway,
)

gateway = InMemoryNotificationGateway()
use_case = SendMessageUseCase(gateway)

request = SendMessageRequest(message="hello", recipient="bob")
response = use_case.execute(request)

print(response.status)   # "sent"
print(response.payload)  # {"message": "hello", "to": "bob"}
```

## Public Symbols

Everything you need is available from the top-level import:

```python
from unimessaging import (
    # Facade
    send_message,
    # Domain
    Message,
    InvalidMessageError,
    NotificationGateway,
    # Application
    SendMessageRequest,
    SendMessageResponse,
    SendMessageUseCase,
    # Adapters
    InMemoryNotificationGateway,
)
```

For the NATS adapter (requires `pip install nats-py>=2.11.0`), import from the adapters sub-package:

```python
from unimessaging.adapters import NATSNotificationGateway, NATSConfig
```
