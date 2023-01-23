from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

__all__ = ["Env", "env"]


@dataclass
class Env:
    H3DAEMON_URI: str


load_dotenv()

env = Env(os.getenv("H3DAEMON_URI", "unix:///run/user/501/podman/podman.sock"))
