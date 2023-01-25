#! /usr/bin/env python3

import logging
import os
from pathlib import Path

import click
import dataconf
import ldap  # type: ignore

from afs_tools.config import Config
from afs_tools.sync import sync_users, sync_volumes

_logger = logging.getLogger(__name__)


@click.group()
@click.option(
    "-c",
    "--config",
    type=click.Path(dir_okay=False),
    default="/etc/afs_tools.yml",
    help="Path to the configuration file.",
)
@click.option("-n", "--dry-run", default=False, is_flag=True)
@click.pass_context
def main(ctx, config: Path, dry_run: bool):
    cfg = dataconf.multi.dict({"ldap": {}, "afs": {}})

    if config and os.path.exists(config):
        cfg = cfg.file(str(config))

    ctx.ensure_object(dict)
    ctx.obj["CFG"] = cfg.on(Config)

    ldap_ = ldap.initialize(ctx.obj["CFG"].ldap.uri)
    if ctx.obj["CFG"].ldap.bind_dn:
        ldap_.simple_bind_s(
            ctx.obj["CFG"].ldap.bind_dn, ctx.obj["CFG"].ldap.bind_password
        )
    ctx.obj["LDAP"] = ldap_

    ctx.obj["DRY"] = dry_run


@main.group
@click.pass_context
def sync(ctx):
    pass


@sync.command()
@click.argument("users", nargs=-1)
@click.pass_context
def users(ctx, users):
    sync_users(ctx, set(users))


@sync.command()
@click.option("-u", "--users", multiple=True)
@click.option("-v", "--volumes", multiple=True)
@click.pass_context
def volumes(ctx, users, volumes):
    sync_volumes(ctx, set(users), set(volumes))


if __name__ == "__main__":
    main()
