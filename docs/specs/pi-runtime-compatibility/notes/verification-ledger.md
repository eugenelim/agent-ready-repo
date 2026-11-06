# Verification ledger: pi-runtime-compatibility

## Baseline

On 2026-11-05, before any change, the named suite list ran serially without Pi, from `packs/core/tests/skills/work-loop/`:

```bash
WORK_SUPERVISOR_INTEGRATION=1 python -m pytest -q -p no:cacheprovider -rs <the twelve named files>
```

- **Result:** 875 passed, 0 skipped, exit code 0.
- **Wall time:** 8,508 seconds (2 h 22 min), on a shared machine at load average 25–45.
- **Without `WORK_SUPERVISOR_INTEGRATION`:** 411 passed and 464 skipped in 6 seconds.

## Environment

- Pi 1.5.0 at `/opt/homebrew/bin/pi`, package `@earendil-works/pi-coding-agent`.
- `agent-ready-pi` v0.1.7 is installed in the user's Pi settings. The harness runs with a fresh `HOME`, so it does not load that package.
