from __future__ import annotations

import atexit
import os
import sys
from functools import partial
from typing import Optional

import psutil
from daemon import DaemonContext

from h3daemon.connect import find_free_port
from h3daemon.errors import ChildNotFoundError
from h3daemon.hmmfile import HMMFile
from h3daemon.master import Master
from h3daemon.polling import wait_until
from h3daemon.worker import Worker

__all__ = ["Sched", "SchedContext"]


def spawn_master(hmmfile: str, cport: int, wport: int):
    cmd = Master.cmd(cport, wport, hmmfile)
    master = Master(psutil.Popen(cmd))
    wait_until(partial(master.is_ready, cport))
    return master


def spawn_worker(wport: int):
    cmd = Worker.cmd(wport)
    worker = Worker(psutil.Popen(cmd))
    wait_until(partial(worker.is_ready))
    return worker


def entry_point(hmmfile: str, cport: int, wport: int):
    sched = Sched(psutil.Process(os.getpid()))
    sched.run(hmmfile, cport, wport)


class SchedContext:
    def __init__(self, hmmfile: HMMFile, cport: int = 0, wport: int = 0):
        self._hmmfile = hmmfile
        self._cport = find_free_port() if cport == 0 else cport
        self._wport = find_free_port() if wport == 0 else wport
        self._exe = sys.executable
        self._scr = os.path.realpath(__file__)
        self._sched: Optional[Sched] = None

    def open(self):
        cmd = [self._exe, self._scr, str(self._hmmfile)]
        cmd += [str(self._cport), str(self._wport)]
        self._sched = Sched(psutil.Popen(cmd))
        atexit.register(self.close)

    def close(self):
        if not self._sched:
            return
        self._sched.kill_children()
        self._sched = None

    @property
    def sched(self) -> Sched:
        assert self._sched
        return self._sched

    def __enter__(self):
        self.open()
        return self.sched

    def __exit__(self, *_):
        self.close()


class Sched:
    def __init__(self, proc: psutil.Process):
        self._proc = proc

    @classmethod
    def possess(cls, hmmfile: HMMFile):
        pid = hmmfile.pidfile.is_locked()
        if pid:
            return cls(psutil.Process(pid))
        raise RuntimeError(f"Failed to possess {hmmfile}. Is it running?")

    @staticmethod
    def daemonize(
        hmmfile: HMMFile,
        cport: int,
        wport: int,
        stdin,
        stdout,
        stderr,
        detach: Optional[bool] = None,
    ):
        assert hmmfile.pidfile.is_locked() is None
        ctx = DaemonContext(
            working_directory=hmmfile.workdir,
            pidfile=hmmfile.pidfile,
            detach_process=detach,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
        )
        with ctx:
            entry_point(str(hmmfile), cport, wport)

    def run(self, hmmfile: str, cport: int, wport: int):
        try:
            master = spawn_master(hmmfile, cport, wport)
            worker = spawn_worker(wport)
            cb = self.terminate_children
            psutil.wait_procs([master.process, worker.process], callback=lambda _: cb())
        finally:
            self.kill_children()

    def kill_children(self):
        for x in self._proc.children():
            x.kill()
        self._proc.kill()
        self._proc.wait()

    def terminate_children(self):
        for x in self._proc.children():
            x.terminate()
        self._proc.terminate()
        self._proc.wait()

    def wait(self):
        self._proc.wait()

    def _is_ready(self):
        try:
            master = self.master
            worker = self.worker
        except ChildNotFoundError:
            return False
        return master.is_ready(master.get_port()) and worker.is_ready()

    def is_ready(self, wait=False):
        if wait:
            wait_until(self._is_ready)
        return self._is_ready()

    @property
    def master(self) -> Master:
        children = self._proc.children()
        if len(children) > 0:
            return Master(children[0])
        raise ChildNotFoundError("Master not found.")

    @property
    def worker(self) -> Worker:
        children = self._proc.children()
        if len(children) > 1:
            return Worker(children[1])
        raise ChildNotFoundError("Worker not found.")


if __name__ == "__main__":
    entry_point(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
