"""Adapters that satisfy domain port contracts."""

from .in_memory.gateway import InMemoryNotificationGateway

try:  # Optional dependency: only available when nats-py is installed.
    from .nats.gateway import NATSConfig, NATSNotificationGateway
except RuntimeError:  # pragma: no cover - triggered when nats-py missing
    NATSNotificationGateway = None  # type: ignore
    NATSConfig = None  # type: ignore

__all__ = [
    "InMemoryNotificationGateway",
    "NATSNotificationGateway",
    "NATSConfig",
]
