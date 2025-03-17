
from rich.theme import Theme
custom_theme = Theme(
    {
        "progress.description": "yellow bold",
    }
)


def _log_formatter(
    record: dict,
    icon: bool = False,
) -> str:
    """Log message formatter"""
    color_map = {
        "TRACE": "dim blue",
        "DEBUG": "cyan",
        "INFO": "bold",
        "SUCCESS": "bold green",
        "WARNING": "yellow",
        "ERROR": "bold red",
        "CRITICAL": "bold white on red",
    }
    lvl_color = color_map.get(record["level"].name, "cyan")

    if icon:
        icon = "{level.icon}"
    else:
        icon = ""
    return (
        "[not bold green]{time:YYYY/MM/DD HH:mm:ss}[/not bold green] |"
        + f"{icon}  - [{lvl_color}]{{message}}[/{lvl_color}]"
        # Right-align code location:
        + " [dim]{name}:{function}:{line}[/dim]"
    )