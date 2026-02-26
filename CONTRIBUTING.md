# Contributing

## Testing

To verify the container environment is set up correctly, start a pi-in-a-box session **on this project itself**:

```bash
pi-in-a-box /path/to/pi-in-a-box
```

Then, from inside that session, run the built-in skill:

```
/skill:test-pi-in-a-box
```

This runs integration tests that check the user, mounts, tools, and permissions. See [tests/agent/README.md](tests/agent/README.md) for details on available tests and how to add new ones.

### From the host

You can also run the integration tests directly from your host machine (no interactive pi session needed):

```bash
./tests/agent-integration.sh          # uses existing image
./tests/agent-integration.sh --build  # rebuilds image first
```

This spins up a pi-in-a-box container for this project, runs all agent tests inside it, and reports pass/fail.
