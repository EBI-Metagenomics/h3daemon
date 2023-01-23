from pathlib import Path

from podman import PodmanClient
from podman.domain.containers import Container

from h3daemon.images import HMMPRESS_IMAGE, fetch_image

__all__ = ["hmmpress"]

WORKING_DIR = "/data"


def hmmpress(clt: PodmanClient, hmmfile: Path):
    hmmfile = hmmfile.resolve()
    ct = clt.containers.run(
        fetch_image(clt, HMMPRESS_IMAGE),
        command=["-f", str(hmmfile.name)],
        stdout=True,
        stderr=True,
        remove=True,
        mounts=[{"type": "bind", "source": str(hmmfile.parent), "target": WORKING_DIR}],
        working_dir=WORKING_DIR,
        detach=True,
    )
    assert isinstance(ct, Container)

    if ct.wait() != 0:
        logs = ct.logs()
        assert not isinstance(logs, bytes)
        raise RuntimeError("".join([x.decode() for x in logs]))
