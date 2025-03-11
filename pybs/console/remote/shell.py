"""Create an interactive shell for remote server."""

import click as ck

from pybs.server import PBSServer
from pybs.console.tabcomplete import complete_hostname
ck.command()
@ck.argument(
    "hostname",
    type=str,
    shell_complete=complete_hostname,
)
def shell(
    hostname: str,
):
    """Start an interactive shell for a remote server."""
    server = PBSServer(hostname)
    
    while True:
        cmd = input(f"{hostname}> ")
        
        # TODO: 
        # to prevent continually typing 'hostname' arguments, 
        # we can now access all q commands directly
        # e.g. 
        # katana> stat
        # QSTAT OUTPUT...
        # katana> sub job.sh
        # QSUB OUTPUT...
        # katana> exit
        # $ 

