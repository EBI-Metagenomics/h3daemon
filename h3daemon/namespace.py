import re
from dataclasses import dataclass

__all__ = ["Namespace"]

PREFIX = set(["h3pod", "h3master", "h3worker"])
PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]+$")


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

        if not PATTERN.match(self.pod):
            raise ValueError(f"{name} is not a valid name.")

    @classmethod
    def from_qualname(cls, qualname: str):
        return cls(qualname.split("_", 1)[1])

    @staticmethod
    def check(name: str):
        return name.split("_", 1)[0] in PREFIX

    def __str__(self):
        return self.pod.split("_", 1)[1]
