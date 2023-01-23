from dataclasses import dataclass
from pathlib import Path

__all__ = ["Namespace"]

PREFIX = set(["h3pod", "h3master", "h3worker"])


@dataclass
class Namespace:
    pod: str
    master: str
    worker: str

    def __hash__(self) -> int:
        return hash(self.pod)

    def __init__(self, name: str):
        self.pod = f"h3pod_{name}"
        self.master = f"h3master_{name}"
        self.worker = f"h3worker_{name}"

    @property
    def name(self):
        return self.pod.split("_", 1)[1]

    @classmethod
    def from_qualname(cls, qualname: str):
        return cls(qualname.split("_", 1)[1])

    @classmethod
    def from_hmmfile(cls, hmmfile: Path):
        return cls(hmmfile.name)

    @staticmethod
    def check(name: str):
        return name.split("_", 1)[0] in PREFIX
