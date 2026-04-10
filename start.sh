#!/usr/bin/env bash
# Thin wrapper – delegates everything to start.py

SCRIPT_PATH="$(realpath "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

export PYTHONPATH=$PYTHONPATH:${SCRIPT_DIR}/src
exec python3 -m piinabox "$@"
