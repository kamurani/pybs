from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
NAME = "PyBS"

SSH_CONFIG_PATH = "~/.ssh/config"
# TODO: replace this path with something from `platformdirs`

if __name__ == "__main__":
    print(PROJECT_ROOT)
