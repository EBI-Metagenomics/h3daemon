from __future__ import annotations

import importlib.metadata
import os
import signal
import sys
from pathlib import Path
from typing import Optional

import psutil
import typer
from daemon import DaemonContext
from daemon.pidfile import PIDLockFile
from typer import echo

from h3daemon import H3Daemon

__all__ = ["app"]


app = typer.Typer(
    add_completion=False,
    pretty_exceptions_short=True,
    pretty_exceptions_show_locals=False,
)

O_VERSION = typer.Option(None, "--version", is_eager=True)
O_PORT = typer.Option(0, help="Port to listen to.")
O_ALL = typer.Option(False, "--all")


@app.callback(invoke_without_command=True)
def cli(version: Optional[bool] = O_VERSION):
    if version:
        echo(importlib.metadata.version(__package__))
        raise typer.Exit()


@app.command()
def start(hmmfile: Path, port: int = O_PORT):
    """
    Start daemon.
    """
    if not hmmfile.name.endswith(".hmm"):
        raise ValueError(f"`{hmmfile}` does not end with `.hmm`.")

    if not hmmfile.exists():
        raise ValueError(f"`{hmmfile}` does not exist.")

    extensions = ["h3f", "h3i", "h3m", "h3p"]
    for x in extensions:
        filename = Path(f"{hmmfile}.{x}")
        if not filename.exists():
            raise ValueError(f"`{filename.name}` must exist as well.")

    workdir = str(hmmfile.parent)
    pidfile = PIDLockFile(hmmfile.name + ".pid")
    with DaemonContext(working_directory=workdir, pidfile=pidfile):
        daemon = H3Daemon(port, hmmfile.name)
        daemon.run()


@app.command()
def stop(hmmfile: Optional[Path] = typer.Argument(None), all: bool = O_ALL):
    """
    Stop daemon.
    """
    if all:
        stop_all()
        return

    assert hmmfile
    if not hmmfile.name.endswith(".hmm"):
        raise ValueError(f"`{hmmfile}` does not end with `.hmm`.")

    if not hmmfile.exists():
        raise ValueError(f"`{hmmfile}` does not exist.")

    os.kill(read_pidfile(str(hmmfile) + ".pid"), signal.SIGTERM)


def stop_all():
    pid = os.getpid()
    exe = sys.argv[0]
    uid = os.getuid()

    found = True
    while found:
        found = False
        for proc in psutil.process_iter(["pid", "cmdline", "uids"]):
            if proc.uids().real != uid or proc.pid == pid:
                continue
            cmdline = proc.cmdline()
            if len(cmdline) > 1 and cmdline[1] == exe:
                proc.terminate()
                found = True
                break


def read_pidfile(pidfile):
    with open(pidfile, "r") as file:
        return int(file.readline().strip())
