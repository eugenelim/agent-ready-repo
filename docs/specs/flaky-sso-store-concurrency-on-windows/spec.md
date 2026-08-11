# Spec: Flaky SSO store concurrency on Windows

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`RFC-0035`](../../rfc/0035-sso-cookie-auth-for-atlassian-pack.md); [`RFC-0013`](../../rfc/0013-credential-broker-contract.md); [`ADR-0026`](../../adr/0026-sso-consumer-resolution-in-credbroker.md); [`sso-store-transition-serialization`](../sso-store-transition-serialization/spec.md); [`docs/architecture/credentials.md`](../../architecture/credentials.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

Mode: full (risk triggers: **security boundary** — authentication material and
filesystem confinement; **unfamiliar** — Windows path canonicalisation during
concurrent directory creation)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Concurrent SSO store operations for one profile acquire the profile lock and
complete without a false `ProfileConfinementError` when the lock directory is
created for the first time on Windows. The lock path remains confined through
the existing canonical-path check. Windows verification proves the targeted
regression and the complete relevant gate; a passing rerun of unchanged code
is not evidence of completion.

## Boundaries

### Always do

- Preserve canonical-path confinement through `_sso_lock_path()` /
  `_contained()` for every profile-derived lock path.
- Reproduce the Windows existence-dependent canonicalisation change with a
  deterministic test that controls the directory-creation boundary.
- Create only the fixed `_SSO_LOCK_DIR` before validating a child path, and
  fail closed before `os.open()`.
- Run the targeted and full `packages/credbroker` suites on macOS and verify
  the complete existing Windows gate.

### Ask first

- Change any public `credbroker` API, broker exit code, lock budget, contention
  behavior, or intended confinement boundary.
- Widen the fix into the shared `_contained` helper or another profile-derived
  path.
- Change the Windows workflow beyond what is necessary to run the existing
  gate.

### Never do

- Add a dependency, module, public interface, configuration switch, retry,
  sleep, rerun-based acceptance, flaky marker, quarantine, or platform skip.
- Weaken, bypass, or catch-and-ignore `ProfileConfinementError`, including by
  replacing canonical resolution with lexical prefix comparison.
- Open a profile-derived child before confinement succeeds or continue with
  unconfined or unserialized access.
- Treat macOS-only results as platform verification.

## Testing Strategy

- **Lock-directory initialisation invariant: TDD at unit-test surface.** A
  deterministic regression models the Python 3.11 Windows transition from a
  lexical missing-parent form to its canonical existing-parent form when a
  competing first-use operation creates the parent between observations. It
  fails against the current ordering with `ProfileConfinementError` and passes
  only when confinement observes a stable parent state.
- **Fail-closed lock boundary: goal-based construction check.** Entering
  `_profile_lock()` with an escape may create its fixed parent, but must raise
  before opening any child. This green-before-and-after non-regression check
  pins the security boundary while existing exit-code mapping stays unchanged.
- **Concurrent file-floor behavior: goal-based integration check.** Both
  existing `test_file_floor_path_is_serialised_too` parameter cases exercise
  two writers through the real lock and file-floor path and must pass.
- **Confinement non-regression: goal-based unit check.** Existing traversal,
  symlink, canonical-path, reserved-name, and wrong-parent tests remain green.
- **Platform and repository compatibility: goal-based gates.** macOS runs the
  complete package suite, lint, typecheck, projection, and repository gate;
  the existing Windows job runs the credential-broker suite on Python 3.11.

## Acceptance Criteria

- [x] **AC1.** A deterministic regression fails on the original operation
      ordering with `ProfileConfinementError` and passes after the fix without
      threads, timing, retry, sleep, or probabilistic scheduling.
- [x] **AC2.** Given a competing first-use caller creates the lock directory
      during an existence-dependent Windows canonicalisation transition, the
      valid victim call opens the expected confined lock location without a
      false `ProfileConfinementError`.
- [x] **AC3.** Given traversal or a wrong-parent profile-derived lock path,
      entering `_profile_lock()` may create only the fixed `_SSO_LOCK_DIR`,
      raises `ProfileConfinementError` before opening a child, retains CLI exit
      code `3`, and never falls back to unconfined or unserialized access.
- [x] **AC4.** Existing traversal, symlink/canonical-path, reserved-name,
      restrictive-mode, timeout, stale-owner, release, and error-mapping tests
      remain unchanged and green.
- [x] **AC5.** Both parameter cases of
      `test_file_floor_path_is_serialised_too` and the deterministic regression
      pass on macOS and are collected without skip by the Windows credential-
      broker suite.
- [x] **AC6.** `.github/workflows/build-check-windows.yml` job
      `build-check-windows` (display name `make build-check (windows)`) is green
      on the PR commit. Its
      `agentbundle catalogue self-host --check --windows --root .` command
      completes `credbroker suite (process-tree kill parity)`, which executes
      the targeted test; an unchanged flaky rerun is not acceptance evidence.
- [x] **AC7.** On macOS, the targeted tests, full `packages/credbroker` suite,
      `make lint-ruff`, `make lint-mypy`, `FORCE=1 make build-self`, and
      `make build-check` are green.
- [x] **AC8.** The `credential-brokers` pack receives a patch version bump and
      its manifest, plugin manifest, changelog, and generated projections are
      synchronized; no unrelated package version changes.
- [x] **AC9.** The diff adds no retry, sleep, skip, flaky marker, quarantine,
      dependency, public API, exit-code, lock-budget, widened confinement, or
      unbounded-wait change.

## Assumptions

- Technical: the failure originates while acquiring the profile lock, before
  the file-floor write; the fixture creates one home and all path overrides
  before starting either writer (source:
  `packages/credbroker/tests/unit/test_sso_store_concurrency.py`).
- Technical: `os.path.normcase()` rules out a case-only mismatch. Python 3.11
  non-strict resolution resolves an existing prefix and appends a missing
  remainder unchecked, so directory existence can change the representation
  observed by consecutive resolves (source: Python 3.11
  [`Path.resolve()`](https://docs.python.org/3.11/library/pathlib.html#pathlib.Path.resolve)
  and
  [`os.path.realpath()`](https://docs.python.org/3.11/library/os.path.html#os.path.realpath)
  documentation, acquired 2026-08-10).
- Technical: `.github/workflows/build-check-windows.yml` selects Python 3.11
  and its self-host check runs the full `packages/credbroker` suite (source:
  workflow and `self_host_windows.py`).
- Product: both concurrent operations complete while confinement remains
  equally strict (source: user confirmation 2026-08-10).
- Process: local `main` is the accepted freshness baseline because enterprise
  policy prevents updating Git metadata in this session (source: user
  confirmation 2026-08-10).
- Process: the user's writable shell can run tests and projection commands
  that this managed shell cannot run because it lacks a writable temp
  directory (source: user confirmation 2026-08-10).
- Process: GitHub authentication will be restored once with `gh auth login`;
  otherwise handoff stops at a locally verified branch with the exact PR
  action (source: user confirmation 2026-08-10).

## Done when

- The deterministic regression is demonstrated red before the runtime edit
  and green after it.
- The macOS commands named in AC7 are green and generated projections match
  their source.
- Adversarial, security, and quality reviewers report clean and both human
  gates are approved.
- A PR is open and the Windows job named in AC6 is green with its credential-
  broker suite complete; any Windows failure has been diagnosed and fixed
  rather than merely rerun.
