#!/usr/bin/env python3
"""Launch pi coding agent in Docker with project mounting."""

import argparse
import os
import subprocess
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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


@dataclass
class Config:
    project_path: Path
    ignore_paths: list[str]
    env: dict[str, str]
    setup: str

    @staticmethod
    def try_parse(project_path: Path, values: dict[str, Any]) -> "Config":
        ignore_paths = values.get("ignore-paths", [])
        setup = values.get("setup", "")
        env_args = values.get("env", {})

        if not isinstance(ignore_paths, list):
            ignore_paths = []

        if not isinstance(setup, str):
            setup = ""

        if not isinstance(env_args, dict):
            env_args = {}

        return Config(
            project_path=project_path,
            ignore_paths=ignore_paths,
            setup=setup,
            env=env_args,
        )


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
    print("* Docker image built successfully")


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


def load_config(project_path: Path) -> Config:
    config_file = project_path / ".piinabox.toml"

    if not config_file.is_file():
        return Config.try_parse(project_path, {})

    if tomllib is None:
        print(
            "Warning: .piinabox.toml found but no TOML parser available. "
            "Upgrade to Python ≥ 3.11 or install 'tomli'."
        )
        return Config.try_parse(project_path, {})

    with open(config_file, "rb") as f:
        config_values = tomllib.load(f)

    return Config.try_parse(project_path, config_values)


def load_ignore_paths(
    config: Config, container_uid: int = 1000, container_gid: int = 1000
) -> list[str]:
    """Read the config and return docker volume args that shadow ignored paths.

    Each ignored path gets an anonymous empty volume mounted over the
    corresponding location inside the container, preventing the host's
    copy (e.g. .venv) from leaking in.
    """
    volume_args: list[str] = []

    for p in config.ignore_paths:
        # Strip leading/trailing slashes so we always get a clean relative path
        clean = p.strip("/")
        if not clean:
            continue

        # Expand glob patterns against the project directory
        matched = sorted(config.project_path.glob(clean))
        if matched:
            targets = [
                m.relative_to(config.project_path) for m in matched if m.is_dir()
            ]
        else:
            # No glob meta-characters or nothing matched – treat as literal
            targets = [Path(clean)]

        for rel in targets:
            container_path = f"/project/{rel}"
            print(f"* Ignoring path: {container_path}")
            # Use tmpfs so the mount is owned by the container user (piuser),
            # not root as with anonymous volumes.
            volume_args.extend(
                [
                    "--tmpfs",
                    f"{container_path}:exec,uid={container_uid},gid={container_gid}",
                ]
            )
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
            f"  {SCRIPT_NAME} -- --skill my-skill            # Pass --skill to pi (current dir)\n"
            f"  {SCRIPT_NAME} --no-interactive --exec 'echo hello' ~/project  # Run a command non-interactively"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=os.getcwd(),
        help="Path to project directory to mount (defaults to current directory)",
    )
    parser.add_argument("-v", "--version", action="version", version=get_version())
    parser.add_argument(
        "--build", action="store_true", help="Force rebuild of Docker image"
    )
    parser.add_argument(
        "--shell",
        action="store_true",
        help="Start bash shell instead of pi",
    )
    parser.add_argument(
        "--exec",
        metavar="CMD",
        help="Execute a command in the container instead of starting pi",
    )
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Disable interactive mode (no TTY allocation)",
    )
    parser.add_argument(
        "--no-setup",
        action="store_true",
        help="Skip running the setup command specified in .piinabox.toml",
    )
    parser.add_argument(
        "pi_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the pi command (after --)",
    )
    return parser


def get_docker_cmd(args: argparse.Namespace, config: Config) -> list[str]:
    """Determine the final docker command to execute, including setup and main command."""
    # Determine the base command
    if getattr(args, "exec", None):
        main_cmd = args.exec
        print(f"* Executing: {args.exec}")
    elif args.shell:
        main_cmd = "bash"
        print("* Starting interactive shell...")
    else:
        main_cmd = " ".join(["pi", *(shlex.quote(arg) for arg in args.pi_args)])
        if args.pi_args:
            print(f"* Starting pi agent with args: {' '.join(args.pi_args)}")
        else:
            print("* Starting pi agent...")

    # Prepend setup command if applicable
    full_cmd = ""
    if config.setup and not args.no_setup:
        print(f"* Setup command: {config.setup}")
        full_cmd = f"{config.setup} && {main_cmd}"
    else:
        full_cmd = main_cmd

    return ["bash", "-c", full_cmd]


def get_env_args(config: Config) -> list[str]:
    result = []

    for k, v in config.env.items():
        result.append("-e")
        result.append(f"{k}={v}")

    return result


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

    home = Path.home().resolve()

    # Safety: refuse to mount the home directory (or a parent of it) as /project.
    # Doing so can lock files, confuse inotify watchers, and freeze programs.
    if project_path == home or home.is_relative_to(project_path):
        print(f"Error: Refusing to mount '{project_path}' as the project directory.")
        print(
            "Mounting your home directory (or a parent) into the container can cause "
            "file locks, inotify storms, and freeze running programs."
        )
        print(
            f"Please run from a specific project directory, or pass one as an argument."
        )
        sys.exit(1)

    # Safety: refuse to mount filesystem root
    if project_path == Path("/"):
        print(f"Error: Refusing to mount '/' as the project directory.")
        print("Please specify a specific project directory.")
        sys.exit(1)

    print(f"* Starting pi agent with project: {project_path}")

    # ---- Docker checks ------------------------------------------------
    if not docker_is_running():
        print("Error: Docker is not running or not accessible")
        print("Please start Docker and try again")
        sys.exit(1)

    if args.build or not image_exists(IMAGE_NAME):
        print("* Building Docker image...")
        build_image()

    # ---- Load config --------------------------------------------------
    config = load_config(project_path)

    # ---- Determine container command ----------------------------------
    interactive = not args.no_interactive
    docker_cmd = get_docker_cmd(args, config)

    # ---- Run the container --------------------------------------------
    container_uid, container_gid = get_container_uid_gid(IMAGE_NAME)
    ignore_volume_args = load_ignore_paths(config, container_uid, container_gid)
    env_args = get_env_args(config)

    print(f"* Mounting: {project_path} -> /project")
    print("* Running container...")

    sys.stdout.flush()
    docker_run_args = ["-it"] if interactive else []
    result = subprocess.run(
        [
            "docker",
            "run",
            *docker_run_args,
            "--rm",
            "-v",
            f"{project_path}:/project",
            *ignore_volume_args,
            "-v",
            f"{home}/.pi:/home/piuser/.pi",
            "-e",
            "HOME=/home/piuser",
            *env_args,
            "-w",
            "/project",
            IMAGE_NAME,
            *docker_cmd,
        ],
    )

    print("[pi session ended]")
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
