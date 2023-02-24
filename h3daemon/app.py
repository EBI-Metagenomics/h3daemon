import signal
import socket
import sys
import time
from contextlib import closing
from functools import partial
from pathlib import Path
from subprocess import DEVNULL, Popen, check_output
from typing import Callable, Optional

import hmmer

__all__ = ["H3Daemon"]


def check_socket(cport: int):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        return sock.connect_ex(("127.0.0.1", cport)) == 0


def is_master_ready(proc: Popen, cport: int, wport: int):
    out = check_output(["lsof", "-p", str(proc.pid)], stderr=DEVNULL).decode()
    cport_listen = False
    wport_listen = False
    for x in out.split("\n"):
        if "TCP" in x and f":{cport}" in x and "LISTEN" in x:
            cport_listen = True
        if "TCP" in x and f":{wport}" in x and "LISTEN" in x:
            wport_listen = True
    return cport_listen and wport_listen and check_socket(cport) and proc.poll() is None


def is_worker_ready(proc: Popen):
    out = check_output(["lsof", "-p", str(proc.pid)], stderr=DEVNULL).decode()
    for x in out.split("\n"):
        if "TCP" in x and "ESTABLISHED" in x:
            return proc.poll() is None
    return False


def wait_until_ready(check_ready: Callable[[], bool]):
    for _ in range(5):
        if check_ready():
            return True
        time.sleep(0.1)
    return False


def spawn_master(cport: int, wport: int, hmm_file: str):
    hmmpgmd = str(Path(hmmer.BIN_DIR) / "hmmpgmd")
    cmd = [hmmpgmd, "--master", "--hmmdb", hmm_file]
    cmd += ["--cport", str(cport), "--wport", str(wport)]
    return Popen(cmd)


def spawn_worker(wport: int):
    hmmpgmd = str(Path(hmmer.BIN_DIR) / "hmmpgmd")
    cmd = [hmmpgmd, "--worker", "127.0.0.1", "--cpu", "1", "--wport", str(wport)]
    return Popen(cmd)


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


class H3Daemon:
    def __init__(self, port: int, hmm_file: str):
        self._port = port
        self._hmmfile = hmm_file
        self._worker: Optional[Popen] = None
        self._master: Optional[Popen] = None

    def _interrupt_terminate(self, *_):
        if self._worker:
            self._worker.terminate()
        if self._master:
            self._master.terminate()

    def run(self):
        cport = find_free_port() if self._port == 0 else self._port
        wport = find_free_port()

        master = spawn_master(cport, wport, self._hmmfile)
        if not wait_until_ready(partial(is_master_ready, master, cport, wport)):
            master.terminate()
            sys.exit(master.wait())

        worker = spawn_worker(wport)
        if not wait_until_ready(partial(is_worker_ready, worker)):
            worker.terminate()
            master.terminate()
            sys.exit(worker.wait())

        self._master = master
        self._worker = worker

        signal.signal(signal.SIGINT, self._interrupt_terminate)
        signal.signal(signal.SIGTERM, self._interrupt_terminate)

        self._master.wait()
        self._worker.wait()
