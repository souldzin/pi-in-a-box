#!/usr/bin/env bash

# Launch pi coding agent in Docker with project mounting

set -e

SCRIPT_NAME="$(basename "$0")"
IMAGE_NAME="pi-in-a-box"

# Function to show usage
show_usage() {
  echo "Usage: $SCRIPT_NAME [PROJECT_PATH]"
  echo ""
  echo "Launch pi coding agent in a Docker container with project directory mounted."
  echo ""
  echo "Arguments:"
  echo "  PROJECT_PATH    Path to project directory to mount (defaults to current directory)"
  echo ""
  echo "Options:"
  echo "  -h, --help      Show this help message"
  echo "  --build         Force rebuild of Docker image"
  echo "  --shell         Start bash shell instead of pi"
  echo "  --              Stop parsing $SCRIPT_NAME options; remaining args are passed to pi"
  echo ""
  echo "Any arguments not consumed by $SCRIPT_NAME are forwarded to the pi command."
  echo ""
  echo "Examples:"
  echo "  $SCRIPT_NAME                                # Mount current directory"
  echo "  $SCRIPT_NAME ~/my-project                   # Mount specific project"
  echo "  $SCRIPT_NAME --build ~/project              # Rebuild image and mount project"
  echo "  $SCRIPT_NAME --shell ~/project              # Start shell in container"
  echo "  $SCRIPT_NAME ~/project -- --model gpt-4     # Pass --model gpt-4 to pi"
  echo "  $SCRIPT_NAME -- --skill my-skill            # Pass --skill to pi (current dir)"
}

# Default values
PROJECT_PATH="$(pwd)"
FORCE_BUILD=false
START_SHELL=false
PI_ARGS=()

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
  -h | --help)
    show_usage
    exit 0
    ;;
  --build)
    FORCE_BUILD=true
    shift
    ;;
  --shell)
    START_SHELL=true
    shift
    ;;
  --)
    shift
    PI_ARGS+=("$@")
    break
    ;;
  -*)
    echo "Unknown option: $1"
    show_usage
    exit 1
    ;;
  *)
    PROJECT_PATH="$1"
    shift
    ;;
  esac
done

# Resolve project path to absolute path
PROJECT_PATH=$(realpath "$PROJECT_PATH" 2>/dev/null || echo "$PROJECT_PATH")

# Validate project path
if [[ ! -d "$PROJECT_PATH" ]]; then
  echo "Error: Directory '$PROJECT_PATH' does not exist"
  exit 1
fi

echo "🚀 Starting pi agent with project: $PROJECT_PATH"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
  echo "Error: Docker is not running or not accessible"
  echo "Please start Docker and try again"
  exit 1
fi

# Check if image exists or force build
if [[ "$FORCE_BUILD" == "true" ]] || ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
  echo "🔨 Building Docker image..."

  # Find Dockerfile (should be in same directory as this script)
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  DOCKERFILE_PATH="$SCRIPT_DIR/Dockerfile"

  if [[ ! -f "$DOCKERFILE_PATH" ]]; then
    echo "Error: Dockerfile not found at $DOCKERFILE_PATH"
    echo "Please ensure Dockerfile is in the same directory as $SCRIPT_NAME"
    exit 1
  fi

  docker build -t "$IMAGE_NAME" -f "$DOCKERFILE_PATH" "$SCRIPT_DIR"
  echo "✅ Docker image built successfully"
fi

# Determine command to run
if [[ "$START_SHELL" == "true" ]]; then
  DOCKER_CMD=("bash")
  echo "🐚 Starting interactive shell..."
else
  DOCKER_CMD=("pi" "${PI_ARGS[@]}")
  if [[ ${#PI_ARGS[@]} -gt 0 ]]; then
    echo "🤖 Starting pi agent with args: ${PI_ARGS[*]}"
  else
    echo "🤖 Starting pi agent..."
  fi
fi

# Run the container
echo "📁 Mounting: $PROJECT_PATH -> /project"
echo "🏃 Running container..."

docker run -it --rm \
  -v "$PROJECT_PATH:/project" \
  -v "$HOME/.pi:/home/piuser/.pi" \
  -e "HOME=/home/piuser" \
  -w "/project" \
  "$IMAGE_NAME" \
  "${DOCKER_CMD[@]}"

echo "👋 pi session ended"
