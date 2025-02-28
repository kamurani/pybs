"""Command line interface for running jobs."""

import click as ck 
import subprocess

from pathlib import Path
from pybs.server import PBSServer

debug = False

@ck.command()
@ck.argument("hostname", type=str)
@ck.argument("remote_path", type=ck.Path(
    exists=False, path_type=Path,
))
@ck.argument("job_script", type=ck.Path(
    exists=False, path_type=Path, 
))
@ck.option("--verbose/--no-verbose", default=True)
@ck.option("--debug/--no-debug", default=True)
def launch(
    hostname: str,
    remote_path: Path,
    job_script: Path,
    debug: bool = False,
    verbose: bool = True,
):
    if debug:
        print(f"Launching job on {hostname} with remote path {remote_path}")
        print(type(remote_path))

    server = PBSServer(hostname, verbose=False, print_output=False) 

    if verbose: print(f"Submitting job to {hostname} with job script {job_script}...")
    job_id = server.submit_job(job_script)
    if verbose: 
        print(f"Job submitted with ID: {job_id}")
        print(f"Retrieving job information:", end=" ")
    
    info = server.job_info(job_id) 
    if verbose: print(f"Status: {info['status']}")
    from time import sleep
    while server.get_status(job_id) != "R":
        if verbose: print(".", end="") 
        sleep(0.5)
    if verbose: print("Job is running.")
    info = server.job_info(job_id)
    node = info["node"]
    if debug: print(info)
    if verbose: 
        print(f"Checking GPU status:") 
        out, err = server.check_gpu(node=node)
        print(out)
        print(err)

    # Launch VScode 
    target_name = f"{hostname}-{node}"

    if verbose: print(f"Launching VScode on {target_name}...")
    cmd_list = ["code", "--remote", f"ssh-remote+{target_name}", remote_path] 
    if debug: print(cmd_list)
    captured = subprocess.run(
        cmd_list, 
        capture_output=True,
    )
    # kill 
    if debug:
        sleep(60)
        if verbose: print(f"Killing job {job_id}...")
        server.kill_job(job_id)

    





    






if __name__ == "__main__":
    launch()


