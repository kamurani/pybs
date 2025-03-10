"""Lauch VScode on a remote server with a job script."""

import os
import sys
import click as ck
import subprocess

from time import sleep
from typing import Literal
from pathlib import Path
from loguru import logger as log
from rich.progress import Progress, TimeElapsedColumn, SpinnerColumn, TextColumn
from rich.console import Console, Group 
from rich.logging import RichHandler
import rich.style
from rich.live import Live
from rich.theme import Theme
custom_theme = Theme({
    "progress.description": "yellow bold", 
})


JOB_STATUS_DICT = {
    "C": "Completed",
    "E": "Exiting",
    "H": "Held",
    "Q": "Queued",
    "R": "Running",
    "T": "Moving", 
    "W": "Waiting",
    "S": "Suspended",
    "B": "Batch", 
}


def _log_formatter(
    record: dict, 
    icon: bool = False, 
) -> str:
    """Log message formatter"""
    color_map = {
        'TRACE': 'dim blue',
        'DEBUG': 'cyan',
        'INFO': 'bold',
        'SUCCESS': 'bold green',
        'WARNING': 'yellow',
        'ERROR': 'bold red',
        'CRITICAL': 'bold white on red'
    }
    lvl_color = color_map.get(record['level'].name, 'cyan')

    if icon:
        icon = "{level.icon}"
    else:
        icon = ""
    return (
        '[not bold green]{time:YYYY/MM/DD HH:mm:ss}[/not bold green] |'
        + f'{icon}  - [{lvl_color}]{{message}}[/{lvl_color}]'
        # Right-align code location:
        + ' [dim]{name}:{function}:{line}[/dim]'
    )

console = Console(
    theme=custom_theme,
    #stderr=True,
)
# Check that theme is set properly: 
#console.print(f"[progress.description]Logging level: {"TRACE"}") #style="bold blue")

log_format = "{message}"
handler = RichHandler(
    show_level=True,
    #console=console, # if this is enabled, it will print the `progress` instances twice
)
level = "TRACE"
#level = "WARNING"
log.remove()
log.add(
    handler, 
    #lambda m: console.print(m, end=""),
    format=log_format, 
    level=level, 
)





from pybs.server import PBSServer
from pybs.console.tabcomplete import complete_remote_path, complete_hostname

POLL_INTERVAL = 0.5


# DONE:
# - add tab autocompletion scripts
# - add hostname tab completion (use ~/.ssh/config)
# - fix logging for qsub wait
# - add TUI timer for job submission
# TODO:
# - add support for local job scripts
# - add intelligent remote server expansion of paths example $SCRATCH

# - add help to ck args
# - add tab complete for remote paths similar to `scp```
# - add auto install of ssh config required hostname alias
# - add arbitrary command execution for any method (with certain decorator)
# from PBSServer class
# e.g. write `qsub` and this will call the `qsub` method of the PBSServer class
# if a method with that name exists.
# - refactoring of PBSServer class to use `ssh_command` decorator
# - add `config` command to add config items to a config file 
# such as turning debug on/off

# Future TODO:
# - add db for currently running jobs, able to login to
# any server and see resources, walltime etc.
# - add "autorefresh" or "keepalive" option to remember when the walltime will
# expire, and request another GPU node that overlaps so we can keep the session logged
# in on the same node.

from rich.progress import Progress, ProgressColumn, Text
from datetime import timedelta

# TODO: make PR for this?
class CompactTimeColumn(ProgressColumn):
    """Renders time elapsed."""

    def render(self, task: "Task") -> Text:
        """Show time elapsed."""
        elapsed = task.finished_time if task.finished else task.elapsed
        if elapsed is None:
            return Text("-:--:--", style="progress.elapsed")
        delta = timedelta(seconds=max(0, elapsed))
        # get number of seconds
        n_seconds = delta.total_seconds()
        # customise progress.elapsed to be gray text
        #style = "progress.elapsed"
        #style = "grey58"
        style = "white"
        return Text(f"({n_seconds:.1f}s)", style=style)

