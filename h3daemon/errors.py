__all__ = ["EarlyExitError", "PodInUseError"]


class EarlyExitError(RuntimeError):
    def __init__(self, msg: str):
        super().__init__(msg)
        self.msg = msg


class PodInUseError(RuntimeError):
    def __init__(self, pod_name: str):
        msg = f"⚠️  {pod_name} is already in used."
        super().__init__(msg)
        self.msg = msg
