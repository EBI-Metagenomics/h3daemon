from podman.domain.containers import Container

from h3daemon.hmmfile import HMMFile
from h3daemon.images import HMMPRESS_IMAGE
from h3daemon.podman import get_podman

__all__ = ["hmmpress"]


def hmmpress(hmmfile: HMMFile):
    workdir = "/data"
    clt = get_podman()
    if not clt.images.exists(HMMPRESS_IMAGE):
        clt.images.pull(HMMPRESS_IMAGE, tag="latest")

    ct = clt.containers.run(
        clt.images.get(HMMPRESS_IMAGE),
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
