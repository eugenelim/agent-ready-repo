# Plan: Execution supervisor attempt security

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** ADR-0144 D11 sets the trust boundary.
  - **Slice 1 primitives** in `work-loop/scripts/`:
    - `_process_safety.py`: POSIX `killpg` tree-kill, and refusal when that is
      missing. It enforces cwd, environment, executable pin, timeouts, and
      output bounds, but not write roots or network.
    - `_security_capability.intersect_grants`.
    - `_security_events.py`.
    - `_containment.py`, whose `launch_untrusted` refuses unless containment is
      verified.
  - **Tests:** `packs/core/tests/skills/work-loop/` (`test_process_safety.py`,
    `test_security_primitives.py`, `test_containment_broker.py`).
  - **Builds on:** `execution-supervisor-core`'s step loop, commit builder,
    `delivery/` lag rule, and TDD guard, and on
    `execution-supervisor-review-gate`'s `review-rules.json`.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`. After approval, execution
> observations belong in
> `docs/specs/execution-supervisor-attempt-security/notes/verification-ledger.md`.

## Approach

1. **T1, the Windows branch:** independent, and it changes live code, so it
   lands first.
2. **T2, the Git helper:** every later check reads Git through it.
3. **T3, attempt checks and residue:** the manifest, the open-attempt checks in
   `next` and `report`, and residue.
4. **T4, launched-code checks, pinning, regeneration, and the untrusted gate.**
5. **T5, result acceptance and grants.**

Every task changes `.apm/`, bumps the Core patch version with a changelog line,
and needs a security-reviewer pass.

## Constraints

- ADR-0144 D2 (standard library only) and D11 (worker attempts untrusted).
- POSIX behavior of `_process_safety` is unchanged.
- Core owns the change set, the request kinds, the commit builder, the
  `delivery/` lag rule, and the step order. This plan adds two steps:
  - the open-attempt check, before core `next` step 1;
  - recording the manifest in the supervisor store whenever core step 4 issues
    or re-issues a worker request.

## Construction tests

**Integration tests:** none beyond the per-task tests.

**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current architecture | T5 | Architecture review in the ledger | Page describes the shipped controls and containment limits |
| Refused Git settings list | T2 | VI-5010 | Handed to the cutover's supervisor reference |
| Release history | every task | Version parity | One changelog line per release |

## Design (LLD)

### Design decisions

- **Git helper.** Every call passes the pinned directories as
  `--git-dir`/`--work-tree` arguments. Scratch worktrees get their own
  directories.
  - **Environment:** the helper sets `GIT_CONFIG_NOSYSTEM=1` and an empty
    `GIT_CONFIG_GLOBAL`, and clears every other `GIT_*` variable apart from
    `GIT_INDEX_FILE` for the private index.
  - **Flags:**
    - `--no-replace-objects`;
    - `-c core.hooksPath=<empty temp dir>`;
    - `-c core.fsmonitor=false`;
    - `-c diff.external=`;
    - `-c commit.gpgSign=false` and `-c tag.gpgSign=false`;
    - `--no-ext-diff` and `--no-textconv` where they apply.
  - **Carried settings:** `core.autocrlf`, `core.eol`, and `core.excludesFile`,
    read once at admission from the effective config, are carried with `-c`.
  - **Out-of-helper config reads.** The spec's definition bounds these; they
    are the only `git` calls made outside the helper:
    - at admission, `git config --show-scope --get-regexp` over the effective
      config, for the carried settings and for the `filter.<name>.*`
      definitions the admission check looks for in every scope;
    - once per run, `git config --get user.name` and `user.email` for the
      commit identity.
  - **Before each call:** the helper checks Git control state by direct file
    reads. With an open attempt it compares against that attempt's manifest
    (built in T3). Otherwise it checks that the gitfile and `commondir` still
    resolve to the Git and common directories pinned at admission (built in
    T2).
- **Admission check.** For each `filter=<name>` attribute in any attributes
  file Git reads for the worktree (nested `.gitattributes` and `info/attributes`
  included),
  `start` refuses when any config scope defines `filter.<name>.*`. It also
  refuses any code-running key in repository or worktree config.
- **Open-attempt check.** For each `delivery/` file, the check compares the
  working copy against `HEAD` using core's prefix rule. It compares trusted
  files and Git control state against the manifest. A moved `HEAD` is accepted
  only when the manifest's `HEAD` is its ancestor and every newer commit id is
  in the supervisor store's list of commits the supervisor made; trailers alone
  never count. Outside an open attempt, supervisor commits are read by their
  trailers, as core reads them; replace refs and graft files are never honored.
  An attempt's report is recorded in the store, so a rebase does not reopen it.
- **Supervisor store.** `<pinned Git directory>/agentbundle-supervisor/<run id>/`
  holds the pinned digests, manifests, refusal records, and made-commit ids.
  Residue derives only from its refusal records, so deleting core's caches
  neither clears residue nor loses a manifest or a pin.
