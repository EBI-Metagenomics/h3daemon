from __future__ import annotations

import signal

from podman import PodmanClient
from podman.domain.containers import Container
from podman.errors import APIError

from h3daemon.env import get_env
from h3daemon.hmmfile import HMMFile
from h3daemon.images import H3MASTER_IMAGE, H3WORKER_IMAGE, HMMPRESS_IMAGE
from h3daemon.info import H3Info
from h3daemon.namespace import Namespace, NamespaceInfo
from h3daemon.pod import H3Pod
from h3daemon.state import State

__all__ = ["H3Manager"]


class H3Manager:
    def __init__(self):
        env = get_env()
        self._podman = PodmanClient(base_url=env.H3DAEMON_URI)

    def system(self):
        x = self._podman.version()
        details = x["Components"][0]["Details"]
        return H3Info(x["Version"], x["ApiVersion"], details["APIVersion"])

    def info(self, ns: Namespace):
        info = NamespaceInfo()
        pod = self._podman.pods.get(ns.pod)

        x = [i for i in pod.attrs["Containers"] if i["Name"] == ns.master]
        if len(x) > 0:
            info.master.state = x[0]["State"]

        x = [i for i in pod.attrs["Containers"] if i["Name"] == ns.worker]
        if len(x) > 0:
            info.worker.state = x[0]["State"]

        binding = pod.attrs["InfraConfig"]["PortBindings"]["51371/tcp"][0]
        info.host.ip = binding["HostIp"]
        info.host.port = binding["HostPort"]

        return info

    def start(self, hmmfile: HMMFile, force=False):
        master_image = self.fetch_image(H3MASTER_IMAGE)
        worker_image = self.fetch_image(H3WORKER_IMAGE)
        pod = H3Pod(hmmfile, master_image, worker_image)
        if force:
            self.stop(pod.namespace)
        pod.start(self._podman)
        return pod

    def stop(self, ns: Namespace):
        if self._podman.pods.exists(ns.pod):
            pod = self._podman.pods.get(ns.pod)
            pod.stop(timeout=1)
            pod.remove(force=True)

    def stop_all(self):
        for ns in self.namespaces():
            pod = self._podman.pods.get(ns.pod)
            pod.stop(timeout=1)
            pod.remove(force=True)

    def state(self, ns: Namespace):
        info = self.info(ns)
        return State(info.worker.state, info.master.state)

    def namespaces(self):
        names = [x.name for x in self._podman.pods.list() if x.name]
        names += [x.name for x in self._podman.containers.list() if x.name]
        names = [Namespace.from_qualname(x) for x in names if Namespace.check(x)]
        return set(names)

    def hmmpress(self, hmmfile: HMMFile):
        workdir = "/data"
        ct = self._podman.containers.run(
            self.fetch_image(HMMPRESS_IMAGE),
            command=["-f", str(hmmfile.name)],
            stdout=True,
            stderr=True,
            remove=True,
            mounts=[{"type": "bind", "source": str(hmmfile.dir), "target": workdir}],
            working_dir=workdir,
            detach=True,
        )
        assert isinstance(ct, Container)

        if ct.wait() != 0:
            logs = ct.logs()
            assert not isinstance(logs, bytes)
            raise RuntimeError("".join([x.decode() for x in logs]))

    def fetch_image(self, name: str, force=False):
        if force or not self._podman.images.exists(name):
            self._podman.images.pull(name)
        return self._podman.images.get(name)

    def close(self):
        self._podman.close()

    def __enter__(self) -> H3Manager:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        del exc_type
        del exc_value
        del traceback
        self.close()

    def rm_quietly(self, ns: Namespace):
        try:
            pod = self._podman.pods.get(ns.pod)
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
