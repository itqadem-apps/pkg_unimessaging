"""Public API for the unimessaging package."""

__version__ = "0.0.2"

# Domain
from .domain.entities import Message
from .domain.exceptions import InvalidMessageError
from .domain.ports import NotificationGateway

# Application
from .application.dto import SendMessageRequest, SendMessageResponse
from .application.use_cases import SendMessageUseCase

# Adapters
from .adapters import InMemoryNotificationGateway

# Facade
from .integrations.common.facade import send_message

__all__ = [
    # Domain
    "Message",
    "InvalidMessageError",
    "NotificationGateway",
    # Application
    "SendMessageRequest",
    "SendMessageResponse",
    "SendMessageUseCase",
    # Adapters
    "InMemoryNotificationGateway",
    # Facade
    "send_message",
]
