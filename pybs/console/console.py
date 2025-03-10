"""Command line interface for PyBS."""
import click as ck

from pybs.console.remote import commands as q
from pybs.console.remote import code 
from pybs.console.local import (
    completions,
    version,
)

@ck.group()
def entry_point():
    pass

entry_point.add_command(completions)
entry_point.add_command(version)
entry_point.add_command(code)
entry_point.add_command(q.stat)
entry_point.add_command(q.sub)