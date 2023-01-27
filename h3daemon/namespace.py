import re
from dataclasses import asdict, dataclass, field

__all__ = ["Namespace", "NamespaceInfo"]

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


@dataclass
class Master:
    state: str = "unknown"


@dataclass
class Worker:
    state: str = "unknown"


@dataclass
class Host:
    ip: str = "unknown"
    port: str = "unknown"


@dataclass
class NamespaceInfo:
    master: Master = field(default_factory=Master)
    worker: Worker = field(default_factory=Worker)
    host: Host = field(default_factory=Host)

    def asdict(self):
        return {
            "master": asdict(self.master),
            "worker": asdict(self.worker),
            "host": asdict(self.host),
        }
