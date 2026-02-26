#!/usr/bin/env python3
"""Launch pi coding agent in Docker with project mounting."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

SCRIPT_NAME = Path(__file__).name
IMAGE_NAME = "pi-in-a-box"
SCRIPT_DIR = Path(__file__).resolve().parent


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


def docker_is_running() -> bool:
    """Check whether the Docker daemon is reachable."""
    try:
        subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def image_exists(name: str) -> bool:
    """Return True if a Docker image with *name* is available locally."""
    try:
        subprocess.run(
            ["docker", "image", "inspect", name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def build_image() -> None:
    """Build the Docker image from the Dockerfile next to this script."""
    dockerfile = SCRIPT_DIR / "Dockerfile"
    if not dockerfile.is_file():
        print(f"Error: Dockerfile not found at {dockerfile}")
        print(f"Please ensure Dockerfile is in the same directory as {SCRIPT_NAME}")
        sys.exit(1)

    subprocess.run(
        ["docker", "build", "-t", IMAGE_NAME, "-f", str(dockerfile), str(SCRIPT_DIR)],
        check=True,
    )
    print("✅ Docker image built successfully")


def get_container_uid_gid(image: str, user: str = "piuser") -> tuple[int, int]:
    """Query the UID and GID of *user* inside the Docker *image*."""
    try:
        out = subprocess.check_output(
            ["docker", "run", "--rm", image, "id", "-u", user],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        uid = int(out)
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        uid = 1000

    try:
        out = subprocess.check_output(
            ["docker", "run", "--rm", image, "id", "-g", user],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        gid = int(out)
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        gid = 1000

    return uid, gid


def load_ignore_paths(project_path: Path, container_uid: int = 1000, container_gid: int = 1000) -> list[str]:
    """Read .piinabox.toml and return docker volume args that shadow ignored paths.

    Each ignored path gets an anonymous empty volume mounted over the
    corresponding location inside the container, preventing the host's
    copy (e.g. .venv) from leaking in.
    """
    config_file = project_path / ".piinabox.toml"
    if not config_file.is_file():
        return []

    if tomllib is None:
        print(
            "Warning: .piinabox.toml found but no TOML parser available. "
            "Upgrade to Python ≥ 3.11 or install 'tomli'."
        )
        return []

    with open(config_file, "rb") as f:
        config = tomllib.load(f)

    ignore_paths: list[str] = config.get("ignore-paths", [])
    volume_args: list[str] = []
    for p in ignore_paths:
        # Strip leading/trailing slashes so we always get a clean relative path
        clean = p.strip("/")
        if not clean:
            continue
        container_path = f"/project/{clean}"
        print(f"🚫 Ignoring path: {container_path}")
        # Use tmpfs so the mount is owned by the container user (piuser),
        # not root as with anonymous volumes.
        volume_args.extend(["--tmpfs", f"{container_path}:exec,uid={container_uid},gid={container_gid}"])
    return volume_args


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="Launch pi coding agent in a Docker container with project directory mounted.",
        epilog=(
            "Any arguments after -- are forwarded to the pi command.\n\n"
            "Examples:\n"
            f"  {SCRIPT_NAME}                                # Mount current directory\n"
            f"  {SCRIPT_NAME} ~/my-project                   # Mount specific project\n"
            f"  {SCRIPT_NAME} --build ~/project              # Rebuild image and mount project\n"
            f"  {SCRIPT_NAME} --shell ~/project              # Start shell in container\n"
            f"  {SCRIPT_NAME} ~/project -- --model gpt-4     # Pass --model gpt-4 to pi\n"
            f"  {SCRIPT_NAME} -- --skill my-skill            # Pass --skill to pi (current dir)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=os.getcwd(),
        help="Path to project directory to mount (defaults to current directory)",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=get_version()
    )
    parser.add_argument(
        "--build", action="store_true", help="Force rebuild of Docker image"
    )
    parser.add_argument(
        "--shell",
        action="store_true",
        help="Start bash shell instead of pi",
    )
    parser.add_argument(
        "pi_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the pi command (after --)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # REMAINDER captures a leading "--" separator; strip it.
    if args.pi_args and args.pi_args[0] == "--":
        args.pi_args = args.pi_args[1:]

    project_path = Path(args.project_path).resolve()
    if not project_path.is_dir():
        print(f"Error: Directory '{project_path}' does not exist")
        sys.exit(1)

    print(f"🚀 Starting pi agent with project: {project_path}")

    # ---- Docker checks ------------------------------------------------
    if not docker_is_running():
        print("Error: Docker is not running or not accessible")
        print("Please start Docker and try again")
        sys.exit(1)

    if args.build or not image_exists(IMAGE_NAME):
        print("🔨 Building Docker image...")
        build_image()

    # ---- Determine container command ----------------------------------
    if args.shell:
        docker_cmd = ["bash"]
        print("🐚 Starting interactive shell...")
    else:
        docker_cmd = ["pi", *args.pi_args]
        if args.pi_args:
            print(f"🤖 Starting pi agent with args: {' '.join(args.pi_args)}")
        else:
            print("🤖 Starting pi agent...")

    # ---- Run the container --------------------------------------------
    home = Path.home()
    container_uid, container_gid = get_container_uid_gid(IMAGE_NAME)
    ignore_volume_args = load_ignore_paths(project_path, container_uid, container_gid)

    print(f"📁 Mounting: {project_path} -> /project")
    print("🏃 Running container...")

    result = subprocess.run(
        [
            "docker", "run", "-it", "--rm",
            "-v", f"{project_path}:/project",
            *ignore_volume_args,
            "-v", f"{home}/.pi:/home/piuser/.pi",
            "-e", "HOME=/home/piuser",
            "-w", "/project",
            IMAGE_NAME,
            *docker_cmd,
        ],
    )

    print("👋 pi session ended")
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
