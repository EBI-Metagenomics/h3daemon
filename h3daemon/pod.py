from pathlib import Path

from podman import PodmanClient
from podman.domain.containers import Container
from podman.domain.pods import Pod

from h3daemon.images import H3MASTER_IMAGE, H3WORKER_IMAGE, fetch_image
from h3daemon.namespace import Namespace

__all__ = ["H3Pod"]

HEALTHCHECK = {
    "Test": ["CMD-SHELL", "healthcheck || exit 1"],
    "Timeout": int(3e9),
    "Retries": int(3),
    "Interval": int(3e9),
}

WORKING_DIR = "/data"
HMMPGMD_PORT = 51371
PORTMAPPING = {
    "host_ip": "0.0.0.0",
    "host_port": 0,
    "container_port": HMMPGMD_PORT,
    "protocol": "tcp",
}


class H3Pod:
    def __init__(self, hmmfile: Path):
        self._hmmfile = hmmfile.resolve()
        self._namespace = Namespace.from_hmmfile(self._hmmfile)
        self._pod: Pod | None = None
        self._master: Container | None = None
        self._worker: Container | None = None

    @property
    def namespace(self):
        return self._namespace

    @property
    def host_port(self) -> int:
        assert self._pod
        bindings = self._pod.attrs["InfraConfig"]["PortBindings"]
        return int(bindings["51371/tcp"][0]["HostPort"])

    @property
    def host_ip(self):
        assert self._pod
        bindings = self._pod.attrs["InfraConfig"]["PortBindings"]
        return bindings["51371/tcp"][0]["HostIp"]

    def create(self, clt: PodmanClient, port: int):
        name = self._namespace.pod
        pm = PORTMAPPING.copy()
        pm["host_port"] = port
        self._pod = clt.pods.create(name, portmappings=[pm], read_only_filesystem=True)
        self._master = self._create_master(clt)
        self._worker = self._create_worker(clt)

    def _create_master(self, clt: PodmanClient):
        return clt.containers.create(
            fetch_image(clt, H3MASTER_IMAGE),
            command=[self._hmmfile.name],
            name=self._namespace.master,
            detach=True,
            tty=True,
            pod=self._pod,
            overlay_volumes=self._overlay_volumes(),
            working_dir=WORKING_DIR,
            healthcheck=HEALTHCHECK,
        )

    def _create_worker(self, clt: PodmanClient):
        return clt.containers.create(
            fetch_image(clt, H3WORKER_IMAGE),
            name=self._namespace.worker,
            detach=True,
            tty=True,
            pod=self._pod,
            overlay_volumes=self._overlay_volumes(),
            working_dir=WORKING_DIR,
            healthcheck=HEALTHCHECK,
        )

    def start(self):
        assert self._master
        assert self._worker
        self._master.start()
        self._worker.start()

    def _datadir(self):
        return self._hmmfile.parent

    def _overlay_volumes(self):
        return [{"source": str(self._datadir()), "destination": "/data"}]
