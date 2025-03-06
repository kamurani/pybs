"""Command line interface for PyBS."""

import sys
from typing import Literal
import click as ck
import subprocess

from pathlib import Path
from loguru import logger as log

#log.add(sys.stderr, level="INFO")
from pybs.server import PBSServer

from typing import (
    Any,
    BinaryIO,
    Callable,
    ContextManager,
    Deque,
    Dict,
    Generic,
    Iterable,
    List,
    NamedTuple,
    NewType,
    Optional,
    Sequence,
    TextIO,
    Tuple,
    Type,
    TypeVar,
    Union,
)


POLL_INTERVAL = 0.5

# DONE: 
# - add tab autocompletion scripts 
# - add hostname tab completion (use ~/.ssh/config)
# TODO:
# - add support for local job scripts
# - add intelligent remote server expansion of paths example $SCRATCH

# - add TUI timer for job submission
# - add help to ck args
# - add tab complete for remote paths similar to `scp```
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
# - add "autorefresh" or "keepalive" option to remember when the walltime will 
# expire, and request another GPU node that overlaps so we can keep the session logged
# in on the same node. 

    
from .completion import complete_remote_path, complete_hostname

@ck.command()
@ck.argument(
    "hostname", type=str, shell_complete=complete_hostname,
    #help="The hostname of the remote server.",
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
    #help="Path to the job script to run on the remote server.  May be a local or remote path.",
)
@ck.option("--job-script-location", type=ck.Choice(["local", "remote"]), default=None)

@ck.option("--debug/--no-debug", default=False)
@ck.option("--verbose/--no-verbose", default=False)
@ck.option("--dryrun/--no-dryrun", default=False)
@ck.option(
    "--killswitch/--no-killswitch", default=False,
    help="Keep the program running until user input, then the job will be killed.",
)
def code(
    hostname: str,
    remote_path: Path,
    job_script: Path,
    # literal 
    job_script_location: Literal["local", "remote"] = None,
    debug: bool = False,
    verbose: bool = True,
    dryrun: bool = False,
    killswitch: bool = False,
):
    """Launch a job on a remote server and open VScode.

    This allows interactive use of GPU compute nodes, such as with a Jupyter notebook.
    """
    log.debug(f"Launching job on {hostname} with remote path {remote_path}")
    log.debug(f"Job script location: {job_script_location}")

    if job_script_location is None:
        log.info(f"Checking if job script {job_script} exists...")
        if job_script.is_file():
            log.info(f"Using local job script: {job_script}")
            job_script_location = "local" 
        else:
            log.info(f"Job script {job_script} not found. Assuming remote path.")
            job_script_location = "remote"
    else: 
        log.info(f"Using user-provided {job_script_location} job script: {job_script}")

    server = PBSServer(hostname, verbose=verbose)

    if dryrun:
        log.debug("Dry run mode enabled. Exiting.") 
        return
    
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

    if killswitch: 
        # Stay open until Ctrl+C
        print("Press Ctrl+C to kill job.")
        user_input = input()
        log.info(f"User input: {user_input}")
        log.info(f"Killing job {job_id}...")
        server.kill_job(job_id)
        log.info("Job killed.")


@ck.command()
@ck.argument(
    "hostname", type=str, shell_complete=complete_hostname,
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


"""Context manager for displaying a timer on the CLI. """
from contextlib import contextmanager
from time import time
from typing import Optional

@contextmanager
def Timer(desc: Optional[str] = None):
    start = time()
    yield
    end = time()
    elapsed = end - start
    if desc:
        ck.echo(f"{desc} took {elapsed:.2f} seconds.")
    else:
        ck.echo(f"Elapsed time: {elapsed:.2f} seconds.")


from rich.progress import Progress, ProgressColumn, Text
from datetime import timedelta

class CompactTimeColumn(ProgressColumn):
    """Renders time elapsed."""

    def render(self, task: "Task") -> Text:
        """Show time elapsed."""
        elapsed = task.finished_time if task.finished else task.elapsed
        if elapsed is None:
            return Text("-:--:--", style="progress.elapsed")
        delta = timedelta(seconds=max(0, elapsed))
        return Text("str(delta)", style="progress.elapsed")


@ck.command()
def cli():
    """Launch a remote shell on a server."""

    import rich 
    import time
    from rich.progress import Progress
    from rich.console import Console

    console = Console()
    progress = Progress()

    from rich.progress import Progress, TimeElapsedColumn, SpinnerColumn, TextColumn
    progress = Progress(
        SpinnerColumn(),
        
        #*Progress.get_default_columns(),
        # show 1dp of seconds (elapsed time)
        TextColumn("[progress.description]{task.description}"),
        #"{task.fields[extra]}"),
        CompactTimeColumn(),
    )
    with progress:

        task1 = progress.add_task("[blue]Submitting job... ")

        while not progress.finished:
            progress.update(task1, advance=0.5)
            
            time.sleep(3)

    

def nothing():
    from tqdm import tqdm
    import time
    c = ck.confirm(ck.style('Do you want to continue?', fg='green'))

    start = time.time()

    while True: 
        elapsed = time.time() - start
        sys.stdout.write("\r")
        sys.stdout.write("Submitting job... ({:2f})".format(elapsed)) 
        sys.stdout.flush()
        #time.sleep(1)
        if elapsed > 3:
            break
    sys.stdout.write("\rComplete!            \n")


@ck.command()
def click():
    """Show a simple example of a progress bar."""
    ck.secho('ATTENTION', blink=True, bold=True)
    # ck input 
     
    c = ck.confirm(ck.style('Do you want to continue?', fg='green'))

    if c == "^C":
        ck.secho("User cancelled.")
        return
    elif c:
        ck.secho("Continuing...")
    else:
        ck.secho("Exiting.")
        return

    ck.pause("Press any key to continue...")
    ck.echo("Continuing...")

@ck.group()
def entry_point():
    pass

entry_point.add_command(code)
entry_point.add_command(stat)
entry_point.add_command(cli)




#if __name__ == "__main__":
#    entry_point()
