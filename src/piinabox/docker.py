import subprocess
from dataclasses import dataclass
from typing import Any
import json


@dataclass(frozen=True)
class DockerImage:
    name: str
    id: str
    meta: dict[str, Any]

    @staticmethod
    def try_parse(values: dict[str, Any]) -> "DockerImage | None":
        name = values.get("Repository", "")
        id = values.get("ID", "")

        if not isinstance(name, str) or not name:
            return None

        if not isinstance(id, str) or not id:
            return None

        return DockerImage(name=name, id=id, meta=values)


@dataclass(frozen=True)
class DockerContainer:
    name: str
    state: str
    image: str
    meta: dict[str, Any]

    @staticmethod
    def try_parse(values: dict[str, Any]) -> "DockerContainer | None":
        name = values.get("Names", "")
        state = values.get("State", "")
        image = values.get("Image", "")

        return DockerContainer(
            name=str(name), state=str(state), image=str(image), meta=values
        )


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


def build_image(image_name: str, dockerfile: str, dockerfile_dir: str):
    return subprocess.run(
        [
            "docker",
            "build",
            "-t",
            image_name,
            "-f",
            dockerfile,
            dockerfile_dir,
        ],
        check=True,
    )


def get_image(image_name: str) -> DockerImage | None:
    image_json = subprocess.check_output(
        [
            "docker",
            "images",
            "-f",
            f"reference={image_name}",
            "--format",
            "json",
        ],
        text=True,
    ).strip()

    if not image_json:
        return None

    image_values = json.loads(image_json)

    if not isinstance(image_values, dict):
        return None

    return DockerImage.try_parse(image_values)


def find_containers(name: str) -> list[DockerContainer]:
    container_json_lines = subprocess.check_output(
        [
            "docker",
            "ps",
            "-a",
            "-f",
            f"name={name}",
            "--format",
            "json",
        ],
        text=True,
    ).strip()

    result: list[DockerContainer] = []

    for line in container_json_lines.splitlines():
        if not line:
            continue

        try:
            container_values = json.loads(line)
        except Exception:
            container_values = None

        container = (
            DockerContainer.try_parse(container_values) if container_values else None
        )

        if container:
            result.append(container)

    return result


def run_container(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", "run", *args])


def remove_container(container_name: str) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", "rm", container_name])


def start_container(
    container_name: str, attach: bool = False, interactive: bool = False
) -> subprocess.CompletedProcess:
    args = []
    if attach:
        args.append("-a")

    if interactive:
        args.append("-i")

    return subprocess.run(["docker", "start", *args, container_name])
