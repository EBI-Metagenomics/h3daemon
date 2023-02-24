import psutil
import time

__all__ = ["wait_for_port"]


def _get_port(proc: psutil.Process):
    master_is_running = False
    worker_is_running = False
    master_listen = []
    master_lport = []
    master_rport = []
    worker_lport = []
    worker_rport = []

    for x in proc.children():
        if "--master" in x.cmdline():
            master_is_running = x.status() == "running"
            for i in x.connections(kind="tcp"):
                if i.status == "LISTEN":
                    master_listen.append(i.laddr.port)

            for i in x.connections(kind="tcp"):
                if i.status == "ESTABLISHED":
                    master_lport.append(i.laddr.port)
                    master_rport.append(i.raddr.port)

        elif "--worker" in x.cmdline():
            worker_is_running = x.status() == "running"
            for i in x.connections(kind="tcp"):
                if i.status == "ESTABLISHED":
                    worker_lport.append(i.laddr.port)
                    worker_rport.append(i.raddr.port)

    assert master_is_running
    assert worker_is_running

    assert len(master_lport) == 1
    assert len(worker_rport) == 1
    assert master_lport[0] == worker_rport[0]
    assert len(master_rport) == 1
    assert len(worker_lport) == 1
    assert master_rport[0] == worker_lport[0]
    assert len(master_listen) == 2
    master_ports = set(master_listen)
    assert len(master_ports) == 2
    master_ports.remove(worker_rport[0])
    assert len(master_ports) == 1
    return int(list(master_ports)[0])


def wait_for_port(pid: int) -> int:
    proc = psutil.Process(pid)
    for _ in range(50):
        try:
            return _get_port(proc)
        except AssertionError:
            time.sleep(0.1)
    return -1
