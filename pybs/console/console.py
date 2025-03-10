"""Command line interface for PyBS."""

import click as ck

from pybs.console.remote import commands as q
from pybs.console.remote import code
from pybs.console.local import (
    completions,
    version,
)

MAX_CONTENT_WIDTH = 120


@ck.group(
    context_settings=dict(
        max_content_width=MAX_CONTENT_WIDTH,
    )
)
def entry_point():
    pass


entry_point.add_command(completions)
entry_point.add_command(version)
entry_point.add_command(code)
entry_point.add_command(q.stat)
entry_point.add_command(q.sub)
