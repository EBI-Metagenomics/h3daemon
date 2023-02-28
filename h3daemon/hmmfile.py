from pathlib import Path
from pidlockfile import PIDLockFile

__all__ = ["HMMFile"]


class HMMFile:
    def __init__(self, file: Path):
        self._file = file.absolute()

        if not file.name.endswith(".hmm"):
            raise ValueError(f"`{file}` does not end with `.hmm`.")

        if not file.exists():
            raise ValueError(f"`{file}` does not exist.")

        extensions = ["h3f", "h3i", "h3m", "h3p"]
        for x in extensions:
            filename = Path(f"{file}.{x}")
            if not filename.exists():
                raise ValueError(f"`{filename.name}` must exist as well.")

        self._pidfile = PIDLockFile(f"{self._file}.pid", timeout=5)

    def __str__(self):
        return str(self._file)

    @property
    def pidfile(self):
        return self._pidfile

    @property
    def workdir(self) -> str:
        return str(self._file.parent)
