# pi-agent-hev

This setup allows you to run the [pi coding agent](https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent) in a Docker container with easy project mounting.

`hev` is a reference to the H.E.V. suit in Half-Life.

## Setup

1. **Make the launch script executable:**

   ```bash
   chmod +x start.sh
   ```

2. **Build the Docker image:**

   ```bash
   ./start.sh --build
   ```

## Usage

### Basic Usage

```bash
# Run pi in current directory
./start.sh

# Run pi in specific directory
./start.sh /path/to/project

# Run pi in specific directory (relative path)
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

### Examples

```bash
# Work on a React project
./start.sh ~/projects/my-react-app

# Work on current directory with fresh image build
./start.sh --build

# Debug container setup
./start.sh --shell
```

## How It Works

The `start.sh` script:

1. **Validates** the project directory exists
2. **Builds** the Docker image if needed (or forced with `--build`)
3. **Mounts** your project directory to `/project` in the container
4. **Mounts** your pi configuration from `~/.pi` to persist settings
5. **Runs** pi in interactive mode within the project directory

## Configuration Persistence

Your pi agent configuration (skills, extensions, settings) is persisted by mounting `~/.pi` from your host system into the container. This means:

- Your API keys and settings are preserved
- Installed skills and extensions persist across container runs
- Session history is maintained

## Project Access

The container has full read/write access to your mounted project directory, so pi can:

- Read and write files
- Execute commands within the project
- Install dependencies (npm, pip, etc.)
- Run build scripts and tests

## Customization

### Environment Variables

You can pass environment variables to the container by modifying the `start.sh` script. For example:

```bash
docker run -it --rm \
    -v "$PROJECT_PATH:/project" \
    -v "$HOME/.pi:/home/piuser/.pi" \
    -e "HOME=/home/piuser" \
    -e "OPENAI_API_KEY=$OPENAI_API_KEY" \
    -e "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY" \
    -w "/project" \
    "$IMAGE_NAME" \
    $DOCKER_CMD
```

### Additional Volumes

To mount additional directories, modify the docker run command in `start.sh`:

```bash
-v "$HOME/Documents:/home/piuser/Documents" \
-v "$HOME/.ssh:/home/piuser/.ssh:ro" \
```

### Custom Dockerfile

To customize the container (add tools, change base image, etc.), modify the `Dockerfile`:

```dockerfile
# Add additional tools
RUN apt-get update && apt-get install -y \
    python3 \
    golang \
    && rm -rf /var/lib/apt/lists/*

# Install additional npm packages globally
RUN npm install -g typescript ts-node
```

## Troubleshooting

### Docker Issues

- **"Docker is not running"**: Start Docker Desktop or the Docker daemon
- **Permission denied**: Ensure your user is in the `docker` group on Linux

### Path Issues

- **"Directory does not exist"**: Check that the path is correct and accessible
- **Relative paths not working**: The script converts relative paths to absolute ones

### Pi Configuration

- **API keys not working**: Ensure your `~/.pi/agent/settings.json` contains valid API keys
- **Skills not loading**: Check that skills are properly installed in `~/.pi/agent/skills/`

### Performance

- **Slow startup**: The first run builds the image; subsequent runs are faster
- **Large projects**: Consider using `.dockerignore` to exclude `node_modules`, build artifacts, etc.

## Security Notes

- The container runs as a non-root user (`piuser`)
- Your project directory is mounted with full read/write access
- Pi configuration directory is mounted to persist settings
- The container has network access for API calls and package installations

## Requirements

- Docker installed and running
- Bash shell (for the launch script)
- Internet connection (for building image and API calls)
