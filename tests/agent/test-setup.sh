#!/bin/sh
# Integration test: to verify that the script command works

set -e

# Verify that the postsetup.txt file exists and contains the expected content
EXPECTED_CONTENT="Agent setup success."
ACTUAL_CONTENT=$(cat /project/tmp/postsetup.txt)

if [ "$ACTUAL_CONTENT" = "$EXPECTED_CONTENT" ]; then
  echo "[OK]: Setup script verification successful: postsetup.txt contains expected content."
else
  echo "[FAIL]: Setup script verification failed: postsetup.txt content mismatch."
  echo "Expected: '$EXPECTED_CONTENT'"
  echo "Actual:   '$ACTUAL_CONTENT'"
  exit 1
fi
