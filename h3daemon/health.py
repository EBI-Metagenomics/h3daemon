from __future__ import annotations

from dataclasses import asdict, dataclass


__all__ = ["Health"]


@dataclass
class Health:
    status: str
    failing_streak: int

    def asdict(self):
        return asdict(self)
