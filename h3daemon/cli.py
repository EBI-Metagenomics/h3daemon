from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Optional

import typer
from podman.errors import APIError
from rich.progress import Progress, SpinnerColumn
from typer import echo

from h3daemon.errors import EarlyExitError
from h3daemon.hmmfile import HMMFile
from h3daemon.hmmpress import hmmpress
from h3daemon.manager import H3Manager
from h3daemon.namespace import Namespace
from h3daemon.pod import H3Pod

__all__ = ["app"]


app = typer.Typer(
    add_completion=False,
    pretty_exceptions_short=True,
    pretty_exceptions_show_locals=False,
)


@app.callback(invoke_without_command=True)
def cli(version: Optional[bool] = typer.Option(None, "--version", is_eager=True)):
    if version:
        echo(importlib.metadata.version(__package__))
        raise typer.Exit()


@app.command()
def sys():
    """
    Show Podman information.
    """
    with H3Manager() as h3:
        x = h3.sys()
        echo(f"Release: {x.release}")
        echo(f"Compatible API: {x.compatible_api}")
        echo(f"Podman API: {x.podman_api}")


@app.command()
def info(namespace: str):
    """
    Show namespace information.
    """
    with H3Manager():
        pod = H3Pod(namespace=Namespace(namespace))
        echo(json.dumps(pod.info().asdict(), indent=2))


@app.command()
def stop(
    namespace: Optional[str] = typer.Argument(None),
    all: bool = typer.Option(False, "--all"),
):
    """
    Stop namespace.
    """
    with Progress(SpinnerColumn(), transient=True) as progress:
        progress.add_task(description="", total=None)
        with H3Manager() as h3:
            namespaces = []
            if all:
                assert not namespace
                namespaces += h3.namespaces()
            else:
                assert namespace
                namespaces.append(Namespace(namespace))

            for ns in namespaces:
                pod = H3Pod(namespace=ns)
                pod.stop()


@app.command()
def ls():
    """
    List namespaces.
    """
    with H3Manager() as h3:
        for ns in h3.namespaces():
            echo(str(ns))


@app.command()
def start(
    hmmfile: Path,
    port: int = typer.Option(
        0, help="Port to listen to. Randomly chooses one that is available if 0."
    ),
    force: bool = typer.Option(
        False, "--force", help="Stop namespace first if it already exists."
    ),
):
    """
    Start daemon.
    """
    with Progress(SpinnerColumn(), transient=True) as progress:
        progress.add_task(description="", total=None)
        with H3Manager() as h3:
            x = HMMFile(hmmfile)
            try:
                pod = H3Pod(hmmfile=x)

                if not force and pod.exists():
                    progress.stop()
                    echo(f"⚠️  {pod.name} is already in used.")
                    raise typer.Exit(1)

                if force and pod.exists():
                    pod.stop()
                pod.start(port)
                progress.stop()
                echo(f"🎉 Daemon started listening at {pod.host_ip}:{pod.host_port}")

            except APIError as excp:
                if excp.status_code != 409:
                    h3.rm_quietly(x.namespace)
                raise excp
            except EarlyExitError as excp:
                h3.rm_quietly(x.namespace)
                raise excp


@app.command()
def press(hmmfile: Path):
    """
    Press HMMER ASCII file.
    """
    with Progress(SpinnerColumn(), transient=True) as progress:
        progress.add_task(description="", total=None)
        with H3Manager():
            hmmpress(HMMFile(hmmfile))
