# Agent Integration Tests

Tests in this directory are designed to be run **by the agent, from inside the
pi-in-a-box container**. They verify that the container environment is set up
correctly.

## Running

Use the built-in skill from inside a pi-in-a-box session:

```
/skill:test-pi-in-a-box
```

This runs all tests automatically and reports results.

## Tests

| Test                        | What it checks                                                                 |
| --------------------------- | ------------------------------------------------------------------------------ |
| `test-user.sh`              | Running as `piuser`, not root                                                  |
| `test-project-mount.sh`     | `/project` is mounted and writable                                             |
| `test-setup.sh`             | The script command in `.piinabox.toml` works                                   |
| `test-home-dir.sh`          | Home directory and `~/.pi` config are accessible and writable                  |
| `test-tools.sh`             | Essential tools are installed (`pi`, `node`, `git`, `curl`, `python3`, `mise`) |
| `test-ignore-paths-exec.sh` | tmpfs mounts for `ignore-paths` have `exec` permission                         |

## Adding tests

Add executable scripts to this directory. Each test should:

1. Exit `0` and print a `✅ PASSED` message on success.
2. Exit non-zero and print a `❌ FAILED` message with diagnostic info on failure.
