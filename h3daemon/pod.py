from podman import PodmanClient
from podman.domain.containers import Container
from podman.domain.images import Image
from podman.domain.pods import Pod

from h3daemon.hmmfile import HMMFile

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
    def __init__(self, hmmfile: HMMFile, master_image: Image, worker_image: Image):
        self._hmmfile = hmmfile
        self._pod: Pod | None = None
        self._master: Container | None = None
        self._worker: Container | None = None
        self._master_image = master_image
        self._worker_image = worker_image

    @property
    def namespace(self):
        return self._hmmfile.namespace

    @property
    def host_port(self) -> int:
        assert self._pod
        bindings = self._pod.attrs["InfraConfig"]["PortBindings"]
        return int(bindings["51371/tcp"][0]["HostPort"])

    @property
    def host_ip(self):
        assert self._pod
        bindings = self._pod.attrs["InfraConfig"]["PortBindings"]
        return bindings[f"{HMMPGMD_PORT}/tcp"][0]["HostIp"]

    def start(self, clt: PodmanClient):
        name = self.namespace.pod
        pm = PORTMAPPING
        self._pod = clt.pods.create(name, portmappings=[pm], read_only_filesystem=True)
        self._master = self._create_master(clt)
        self._worker = self._create_worker(clt)
        assert self._master
        assert self._worker
        self._master.start()
        self._worker.start()

    def _create_master(self, clt: PodmanClient):
        return clt.containers.create(
            self._master_image,
            command=[self._hmmfile.name],
            name=self.namespace.master,
            detach=True,
            tty=True,
            pod=self._pod,
            overlay_volumes=self._overlay_volumes(),
            working_dir=WORKING_DIR,
            healthcheck=HEALTHCHECK,
            remove=True,
        )

    def _create_worker(self, clt: PodmanClient):
        return clt.containers.create(
            self._worker_image,
            name=self.namespace.worker,
            detach=True,
            tty=True,
            pod=self._pod,
            overlay_volumes=self._overlay_volumes(),
            working_dir=WORKING_DIR,
            healthcheck=HEALTHCHECK,
            remove=True,
        )

    def _overlay_volumes(self):
        return [{"source": str(self._hmmfile.dir), "destination": "/data"}]
