#!/bin/sh
# Integration test: verify home directory and .pi config are accessible.

set -e

if [ ! -d "$HOME" ]; then
    echo "❌ FAILED: \$HOME ($HOME) does not exist"
    exit 1
fi

if [ ! -d "$HOME/.pi" ]; then
    echo "❌ FAILED: $HOME/.pi does not exist — config volume not mounted?"
    exit 1
fi

if ! touch "$HOME/.pi/.test-write-$$" 2>/dev/null; then
    echo "❌ FAILED: $HOME/.pi is not writable"
    exit 1
fi
rm -f "$HOME/.pi/.test-write-$$"

echo "✅ PASSED: home directory and .pi config are accessible and writable"
