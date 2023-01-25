from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LdapConfig:
    uri: str = "ldap://auth.pie.prologin.org"
    user_base: str = "cn=users,cn=accounts,dc=prologin,dc=org"
    user_filter: str = "(objectClass=posixAccount)"
    bind_dn: Optional[str] = None
    bind_password: Optional[str] = None


@dataclass
class AfsConfig:
    pts_default_args: List[str] = field(default_factory=lambda: ["-localauth"])
    pts_ignore_users: List[str] = field(default_factory=lambda: ["anonymous"])
    vos_default_args: List[str] = field(default_factory=lambda: ["-localauth"])
    user_volume_prefix: str = "user_"
    user_volume_quota: int = 2000000  # 2GB
    volume_creation_location: str = "mod"  # or "addr:/vicepa"
    user_base: str = "/afs/.prologin.org/user"
    user_tree: str = "split"  # or "flat"
    user_volume_acl: str = "rlidwka"  # all minus administer
    user_home_skeleton: str = "/afs/prologin.org/resources/skeleton"


@dataclass
class Config:
    ldap: LdapConfig = field(default_factory=LdapConfig)
    afs: AfsConfig = field(default_factory=AfsConfig)
