"""PBS commands for remote server."""
import click as ck

from pybs.server import PBSServer
from pybs.console.tabcomplete import complete_hostname

@ck.command()
@ck.argument(
    "hostname",
    type=str,
    shell_complete=complete_hostname,
)
@ck.argument(
    "job_id",
    required=False,
    type=ck.STRING,
)
def stat(
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
    stdout, stderr = server.stat(job_id)
    ck.echo(stdout)
    ck.echo(stderr)

@ck.command()
@ck.argument(
    "hostname",
    type=str,
    shell_complete=complete_hostname,
)
@ck.argument(
    "job_script",
    type=ck.STRING,
    shell_complete=complete_hostname,
)
@ck.option("--job-script-location", type=ck.Choice(["local", "remote"]), default=None)
def sub(
    hostname: str,
    job_script: str,
    job_script_location: str,
):
    """Submit a job to a remote server."""
    server = PBSServer(hostname)
    stdout, stderr = server.sub(job_script, job_script_location)
    ck.echo(stdout)
    ck.echo(stderr)
