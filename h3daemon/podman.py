from podman import PodmanClient

__all__ = ["get_podman", "connect_podman", "close_podman", "is_uri_online"]

_podman: PodmanClient | None = None


def get_podman():
    assert _podman
    return _podman


def connect_podman(uri: str):
    global _podman
    _podman = PodmanClient(base_url=uri)


def close_podman():
    global _podman
    if _podman:
        _podman.close()
        _podman = None


def is_uri_online(uri: str) -> bool:
    try:
        with PodmanClient(base_url=uri) as clt:
            clt.ping()
            return True
    except Exception:
        return False
