---
name: test-pi-in-a-box
description: Runs integration tests that verify the pi-in-a-box container environment is set up correctly. Use when the user asks to test or verify the container setup, or troubleshoot container issues.
---

# Test pi-in-a-box

Integration tests that run **inside** the container to verify the pi-in-a-box environment.

## Running all tests

```bash
sh tests/agent-integration.sh
```

## Running a specific test

```bash
sh tests/agent/test-ignore-paths-exec.sh
```

## Available tests

See [tests/agent/README.md](../../../tests/agent/README.md) for the full list of tests and what they check.

## Interpreting results

- `[OK]` — the check succeeded.
- `[FAIL]` — something is wrong with the container setup. Diagnostic info is printed.

## Adding tests

See [tests/agent/README.md](../../../tests/agent/README.md) for conventions.