- **Bytecode.** Each entry point sets `sys.dont_write_bytecode = True` and
  points `sys.pycache_prefix` at a per-process temporary directory before
  loading any sibling.
- **Regeneration.** Only when `HEAD` holds `packs/core/.apm/skills/work-loop/`,
  the supervisor computes digests of that source's bytes. It emits `regenerate`
  when review readiness holds and those digests differ from the installed
  skill's. While the request is open, entry points accept either the pinned
  digests or the source digests. It admits the result only on a match, then
  re-pins.
- **First pin.** The admitted `start` that finds no pin record for its run
  computes the pinned digests from the installed bytes before loading any
  sibling and writes them to the supervisor store. Every other entry point, and
  any later `start` for the run, compares against that record (T4).
- **Windows Job Object.** The process is created by `CreateProcessW` with
  `CREATE_SUSPENDED | CREATE_NEW_PROCESS_GROUP | EXTENDED_STARTUPINFO_PRESENT`.
  A `STARTUPINFOEX` attribute list carries `PROC_THREAD_ATTRIBUTE_HANDLE_LIST`,
  limited to the standard streams. The sequence then continues:
  1. `CreateJobObjectW`;
  2. `SetInformationJobObject` with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` and no
     breakaway flags;
  3. `AssignProcessToJobObject`;
  4. `ResumeThread`.

  A timeout calls `TerminateJobObject`.

Owned by: T1, T2, T3, T4.

## Tasks

### T1: Windows launches run in a breakaway-denied Job Object

- **Depends on:** none
- **Spec behavior:** AC-0021, AC-0022, AC-0023, AC-0024, AC-0025; TDD.
- **Touches:** `work-loop/scripts/_process_safety.py`; `test_process_safety.py`; `.github/workflows/build-check-windows.yml`; Core manifests and changelog
- **Verification mode:** TDD
- **Tests:**
  - **VI-5001 (AC-0021, AC-0022):** a child that spawns immediately is assigned
    before it runs. An injected assignment failure gives `denied-job-object`,
    and the process ends.
  - **VI-5002 (AC-0023):** after a timeout, `tasklist` shows no survivor in
    three cases: an exited intermediate process that left a grandchild, a child
    that requested breakaway, and a plain tree.
  - **VI-5003 (AC-0024):** the `safe-process.v1` contract cases pass. The
    parent opens an extra inheritable file handle, and the child finds it
    unusable.
  - **VI-5004 (AC-0025):** `test_process_safety.py` passes unchanged on POSIX
    CI.
- **Done when:** VI-5001–VI-5003 pass on the Windows job, VI-5004 passes on POSIX, and security-reviewer returns clean.

### T2: Supervisor git calls run no configured code and change no staged bytes

- **Depends on:** spec:execution-supervisor-core/T4
- **Spec behavior:** AC-0009, AC-0010, AC-0011, AC-0012; TDD.
- **Touches:** new `_supervisor_git.py`; every core `git` call site; `_supervisor_admission.py`; Core manifests and changelog
- **Verification mode:** TDD
- **Tests:**
  - **VI-5010 (AC-0009):** `start` refuses in each of these cases:
    - a code-running key, including `gpg.ssh.defaultKeyCommand` and an unlisted
      `*.command`, in repository or worktree config;
    - a global `filter.lfs.*` with a `.gitattributes` `filter=lfs` line.

    The same global filter with no attribute that uses it does not refuse, and
    a global filter defined under `XDG_CONFIG_HOME` refuses the same way.
  - **VI-5011 (AC-0010, AC-0011):** marker files are planted for a hook,
    fsmonitor, a filter, textconv, an external diff, SSH signing, and an
    include. None of them runs during a change-set read, a stage, a commit, or
    a `log`. With `core.autocrlf=true` carried, staged bytes match plain
    `git add`.
  - **VI-5012 (AC-0012):** these forgeries leave completion unchanged:
    `git replace` of a supervisor commit and a graft. Core's message-preserving
    rebase cases still converge.
- **Done when:** VI-5010 through VI-5012 pass, and security-reviewer returns clean.

### T3: Worker changes to trusted files are refused and never adopted

- **Depends on:** T2
- **Spec behavior:** AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0012 (its open-attempt clause; T2 owns the rest), AC-0026, AC-0027; TDD.
- **Touches:** new `_supervisor_attempt.py`; `_supervisor_loop.py` (manifest at attempt issue, open-attempt check, `report` checks); `_supervisor_git.py` (helper pre-check against an open attempt's manifest); Core manifests and changelog
- **Verification mode:** TDD
- **Tests:**
  - **VI-5020 (AC-0001, AC-0012):** each of these worker changes is refused at `report`:
    `plan.md`, a cited ADR, the installed skill, an `evidence.jsonl` append, a
    branch-ref move, a packed-ref move, `refs/replace/`, `.git/config`, a hook,
    the gitfile, and `commondir`. An attempt already reported stays closed
    after a message-preserving rebase.
  - **VI-5021 (AC-0002, AC-0003):** an implementer, and separately a
    reviewer, edits `plan.md`, `## Acceptance Criteria`, and `evidence.jsonl`,
    then `next` runs before `report`. Each gives `attempt-residue` before any
    envelope refusal, with no `replan` commit and an unchanged projection. The
    same holds on the re-issuance after that refusal clears.
  - **VI-5022 (AC-0004):** a `resolve-effect` and a re-approval during an open
    attempt advance `HEAD`, and the attempt still passes. Core's crash corpus,
    with the journal deleted during the lease, still converges.
  - **VI-5023 (AC-0005, AC-0006):** after a refusal, residue persists until the
    paths are restored. A refused ADR edit is never committed.
  - **VI-5025 (AC-0026, AC-0027):** a worker `git reset --soft HEAD~1`, a
    `commit --amend` of the last supervisor commit, and a `commit -C` copying its
    trailers are each refused. Deleting the journal, `run.json`, and the local
    security log during an attempt and after a refusal leaves the forged
    attempt refused and residue standing.
  - **VI-5024 (AC-0007, AC-0008):** symlinks out of the root, into a trusted
    file, and into `.git` are refused. An honest write that imports the
    installed scripts passes.
