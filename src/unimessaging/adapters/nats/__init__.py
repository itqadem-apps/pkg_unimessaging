try:
    from .async_adapter import NATSAdapter
except RuntimeError:  # pragma: no cover
    NATSAdapter = None  # type: ignore

__all__ = ["NATSAdapter"]