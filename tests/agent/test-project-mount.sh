#!/bin/sh
# Integration test: verify /project is mounted and writable.

set -e

if [ ! -d /project ]; then
  echo "[FAIL]: /project does not exist"
  exit 1
fi

TMPFILE="/project/.test-write-$$"
if ! touch "$TMPFILE" 2>/dev/null; then
  echo "[FAIL]: /project is not writable"
  exit 1
fi
rm -f "$TMPFILE"

echo "[OK]: /project is mounted and writable"
