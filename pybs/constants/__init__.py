"""Constants for PyBS."""

from pybs import DEFAULT_PBS_SCRIPT_PATH
POLL_INTERVAL = 0.5

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