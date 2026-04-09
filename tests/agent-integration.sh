#!/usr/bin/env bash
# Integration test: starts a pi-in-a-box container for THIS project
# (via start.sh) and runs the agent test suite inside it.
#
# This goes through the full start.sh/start.py code path, so it
# tests the actual container setup — mounts, ignore-paths, user, etc.
#
# Usage:
#   ./tests/agent-integration.sh          # uses existing image
#   ./tests/agent-integration.sh --build  # rebuilds image first

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- Options ---------------------------------------------------------------
BUILD_ARG=""
if [[ "${1:-}" == "--build" ]]; then
  BUILD_ARG="--build"
fi

# --- Run tests via start.sh ------------------------------------------------
echo "* Running agent integration tests..."

TEST_CMD='for t in /project/tests/agent/test-*.sh; do echo "--- $t ---"; sh "$t"; done'

OUTPUT=$("$PROJECT_DIR/start.sh" $BUILD_ARG --no-interactive --exec "$TEST_CMD" "$PROJECT_DIR" 2>&1) || true

echo "$OUTPUT"

# --- Check results ---------------------------------------------------------
TOTAL=$(echo "$OUTPUT" | grep -c "\[OK\]\|\[FAIL\]" || true)
PASSED=$(echo "$OUTPUT" | grep -c "\[OK\]" || true)
FAILED=$(echo "$OUTPUT" | grep -c "\[FAIL\]" || true)

echo ""
echo "--- Results: $PASSED/$TOTAL passed ---"

if [[ "$FAILED" -gt 0 ]]; then
  echo "[FAIL] Integration tests FAILED"
  exit 1
fi

if [[ "$PASSED" -eq 0 ]]; then
  echo "[FAIL] No tests ran"
  exit 1
fi

echo "[OK] All integration tests passed"
