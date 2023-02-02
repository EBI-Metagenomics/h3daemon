from podman.domain.pods import Pod

from h3daemon.container import H3Container
from h3daemon.hmmfile import HMMFile
from h3daemon.images import H3WORKER_IMAGE
from h3daemon.namespace import Namespace
from h3daemon.podman import get_podman

HEALTHCHECK = {
    "Test": ["CMD-SHELL", "healthcheck || exit 1"],
    "Timeout": int(3e9),
    "Retries": int(3),
    "Interval": int(3e9),
}


__all__ = ["Worker"]


class Worker(H3Container):
    def __init__(
        self, hmmfile: HMMFile | None = None, namespace: Namespace | None = None
    ):
        super().__init__(hmmfile=hmmfile, namespace=namespace)

    def create_container(self, pod: Pod):
        clt = get_podman()
        vol = [{"source": str(self.hmmfile.dir), "destination": "/data"}]
        self._container = clt.containers.create(
            self.image,
            name=self.container_name,
            detach=True,
            tty=True,
            pod=pod,
            overlay_volumes=vol,
            working_dir="/data",
            healthcheck=HEALTHCHECK,
            remove=True,
        )

    @property
    def container_name(self):
        return self.namespace.worker

    @property
    def image_name(self):
        return H3WORKER_IMAGE
