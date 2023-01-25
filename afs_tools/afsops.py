from dataclasses import dataclass
from itertools import islice
from pathlib import Path
from typing import List, Optional, Set

from sh import chown, cp, fs, mkdir, pts, vos  # type: ignore

from afs_tools import utils
from afs_tools.config import AfsConfig


@dataclass(frozen=True)
class PtsUser:
    name: str
    uid: int
    owner: int
    creator: int


@dataclass(frozen=True)
class VosAddr:
    addr: str


@dataclass(frozen=True)
class VosPart:
    addr: VosAddr
    part: str


@dataclass(frozen=True)
class VosVolume:
    name: str
    vol_id: int
    vol_type: str
    size_kb: int
    status: str


def pts_get_users(cfg: AfsConfig) -> List[PtsUser]:
    results = []

    entries = pts.listentries(*cfg.pts_default_args, "-users", _iter="out")
    entries = islice(entries, 1, None)  # Skip first line, it's a header
    for entry in entries:
        name, uid, owner, creator = entry.strip().split()
        if name in cfg.pts_ignore_users:
            continue
        results.append(PtsUser(name, int(uid), int(owner), int(creator)))

    return results


def pts_create_user(cfg: AfsConfig, name: str, uid: int, dry: bool = False):
    cmd = pts.createuser.bake(*cfg.pts_default_args, "-name", name, "-id", uid)
    utils.cmd_dry(cmd, dry)


def pts_delete_user(cfg: AfsConfig, name: str, dry: bool = False):
    cmd = pts.removeuser.bake(*cfg.pts_default_args, "-user", name)
    utils.cmd_dry(cmd, dry)


def vos_get_addrs(cfg: AfsConfig) -> List[VosAddr]:
    return list(
        VosAddr(addr.strip())
        for addr in vos.listaddr(*cfg.vos_default_args, _iter="out")
    )


def vos_get_parts(cfg: AfsConfig, addr: VosAddr) -> List[VosPart]:
    results = []

    entries = vos.listpart(
        *cfg.vos_default_args, "-server", addr.addr, _iter="out"
    )
    # Skip first and last lines, they are headers and footers
    entries = list(islice(entries, 1, None))[:-1]
    for entry in entries:
        results.append(VosPart(addr, entry.strip()))

    return results


def vos_listvol(
    cfg: AfsConfig, addr: VosAddr, part: Optional[VosPart] = None
) -> List[VosVolume]:
    results = []

    # TODO: user `-extended -format` for parsing
    args = [*cfg.vos_default_args, "-server", addr.addr]
    if part:
        args += ["-partition", part.part]

    entries = vos.listvol(*args)
    # Skip first and last lines, they are headers and footers
    entries = list(islice(entries, 1, None))[:-2]

    for entry in entries:
        # Entry is not healthy, do not consider it:
        # **** Volume <volume_ID> is busy ****
        # **** Could not attach volume <volume_ID> ****
        if "****" in entry:
            continue

        entry = entry.strip()
        if not entry:
            continue

        name, vol_id, vol_type, size, _, status = entry.split()
        results.append(
            VosVolume(name, int(vol_id), vol_type, int(size), status)
        )

    return results


def vos_get_user_volumes(cfg: AfsConfig) -> Set[VosVolume]:
    results = set()

    for addr in vos_get_addrs(cfg):
        for part in vos_get_parts(cfg, addr):
            for vol in vos_listvol(cfg, addr, part):
                # Only get user volumes
                # Exclude backup volumes
                if vol.name.startswith(
                    cfg.user_volume_prefix
                ) and not vol.name.endswith(".backup"):
                    results.add(vol)

    return results


def vos_create_volume(
    cfg: AfsConfig, part: VosPart, name: str, dry: bool = False
):
    cmd = vos.create.bake(
        *cfg.vos_default_args,
        "-server",
        part.addr.addr,
        "-partition",
        part.part,
        "-name",
        name,
        "-maxquota",
        cfg.user_volume_quota,
    )
    utils.cmd_dry(cmd, dry)


def fs_configure_volume_mount(
    cfg: AfsConfig, volume_name: str, login: str, dry: bool = False
) -> Path:
    home_path = Path(cfg.user_base)
    user_paths = utils.home_path(cfg, login)

    for path in user_paths[:-1]:
        home_path /= path
        utils.cmd_dry(mkdir.bake("-p", home_path), dry)
        utils.cmd_dry(chown.bake("root:root", home_path), dry)
    home_path /= user_paths[-1]

    utils.cmd_dry(fs.bake("checkvolumes"), dry)
    utils.cmd_dry(
        fs.bake("mkmount", "-dir", home_path, "-vol", volume_name, "-rw"), dry
    )

    utils.cmd_dry(fs.bake("checkvolumes"), dry)
    utils.cmd_dry(
        fs.bake(
            "setacl", "-dir", home_path, "-acl", login, cfg.user_volume_acl
        ),
        dry,
    )

    return home_path


def fs_home_from_skeleton(
    cfg: AfsConfig,
    home_path: Path,
    uidNumber: int,
    gidNumber: int,
    dry: bool = False,
):
    utils.cmd_dry(cp.bake("-a", cfg.user_home_skeleton, home_path / "u"), dry)
    utils.cmd_dry(chown.bake("-R", f"{uidNumber}:{gidNumber}", home_path), dry)


def vos_delete_volume(cfg: AfsConfig, name: str, dry: bool = False):
    cmd = vos.remove.bake(*cfg.vos_default_args, "-id", name)
    utils.cmd_dry(cmd, dry)
