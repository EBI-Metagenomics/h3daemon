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
from pidlockfile import PIDLockFile
from typer import echo

from h3daemon.app import app_setup, app_terminate, app_main
from h3daemon.process import wait_for_port

__all__ = ["app"]


app = typer.Typer(
    add_completion=False,
    pretty_exceptions_short=True,
    pretty_exceptions_show_locals=False,
)

O_VERSION = typer.Option(None, "--version", is_eager=True)
O_PORT = typer.Option(0, help="Port to listen to.")
O_ALL = typer.Option(False, "--all")
O_STDIN = typer.Option(None, "--stdin")
O_STDOUT = typer.Option(None, "--stdout")
O_STDERR = typer.Option(None, "--stderr")


@app.callback(invoke_without_command=True)
def cli(version: Optional[bool] = O_VERSION):
    if version:
        echo(importlib.metadata.version(__package__))
        raise typer.Exit()


@app.command()
def start(
    hmmfile: Path,
    port: int = O_PORT,
    stdin: Optional[Path] = O_STDIN,
    stdout: Optional[Path] = O_STDOUT,
    stderr: Optional[Path] = O_STDERR,
):
    """
    Start daemon.
    """
    hmmfile = hmmfile.absolute()

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
    pidfile = PIDLockFile(f"{hmmfile}.pid", timeout=5)
    ctx = DaemonContext(working_directory=workdir, pidfile=pidfile)
    ctx.stdin = open(stdin, "r") if stdin else stdin
    ctx.stdout = open(stdout, "w+") if stdout else stdout
    ctx.stderr = open(stderr, "w+") if stderr else stderr
    ctx.signal_map = {signal.SIGTERM: app_terminate, signal.SIGINT: app_terminate}
    app_setup(port)
    with ctx:
        app_main(str(hmmfile))


@app.command()
def stop(hmmfile: Optional[Path] = typer.Argument(None), all: bool = O_ALL):
    """
    Stop daemon.
    """
    if all:
        stop_all()
        return

    assert hmmfile
    hmmfile = hmmfile.absolute()

    if not hmmfile.name.endswith(".hmm"):
        raise ValueError(f"`{hmmfile}` does not end with `.hmm`.")

    if not hmmfile.exists():
        raise ValueError(f"`{hmmfile}` does not exist.")

    pidfile = PIDLockFile(f"{hmmfile}.pid", timeout=5)
    pid = pidfile.is_locked()
    if pid:
        os.kill(pid, signal.SIGTERM)
    else:
        echo(f"{hmmfile}: NOT running")


@app.command()
def port(hmmfile: Path):
    """
    Get port or fail.
    """
    hmmfile = hmmfile.absolute()

    if not hmmfile.name.endswith(".hmm"):
        raise ValueError(f"`{hmmfile}` does not end with `.hmm`.")

    if not hmmfile.exists():
        raise ValueError(f"`{hmmfile}` does not exist.")

    pidfile = PIDLockFile(f"{hmmfile}.pid", timeout=5)
    pid = pidfile.is_locked()
    if pid:
        port = wait_for_port(pid)
        if port == -1:
            raise typer.Exit(1)
        echo(f"{port}")


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
            if proc.status() == "zombie":
                continue
            cmdline = proc.cmdline()
            if len(cmdline) > 1 and cmdline[1] == exe:
                proc.terminate()
                found = True
                break
