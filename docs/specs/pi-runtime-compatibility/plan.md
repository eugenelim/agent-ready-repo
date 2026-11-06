# Plan: Pi runtime compatibility

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `tests/AGENTS.md` (roster placement and CI wiring); `tests/roster/test_t9a_clean_env_fence.py` (static import scan with red evidence, and the supervisor `start`/`next` subprocess fence built on `packs/core/tests/skills/work-loop/supervisor_harness.py`); `tools/lint-ci-parity.py` `STEP_DISPOSITION`.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (contract, scope and non-goals, durable outputs, agent rules, testing
> strategy, acceptance criteria, accepted risk) or its `Terminal Intent`. A change
> to tasks, tests, stubs, design, or approach needs none. Execution
> observations belong in `docs/specs/pi-runtime-compatibility/notes/verification-ledger.md`.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads. `Design`, `Approach`, `Grounding` and `Risks` are working
> material the controller corrects in place.

## Approach

Two roster tests and two doc edits, with nothing under `packs/`. The Pi-absent
check lands first because CI runs it on every pull request and it needs no Pi.
The harness lands second; it reuses the suites as they are and adds only a
launcher, a JUnit reader and a parent-PID check. The riskiest part is the
harness's process handling: a hung Pi or pytest must not outlive the test.

## Constraints

- ADR-0144: the supervisor owns procedure and reaches a runtime only through
  its CLI; no runtime adapter enters Core.
- ADR-0074: skill scripts stay standard-library; neither new test adds a
  dependency to any manifest.
- `tests/AGENTS.md`: each roster file gets a named `build-check.yml` step above
  the bulk step and a `LOCAL("test-after-build-check")` entry in
  `tools/lint-ci-parity.py`.
- Owner decision 2026-11-05: model-free Pi host only; no `agent-ready-pi`
  change; no provider calls.

## Construction tests

Owned by T1 and T2. Each task's `Tests:` names its cases.

## Durable-output map

| Spec durable output | Task | Evidence |
| --- | --- | --- |
| Current architecture (crosswalk) | T3 | AC-0014 checks |
| Product history (brief spec map) | T3 | row present |
| Maintainer procedure (harness docstring) | T2 | AC-0007 run from the docstring command |

## Design (LLD)

### Design decisions
<!-- Owned by: T1, T2, T4. -->

- **Model-free host.** Pi's RPC `bash` command runs a shell command through
  Pi's own executor (`executeBash` with no timeout) and returns
  `{success, data: {exitCode, output, truncated}}` without a model call (probe
  2026-11-05, Pi 1.5.0, offline, empty `HOME`). Pi's RPC handler exposes no
  other command the harness sends.
- **Isolation.** The child environment is an allowlist, so `PI_CODING_AGENT_DIR`,
  `PI_CODING_AGENT_SESSION_DIR`, `PI_PACKAGE_DIR`, provider keys, tokens and
  proxy variables never reach Pi or pytest. With a fresh `HOME` Pi loads no user
  settings (so no `shellCommandPrefix`) and no installed package, so
  `agent-ready-pi` is not loaded. Pi's own shell adds `AI_AGENT`,
  `PI_CODING_AGENT`, `PI_OFFLINE`, `PI_SKIP_VERSION_CHECK` and a
  `<HOME>/.pi/agent/bin` `PATH` prefix (probe 2026-11-06); none carries a
  credential, and the harness asserts that nothing else is added. `--no-approve` makes Pi ignore project-local
  files; the working directory is empty in any case.
- **Results travel by file.** Pi keeps only the tail of `output`
  (50 KB / 2,000 lines), so the parent PID, the collected count and the JUnit
  report are written to files in the temporary directory. `output` is used only in failure messages.
- **Zero skips.** The suites skip their integration cases unless
  `WORK_SUPERVISOR_INTEGRATION=1` (probe: 464 of 875 cases skipped without it).
