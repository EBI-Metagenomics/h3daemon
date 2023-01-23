from podman import PodmanClient

__all__ = ["H3MASTER_IMAGE", "H3WORKER_IMAGE", "HMMPRESS_IMAGE", "fetch_image"]

H3MASTER_IMAGE = "quay.io/danilohorta/h3master"
H3WORKER_IMAGE = "quay.io/danilohorta/h3worker"
HMMPRESS_IMAGE = "quay.io/danilohorta/hmmpress"


def fetch_image(clt: PodmanClient, name: str, force=False):
    if force or not clt.images.exists(name):
        clt.images.pull(name)
    return clt.images.get(name)
