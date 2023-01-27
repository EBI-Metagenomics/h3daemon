from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

from h3daemon.local import Local

__all__ = ["Env", "get_env"]


@dataclass
class Env:
    H3DAEMON_URI: str


@lru_cache
def get_env():
    load_dotenv()

    uri = os.getenv("H3DAEMON_URI", None)
    if not uri:
        local = Local()
        local.assert_running_state()
        uri = local.api_uri()

    return Env(uri)
