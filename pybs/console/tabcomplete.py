"""Tab completion functions for CLI arguments."""

import sys
import click as ck
import subprocess

from pathlib import Path
from os.path import expanduser
from loguru import logger as log
from sshconf import read_ssh_config

from pybs import SSH_CONFIG_PATH
from pybs.server import PBSServer


def complete_remote_path(ctx, param, incomplete):
    """Tab completion for REMOTE_PATH CLI argument."""
    log.debug(f"Completing {param}: {incomplete}")
    log.debug(f"Context: {ctx.params}")

    hostname = ctx.params["hostname"]

    server = PBSServer(hostname)

    # Generate list of remote paths that match the incomplete string
    # To find that, find the last '/' in the incomplete string
    # Then use that to filter the list of remote paths

    path = Path(incomplete)
    partial = str(path.parent)
    incomplete = path.name

    stdout, stderr = server.ls(f"{partial}*")

    log.debug(f"stdout: {stdout}")
    log.debug(f"stderr: {stderr}")

    remote_paths = stdout.split("\n")
    log.debug(f"Remote paths: {remote_paths}")
    return remote_paths
    return [p for p in remote_paths if incomplete in p]


def complete_hostname(ctx, param, incomplete):
    """Tab completion for HOSTNAME CLI argument."""
    log.debug(f"Completing {param}: {incomplete}")
    log.debug(f"Context: {ctx.params}")
    c = read_ssh_config(expanduser(SSH_CONFIG_PATH))
    hostnames = c.hosts()
    return [h for h in hostnames if incomplete in h]
