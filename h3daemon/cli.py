from __future__ import annotations

import pprint
from enum import IntEnum
from pathlib import Path
from typing import Optional

import typer
from podman.errors import APIError, NotFound

from h3daemon.hmmfile import HMMFile
from h3daemon.manager import H3Manager
from h3daemon.meta import __version__
from h3daemon.namespace import Namespace

__all__ = ["app"]


class EXIT_CODE(IntEnum):
    SUCCESS = 0
    FAILURE = 1


app = typer.Typer(add_completion=False)


@app.callback(invoke_without_command=True)
def cli(version: Optional[bool] = typer.Option(None, "--version", is_eager=True)):
    if version:
        print(__version__)
        raise typer.Exit()


@app.command()
def system():
    """
    Show Podman information.
    """
    with H3Manager() as h3:
        x = h3.system()
        typer.echo(f"Release: {x.release}")
        typer.echo(f"Compatible API: {x.compatible_api}")
        typer.echo(f"Podman API: {x.podman_api}")


@app.command()
def info(namespace: str):
    """
    Show namespace information.
    """
    with H3Manager() as h3:
        ns = Namespace(namespace)
        try:
            typer.echo(pprint.pformat(h3.info(ns).asdict()))
        except NotFound:
            typer.secho(f"Pod {ns} not found", fg=typer.colors.RED, bold=True)
            raise typer.Exit(EXIT_CODE.FAILURE)


@app.command()
def stop(
    namespace: Optional[str] = typer.Argument(None),
    all: bool = typer.Option(False, "--all"),
):
    """
    Stop namespace.
    """
    with H3Manager() as h3:
        if all:
            assert not namespace
            h3.stop_all()
        else:
            assert namespace
            h3.stop(Namespace(namespace))


@app.command()
def ls():
    """
    List namespaces.
    """
    with H3Manager() as h3:
        for ns in h3.namespaces():
            typer.echo(str(ns))


def rich_state(state: str):
    if state == "running":
        return typer.style("✔", fg=typer.colors.GREEN) + " running"
    return typer.style("✘", fg=typer.colors.RED) + f" {state}"


@app.command()
def state(namespace: str):
    """
    Show namespace state.
    """
    with H3Manager() as h3:
        ns = Namespace(namespace)
        try:
            st = h3.state(ns)
            typer.echo("Master: " + rich_state(st.master))
            typer.echo("Worker: " + rich_state(st.worker))
        except NotFound:
            typer.secho(f"Pod {ns} not found", fg=typer.colors.RED, bold=True)
            raise typer.Exit(EXIT_CODE.FAILURE)


@app.command()
def start(
    hmmfile: Path,
    force: bool = typer.Option(
        False, "--force", help="Stop namespace first if it already exists."
    ),
):
    """
    Start daemon.
    """
    with H3Manager() as h3:
        x = HMMFile(hmmfile)
        try:
            pod = h3.start(x, force)
            typer.echo(f"Daemon started listening at {pod.host_ip}:{pod.host_port}")
        except APIError as err:
            if err.status_code == 409:
                msg = f"Pod and/or containers within the namespace {x.namespace} already exist."
                typer.secho(msg, fg=typer.colors.RED, bold=True)
                raise typer.Exit(EXIT_CODE.FAILURE)
            h3.rm_quietly(x.namespace)


@app.command()
def press(hmmfile: Path):
    """
    Press hmmer3 ASCII file.
    """
    with H3Manager() as h3:
        h3.hmmpress(HMMFile(hmmfile))
