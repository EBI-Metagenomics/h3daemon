from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from time import sleep
from typing import Union

from podman.domain.containers import Container
from podman.domain.images import Image
from podman.domain.pods import Pod

from h3daemon.errors import EarlyExitError
from h3daemon.health import Health
from h3daemon.hmmfile import HMMFile
from h3daemon.namespace import Namespace
from h3daemon.podman import get_podman

__all__ = ["H3Container", "H3ContainerInfo"]


class H3Container(ABC):
    def __init__(
        self,
        hmmfile: Union[HMMFile, None] = None,
        namespace: Union[Namespace, None] = None,
    ):
        self._hmmfile: Union[HMMFile, None] = hmmfile
        self._namespace: Union[Namespace, None] = namespace
        self._container: Union[Container, None] = None
        self._image: Union[Image, None] = None

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
    def container(self):
        if not self._container:
            self.fetch_container()
        assert self._container
        return self._container

    @property
    def image(self):
        if not self._image:
            self.fetch_image()
        assert self._image
        return self._image

    @image.setter
    def image(self, image: Image):
        self._image = image

    @abstractmethod
    def create_container(self, pod: Pod):
        ...

    @property
    @abstractmethod
    def container_name(self) -> str:
        ...

    @property
    @abstractmethod
    def image_name(self) -> str:
        ...

    def fetch_container(self):
        clt = get_podman()
        self._container = clt.containers.get(self.container_name)

    def fetch_image(self, force=False):
        clt = get_podman()
        if force or not clt.images.exists(self.image_name):
            clt.images.pull(self.image_name, tag="latest")
        self._image = clt.images.get(self.image_name)

    def info(self):
        x = self.container.attrs["State"]
        y = x.get("Health", x.get("Healthcheck"))
        health = Health(y["Status"], int(y["FailingStreak"]))
        return H3ContainerInfo(
            x["Status"],
            bool(x["Running"]),
            bool(x["Paused"]),
            int(x["ExitCode"]),
            health,
        )

    def logs(self) -> str:
        it = self.container.logs(stream=False)
        assert not isinstance(it, bytes)
        return "".join(list(x.decode().replace("\r\n", "\n") for x in it))

    def start(self):
        self.container.start()
        sleep(1)
        self.fetch_container()
        info = self.info()
        if info.exited:
            raise EarlyExitError(
                f"Container {self.container_name}"
                " exited with code "
                f"{info.exit_code}.\n{self.logs()}"
            )


@dataclass
class H3ContainerInfo:
    status: str
    running: bool
    paused: bool
    exit_code: int
    health: Health

    @property
    def exited(self) -> bool:
        return self.status == "exited"

    def asdict(self):
        return asdict(self)
