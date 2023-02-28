import time
from typing import Callable

__all__ = ["wait_until"]


def wait_until(ok: Callable[[], bool], n=50, ignore_exceptions=False):
    for _ in range(n):
        if ignore_exceptions:
            try:
                if ok():
                    return
            except Exception:
                pass
        else:
            if ok():
                return
        time.sleep(0.1)
    raise TimeoutError()
