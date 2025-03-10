"""Local commands for the console."""

import os
import sys
import click as ck

from loguru import logger as log
from pybs import NAME


@ck.command()
@ck.argument(
    "shell",
    required=False,
    type=ck.Choice(["bash", "zsh", "fish", "auto"]),
    default="auto",
)
def completions(
    shell: str,
):
    """Generate shell completion scripts for your shell.
    If no shell is specified, it will default to $SHELL."""

    # Change loggers to use stderr (ONLY for this command)
    # This is until we change `rich.RichHandler` to use stderr
    # on specific logs.
    # NOTE: if we use console=console(stderr=True), it messes up
    # the progress bar graphics for some reason.
    log.remove()
    log.add(sys.stderr)

    script_name = f"{ck.get_current_context().parent.info_name}"
    if shell is None or shell == "auto":
        log.info("No shell specified, defaulting to $SHELL.")
        shell = os.environ.get("SHELL")
        log.info(f"Detected shell: {shell}")
        shell = shell.split("/")[-1]
        log.info(f"Extracted shell name: {shell}")
    else:
        log.info(f"Using user-provided shell: {shell}")
    if shell is None:
        log.error("No shell detected. Exiting.")

    if shell not in ["bash", "zsh", "fish"]:
        log.error(f"Unsupported shell: {shell}. Exiting.")
        return
    # Use click to generate the completion script
    script = os.popen(f"_PYBS_COMPLETE={shell}_source {script_name}").read()
    ck.echo(script)


@ck.command()
def version():
    """Show the current version of PyBS."""
    pkg_name = f"{ck.get_current_context().parent.info_name}"  # this is `pybs`, not the package name

    import pybs

    ck.echo(f"{NAME} {pybs.__version__}")
