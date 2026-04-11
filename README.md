# pi-in-a-box

> **Deprecated:** This project has been replaced by [silentshell](https://github.com/souldzin/silentshell), which supports launching any coding agent — not just pi. New development happens there.

Run the [pi coding agent](https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent) in a Docker container with your project directory mounted inside it. This gives you _some_ peace-of-mind while your agent runs in YOLO-mode.

## Requirements

- Python 3 installed (3.11+ recommended for `.piinabox.toml` support)
- Docker installed and running
- Verified on **macOS only**

## Security

**DISCLAIMER:** Running an AI agent in a container does not guarantee security. Please use AI agents with appropriate caution.

- The container runs as a non-root user (`piuser`)
- Your project directory is mounted with full read/write access
- The container has network access for API calls and package installations

**AI DISCLAIMER:** This project was built with AI assistance. All AI contributions have been fully reviewed and validated by a human :)

## Installation

1. Clone the repo:

   ```bash
   git clone https://github.com/souldzin/pi-in-a-box.git
   ```

2. Add a symlink to `start.sh` somewhere on your `PATH` (e.g. `/usr/local/bin`):

   ```bash
   ln -s /path/to/pi-in-a-box/start.sh /usr/local/bin/pi-in-a-box
   ```

3. Run `pi-in-a-box --help` to verify installation.

## Setup

Build the Docker image:

```bash
pi-in-a-box --build
```

## Usage

### Basic Usage

```bash
# Run pi in current directory
pi-in-a-box

# Run pi in a specific directory
pi-in-a-box /path/to/project
pi-in-a-box ../my-project
```

### Options

```bash
# Force rebuild the Docker image
pi-in-a-box --build /path/to/project

# Start a shell instead of pi (for debugging)
pi-in-a-box --shell /path/to/project

# Show help
pi-in-a-box --help
```

### Passing Arguments to pi

pi itself accepts flags (e.g. `--model`); use `--` to pass them through `pi-in-a-box`:

```bash
# Pass --model to pi
pi-in-a-box ~/projects/my-app -- --model gpt-4

# Pass multiple arguments to pi
pi-in-a-box ~/projects/my-app -- --model claude-sonnet --skill my-skill

# Pass args to pi using current directory
pi-in-a-box -- --skill my-skill

# Combine pi-in-a-box options with pi args
pi-in-a-box --build ~/projects/my-app -- --model gpt-4
```

Everything after `--` is passed directly to the `pi` command.

## Configuration

You can add a `.piinabox.toml` file to your project root to configure the container environment.

### Setup Script

Use the `setup` key to specify a script that will be executed inside the container _before_ the main `pi` command (or `--exec` command). This is useful for installing dependencies or performing other setup tasks.

```toml
# .piinabox.toml
setup = "./scripts/setup.sh"
```

The script will be executed with `bash -c "<your-setup-script> && <main-command>"`. You can skip running the setup script with the `--no-setup` command-line option.

### Environment Variables

Use the `env` section to define environment variables that will be passed into the container.

```toml
# .piinabox.toml
[env]
PYTHONDONTWRITEBYTECODE=1
DEBUG_MODE = "true"
```

### Ignoring Paths

Use `ignore-paths` to list directories that should **not** be shared between your host and the container. Each ignored path gets an anonymous empty volume mounted over it inside the container, so the host and container versions stay completely independent.

This is useful for environment-specific directories like `.venv`, or build output that may be incompatible between your host OS and the container's Linux environment.

```toml
# .piinabox.toml
ignore-paths = [
    ".venv"
]
```

### Persistent Container

By default, `pi-in-a-box` runs an ephemeral Docker container that is removed after each session. You can configure a named, persistent container by adding a `[container]` section and `name` key to your `.piinabox.toml` file.

```toml
# .piinabox.toml
[container]
name = "my-project-pi"
```

When `container.name` is set:

- A hash of the configuration is added to `container.name` for the actual container name
  (example: `piinabox_my_fun_project_62473a43`).
- If the named container does not exist, a new one will be created.
- If the named container exists and is stopped, it will be started.
- If the named container exists and is running, the command will be executed within the existing container.
- Outdated stopped containers with the same prefix will be automatically removed.

**Important Note:** If you modify your `piinabox.toml` (e.g., change `ignore-paths` or `env` variables) while a persistent container is running, the running container will continue to use its initial configuration. To apply new configuration, you will need to stop and remove the container manually.

## How It Works

The `start.sh` script invokes the python module which:

1. **Validates** the project directory exists
2. **Builds** the Docker image if needed (or forced with `--build`)
3. **Mounts** your project directory to `/project` in the container
4. **Mounts** your pi configuration from `~/.pi` to persist settings
5. **Runs** pi in interactive mode within the project directory

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
