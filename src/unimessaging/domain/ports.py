from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Optional, Protocol

from unimessaging.domain.entities import Message

MessageHandler = Callable[[bytes, Dict[str, Any]], Awaitable[None]]


class NotificationGateway(Protocol):
    """Gateway abstraction implemented by infrastructure adapters."""

    def deliver(self, message: Message) -> dict:
        """Send the message to the infrastructure channel and return payload metadata."""
        raise NotImplementedError


class AsyncMessagingPort(Protocol):
    """Async messaging adapter contract for persistent pub/sub connections."""

    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def publish(
        self, subject: str, data: Any = None, headers: Optional[Dict[str, str]] = None
    ) -> None: ...

    async def subscribe(
        self,
        subject: str,
        handler: MessageHandler,
        queue: Optional[str] = None,
    ) -> Any: ...

    async def request(
        self,
        subject: str,
        data: Any = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]: ...

    async def reply(
        self,
        subject: str,
        fn: MessageHandler,
        queue: Optional[str] = None,
    ) -> Any: ...
