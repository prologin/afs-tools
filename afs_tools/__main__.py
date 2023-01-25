#! /usr/bin/env python3

import logging

import click
import dataconf
import ldap  # type: ignore

from afs_tools.sync import sync_users
from afs_tools.config import Config

_logger = logging.getLogger(__name__)


@click.group()
@click.option("-c", "--config")
@click.pass_context
def main(ctx, config):
    cfg = dataconf.multi.dict({"ldap": {}, "afs": {}})

    if config:
        cfg = cfg.file(config)

    ctx.ensure_object(dict)
    ctx.obj["CFG"] = cfg.on(Config)

    ldap_ = ldap.initialize(ctx.obj["CFG"].ldap.uri)
    if ctx.obj["CFG"].ldap.bind_dn:
        ldap_.simple_bind_s(
            ctx.obj["CFG"].ldap.bind_dn, ctx.obj["CFG"].ldap.bind_password
        )
    ctx.obj["LDAP"] = ldap_


@main.group
@click.pass_context
def sync(ctx):
    pass


@sync.command()
@click.argument("users", nargs=-1)
@click.pass_context
def users(ctx, users):
    sync_users(ctx, users)


@sync.command()
@click.argument("volumes", nargs=-1)
@click.pass_context
def volumes(ctx, volumes):
    print(f"syncing vol {volumes}")


if __name__ == "__main__":
    main()
