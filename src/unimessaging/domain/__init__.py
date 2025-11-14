"""Domain layer entities and exceptions for unimessaging."""

from .entities import Message
from .exceptions import InvalidMessageError

__all__ = ["Message", "InvalidMessageError"]
