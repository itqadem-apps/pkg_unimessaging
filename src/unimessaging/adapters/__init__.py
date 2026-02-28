"""Adapters that satisfy domain port contracts."""

from .in_memory.gateway import InMemoryNotificationGateway
from .in_memory_broker import InMemoryBrokerAdapter

try:  # Optional dependency: only available when nats-py is installed.
    from .nats.gateway import NATSConfig, NATSNotificationGateway
except RuntimeError:  # pragma: no cover - triggered when nats-py missing
    NATSNotificationGateway = None  # type: ignore
    NATSConfig = None  # type: ignore

try:
    from .nats.async_adapter import NATSAdapter
except RuntimeError:  # pragma: no cover
    NATSAdapter = None  # type: ignore

__all__ = [
    "InMemoryNotificationGateway",
    "InMemoryBrokerAdapter",
    "NATSNotificationGateway",
    "NATSAdapter",
    "NATSConfig",
]
