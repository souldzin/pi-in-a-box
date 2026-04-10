import subprocess
from typing import Protocol
from dataclasses import dataclass

from piinabox import docker
from piinabox.config import Config


class CompletedProcessAdapter(Protocol):
    def get_return_code(self) -> int: ...

    def check(self) -> None: ...


class NoopCompletedProcess(CompletedProcessAdapter):
    def get_return_code(self) -> int:
        return 0

    def check(self) -> None:
        return None


@dataclass(frozen=True)
class DefaultCompletedProcess(CompletedProcessAdapter):
    process: subprocess.CompletedProcess

    def get_return_code(self) -> int:
        return self.process.returncode

    def check(self) -> None:
        return self.process.check_returncode()


class ExecutionStrategy(Protocol):
    def execute(self, run_args: list[str]) -> CompletedProcessAdapter: ...


class NoNameExecutionStrategy(ExecutionStrategy):
    def execute(self, run_args: list[str]) -> CompletedProcessAdapter:
        print("* Running ephemeral container...")
        result = docker.run_container(
            [
                "--rm",
                *run_args,
            ]
        )

        return DefaultCompletedProcess(result)


@dataclass(frozen=True)
class CreateContainerExecutionStrategy(ExecutionStrategy):
    container_name: str

    def execute(self, run_args: list[str]) -> CompletedProcessAdapter:
        print(f"* Creating new container ({self.container_name})...")
        result = docker.run_container(["--name", self.container_name, *run_args])

        return DefaultCompletedProcess(result)


@dataclass(frozen=True)
class StartContainerExecutionStrategy(ExecutionStrategy):
    container_name: str

    def execute(self, run_args: list[str]) -> CompletedProcessAdapter:
        interactive = "-i" in run_args or "--interactive" in run_args

        print(f"* Starting container ({self.container_name})...")
        result = docker.start_container(
            container_name=self.container_name, attach=True, interactive=interactive
        )

        return DefaultCompletedProcess(result)


@dataclass(frozen=True)
class RemoveContainersExecutionStrategy(ExecutionStrategy):
    containers_to_remove: list[str]

    def execute(self, run_args: list[str]) -> CompletedProcessAdapter:
        result: CompletedProcessAdapter = NoopCompletedProcess()

        if not self.containers_to_remove:
            return result

        for x in self.containers_to_remove:
            result.check()
            print(f"* Removing outdated container: {x}")
            result = DefaultCompletedProcess(docker.remove_container(x))

        return result


@dataclass(frozen=True)
class MultiExecutionStrategy(ExecutionStrategy):
    strategies: list[ExecutionStrategy]

    def add(self, strategy: ExecutionStrategy):
        self.strategies.append(strategy)

    def execute(self, run_args: list[str]) -> CompletedProcessAdapter:
        result: CompletedProcessAdapter = NoopCompletedProcess()

        for s in self.strategies:
            result.check()
            result = s.execute(run_args)

        return result


def get_container_name_prefix(container_name: str) -> str:
    return f"piinabox_{container_name}_"


def get_container_name_full(container_name: str, run_hash: str) -> str:
    return f"{get_container_name_prefix(container_name)}{run_hash}"


def get_execution_strategy(config: Config, run_hash: str) -> ExecutionStrategy:
    container_name = config.container_name

    if not container_name:
        return NoNameExecutionStrategy()

    # STEP 1 - Let's find old containers we might need to clean up
    container_prefix = get_container_name_prefix(container_name)
    container_name = get_container_name_full(
        container_name=container_name, run_hash=run_hash
    )
    matching_containers = docker.find_containers(name=container_prefix)
    container: docker.DockerContainer | None = None
    containers_to_remove: list[str] = []

    for c in matching_containers:
        if c.name == container_name:
            container = c
        elif c.state == "exited":
            containers_to_remove.append(c.name)

    result = MultiExecutionStrategy(
        strategies=[RemoveContainersExecutionStrategy(containers_to_remove)]
    )

    # STEP 2 - How do we need to start the main container?
    if not container:
        result.add(CreateContainerExecutionStrategy(container_name))
    elif container.state == "running":
        result.add(NoNameExecutionStrategy())
    else:
        result.add(StartContainerExecutionStrategy(container_name))

    return result
