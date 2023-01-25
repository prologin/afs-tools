from itertools import chain
from typing import Callable, List, Optional, Set

from afs_tools import afsops, ldapops


def sync_users(ctx, users: Optional[Set[str]] = None):
    ldap_users = ldapops.users_search(ctx.obj["CFG"].ldap, ctx.obj["LDAP"])
    pts_users = afsops.pts_get_users(ctx.obj["CFG"].afs)

    ldap_logins = {user.uid for user in ldap_users}
    pts_logins = {user.name for user in pts_users}

    if users:
        ldap_logins = users & ldap_logins
        pts_logins = users & pts_logins

    logins_to_create = ldap_logins - pts_logins
    logins_to_delete = pts_logins - ldap_logins

    for login in logins_to_create:
        ldap_user = [user for user in ldap_users if user.uid == login][0]
        afsops.pts_create_user(
            ctx.obj["CFG"].afs, login, ldap_user.uidNumber, ctx.obj["DRY"]
        )

    for login in logins_to_delete:
        afsops.pts_delete_user(ctx.obj["CFG"].afs, login, ctx.obj["DRY"])


def sync_volumes(ctx, users: Set[str] = set(), volumes: Set[str] = set()):
    ldap_users = set(
        ldapops.users_search(ctx.obj["CFG"].ldap, ctx.obj["LDAP"])
    )
    vos_volumes = afsops.vos_get_user_volumes(ctx.obj["CFG"].afs)

    if users:
        ldap_users_filter: Callable[[ldapops.LDAPUser], bool] = (
            lambda user: user.uid in users
        )
        ldap_users = set(filter(ldap_users_filter, ldap_users))
    if volumes:
        vos_volumes_filter: Callable[[afsops.VosVolume], bool] = (
            lambda volume: volume.name in volumes
        )
        vos_volumes = set(filter(vos_volumes_filter, vos_volumes))

    ldap_volume_names = {
        f"{ctx.obj['CFG'].afs.user_volume_prefix}{user.uidNumber}"
        for user in ldap_users
    }
    vos_volume_names = {volume.name for volume in vos_volumes}

    volumes_to_create = ldap_volume_names - vos_volume_names
    volumes_to_delete = vos_volume_names - ldap_volume_names

    all_parts = list(
        chain(
            *[
                afsops.vos_get_parts(ctx.obj["CFG"].afs, addr)
                for addr in afsops.vos_get_addrs(ctx.obj["CFG"].afs)
            ]
        )
    )

    for volume in volumes_to_create:
        uidNumber = int(
            volume.removeprefix(ctx.obj["CFG"].afs.user_volume_prefix)
        )
        user = list(
            filter(lambda user: user.uidNumber == uidNumber, ldap_users)
        )[0]

        if ctx.obj["CFG"].afs.volume_creation_location == "mod":
            part = all_parts[uidNumber % len(all_parts)]
        else:
            addr, part = ctx.obj["CFG"].afs.volume_creation_location.split(
                ":", max_split=1
            )
            parts = list(
                filter(
                    lambda part: part.addr.addr == addr and part.part == part,
                    all_parts,
                )
            )
            if not parts:
                raise ValueError(f"Unknown location {addr}:{part}")
            part = parts[0]

        afsops.vos_create_volume(
            ctx.obj["CFG"].afs, part, volume, ctx.obj["DRY"]
        )

        home_path = afsops.fs_configure_volume_mount(
            ctx.obj["CFG"].afs, volume, user.uid, ctx.obj["DRY"]
        )

        afsops.fs_home_from_skeleton(
            ctx.obj["CFG"].afs,
            home_path,
            user.uidNumber,
            user.gidNumber,
            ctx.obj["DRY"],
        )

    for volume in volumes_to_delete:
        afsops.vos_delete_volume(ctx.obj["CFG"].afs, volume, ctx.obj["DRY"])
