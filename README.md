# pi-in-a-box

Run the [pi coding agent](https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent) in a Docker container with your project directory mounted inside it. This gives you _some_ peace-of-mind while your agent runs in YOLO-mode.

## Requirements

- Docker installed and running
- Verified on **macOS only**

## Security

**DISCLAIMER:** Running an AI agent in a container does not guarantee security. Please use AI agents with appropriate caution.

- The container runs as a non-root user (`piuser`)
- Your project directory is mounted with full read/write access
- The container has network access for API calls and package installations

**AI DISCLAIMER:** This project was built with AI assistance, but fully reviewed and validated by a human :)

## Setup

Build the Docker image:

```bash
./start.sh --build
```

## Usage

### Basic Usage

```bash
# Run pi in current directory
./start.sh

# Run pi in a specific directory
./start.sh /path/to/project
./start.sh ../my-project
```

### Options

```bash
# Force rebuild the Docker image
./start.sh --build /path/to/project

# Start a shell instead of pi (for debugging)
./start.sh --shell /path/to/project

# Show help
./start.sh --help
```

### Passing Arguments to pi

pi itself accepts flags (e.g. `--model`); use `--` to pass them through `start.sh`:

```bash
# Pass --model to pi
./start.sh ~/projects/my-app -- --model gpt-4

# Pass multiple arguments to pi
./start.sh ~/projects/my-app -- --model claude-sonnet --skill my-skill

# Pass args to pi using current directory
./start.sh -- --skill my-skill

# Combine start.sh options with pi args
./start.sh --build ~/projects/my-app -- --model gpt-4
```

Everything after `--` is passed directly to the `pi` command.

## How It Works

The `start.sh` script:

1. **Validates** the project directory exists
2. **Builds** the Docker image if needed (or forced with `--build`)
3. **Mounts** your project directory to `/project` in the container
4. **Mounts** your pi configuration from `~/.pi` to persist settings
5. **Runs** pi in interactive mode within the project directory
