from __future__ import annotations
from platformdirs import user_runtime_dir
from pathlib import Path

import signal
from dataclasses import dataclass

from podman.errors import APIError

from h3daemon.env import get_env
from h3daemon.namespace import Namespace
from h3daemon.podman import close_podman, connect_podman, get_podman, is_uri_online
from h3daemon.podman_runtime import PodmanRuntime

__all__ = ["H3Manager", "SysInfo"]


@dataclass
class SysInfo:
    release: str
    compatible_api: str
    podman_api: str


class H3Manager:
    def sys(self):
        x = get_podman().version()
        details = x["Components"][0]["Details"]
        return SysInfo(x["Version"], x["ApiVersion"], details["APIVersion"])

    def namespaces(self):
        names = [x.name for x in get_podman().pods.list() if x.name]
        names += [x.name for x in get_podman().containers.list() if x.name]
        names = [Namespace.from_qualname(x) for x in names if Namespace.check(x)]
        return set(names)

    def close(self):
        close_podman()

    def _try_user_sock_file(self):
        sock_file = (Path(user_runtime_dir("podman")) / "podman.sock").resolve()
        uri = f"unix://{str(sock_file)}"
        return sock_file.exists() or is_uri_online(uri)

    def __enter__(self) -> H3Manager:
        env = get_env()
        uri = env.H3DAEMON_URI if env.H3DAEMON_URI else ""

        if not is_uri_online(uri):
            # Try user sock file
            sock_file = (Path(user_runtime_dir("podman")) / "podman.sock").resolve()
            uri = f"unix://{str(sock_file)}"

        if not is_uri_online(uri):
            # Try Podman runtime
            x = PodmanRuntime()
            x.ensure_running()
            uri = x.api_uri()

        connect_podman(uri)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        del exc_type
        del exc_value
        del traceback
        self.close()

    def rm_quietly(self, ns: Namespace):
        try:
            pod = get_podman().pods.get(ns.pod)
        except APIError:
            return

        try:
            pod.kill(signal.SIGKILL)
        except APIError:
            pass

        try:
            pod.remove(force=True)
        except APIError:
            pass
