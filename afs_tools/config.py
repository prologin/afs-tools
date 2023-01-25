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


@dataclass
class Config:
    ldap: LdapConfig = field(default_factory=LdapConfig)
    afs: AfsConfig = field(default_factory=AfsConfig)
