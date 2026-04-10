import subprocess

from .constants import SCRIPT_DIR, SCRIPT_NAME


def get_version() -> str:
    """Return version string from git info."""
    try:
        sha = subprocess.check_output(
            ["git", "-C", str(SCRIPT_DIR), "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        sha = "unknown"

    try:
        date = subprocess.check_output(
            ["git", "-C", str(SCRIPT_DIR), "log", "-1", "--format=%cI"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        date = "unknown"

    return f"{SCRIPT_NAME} {sha} ({date})"
