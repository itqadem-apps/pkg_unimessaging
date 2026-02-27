# Integrations

The integrations layer wires use cases with adapters and exposes a consumer-friendly API. It lives under `src/unimessaging/integrations/common/`.

## The `send_message` Facade

**Module:** `unimessaging.integrations.common.facade`
**Also exported from:** `unimessaging` (top-level)

This is the primary entry point for most consumers.

### Signature

```python
def send_message(
    message: str,
    recipient: str | None = None,
    *,
    gateway: NotificationGateway | None = None,
) -> dict:
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | `str` | (required) | The message content |
| `recipient` | `str \| None` | `None` | The target recipient. **Required** -- raises `ValueError` if `None`. |
| `gateway` | `NotificationGateway \| None` | `None` | Optional custom gateway. Defaults to `InMemoryNotificationGateway`. |

### Return Value

```python
{
    "status": "sent",
    "payload": {
        "message": "...",
        "to": "..."
    }
}
```

The `payload` dict contents depend on the gateway implementation. The NATS gateway adds a `"subject"` key.

### How It Works

1. If no `gateway` is provided, uses a cached `InMemoryNotificationGateway` singleton
2. If a `gateway` is provided, creates a fresh `SendMessageUseCase` with that gateway
3. Constructs a `SendMessageRequest` DTO
4. Calls `use_case.execute(request)`
5. Unwraps the `SendMessageResponse` into a plain dict

### Caching

The default use case (no custom gateway) is cached with `@lru_cache(maxsize=1)`. This avoids reconstructing the gateway and use case on every call.

When a custom gateway is passed, a new use case is created each time -- no caching.

### Examples

Default gateway:

```python
from unimessaging import send_message

send_message("hello", "alice")
```

Custom gateway:

```python
from unimessaging import send_message
from unimessaging.adapters import NATSNotificationGateway, NATSConfig

nats_gw = NATSNotificationGateway(NATSConfig(subject="notifications.orders"))
send_message("Order shipped", "user-42", gateway=nats_gw)
```

### Errors

| Error | When |
|-------|------|
| `ValueError("recipient is required")` | `recipient` is `None` |
| `InvalidMessageError` | Empty/whitespace `message` or `recipient` |
| `RuntimeError` | NATS gateway called inside an active event loop |
