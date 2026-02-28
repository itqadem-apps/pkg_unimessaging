from __future__ import annotations

from fnmatch import fnmatch
from typing import Callable, Dict, Optional


class HandlerRegistry:
    """Instance-based handler registry for test isolation."""

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable] = {}
        self._rpc_handlers: Dict[str, Callable] = {}

    def register_handler(self, pattern: str, handler: Callable) -> None:
        self._handlers[pattern] = handler

    def register_rpc(self, subject: str, handler: Callable) -> None:
        self._rpc_handlers[subject] = handler

    def resolve_handler(self, subject: str) -> Optional[Callable]:
        for pattern, h in self._handlers.items():
            if fnmatch(subject, pattern):
                return h
        return None

    def resolve_rpc_handler(self, subject: str) -> Optional[Callable]:
        return self._rpc_handlers.get(subject)


# Module-level convenience functions (delegate to a default instance).
_default_registry = HandlerRegistry()
register_handler = _default_registry.register_handler
register_rpc = _default_registry.register_rpc
resolve_handler = _default_registry.resolve_handler
resolve_rpc_handler = _default_registry.resolve_rpc_handler