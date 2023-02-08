import sys
from functools import lru_cache
from json import loads
from shutil import which
from subprocess import (
    DEVNULL,
    PIPE,
    STDOUT,
    CalledProcessError,
    Popen,
    check_output,
    run,
)

from packaging.version import parse as parse_version

__all__ = ["PodmanRuntime"]


class PodmanRuntime:
    def __init__(self):
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
            msg = f"Installed Podman is too old: {version} < {self.minimum_version}."
            raise RuntimeError(msg)

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
        with Popen(cmd, shell=False, stdout=PIPE, stderr=STDOUT, text=True) as proc:
            assert proc.stdout
            for data in proc.stdout:
                print(data, end="")
        if proc.returncode:
            raise CalledProcessError(proc.returncode, cmd)

    def _machine_start(self):
        cmd = [self.podman, "machine", "start", self._machine_name]
        with Popen(cmd, shell=False, stdout=PIPE, stderr=STDOUT, text=True) as proc:
            assert proc.stdout
            for data in proc.stdout:
                print(data, end="")
        if proc.returncode:
            raise CalledProcessError(proc.returncode, cmd)

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
        raise RuntimeError("Failed to infer Podman API URI.")
