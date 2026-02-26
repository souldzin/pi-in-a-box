#!/bin/sh
# Integration test: verify /project is mounted and writable.

set -e

if [ ! -d /project ]; then
    echo "❌ FAILED: /project does not exist"
    exit 1
fi

TMPFILE="/project/.test-write-$$"
if ! touch "$TMPFILE" 2>/dev/null; then
    echo "❌ FAILED: /project is not writable"
    exit 1
fi
rm -f "$TMPFILE"

echo "✅ PASSED: /project is mounted and writable"
