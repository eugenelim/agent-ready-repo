# Verification ledger: pi-runtime-compatibility

## Closing result

On 2026-11-07, the opt-in Pi-hosted run passed on the shipped code, in a quiet
window under `caffeinate -i`, at load average 7–16:

```bash
caffeinate -i env AGENT_READY_PI_CONFORMANCE=1 python -m pytest tests/roster/test_pi_hosted_conformance.py -q -rsP
```

- **Result:** 43 passed, exit code 0, in 5,276 seconds (1 h 28 min).
- **Printed by the harness:** `pi: /opt/homebrew/lib/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js`, `pi --version: 1.5.0`, `passed: 875 collected: 875`.
- **Run by:** supervisor run `run-3dae9b1d0df40f50`, T5 attempt, on `main` at `6fe5a6be7`. The run is terminal and `status --check` exits 0.

## Environment

- **Pi:** 1.5.0, package `@earendil-works/pi-coding-agent`. `/opt/homebrew/bin/pi` is a symlink, and the harness launches its resolved target, the `cli.js` path above.
- **`agent-ready-pi`:** v0.1.7 is installed in the user's Pi settings. The harness runs with a fresh `HOME`, so it does not load that package.
- **What Pi adds to its shell:** `AI_AGENT`, `PI_CODING_AGENT`, `PI_OFFLINE` and `PI_SKIP_VERSION_CHECK`, plus `<HOME>/.pi/agent/bin` at the front of `PATH`. None carries a credential, and the harness asserts that nothing else reaches the shell.

## Baseline

On 2026-11-05, before any change, the named suite list ran serially without Pi, from `packs/core/tests/skills/work-loop/`:

```bash
WORK_SUPERVISOR_INTEGRATION=1 python -m pytest -q -p no:cacheprovider -rs <the twelve named files>
```

- **Result:** 875 passed, 0 skipped, exit code 0.
- **Wall time:** 8,508 seconds (2 h 22 min), on a shared machine at load average 25–45.
- **Without `WORK_SUPERVISOR_INTEGRATION`:** 411 passed and 464 skipped in 6 seconds.

## Earlier real runs

Every real run listed every problem it found. Each failure below had exactly one problem: the process watcher.

| Date | Harness state | Result | Wall time | Note |
| --- | --- | --- | ---: | --- |
| 2026-11-06 | after T2 | 875/875, pass | 8,253 s | before review |
| 2026-11-06 | after T4 repairs | 875/875, pass | 5,385 s | |
| 2026-11-06 | T5, 1 s gap rule | fail | 4,361 s | one 1.4 s gap between samples; led to the amendment |
| 2026-11-06 | T5, 5 s gap rule | fail | 9,554 s | one `ps` call over 5 s at load ~42 |
| 2026-11-06 | T5, 5 s gap rule | fail | 18,314 s | one `ps` call over 5 s at load up to 93; the machine also slept |

## Amendment

On 2026-11-06 the owner amended the "Run processes" term: the watcher samples every 0.5 seconds, and a gap of more than 5 seconds between read starts, or any failed read, fails the run. The accepted risk names gaps of up to 5 seconds. A strict 1-second rule had failed a run on one scheduler gap. The amendment was re-approved and admitted as approval pair 2 of the first run.

## Run history

- **First run:** `run-6161f299cf44cd58` covered T1 to T5 and three review rounds. One store edit was made under owner authority: the open T5 attempt's `common:info/refs` entry was re-baselined after a sibling worktree's fetch rewrote that shared file.
- **Restart:** that run was retired, on the owner's instruction, to take in `main`'s supervisor fix for whole-tree scan timeouts. The product was re-applied on `main` as one commit, with byte-identical approved spec and plan. The new run reused the owner's approved digests and accepted T1 to T4 as already implemented, with no git timeouts.

## Observations

- **Sleep:** on macOS, `time.monotonic()` does not count system sleep, so the deadline measures awake time. A run that spans a sleep can exceed six hours of wall time without reaching the deadline. A candidate "check the deadline before every read" change made no test red either way, so it was not kept.
- **Stopping the harness:** a SIGINT did not stop the harness within two minutes. Stopping a run needs SIGTERM to Pi's process group and to the harness.
- **Mutation proofs:** the run-phase `ps` failure pin, the sample-gap pin and the JUnit summary-attribute pin each fail with their guard removed.
- **Project knowledge:** neither the `spec-approved` nor the `plan-locked` capture admitted a practice.
