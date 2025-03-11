"""Custom UI elements for CLI console."""

from rich.console import Console
from rich.progress import Progress, ProgressColumn, Text
from rich.text import Text
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
        # style = "progress.elapsed"
        # style = "grey58"
        style = "white"
        return Text(f"({n_seconds:.1f}s)", style=style)
