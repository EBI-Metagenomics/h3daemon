from json import loads
from shutil import which
from subprocess import check_output

__all__ = ["Local"]


HINT = "HINT: Set the H3DAEMON_URI environment variable."


class Local:
    def __init__(self):
        self._prog = which("podman")
        if not self._prog:
            raise RuntimeError(f"Could not find podman executable. {HINT}")

    def api_uri(self):
        cmd = [self._prog, "system", "connection", "list", "--format=json"]
        out = check_output(cmd, shell=False).decode()
        for i in loads(out):
            if i["Default"]:
                return i["URI"]
        raise RuntimeError(f"Failed to infer the Podman API URI. {HINT}")

    def assert_running_state(self):
        cmd = [self._prog, "machine", "info", "--format", "json"]
        out = check_output(cmd, shell=False).decode()
        x = loads(out)
        if x["Host"]["MachineState"] != "Running":
            raise RuntimeError(f"Local Podman machine is not running. {HINT}")