@ck.command()
@ck.argument(
    "hostname",
    type=str,
    shell_complete=complete_hostname,
    # help="The hostname of the remote server.",
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
    # help="Path to the job script to run on the remote server.  May be a local or remote path.",
)
@ck.option("--job-script-location", type=ck.Choice(["local", "remote"]), default=None)
@ck.option("--debug/--no-debug", default=False)
@ck.option("--verbose/--no-verbose", default=False)
@ck.option("--dryrun/--no-dryrun", default=False)
@ck.option(
    "--killswitch/--no-killswitch",
    default=True,
    help="Keep the program running until user input, then the job will be killed.",
)
@ck.option(
    "--skip-check/--no-skip-check", 
    default=False, 
    help="If enabled, skips checking remote file existence and GPU usage check."
    "This may be useful for launching more quickly."
)
def code(
    hostname: str,
    remote_path: Path,
    job_script: Path,
    job_script_location: Literal["local", "remote"] = None,
    debug: bool = False,
    verbose: bool = True,
    dryrun: bool = False,
    killswitch: bool = False,
    skip_check: bool = False, 
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

    progress = Progress(
        SpinnerColumn(
            spinner_name="line",
            #spinner_name="simpleDots",
            #spinner_name="simpleDotsScrolling",
            style="blue",
        ),
        TextColumn(
            "[progress.description]{task.description}", style="blue"), 
        # SpinnerColumn(
        #     spinner_name="simpleDotsScrolling",
        #     style="blue",
        # ),
        CompactTimeColumn(),
    )

    monitor_job_status = Progress(
        SpinnerColumn(spinner_name="dots", style="white"),
        TextColumn("""
        Status:     {task.fields[job_status]}
        Node:       {task.fields[node]}
        """, style="blink bold black on orange"),
                
        #TextColumn("[progress.description]{task.fields[job_status]}"),
        #TextColumn("[progress.description]Node: {task.fields[node]}"), 
        #CompactTimeColumn(), # show 1dp of seconds (elapsed time)
    )

    import time 

    # If remote, check if the file exists on the remote server
    server = PBSServer(hostname, verbose=verbose)
    if job_script_location == "remote":
        with progress:
            task1 = progress.add_task(
                f"Checking job script on [bold][white]{hostname}[/white][/bold] exists... ",
                total=1, 
            )
            if not server.check_file_exists(job_script):
                log.error(f"Job script {job_script} not found on {hostname}. Exiting.")
                return
            else: 
                log.info(f"Job script {job_script} found on {hostname}.")
                # mark progress as complete 
                progress.update(task1, completed=True) 
    
    progress.remove_task(task1) # prevent showing task twice in CLI output when we re-use `progress` object 

    # Check directory 
    if skip_check:
        log.info("Skipping remote path existence check.")
    else:
        with progress:
            task1 = progress.add_task(
                f"Checking that workspace directory on [bold][white]{hostname}[/white][/bold] exists... ",
                total=1, 
            )
            if not server.check_dir_exists(remote_path):
                log.error(f"Remote path {remote_path} not found on {hostname}. Exiting.")
                return
            else: 
                log.info(f"Remote path {remote_path} found on {hostname}.")
                # mark progress as complete 
                progress.update(task1, completed=True)
        
        progress.remove_task(task1) # prevent showing task twice in CLI output when we re-use `progress` object


    if dryrun:
        log.debug("Dry run mode enabled. Won't submit real job.")

    # Submit job to remote server
    with progress:
        task2 = progress.add_task(f"Submitting job to [bold][white]{hostname}[/white][/bold]... ")
        if dryrun: time.sleep(1)
        else: 
            job_id = server.submit_job(job_script) 

    progress.remove_task(task2)
    #ck.secho(f"Job submitted with ID: {job_id}", fg="green") 
    log.success(f"Job submitted with ID: {job_id}")
    

    try: # Now listen for program exit so we can kill the job if needed


        # Refactored with `Live`
        

        # Clear all tasks from progress 
        ids = progress.task_ids
        for task_id in ids:
            progress.remove_task(task_id)

        progress_group = Group(
            progress, 
            monitor_job_status,
        )
        with Live(progress_group, refresh_per_second=10):

            task3 = progress.add_task(f"Retrieving job information... ", total=1)
            info = server.job_info(job_id)
            progress.update(task3, completed=True)
            progress.remove_task(task3) 
            # 'Retrieving' is completed, but we are still 'waiting'
            task4 = progress.add_task(f"Waiting for job to queue... ", total=1)

            task5 = monitor_job_status.add_task(
                f"", job_status="--", node="--", total=1) # total=1 so we can update and remove
            
            task7 = None
            while not monitor_job_status.finished:
                sleep(POLL_INTERVAL)

                # Update job status display
                status = server.get_status(job_id)
                node = server.get_node(job_id)
                node_display = node if node is not None else "--"
                status_display = f"[r][yellow]{JOB_STATUS_DICT.get(status, '-').upper()}[/yellow][/r]"
                monitor_job_status.update(task5, job_status=status_display, node=node_display)

                # Update progress display 
                if status == "Q" and task4 in progress.task_ids:
                    task6 = progress.add_task(f"Waiting for job to start... ", total=1)
                    progress.update(task4, completed=True)
                    progress.remove_task(task4)   # complete 'waiting'
                if status == "R" and task6 in progress.task_ids: 
                    progress.remove_task(task6)   # complete 'waiting'
                    if node is None: 
                        task7 = progress.add_task(f"Waiting for node to be assigned... ", total=1)
                        log.info("Job started.")
                    else: 
                        log.info("Node assigned.")
                    monitor_job_status.update(task5, completed=True)

                if node is not None and task7 in progress.task_ids: 
                    # Note: We only show 'waiting for node' progress bar if node is assigned AFTER job starts. 
                    # usually, the node is assigned during 'QUEUE'.
                    progress.remove_task(task7)
                    log.info(f"Node {node} assigned.")
                    break
                

            #monitor_job_status.remove_task(task6)   # complete 'waiting'
            #monitor_job_status.remove_task(task5)   # complete 'job status'
            info = server.job_info(job_id)
            node = info["node"]
            log.debug(info)

        if skip_check:
            log.info("Skipping GPU check.")
        else:
            with progress:
                try:
                    task5 = progress.add_task(f"Checking GPU status (Ctrl+C to skip)... ")
                    out, err = server.check_gpu(node=node)
                    # newline 
                    # console print 
                    log.info(out)
                    if err: log.error(err)

                    progress.update(task5, completed=True)
                    progress.remove_task(task5)
                except KeyboardInterrupt:
                    log.info(f"Skipping GPU check...")

            #progress.remove_task(task5)

            # TODO: figure out why sometimes our progress bars 'hide' and are transient (even though we are
            # not setting transient=True), and other times they are left behind on the screen.
            # NOTE: I think it's because we are removing a task from WITHIN the `with progress` block. 

        # Launch VS code
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
    
    except KeyboardInterrupt:
        
        # Clear all tasks from progress 
        ids = progress.task_ids
        for task_id in ids:
            progress.remove_task(task_id)

        progress_group = Group(
            progress, 
            monitor_job_status,
        )
        with Live(progress_group, refresh_per_second=10):
            task6 = progress.add_task(f"Killing job {job_id}... ")
            task7 = monitor_job_status.add_task(f"Job status: ", job_status="--", node="--", total=1)
            server.kill_job(job_id)
            while not progress.finished:
                sleep(POLL_INTERVAL)
                status = server.get_status(job_id)
                status_display = f"[r][orange]{JOB_STATUS_DICT.get(status, '-').upper()}[/orange][/r]"
                progress.update(task7, job_status=status_display)
                if status == "C":
                    progress.update(task7, completed=True)
                    log.info("Job killed.")
            progress.update(task6, completed=True)
            log.info("Job killed.")
        progress.remove_task(task6)
       
        try: 
            sys.exit(130)
        except SystemExit:
            os._exit(130) 
    

    if killswitch:
        # Stay open until Ctrl+C
        # add check from ck.confirm. 
        # If Ctrl+C, kill job
        try:
            while c := ck.prompt(
                ck.style(text="Press Ctrl+C to kill job.", fg="red"),
                default=None, 
                hide_input=True, 
                prompt_suffix="",

            ) != "^C": 
                pass
        except ck.Abort:
            log.info(f"Caught Ctrl+C")
            log.info(f"Killing job {job_id}...")
            server.kill_job(job_id)

            # TODO: 
            # actually display the status of the job using `stat` while it exits. 
            log.info("Job killed.") 
