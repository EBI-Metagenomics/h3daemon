__all__ = ["EarlyExitError"]


class EarlyExitError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
