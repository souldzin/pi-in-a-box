#!/bin/sh
# Integration test: verify tmpfs mounts for ignore-paths allow execution.
# .test-ignore-paths must be listed in .piinabox.toml ignore-paths.

set -e

MOUNT_OPTS=$(mount | grep "/project/.test-ignore-paths" || true)

if [ -z "$MOUNT_OPTS" ]; then
  echo "[FAIL]: /project/.test-ignore-paths is not a tmpfs mount"
  exit 1
fi

if echo "$MOUNT_OPTS" | grep -q "noexec"; then
  echo "[FAIL]: tmpfs mount has noexec — binaries in ignored paths won't run"
  echo "  $MOUNT_OPTS"
  exit 1
fi

echo "[OK]: tmpfs mount allows exec"
