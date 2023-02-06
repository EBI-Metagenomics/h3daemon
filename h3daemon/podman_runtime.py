import sys
from json import loads
from shutil import which
from subprocess import check_output, check_call
from typer import get_binary_stream

__all__ = ["PodmanRuntime"]


HINT = "HINT: Set the H3DAEMON_URI environment variable."


class PodmanRuntime:
    def __init__(self):
        self.stdout = get_binary_stream("stdout")
        self.stderr = get_binary_stream("stderr")
        self._prog = which("podman")
        if not self._prog:
            raise RuntimeError(f"Could not find Podman executable. {HINT}")

    @property
    def _machine_name(self):
        return "podman-machine-default"

    def _is_there_default_vm(self):
        cmd = [self._prog, "machine", "list", "--format", "json"]
        out = check_output(cmd, shell=False).decode()
        for i in loads(out):
            if i["Name"] == self._machine_name:
                return True
        return False

    def _machine_inspect(self):
        cmd = [self._prog, "machine", "inspect", self._machine_name]
        out = check_output(cmd, shell=False).decode()
        return loads(out)[0]

    def _machine_init(self):
        cmd = [self._prog, "machine", "init", self._machine_name]
        check_call(cmd, shell=False, stdout=self.stdout, stderr=self.stderr)

    def _machine_start(self):
        cmd = [self._prog, "machine", "start", self._machine_name]
        check_call(cmd, shell=False, stdout=self.stdout, stderr=self.stderr)

    def _is_machine_running(self):
        return self._machine_inspect()["State"] == "running"

    def ensure_running(self):
        if sys.platform == "darwin":
            if not self._is_there_default_vm():
                self._machine_init()
            if not self._is_machine_running():
                self._machine_start()
            if not self._is_machine_running():
                raise RuntimeError("Podman VM is not running.")

    def api_uri(self):
        cmd = [self._prog, "system", "connection", "list", "--format=json"]
        out = check_output(cmd, shell=False).decode()
        for i in loads(out):
            if i["Default"]:
                return i["URI"]
        raise RuntimeError(f"Failed to infer Podman API URI. {HINT}")

    def assert_running_state(self):
        cmd = [self._prog, "machine", "info", "--format", "json"]
        out = check_output(cmd, shell=False).decode()
        x = loads(out)
        if x["Host"]["MachineState"] != "Running":
            raise RuntimeError("Podman VM is not running.")