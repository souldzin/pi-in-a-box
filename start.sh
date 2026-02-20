#!/usr/bin/env bash
# Thin wrapper – delegates everything to start.py

SCRIPT_PATH="$(realpath "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
exec python3 "$SCRIPT_DIR/start.py" "$@"
