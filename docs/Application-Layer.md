# Application Layer

The application layer orchestrates domain objects through use cases. It defines DTOs for input/output and coordinates the flow between the caller and the domain. All application types live under `src/unimessaging/application/`.

## DTOs

**Module:** `unimessaging.application.dto`

### SendMessageRequest

A frozen dataclass representing the input to the `SendMessageUseCase`.

```python
from unimessaging.application.dto import SendMessageRequest

request = SendMessageRequest(message="hello", recipient="alice")
```

| Field | Type | Description |
|-------|------|-------------|
| `message` | `str` | The message content to send |
| `recipient` | `str` | The target recipient |

### SendMessageResponse

A frozen dataclass representing the output of the `SendMessageUseCase`.

```python
from unimessaging.application.dto import SendMessageResponse
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | `str` | Delivery status (e.g., `"sent"`) |
| `payload` | `dict` | Metadata returned by the gateway |

---

## SendMessageUseCase

**Module:** `unimessaging.application.use_cases.send_message`
**Also exported from:** `unimessaging.application.use_cases`

The core use case that dispatches a message through a gateway.

### Constructor

```python
from unimessaging.application.use_cases import SendMessageUseCase

use_case = SendMessageUseCase(gateway)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `gateway` | `NotificationGateway` | Any object satisfying the `NotificationGateway` protocol |

### execute()

```python
response = use_case.execute(request)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `request` | `SendMessageRequest` | The message request DTO |

**Returns:** `SendMessageResponse`

### Flow

1. Constructs a `Message` domain entity from the request DTO fields
2. Calls `gateway.deliver(message)` to send it through the transport
3. Wraps the gateway's return value in a `SendMessageResponse` with `status="sent"`

### Example

```python
from unimessaging.application.dto import SendMessageRequest
from unimessaging.application.use_cases import SendMessageUseCase
from unimessaging.adapters import InMemoryNotificationGateway

gateway = InMemoryNotificationGateway()
use_case = SendMessageUseCase(gateway)

request = SendMessageRequest(message="Order shipped", recipient="user-99")
response = use_case.execute(request)

print(response.status)   # "sent"
print(response.payload)  # {"message": "Order shipped", "to": "user-99"}
```

### Error Propagation

If the `Message` constructor raises `InvalidMessageError` (e.g., empty content), the exception propagates out of `execute()` to the caller. The use case does not catch domain exceptions.
