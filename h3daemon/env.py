from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

__all__ = ["Env", "get_env"]


@dataclass
class Env:
    H3DAEMON_URI: str | None


@lru_cache
def get_env():
    load_dotenv()
    return Env(os.getenv("H3DAEMON_URI", None))
