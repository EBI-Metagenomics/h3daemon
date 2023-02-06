import sys
from functools import lru_cache
from json import loads
from shutil import which
from subprocess import DEVNULL, check_output, run

from packaging.version import parse as parse_version
from typer import get_binary_stream

__all__ = ["PodmanRuntime"]


class PodmanRuntime:
    def __init__(self):
        self.stdout = get_binary_stream("stdout")
        self.stderr = get_binary_stream("stderr")
        self.minimum_version = "3.4"
        self._assert_minimum_podman_version()

    @property
    @lru_cache
    def podman_version(self):
        out = check_output([self.podman, "--version"]).decode()
        return out.split(" ", 2)[2]

    @property
    @lru_cache
    def podman(self):
        x = which("podman")
        if not x:
            raise RuntimeError("Could not find Podman executable.")
        return x

    def _assert_minimum_podman_version(self):
        out = check_output([self.podman, "--version"]).decode()
        version = parse_version(out.split(" ", 2)[2])
        if version < parse_version(self.minimum_version):
            raise RuntimeError(
                f"Installed Podman is too old: {version} < {self.minimum_version}."
            )

    @property
    @lru_cache
    def systemctl(self):
        x = which("systemctl")
        if not x:
            raise RuntimeError("Could not find systemctl executable.")
        return x

    @property
    def _machine_name(self):
        return "podman-machine-default"

    def _is_there_default_vm(self):
        cmd = [self.podman, "machine", "list", "--format", "json"]
        out = check_output(cmd, shell=False).decode()
        for i in loads(out):
            if i["Name"] == self._machine_name:
                return True
        return False

    def _machine_inspect(self):
        cmd = [self.podman, "machine", "inspect", self._machine_name]
        out = check_output(cmd, shell=False).decode()
        return loads(out)[0]

    def _machine_init(self):
        cmd = [self.podman, "machine", "init", self._machine_name]
        run(cmd, shell=False, check=True, stdout=self.stdout, stderr=self.stderr)

    def _machine_start(self):
        cmd = [self.podman, "machine", "start", self._machine_name]
        run(cmd, shell=False, check=True, stdout=self.stdout, stderr=self.stderr)

    def _is_machine_running(self):
        return self._machine_inspect()["State"] == "running"

    def _enable_podman_socket(self):
        cmd = [self.systemctl, "--user", "enable", "--now", "podman.socket"]
        run(cmd, shell=False, check=True, stdout=DEVNULL, stderr=DEVNULL)

    def ensure_running(self):
        if sys.platform == "darwin":
            if not self._is_there_default_vm():
                self._machine_init()
            if not self._is_machine_running():
                self._machine_start()
            if not self._is_machine_running():
                raise RuntimeError("Podman VM is not running.")
        else:
            self._enable_podman_socket()

    def api_uri(self):
        if sys.platform == "darwin":
            cmd = [self.podman, "system", "connection", "list", "--format=json"]
            out = check_output(cmd, shell=False).decode()
            for i in loads(out):
                if i["Default"]:
                    return i["URI"]
        else:
            cmd = [self.podman, "info", "--format", "json"]
            out = check_output(cmd, shell=False).decode()
            sock_file = loads(out)["host"]["remoteSocket"]["path"]
            return f"unix://{str(sock_file)}"
        raise RuntimeError(f"Failed to infer Podman API URI. {HINT}")
