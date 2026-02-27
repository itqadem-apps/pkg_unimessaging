# Custom Adapters

You can implement your own transport gateway by satisfying the `NotificationGateway` protocol.

## The Protocol

```python
from unimessaging.domain.ports import NotificationGateway
from unimessaging.domain.entities import Message

class NotificationGateway(Protocol):
    def deliver(self, message: Message) -> dict:
        ...
```

Your adapter must implement a `deliver` method that:
- Accepts a `Message` domain entity
- Returns a `dict` containing payload metadata

## Example: Console Gateway

A gateway that prints messages to stdout:

```python
from unimessaging.domain.entities import Message
from unimessaging.domain.ports import NotificationGateway


class ConsoleNotificationGateway(NotificationGateway):
    """Prints messages to the console."""

    def deliver(self, message: Message) -> dict:
        payload = message.to_dict()
        print(f"[NOTIFY] to={payload['to']} message={payload['message']}")
        return payload
```

Use it with the facade:

```python
from unimessaging import send_message

gateway = ConsoleNotificationGateway()
send_message("Server restarted", "ops-team", gateway=gateway)
# [NOTIFY] to=ops-team message=Server restarted
```

## Example: HTTP Webhook Gateway

A gateway that POSTs messages to an external webhook:

```python
import requests
from unimessaging.domain.entities import Message
from unimessaging.domain.ports import NotificationGateway


class WebhookNotificationGateway(NotificationGateway):
    def __init__(self, webhook_url: str, timeout: float = 5.0):
        self._url = webhook_url
        self._timeout = timeout

    def deliver(self, message: Message) -> dict:
        payload = message.to_dict()
        response = requests.post(self._url, json=payload, timeout=self._timeout)
        response.raise_for_status()
        return {**payload, "webhook_status": response.status_code}
```

## Example: RabbitMQ Gateway

```python
import json
import pika
from unimessaging.domain.entities import Message
from unimessaging.domain.ports import NotificationGateway


class RabbitMQNotificationGateway(NotificationGateway):
    def __init__(self, url: str = "amqp://localhost", queue: str = "notifications"):
        self._url = url
        self._queue = queue

    def deliver(self, message: Message) -> dict:
        payload = message.to_dict()
        connection = pika.BlockingConnection(pika.URLParameters(self._url))
        channel = connection.channel()
        channel.queue_declare(queue=self._queue, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=self._queue,
            body=json.dumps(payload),
        )
        connection.close()
        return {**payload, "queue": self._queue}
```

## Structural Typing

Inheriting from `NotificationGateway` is optional. Because it's a `Protocol`, any class with a matching `deliver(self, message: Message) -> dict` signature works:

```python
class MinimalGateway:
    def deliver(self, message):
        return message.to_dict()

# This works -- no inheritance needed
send_message("test", "bob", gateway=MinimalGateway())
```

Explicit inheritance is recommended for clarity and IDE support.

## Adapter Directory Convention

When contributing adapters to the package, follow the monorepo convention:

```
src/unimessaging/adapters/
└── your_transport/
    ├── __init__.py
    └── gateway.py       # YourTransportNotificationGateway class
```

Then register the export in `adapters/__init__.py`:

```python
from .your_transport.gateway import YourTransportNotificationGateway
```

## Testing Custom Adapters

```python
import pytest
from unimessaging.domain.entities import Message


class TestMyGateway:
    def test_deliver_returns_dict(self):
        gateway = MyCustomGateway()
        msg = Message("hello", "alice")
        result = gateway.deliver(msg)
        assert isinstance(result, dict)
        assert "message" in result
        assert "to" in result

    def test_deliver_preserves_content(self):
        gateway = MyCustomGateway()
        msg = Message("test content", "bob")
        result = gateway.deliver(msg)
        assert result["message"] == "test content"
        assert result["to"] == "bob"
```
