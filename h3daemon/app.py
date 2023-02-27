import socket
import sys
import time
from contextlib import closing
from functools import partial
from pathlib import Path
from subprocess import Popen
from typing import Callable, Optional

import hmmer
import psutil

__all__ = ["app_setup", "app_main", "app_terminate"]


def check_socket(cport: int):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        return sock.connect_ex(("127.0.0.1", cport)) == 0


def is_listening(pid: int, port: int):
    try:
        for x in psutil.Process(pid).connections(kind="tcp"):
            if x.status == "LISTEN" and x.laddr.port == port:
                return True
    except RuntimeError:
        # Bug to be fixed: https://github.com/giampaolo/psutil/issues/2116
        time.sleep(0.2)
        return True
    return False


def has_connected(pid: int):
    try:
        for x in psutil.Process(pid).connections(kind="tcp"):
            if x.status == "ESTABLISHED":
                return True
    except RuntimeError:
        # Bug to be fixed: https://github.com/giampaolo/psutil/issues/2116
        time.sleep(0.2)
        return True
    return False


def is_master_ready(proc: Popen, cport: int):
    return is_listening(proc.pid, cport) and check_socket(cport) and proc.poll() is None


def is_worker_ready(proc: Popen):
    return has_connected(proc.pid) and proc.poll() is None


def wait_until_ready(check_ready: Callable[[], bool]):
    for _ in range(50):
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


def _find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def find_free_port():
    port = _find_free_port()
    while not (49152 <= port and port <= 65535):
        port = _find_free_port()
    return port


client_port: int = -1
worker_port: int = -1
worker: Optional[Popen] = None
master: Optional[Popen] = None


def app_setup(port: int):
    global client_port, worker_port
    client_port = find_free_port() if port == 0 else port
    worker_port = find_free_port()


def app_main(hmmfile: str):
    global client_port, worker_port
    global worker, master

    master = spawn_master(client_port, worker_port, hmmfile)
    if not wait_until_ready(partial(is_master_ready, master, client_port)):
        master.kill()
        sys.exit(master.wait())

    worker = spawn_worker(worker_port)
    if not wait_until_ready(partial(is_worker_ready, worker)):
        worker.kill()
        master.kill()
        sys.exit(worker.wait())

    open("/Users/horta/code/h3daemon/ponto1.txt", "w").close()
    procs = [psutil.Process(master.pid), psutil.Process(worker.pid)]
    open("/Users/horta/code/h3daemon/ponto2.txt", "w").close()
    while len(psutil.wait_procs(procs, timeout=1)[0]) == 0:
        open("/Users/horta/code/h3daemon/ponto3.txt", "w").close()
        pass
    open("/Users/horta/code/h3daemon/ponto4.txt", "w").close()

    for x in psutil.wait_procs(procs, timeout=3)[1]:
        x.kill()


def app_terminate(*_):
    global worker, master
    if worker:
        worker.terminate()
    if master:
        master.terminate()
