import time
from typing import Callable

__all__ = ["wait_until"]


def wait_until(ok: Callable[[], bool], n=50):
    for _ in range(n):
        if ok():
            return
        time.sleep(0.1)
    raise TimeoutError()