- **Done when:** VI-5020 through VI-5025 pass, and security-reviewer returns clean.

### T4: Launched code is checked, the supervisor is pinned, and untrusted code is gated

- **Depends on:** T3, spec:execution-supervisor-core/T5, spec:execution-supervisor-core/T6, spec:execution-supervisor-review-gate/T2
- **Spec behavior:** AC-0013, AC-0014, AC-0015, AC-0016, AC-0017; TDD.
- **Touches:** `_supervisor_attempt.py`; `_supervisor_loop.py`; `_supervisor_tdd.py`; `work-supervisor.py` (first-pin recording at `start` and the entry-point pin check); Core manifests and changelog
- **Verification mode:** TDD
- **Tests:**
  - **VI-5030 (AC-0013):** a `conftest.py` that an earlier task added writes
    `plan.md` during a red proof and during a gate run. Both are refused before
    commit.
  - **VI-5031 (AC-0014, AC-0015):** an edited installed module gives
    `supervisor-changed` at every entry point, including after core's caches
    are deleted. The first admitted `start` records the pins, and a second
    `start` neither overwrites nor accepts a differing record. After admission,
    a missing or malformed pin record gives `supervisor-changed`. A malicious `.pyc` never runs.
  - **VI-5032 (AC-0016):** after readiness, with the pack source edited, exactly
    one `regenerate` is emitted, admitted, and re-pinned. A mismatched install is
    refused.
  - **VI-5033 (AC-0017):** under `untrusted` with no attestation, there is no
    `run-gates` request and no red-proof or scratch launch, and a
    `human-decision` is emitted.
- **Done when:** VI-5030 through VI-5033 pass, and security-reviewer returns clean.

### T5: Results assert only their kind's facts, under recorded grants

- **Depends on:** T3, spec:execution-supervisor-core/T5, spec:execution-supervisor-core/T7, spec:execution-supervisor-review-gate/T2
- **Spec behavior:** AC-0018, AC-0019, AC-0020; TDD.
- **Touches:** `_supervisor_loop.py`; `_supervisor_tdd.py`; `_supervisor_git.py`; `docs/architecture/runtime-security-primitives.md`; Core manifests and changelog
- **Verification mode:** TDD
- **Tests:**
  - **VI-5040 (AC-0018):** one fixture per Result acceptance row. It includes
    an unknown kind, an `implement-task` result that carries gate outcomes, and
    a `regenerate` result that asserts digests.
  - **VI-5041 (AC-0019, AC-0020):** each launch kind's `safe-process.v1` record
    holds its table row. A probe child sees only the allowlisted variables.
- **Done when:** VI-5040 and VI-5041 pass, the architecture review is recorded, and security-reviewer returns clean.

## Rollout

- **Delivery:** each task ships in a Core 3.x patch release.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** T2–T5 follow the sibling tasks they name.

## Risks

- **`CreateProcessW` through `ctypes`:** handle leaks. Mitigation: VI-5003 and
  the security-reviewer pass.
- **Unsupported Git configurations:** repositories with custom filters, LFS
  among them, cannot run full mode. Mitigation: `start` names the setting, and
  the cutover documents the list.

## Changelog

<!-- Approvals only. -->

- 2026-10-20: spec approved by eugenelim
- 2026-10-20: plan approved by eugenelim
- 2026-10-20: spec approved by eugenelim
- 2026-10-20: plan approved by eugenelim
- 2026-10-20: spec approved by eugenelim
- 2026-10-20: plan approved by eugenelim
