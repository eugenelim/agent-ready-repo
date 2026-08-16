# Spec: gate-chain-cwd-steps

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** the local gate chain gains a step kind. No published interface
  changes; `tools/` is non-release-impacting.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full. Risk trigger: structural — a new step kind in the gate chain
changes what `make build-check` runs, and relaxes an assertion that guards
Windows portability. -->

## Objective

A suite that must run from its own directory could not be expressed in the local
gate chain, so it ran only in CI. `make build-check` silently skipped it.

## Acceptance Criteria

- [x] **AC1 — the chain can express "run from here".** `_pytest_step_cwd(label,
  cwd, *targets)` uses `subprocess`'s own `cwd=`, so there is no `cd &&`, no
  shell, and no POSIX-only quoting — the argv stays a plain list and the step
  stays Windows-clean.

- [x] **AC2 — the credential-setup gate is now locally covered.** It moves from
  `CI_ONLY` to `LOCAL("build-check")`; `lint-ci-parity` reports 31 locally
  covered where it reported 30.

- [x] **AC3 — the parity linter can see a cwd-scoped target.** Its reachability
  scan matches literal repo-root paths, and this step's targets are bare
  filenames. The extractor joins `cwd` and target, so the gate is not reported
  CI-only while it is in fact wired locally.

- [x] **AC4 — the relaxed assertion still asserts the thing that matters.**
  `test_script_steps_are_windows_clean` pinned argv *length*, which was only ever
  a proxy for "nothing clever is going on" — and the proxy had become the
  constraint. It now checks the claim directly: no `bash`/`sh`/`-c`, no `.sh`, no
  shell metacharacter in any token, and any `cwd` is a real absolute path.

- [x] **AC5 — the new step kind is itself covered.** A test asserts a cwd-scoped
  step exists, runs from the expected directory, and passes bare filenames rather
  than repo-root paths.

- [x] **AC6 — the gap is demonstrated, not asserted.** From the repo root the
  suite collects nothing ("no tests ran"); from its directory, 16 pass. That
  difference is the entire reason the vocabulary was needed.

- [x] **AC7 — the remaining exemption's reason is corrected, not inherited.**
  The catalogue-curation step stays CI-only, but *not* for the reason recorded:
  its shell body counts collected tests and asserts a floor, because its
  invocations are directory-scoped with no filenames, so a suite that fails to
  land would reduce the count and still exit 0. Porting it means reimplementing
  that floor in Python. Recorded as `gate-chain-curation-count-floor`.

- [x] **AC8 — CI's import probe stays in CI.** The CI step also asserts
  `credbroker`, `cryptography` and `argon2` import — provisioning verification
  for that runner. The local step deliberately omits it: the suite self-skips its
  crypto-gated cases via `requires_crypto`, so a contributor without the extra
  gets a passing build-check rather than a failure about an optional dependency.

## Boundaries

### Never do

- Never express a cwd with `cd &&` or a shell string. AC1 is the reason the step
  kind exists.
- Never re-pin argv length as the Windows-cleanliness proxy. AC4.

## Testing Strategy

- **TDD** for AC4/AC5; **goal-based** for AC2/AC3/AC6 (linter output and a real
  run from each directory).
