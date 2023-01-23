from pathlib import Path

from h3daemon.namespace import Namespace

__all__ = ["HMMFile"]


class HMMFile:
    def __init__(self, hmmfile: Path):
        if not hmmfile.name.endswith(".hmm"):
            raise ValueError(f"{hmmfile} does not end with .hmm")
        self._file = hmmfile.resolve()

    @property
    def name(self):
        return self._file.name

    @property
    def dir(self):
        return self._file.parent

    @property
    def namespace(self):
        return Namespace(self.name)
