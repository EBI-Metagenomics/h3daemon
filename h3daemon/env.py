from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

from h3daemon.infer_api_uri import infer_api_uri

__all__ = ["Env", "get_env"]


@dataclass
class Env:
    H3DAEMON_URI: str


@lru_cache
def get_env():
    load_dotenv()

    uri = os.getenv("H3DAEMON_URI", None)
    return Env(uri if uri else infer_api_uri())
