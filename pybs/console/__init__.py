"""Command line interface for PyBS."""

import sys
import click as ck
import subprocess

from pathlib import Path
from loguru import logger as log

log.add(sys.stderr, level="INFO")
from pybs.server import PBSServer

POLL_INTERVAL = 0.5

# TODO:
# - add help to ck args
# - add tab autocompletion scripts 
# - add hostname tab completion (use ~/.ssh/config)
# - add support for local job scripts
# - add intelligent remote server expansion of paths example $SCRATCH
# - add auto install of ssh config required hostname alias
# - fix logging for qsub wait
# - add arbitrary command execution for any method (with certain decorator)
# from PBSServer class
# e.g. write `qsub` and this will call the `qsub` method of the PBSServer class
# if a method with that name exists.
# - refactoring of PBSServer class to use `ssh_command` decorator

# Future TODO: 
# - add db for currently running jobs, able to login to 
# any server and see resources, walltime etc. 

from sshconf import read_ssh_config
from os.path import expanduser
from pybs import SSH_CONFIG_PATH

def complete_hostname(ctx, param, incomplete):
    """Tab completion for HOSTNAME CLI argument."""
    log.debug(f"Completing {param}: {incomplete}")
    log.debug(f"Context: {ctx.params}")
    c = read_ssh_config(expanduser(SSH_CONFIG_PATH))    
    hostnames = c.hosts()
    return [h for h in hostnames if incomplete in h]


    
from .completion import complete_remote_path

@ck.command()
@ck.argument(
    "hostname", type=str, shell_complete=complete_hostname,
)
@ck.argument(
    "remote_path",
    type=ck.Path(
        exists=False,
        path_type=Path,
    ),
    shell_complete=complete_remote_path, 
)
@ck.argument(
    "job_script",
    type=ck.Path(
        exists=False,
        path_type=Path,
    ),
)
@ck.option("--verbose/--no-verbose", default=False)
@ck.option("--debug/--no-debug", default=False)
def code(
    hostname: str,
    remote_path: Path,
    job_script: Path,
    debug: bool = False,
    verbose: bool = True,
):
    """Launch a job on a remote server and open VScode.

    This allows interactive use of GPU compute nodes, such as with a Jupyter notebook.
    """

    if debug:
        log.debug(f"Debug mode enabled")
    log.debug(f"Launching job on {hostname} with remote path {remote_path}")
    log.debug(type(remote_path))

    server = PBSServer(hostname, verbose=verbose)

    if verbose:
        print(f"Submitting job to {hostname} with job script {job_script}...")
    job_id = server.submit_job(job_script)
    if verbose:
        print(f"Job submitted with ID: {job_id}")
        print(f"Retrieving job information:", end=" ")

    info = server.job_info(job_id)
    if verbose:
        print(f"Status: {info['status']}")
    from time import sleep

    while server.get_status(job_id) != "R":
        if verbose:
            print(".", end="")
        sleep(POLL_INTERVAL)
    if verbose:
        print("Job is running.")
    info = server.job_info(job_id)
    node = info["node"]
    log.debug(info)
    if verbose:
        print(f"Checking GPU status:")
        out, err = server.check_gpu(node=node)
        print(out)
        print(err)

    # Launch VScode
    target_name = f"{hostname}-{node}"
    if verbose:
        print(f"Launching VScode on {target_name}...")
    cmd_list = ["code", "--remote", f"ssh-remote+{target_name}", remote_path]
    if debug:
        print(cmd_list)
    captured = subprocess.run(
        cmd_list,
        capture_output=True,
    )
    # kill
    if debug:
        sleep(60)
        if verbose:
            print(f"Killing job {job_id}...")
        server.kill_job(job_id)


@ck.command()
@ck.argument("hostname", type=str)
@ck.argument("job_id", type=str)
def qstat(
    hostname: str,
    job_id: str,
):
    """Get information about jobs in the queue.

    Job Status codes:
    H - Held
    Q - Queued
    R - Running
    """
    server = PBSServer(hostname)
    info = server.job_info(job_id)
    ck.echo(info)


@ck.group()
def entry_point():
    pass

entry_point.add_command(code)
entry_point.add_command(qstat)




#if __name__ == "__main__":
#    entry_point()
