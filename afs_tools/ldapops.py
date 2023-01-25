from dataclasses import dataclass
from typing import Dict, List, Tuple

import ldap  # type: ignore

from afs_tools.config import LdapConfig


@dataclass(frozen=True)
class LDAPUser:
    dn: str
    uid: str
    uidNumber: int
    gidNumber: int


def users_search(
    cfg: LdapConfig, client: ldap.ldapobject.LDAPObject
) -> List[LDAPUser]:
    ldap_search_id = client.search(
        cfg.user_base, ldap.SCOPE_SUBTREE, cfg.user_filter
    )

    result_type, result_data = client.result(ldap_search_id, 1)

    if result_type != ldap.RES_SEARCH_RESULT:
        return []

    results = []
    for user in result_data:
        dn, user = user
        uid = user["uid"][0].decode()
        uidNumber = int(user["uidNumber"][0].decode())
        gidNumber = int(user["gidNumber"][0].decode())
        results.append(LDAPUser(dn, uid, uidNumber, gidNumber))
    return results
