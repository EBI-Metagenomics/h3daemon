from __future__ import annotations

import signal
from enum import IntEnum
from pathlib import Path
from typing import Optional

import typer
from podman import PodmanClient
from podman.errors import APIError

from h3daemon.env import env
from h3daemon.hmmpress import hmmpress
from h3daemon.info import list_namespaces
from h3daemon.meta import __version__
from h3daemon.namespace import Namespace
from h3daemon.pod import H3Pod

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
def info():
    """
    Show Podman information.
    """
    with PodmanClient(base_url=env.H3DAEMON_URI) as clt:
        version = clt.version()
        typer.echo("Release: ", version["Version"])
        typer.echo("Compatible API: ", version["ApiVersion"])
        typer.echo("Podman API: ", version["Components"][0]["Details"]["APIVersion"])


@app.command()
def rm(
    namespace: Optional[str] = typer.Argument(None),
    all: bool = typer.Option(False, "--all"),
):
    """
    Remove namespace.
    """
    with PodmanClient(base_url=env.H3DAEMON_URI) as clt:
        if all:
            assert not namespace
            for ns in list_namespaces(clt):
                pod = clt.pods.get(ns.pod)
                pod.remove(force=True)
        else:
            assert namespace
            ns = Namespace(namespace)
            if clt.pods.exists(ns.pod):
                pod = clt.pods.get(ns.pod)
                pod.remove(force=True)


@app.command()
def stop(
    namespace: Optional[str] = typer.Argument(None),
    all: bool = typer.Option(False, "--all"),
):
    """
    Stop namespace.
    """
    with PodmanClient(base_url=env.H3DAEMON_URI) as clt:
        if all:
            assert not namespace
            for ns in list_namespaces(clt):
                pod = clt.pods.get(ns.pod)
                pod.stop(timeout=1)
        else:
            assert namespace
            ns = Namespace(namespace)
            if clt.pods.exists(ns.pod):
                pod = clt.pods.get(ns.pod)
                pod.stop(timeout=1)


@app.command()
def ls():
    """
    List namespaces.
    """
    with PodmanClient(base_url=env.H3DAEMON_URI) as clt:
        for name in list_namespaces(clt):
            typer.echo(name.name)


@app.command()
def start(hmmfile: Path):
    """
    Start daemon.
    """
    with PodmanClient(base_url=env.H3DAEMON_URI) as clt:
        pod = H3Pod(hmmfile)
        try:
            pod.create(clt, 0)
            pod.start()
            print(f"Daemon listening on {pod.host_ip}:{pod.host_port}")
        except APIError as e:
            remove_silently(pod.namespace)
            raise e


@app.command()
def press(hmmfile: Path):
    """
    Press hmmer3 ASCII file.
    """
    with PodmanClient(base_url=env.H3DAEMON_URI) as clt:
        hmmpress(clt, hmmfile)


def remove_silently(namespace: Namespace):
    with PodmanClient(base_url=env.H3DAEMON_URI) as clt:
        if clt.pods.exists(namespace.pod):
            pod = clt.pods.get(namespace.pod)
            try:
                pod.kill(signal.SIGKILL)
            except APIError:
                pass

            try:
                pod.remove(force=True)
            except APIError:
                pass
