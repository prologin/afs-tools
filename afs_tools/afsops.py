from dataclasses import dataclass
from itertools import islice
from sh import pts # type: ignore
from afs_tools.config import AfsConfig
from typing import List


@dataclass
class PtsUser:
    name: str
    uid: int
    owner: int
    creator: int


def pts_get_users(cfg: AfsConfig) -> List[PtsUser]:
    results = []

    entries = pts.listentries(*cfg.pts_default_args, "-users", _iter="out")
    entries = islice(entries, 1, None) # Skip first line, it's a header
    for entry in entries:
        name, uid, owner, creator = entry.strip().split()
        if name in cfg.pts_ignore_users:
            continue
        results.append(PtsUser(name, int(uid), int(owner), int(creator)))

    return results


def pts_create_user(cfg: AfsConfig, name: str, uid: int, dry: bool = False):
    cmd = pts.createuser.bake(*cfg.pts_default_args, "-name", name, "-id", uid)
    if dry:
        print(cmd)
    else:
        cmd()


def pts_delete_user(cfg: AfsConfig, name: str, dry: bool = False):
    cmd = pts.removeuser.bake(*cfg.pts_default_args, "-user", name)
    if dry:
        print(cmd)
    else:
        cmd()
