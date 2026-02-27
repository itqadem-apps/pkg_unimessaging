from __future__ import annotations

from unimessaging.domain.entities import Message
from unimessaging.domain.ports import NotificationGateway

from ..dto import SendMessageRequest, SendMessageResponse


class SendMessageUseCase:
    """Use case responsible for dispatching a message."""

    def __init__(self, gateway: NotificationGateway):
        self._gateway = gateway

    def execute(self, request: SendMessageRequest) -> SendMessageResponse:
        message = Message(request.message, request.recipient)
        payload = self._gateway.deliver(message)
        return SendMessageResponse(status="sent", payload=payload)
