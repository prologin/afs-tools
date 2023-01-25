from afs_tools import ldapops, afsops
from typing import List, Optional


def sync_users(ctx, users: Optional[List[str]] = None):
    ldap_users = ldapops.users_search(ctx.obj["CFG"].ldap, ctx.obj["LDAP"])
    pts_users = afsops.pts_get_users(ctx.obj["CFG"].afs)

    ldap_logins = {user.uid for user in ldap_users}
    pts_logins = {user.name for user in pts_users}

    logins_to_create = ldap_logins - pts_logins
    logins_to_delete = pts_logins - ldap_logins

    for login in logins_to_create:
        ldap_user = [user for user in ldap_users if user.uid == login][0]
        afsops.pts_create_user(ctx.obj["CFG"].afs, login, ldap_user.uidNumber)

    for login in logins_to_delete:
        afsops.pts_delete_user(ctx.obj["CFG"].afs, login)