- **Deadline value.** Six hours. The serial run of the named suite list under
  `WORK_SUPERVISOR_INTEGRATION=1`, without Pi, took 8,508 seconds on the owner's
  shared machine at load average 25–45 on 2026-11-05 (875 passed, 0 skipped;
  ledger § Baseline), so the deadline leaves about 2.5× margin. Pi's bash
  command has no timeout of its own, so the harness deadline binds.
- **Process watcher.** Core's managed launches use `start_new_session=True`
  (`_process_safety.py`), and Pi starts its shell detached, so no process group
  covers the run. A watcher thread polls `ps -A -o pid=,ppid=,lstart=` every
  0.5 seconds, each call bounded at 5 seconds, and adds any process whose parent PID and start time match a
  recorded run process and which started no earlier than that parent. It runs
  with the child environment, so it carries no credentials.

### Interfaces & contracts
<!-- Owned by: T2. -->

- Opt-in: `AGENT_READY_PI_CONFORMANCE=1`. Documented command:
  `AGENT_READY_PI_CONFORMANCE=1 python -m pytest tests/roster/test_pi_hosted_conformance.py -q -rsP`.
- RPC request: one JSON line `{"id": "conformance", "type": "bash", "command": …}`
  on stdin; read stdout lines until the `response` with that `id`, then close stdin.

### Behavior & rules
<!-- Owned by: T1. -->

- The Pi-reference rule is the spec's term, implemented as regexes over every
  file's text plus an `ast` walk for `.py` files. Probe 2026-11-05: zero matches
  under `packs/core/`. Known near-misses that must stay green: `pip install`
  lines, the `pi = sibling("_policy_import.py")` assignment in
  `_supervisor_admission.py`, and the `"pi_t5"` module-name literal in
  `packs/core/tests/skills/work-loop/test_policy_import.py`.
- Manifest parsing uses `tomllib` and `json`; a requirement line's name is the
  text before the first version or marker character.

### Failure, edge cases & resilience
<!-- Owned by: T2, T4, T5. -->

- Pi is started with `start_new_session=True`. Cleanup, in a `finally`, with
  the watcher still sampling: send `SIGTERM` to every recorded run process
  still alive with its recorded start time, wait up to 10 seconds, then
  `SIGKILL` every recorded run process still alive, including any recorded
  during the wait, and reap Pi. Repeat the `SIGKILL` pass until a sample taken
  after it records no new run process; then stop the watcher. The survivor
  check fails the test if any recorded run process is alive with its recorded
  start time. The run fails as unknown on any of the failures the spec's "Run
  processes" term names (a failed or unparseable read, or a gap over 5 seconds), and Pi is always ended through its own
  `Popen` handle, `terminate()` then `kill()`.
- Pi exits early or prints a non-JSON line: the test fails and quotes the line.
- `PATH` without Pi (AC-0012): keep only `PATH` entries holding no `pi`
  executable; if `git` then no longer resolves, symlink it into a temporary bin
  directory placed first.

### Dependencies & integration
<!-- Owned by: T2. -->

- Pi 1.5.0 at `/opt/homebrew/bin/pi` (package `@earendil-works/pi-coding-agent`)
  and `agent-ready-pi` v0.1.7 on the owner's machine; neither is installed or
  updated by this work.

## Tasks

### T1: Pi-absent check passes on this branch and reds on planted violations

**Depends on:** none

**Touches:** tests/roster/test_core_pi_absent.py, .github/workflows/build-check.yml, tools/lint-ci-parity.py

**Tests:**
- AC-0010: the scan of `packs/core/` passes; one scratch-copy plant per
  Pi-reference alternative reds (each text pattern, each import form, the
  string literals `"pi"` and `"pi --mode rpc"`, `importlib.import_module("pi")`
  and `__import__("pi_x")`, a JavaScript `spawn("pi", [])`, a `"bin/pi"`
  literal, a `".pi"` literal, and `PI_CODING_AGENT_DIR`); the three near-misses
  in Design and an `openapi install` line stay green.
