from __future__ import annotations

from dataclasses import dataclass

from .exceptions import InvalidMessageError


@dataclass(frozen=True)
class Message:
    """Value object representing a message being dispatched."""

    content: str
    recipient: str

    def __post_init__(self) -> None:  # pragma: no cover - dataclass hook
        content = (self.content or "").strip()
        recipient = (self.recipient or "").strip()
        if not content:
            raise InvalidMessageError("message content cannot be empty")
        if not recipient:
            raise InvalidMessageError("recipient cannot be empty")
        object.__setattr__(self, "content", content)
        object.__setattr__(self, "recipient", recipient)

    def to_dict(self) -> dict:
        return {"message": self.content, "to": self.recipient}
