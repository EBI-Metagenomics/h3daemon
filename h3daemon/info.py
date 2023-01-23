from dataclasses import dataclass

__all__ = ["H3Info"]


@dataclass
class H3Info:
    release: str
    compatible_api: str
    podman_api: str
