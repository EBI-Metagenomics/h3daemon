import os
from functools import partial

import psutil
from daemon import DaemonContext

from h3daemon.hmmfile import HMMFile
from h3daemon.master import Master
from h3daemon.polling import wait_until
from h3daemon.worker import Worker

from typing import Optional

__all__ = ["Sched"]


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
    def spawn(
        cport: int,
        wport: int,
        hmmfile: HMMFile,
        fin,
        fout,
        ferr,
        detach: Optional[bool] = None,
    ):
        assert hmmfile.pidfile.is_locked() is None
        ctx = DaemonContext(
            working_directory=hmmfile.workdir,
            pidfile=hmmfile.pidfile,
            detach_process=detach,
        )
        ctx.stdin = fin
        ctx.stdout = fout
        ctx.stderr = ferr

        ctx.open()
        sched = Sched(psutil.Process(os.getpid()))
        try:
            cmd = Master.cmd(cport, wport, str(hmmfile))
            master = Master(psutil.Popen(cmd))
            wait_until(partial(master.is_ready, cport))

            cmd = Worker.cmd(wport)
            worker = Worker(psutil.Popen(cmd))
            wait_until(partial(worker.is_ready))

            term = sched.terminate_children
            psutil.wait_procs([master._proc, worker._proc], callback=lambda _: term())
        finally:
            sched.kill_children()
            ctx.close()

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

    def is_ready(self):
        master = self.master
        return master.is_ready(master.get_port()) and self.worker.is_ready()

    @property
    def master(self) -> Master:
        children = self._proc.children()
        if len(children) > 0:
            return Master(children[0])
        raise RuntimeError("Master not found.")

    @property
    def worker(self) -> Worker:
        children = self._proc.children()
        if len(children) > 1:
            return Worker(children[1])
        raise RuntimeError("Worker not found.")
