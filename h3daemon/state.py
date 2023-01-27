from dataclasses import dataclass

__all__ = ["State"]


@dataclass
class State:
    master: str
    worker: str