- AC-0011: one plant per manifest source reds (`runtime-dependencies`,
  `integrations.pack`, `plugin.json`, `package.json`, `requirements.txt`,
  `pyproject.toml`); a name like `pipx` or `api-client` stays green.
- AC-0012: guard asserts `shutil.which("pi", path=env["PATH"])` is `None` and no
  `PI_` key is in the environment; then `start` and `next` exit `0`, reusing the
  T9a fence's fixture and argument shape.
- AC-0013: the sentinel's record file is absent after `start` and `next`; a
  control run that calls the sentinel directly proves it records.
- AC-0015 (this file's half): `tools/lint-ci-parity.py` exits `0`.

**Done when:** the T1 cases pass locally, `make lint-ruff lint-mypy` passes, and the CI-parity lint exits `0`.

### T2: Pi-hosted harness passes on the owner's machine

**Depends on:** T1

**Touches:** tests/roster/test_pi_hosted_conformance.py, .github/workflows/build-check.yml, tools/lint-ci-parity.py

**Tests:**
- AC-0003, AC-0004 pins: hand-built JUnit files and PID files red on each case
  the Testing Strategy names.
- AC-0001, AC-0002 pins: a stub `pi` script records its argv, its environment
  and the RPC line it received; with `ANTHROPIC_API_KEY` and
  `PI_CODING_AGENT_DIR` planted in the test environment, neither reaches the
  stub, and the recorded argv and command match the spec.
- AC-0005, AC-0006 pin: a stub `pi` that starts a child in its own session,
  which starts a grandchild in a further session, stays alive for at least 6
  seconds, longer than the 5-second gap the term allows, and then exits; the stub never answers. With the deadline
  lowered, the test
  fails on the deadline and neither the stub, the child nor the grandchild is
  running afterwards.
- AC-0006 pin: a stub run process that starts a new child when it receives
  `SIGTERM`; after cleanup neither is running.
- AC-0006 pin: a recorded run process exits and a foreign process is planted
  as if it held that PID with a different start time; its child is not
  recorded or signalled.
- AC-0016 pin: the stub run's recorded command writes the PID and count files
  before the pytest invocation.
- AC-0007 pin: the stub records the environment and `HOME` of its `--version`
  call, which match the child environment with a fresh `HOME`.
- AC-0008, AC-0009: the three skip cases, each asserting the reason and that no
  `pi` process started (a stub `pi` on `PATH` records no run).
- AC-0001 to AC-0007 real run: one run with the opt-in set; full output and
  exit code saved to the evidence directory and summarised in the ledger.
- AC-0015 (this file's half).

**Approach:** the deadline is a module constant, and the launch goes through one function, so the stub pins exercise the real launch and cleanup code.

**Done when:** the pins pass with no real Pi involved, the real run passes with the opt-in set, and the CI-parity lint exits `0`.

### T3: Crosswalk and brief spec map name the Pi proof

**Depends on:** T2

**Touches:** docs/architecture/runtime-adapter-crosswalk.md, docs/product/briefs/acceptance-centered-work-loop.md

**Tests:**
- AC-0014: the check collapses whitespace in the page before matching; run
  against the page at the base commit it reports all three removed phrases
  present (red); after the edit it reports the sentence present and none of
  them. The repository's doc link check passes.
- The brief's spec map has a `pi-runtime-compatibility` row and the brief lints
  that read it pass.

**Done when:** the T3 checks pass and the docs lints pass.

### T4: Review repairs close the supported findings

**Depends on:** T1, T2, T3

**Touches:** tests/roster/test_pi_hosted_conformance.py, tests/roster/test_core_pi_absent.py, docs/architecture/runtime-adapter-crosswalk.md

**Tests:**
- AC-0006 (adv-1): with `ps` unavailable (the watcher's `ps` path patched to a
  missing or failing binary), cleanup still ends the launched Pi through its own
  `Popen` handle, the run reports the unreadable process table as a failure,
  and the test returns without blocking on Pi's stdout.
- AC-0006 (qe-2): the stub chain and SIGTERM-respawn pins start their deadline
  only after the stub writes a ready file; a missing record file fails with a
  readable assertion.
- AC-0003 (qe-4): a pin feeds `evaluate` a clean result directory with a
  response of `success: false`, then one with a non-zero `exitCode`; each names
  the response problem.
- AC-0010 (qe-1): each planted violation asserts the finding names the rule it
  targets, and an AST-only plant (`"pi run"`, `importlib.import_module("pi")`
  in a form no text pattern matches) reds only through its AST rule.
- AC-0012, AC-0013 (qe-5): each supervisor subprocess call has a timeout of 900
  seconds and fails with the command and captured output on expiry.
- AC-0001 (sec-2): the real-run command also writes the variable names its
  shell sees to `<tmp>/env-names`; the harness fails when any name falls outside
  the child environment, the shell's own (`PWD`, `SHLVL`, `_`,
  `__CF_USER_TEXT_ENCODING`), and the markers Pi itself adds (`AI_AGENT`,
  `PI_CODING_AGENT`, `PI_OFFLINE`, `PI_SKIP_VERSION_CHECK`), and when `PATH` is
  not the child `PATH` with at most Pi's `<HOME>/.pi/agent/bin` prefixed. A stub
  pin plants an extra name and reds.
- Nits folded in: requirement lines naming a package through `#egg=` are
  checked (adv-2); a quoted literal ending `/pi` that holds another quote kind
  matches (adv-3); the
  crosswalk § 3 row and § 4 bullet describe the Pi proof and the fence as they
  are (adv-5, sec-3); the Core-tree scan failure lists every hit and names the
  spec term (qe-6); the line-report pin does not index pattern order (qe-7); the
  failure, error and skip pins assert the named problem (qe-8).
- A fresh real opt-in run passes with the repaired harness; full output saved
  to the evidence directory. The ledger, written at closeout outside any
  attempt, records the resolved launch path (adv-4) and summarises the run.

**Done when:** the T4 pins pass with no real Pi involved, the fresh real run passes, `make lint-ruff lint-mypy` and the CI-parity lint exit `0`.

### T5: A process-table read that fails during the run fails the run

**Depends on:** T4

**Touches:** tests/roster/test_pi_hosted_conformance.py

**Tests:**
- AC-0006 (qe2-1, sec2-1): a failed, timed-out, non-zero or unparseable `ps`
  read at any point from the Pi launch to the end of cleanup is recorded, and
  the outcome reports the run as failed with "process table unreadable"; a gap
  of more than 5 seconds between two watcher samples is recorded the same way,
  and a gap of 1.4 seconds, as the first real run saw, is not. A pin with a fake
  `ps` that fails only before cleanup and reads cleanly afterwards reds the run.
- A fresh real opt-in run passes with the repaired harness; full output saved
  to the evidence directory.

**Done when:** the T5 pins pass with no real Pi involved, the fresh real run passes, `make lint-ruff lint-mypy` and the CI-parity lint exit `0`.

## Rollout

Test and doc change only. No `packs/` content moves, so there is no release.
Reverting the PR removes both tests and the doc links.

## Risks

- The integration-lane suites may change their skip guards later; the
  zero-skip rule then reds the harness rather than passing silently.
- `build-check.yml` placement must keep the existing step order; the CI-parity
  lint catches a missing disposition.

## Changelog

- 2026-11-06: spec approved by eugenelim (scope)
- 2026-11-06: plan approved by eugenelim (build strategy)
- 2026-11-06: amendment approved by eugenelim (scope)
- 2026-11-06: amendment approved by eugenelim (build strategy)
