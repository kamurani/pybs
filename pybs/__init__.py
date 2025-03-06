from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent

SSH_CONFIG_PATH = "~/.ssh/config"

if __name__ == "__main__":
    print(PROJECT_ROOT)
   