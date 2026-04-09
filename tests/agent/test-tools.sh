#!/bin/sh
# Integration test: verify essential tools are available.

set -e

FAILED=0

for cmd in pi node git curl python3 mise; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "  ✓ $cmd: $(command -v "$cmd")"
  else
    echo "  ✗ $cmd: NOT FOUND"
    FAILED=1
  fi
done

if [ "$FAILED" -eq 1 ]; then
  echo "[FAIL]: one or more required tools missing"
  exit 1
fi

echo "[OK]: all required tools available"
