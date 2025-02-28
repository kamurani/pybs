import subprocess
import os

from functools import partial
from typing import Tuple
from pathlib import Path

from .sshconf import read_ssh_config
from os.path import expanduser

SSH_CONFIG_PATH = "~/.ssh/config"

class PBSServer:
    """Class to interact with the PBS server.

    Parameters
    ----------
    remotehost : str
        The hostname of the remote server.
    print_output : bool
        Whether to print the output of the commands.

    """
    def __init__(
        self, 
        remotehost: str,
        print_output: bool = False,
        verbose: bool = True,

    ): 
        self.remotehost = remotehost
        self.print_output = print_output
        self.verbose = verbose
        
        ssh_config_path = Path(expanduser(SSH_CONFIG_PATH))
        assert ssh_config_path.is_file(), f"SSH config file not found at {ssh_config_path}"

        c = read_ssh_config(ssh_config_path)
        hostnames = c.hosts() 
        if self.verbose: print(f"Found {len(hostnames)} hostnames in ssh config")

        # check that supplied hostname is in the ssh config
        assert remotehost in hostnames, f"Specified hostname '{remotehost}' not found in ssh config"
        username = c.host(remotehost)["user"]
        self.username = username
        if self.verbose: print(f"Found hostname '{remotehost}' in ssh config. Using username '{username}'")



    """Decorator for stdout and stderr collection."""
    def print_stdout(func):
        def decorated(self, *args, **kwargs):
            stdout, stderr = None, None
            try:
                stdout, stderr = func(self, *args, **kwargs)
            except Exception as e:
                print(e)
            
            if self.print_output: 
                print(stdout)
                print(stderr)
            return stdout, stderr
        return decorated
    
    def get_status(self, job_id: str):
        """Get the status of the server."""
        info = self.job_info(job_id)
        return info["status"]

    @print_stdout
    def ssh_execute(self, cmd):
        cmd = ["ssh", self.remotehost, cmd]
        captured = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        stdout = captured.stdout.read().decode()
        stderr = captured.stderr.read().decode()
        return stdout, stderr
    
    def ssh_jump_execute(self, cmd: str, target_node: str, login_node: str = None):
        login_node = self.remotehost if login_node is None else login_node
        cmd = ["ssh", "-J", login_node, f"{self.username}@{target_node}", cmd]
        captured = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        stdout = captured.stdout.read().decode()
        stderr = captured.stderr.read().decode()
        return stdout, stderr
    
    @print_stdout
    def check_gpu(
        self, 
        node: str = None, 
        job_id: str = None, 
    ) -> Tuple[str, str]:
        """Check the GPU usage on a node."""
        cmd = "nvidia-smi"
        if node is None: 
            if job_id is None:
                raise ValueError("Either node or job_id must be provided.")
            info_dict = self.job_info(job_id)
            node = info_dict["node"]
        stdout, stderr = self.ssh_jump_execute(cmd, target_node=node)
        return stdout, stderr
    
    @print_stdout
    def qstat(
        self,
        job_id: str = None,
        arguments: list = ["-n", "-f"],

    ):
        """Get information about jobs in the queue.
        
        Job Status codes: 
        H - Held
        Q - Queued
        R - Running
        C - Completed
        E - Exiting


        """
        cmd = "qstat"
        if job_id is not None:
            cmd += f" {job_id}"

        cmd = " ".join([cmd] + arguments)
        stdout, stderr = self.ssh_execute(cmd)
        return stdout, stderr
    
    @print_stdout
    def pstat(self):
        """Get overview of the compute nodes and list of jobs running on each node."""
        cmd = "pstat"
        stdout, stderr = self.ssh_execute(cmd)
        return stdout, stderr  

    @print_stdout
    def pbsnodes(self, node: str):
        cmd = f"pbsnodes {node}"
        stdout, stderr = self.ssh_execute(cmd)
        return stdout, stderr  
    
    def job_info(self, job_id: str):
        """Parse the output of pstat command."""
        job_id = str(job_id).strip()
        info_dict = self._parse_pstat(job_id)
        return info_dict

    def send_file(self, local_path: Path, remote_path: Path):
        """Send a file to the remote server."""
        pass 

    def parse_job_id(self, out: str) -> str:
        if "." not in out:
            raise ValueError(f"Job submission did not return valid job ID string: {out}")
        parsed = out.split(".")
        job_id, address = parsed[0], parsed[1:]
        return job_id, address

    def qsub(self, job_script: Path):
        """Submit a job to the queue."""
        cmd = f"qsub {job_script}"
        stdout, stderr = self.ssh_execute(cmd)
        return stdout, stderr

    def submit_job(self, job_script: Path):
        """Submit a job to the queue and return the job ID."""
        stdout, stderr = self.qsub(job_script)
        job_id, _ = self.parse_job_id(stdout)
        return job_id

    def _parse_pstat(
        self, 
        job_id: str,
    ) -> str: 
        """Parse qstat output for a particular job and return the information."""
        if job_id is None:
            raise ValueError("job_id must be provided.")
        stdout, _ = self.qstat(job_id=job_id)
        # find job name line 
        lines = stdout.split("\n")
        for i, line in enumerate(lines):
            if line.startswith(job_id):
                break

        if i <= 2:
            print(stdout)
            raise ValueError(f"Job ID {job_id} not found in qstat output.")
        header = lines[i-2] 
        info_line = lines[i]
        node_line = lines[i+1]

        header = header.replace("Job ID", "Job_ID") # to avoid splitting on space
        header = header.split()
        fields = info_line.split()
        assert len(fields) == len(header), f"Parse error: Fields and header mismatch: {len(fields)} vs {len(header)}"

        node_line = node_line.strip()
        print("Node line:", node_line)
        if "/" not in node_line:
            node_name = node_line.strip()
            resources = None
        else:    
            node_name, resources = node_line.split("/")

        status = fields[header.index("S")] 
        return dict(
            status=status,
            node=node_name,
            resources=resources,
        )
    
    def kill_job(self, job_id: str):
        """Kill a job."""
        cmd = f"qdel {job_id}"
        stdout, stderr = self.ssh_execute(cmd)
        return stdout, stderr