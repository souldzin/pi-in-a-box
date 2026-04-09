#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- Options ---------------------------------------------------------------
mkdir -p ${PROJECT_DIR}/tmp
echo "Agent setup success." >${PROJECT_DIR}/tmp/postsetup.txt
