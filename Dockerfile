# Dockerfile for pi coding agent
FROM node:20-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Install mise (polyglot tool version manager)
RUN curl https://mise.run | MISE_INSTALL_PATH=/usr/local/bin/mise sh

# Install pi coding agent globally
RUN npm install -g @mariozechner/pi-coding-agent

# Create a non-root user
RUN useradd -m -s /bin/bash piuser && \
    mkdir -p /home/piuser/.pi && \
    chown -R piuser:piuser /home/piuser

# Switch to non-root user
USER piuser

# Prevent Python from writing __pycache__ / .pyc files into the mounted project
ENV PYTHONDONTWRITEBYTECODE=1

# Set up the project mount point
WORKDIR /project

# Default command - run pi in interactive mode
CMD ["pi"]
