from pathlib import Path
from typing import Callable, List

from afs_tools.config import AfsConfig


def home_path(cfg: AfsConfig, login: str) -> List[Path]:
    if cfg.user_tree == "flat":
        return [Path(login)]
    if cfg.user_tree == "split":
        return [Path(login[0:1]), Path(login[0:2]), Path(login)]
    raise ValueError(f"Unsupported user tree configuration: {cfg.user_tree}")


def cmd_dry(cmd: Callable, dry):
    if dry:
        print(cmd)
    else:
        cmd()
