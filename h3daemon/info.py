from podman import PodmanClient

from h3daemon.namespace import Namespace

__all__ = ["list_namespaces"]


def list_namespaces(clt: PodmanClient):
    names = [x.name for x in clt.pods.list() if x.name]
    names += [x.name for x in clt.containers.list() if x.name]
    names = [Namespace.from_qualname(x) for x in names if Namespace.check(x)]
    return set(names)
