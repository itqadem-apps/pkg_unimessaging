"""Django integration for unimessaging.

Provides ``start_messaging()`` / ``stop_messaging()`` helpers and
module-level accessors for the broker and messaging client.
"""

from .startup import get_broker, get_messaging, start_messaging, stop_messaging

__all__ = ["start_messaging", "stop_messaging", "get_messaging", "get_broker"]
