from __future__ import annotations

from dataclasses import asdict, dataclass

from podman.domain.pods import Pod

from h3daemon.container import H3ContainerInfo
from h3daemon.health import Health
from h3daemon.hmmfile import HMMFile
from h3daemon.master import Master
from h3daemon.namespace import Namespace
from h3daemon.podman import get_podman
from h3daemon.worker import Worker

__all__ = ["H3Pod", "H3PodInfo"]


HMMPGMD_PORT = 51371
PORTMAPPING = {
    "host_ip": "0.0.0.0",
    "host_port": 0,
    "container_port": HMMPGMD_PORT,
    "protocol": "tcp",
}


class H3Pod:
    def __init__(
        self, hmmfile: HMMFile | None = None, namespace: Namespace | None = None
    ):
        self._hmmfile: HMMFile | None = hmmfile
        self._namespace: Namespace | None = namespace
        self._pod: Pod | None = None
        self._master = Master(hmmfile=hmmfile, namespace=namespace)
        self._worker = Worker(hmmfile=hmmfile, namespace=namespace)

    @property
    def hmmfile(self):
        assert self._hmmfile
        return self._hmmfile

    @hmmfile.setter
    def hmmfile(self, hmmfile: HMMFile):
        self._hmmfile = hmmfile

    @property
    def namespace(self):
        if self._namespace:
            return self._namespace

        return self.hmmfile.namespace

    @namespace.setter
    def namespace(self, ns: Namespace):
        self._namespace = ns

    @property
    def name(self):
        return self.namespace.pod

    @property
    def pod(self):
        assert self._pod
        return self._pod

    @property
    def host_port(self) -> int:
        attrs = self.pod.attrs
        return int(attrs["InfraConfig"]["PortBindings"]["51371/tcp"][0]["HostPort"])

    @property
    def host_ip(self):
        attrs = self.pod.attrs
        return attrs["InfraConfig"]["PortBindings"][f"{HMMPGMD_PORT}/tcp"][0]["HostIp"]

    def start(self, port: int = 0):
        self._create_pod(port)
        self._master.create_container(self.pod)
        self._worker.create_container(self.pod)
        self._master.start()
        self._worker.start()

    def stop(self):
        pod = get_podman().pods.get(self.name)
        pod.stop(timeout=1)
        pod.remove(force=True)

    def exists(self):
        return get_podman().pods.exists(self.name)

    def _create_pod(self, port: int = 0):
        clt = get_podman()
        name = self.namespace.pod
        pm = PORTMAPPING.copy()
        pm["host_port"] = port
        self._pod = clt.pods.create(name, portmappings=[pm], read_only_filesystem=True)

    def info(self):
        pod = get_podman().pods.get(self.name)
        binding = pod.attrs["InfraConfig"]["PortBindings"]["51371/tcp"][0]
        ip = binding["HostIp"]
        port = int(binding["HostPort"])
        master = self._master.info()
        worker = self._master.info()
        return H3PodInfo.create(master, worker, ip, port)


@dataclass
class H3PodInfo:
    master: H3ContainerInfo
    worker: H3ContainerInfo
    ip: str
    port: int
    health: Health

    @classmethod
    def create(
        cls, master: H3ContainerInfo, worker: H3ContainerInfo, ip: str, port: int
    ):
        failing_streak = max(master.health.failing_streak, worker.health.failing_streak)
        status = master.health.status
        if status == "healthy":
            status = worker.health.status
        return cls(master, worker, ip, port, Health(status, failing_streak))

    def asdict(self):
        return asdict(self)
