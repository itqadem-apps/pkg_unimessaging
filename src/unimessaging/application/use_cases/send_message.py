from __future__ import annotations

from unimessaging.domain import Message

from ..dto import SendMessageRequest, SendMessageResponse
from ..interfaces import NotificationGateway


class SendMessageUseCase:
    """Use case responsible for dispatching a message."""

    def __init__(self, gateway: NotificationGateway):
        self._gateway = gateway

    def execute(self, request: SendMessageRequest) -> SendMessageResponse:
        message = Message(request.message, request.recipient)
        payload = self._gateway.deliver(message)
        return SendMessageResponse(status="sent", payload=payload)
