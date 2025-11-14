class InvalidMessageError(ValueError):
    """Domain level error raised when a message is invalid."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail
