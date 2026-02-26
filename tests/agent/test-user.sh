#!/bin/sh
# Integration test: verify we're running as piuser, not root.

set -e

CURRENT_USER=$(whoami)

if [ "$CURRENT_USER" = "root" ]; then
    echo "❌ FAILED: running as root — container should run as piuser"
    exit 1
fi

if [ "$CURRENT_USER" != "piuser" ]; then
    echo "❌ FAILED: running as '$CURRENT_USER' — expected piuser"
    exit 1
fi

echo "✅ PASSED: running as piuser"
