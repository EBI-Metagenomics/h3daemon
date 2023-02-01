from pathlib import Path

from platformdirs import user_runtime_dir

from h3daemon.local import Local

__all__ = ["infer_api_uri"]

def infer_api_uri():
    uri = (Path(user_runtime_dir("podman")) / "podman.sock").resolve()
    if uri.exists():
        return f"unix://{str(uri)}"

    local = Local()
    local.assert_running_state()
    return local.api_uri()
