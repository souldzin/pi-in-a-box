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


@dataclass(frozen=True)
class Config:
    project_path: Path
    ignore_paths: list[str]
    env: dict[str, str]
    setup: str
    container_name: str | None

    @staticmethod
    def try_parse(project_path: Path, values: dict[str, Any]) -> "Config":
        ignore_paths = values.get("ignore-paths", [])
        setup = values.get("setup", "")
        env_args = values.get("env", {})
        container_opts = values.get("container", {})

        if not isinstance(ignore_paths, list):
            ignore_paths = []

        if not isinstance(setup, str):
            setup = ""

        if not isinstance(env_args, dict):
            env_args = {}

        if not isinstance(container_opts, dict):
            container_opts = {}

        return Config(
            project_path=project_path,
            ignore_paths=ignore_paths,
            setup=setup,
            env=env_args,
            container_name=container_opts.get("name", None),
        )


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
