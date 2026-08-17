# Spec: semgrep-selftest-batching

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0017 (custom Semgrep `mode: taint` rules live in
  `tools/semgrep/` and run in `make sast`; this file is what proves the rule fires)
- **Brief:** none
- **Discovery:** none
- **Contract:** none — internal gate self-test. Invocation
  (`python3 tools/test-semgrep-argv-boundary.py`) and exit codes (`0` pass or
  semgrep absent, `1` any failure) are unchanged.
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: light (no risk trigger fired). The change is a behaviour-preserving
refactor of one test's process usage, in familiar territory, single task,
reversible, no new dependency, and no structural or public-interface change. It
alters nothing about what the SAST gate scans, suppresses, or blocks on — the
same rule is applied to the same five targets with the same assertions. -->

## Objective

`tools/test-semgrep-argv-boundary.py` proves the `argv-path-boundary` taint rule fires
on its positive fixture and stays silent on its negative fixture and on the three
production scripts it ratchets — using **one** `semgrep` process instead of five. The
five separate invocations cost about 6s each, almost all of it semgrep's process
startup rather than scanning, so batching takes about 21s off `make sast` (locally
29.8s → 8.9s) while proving exactly the same things.

The merge is safe because semgrep parses and matches each file independently and names
the file in every finding, so per-target attribution survives natively. Every assertion
still confirms the rule actually **reached** its target before trusting the target's
silence — and that confirmation now covers the negative fixture too, because once
findings arrive keyed by path, a path-key mismatch would otherwise make a
"zero findings" assertion pass without the rule having looked at anything.

## Acceptance Criteria

- [ ] The self-test spawns exactly **one** `semgrep` process, and
      `python3 tools/test-semgrep-argv-boundary.py` completes in under 15 seconds
      (baseline: 29.8s).
- [ ] The same five targets are scanned: the positive and negative fixtures plus
      `lint-traceability.py`, `lint-spec-status.py`, and `loop-cohort.py` under
      `packs/core/.apm/skills/work-loop/scripts/`.
- [ ] The positive fixture still asserts **exactly one** finding; the negative fixture
      and all three production scripts still assert **zero**.
- [ ] Every one of the five targets is confirmed present in semgrep's reported scanned
      set before its findings are asserted on. A target semgrep did not scan is a
      failure, never a silent pass — including the negative fixture, which the
      per-invocation version did not check.
- [ ] The test still **fails** when the rule is broken: proven by mutation, not by
      inspection. Reverting the fix in one ratcheted production script makes it fail,
      and neutering the rule's pattern makes the positive-fixture case fail.
- [ ] The test still exits 0 with a skip message when `semgrep` is absent from `PATH`,
      and exits 1 when the rule file is missing.
- [ ] Exit codes and the `ok [...]` / `FAIL [...]` output contract are unchanged, so
      `make sast`'s recipe needs no edit.
- [ ] `make sast`, `python3 tools/lint-ruff.py`, and
      `python3 -m pytest tools/test_build_gate_chain.py -q` are green.

## Testing Strategy

- **The refactor itself is goal-based**: `Done when:` the self-test exits 0, spawns one
  semgrep process, and runs under 15s. There is no invariant to compress into a unit
  test here — the artifact *is* a test, and its correctness is whether it still
  discriminates a working rule from a broken one.
- **That discrimination is verified by mutation, which is the load-bearing check.** A
  faster self-test that can no longer fail is strictly worse than the slow one it
  replaced, and the specific failure mode this refactor introduces — findings keyed by
  a path that never matches, so every "zero findings" assertion passes vacuously — is
  invisible to a green run. Two mutations are required: break a ratcheted script (a
  zero-findings assertion must fail) and neuter the rule (the one-finding assertion
  must fail). A single mutation would not cover both directions.
- **Skip and missing-rule paths are goal-based**, exercised by invoking with `semgrep`
  off `PATH` and with the rule path pointed elsewhere.

## Assumptions

- Technical: semgrep accepts multiple target paths in one invocation and reports
  `results[].path` per finding plus `paths.scanned` listing every file it examined
  (source: probe — one invocation over all five targets returned all five in
  `paths.scanned` with 1 finding on `positive.py` and 0 elsewhere, 2026-08-17)
- Technical: semgrep has a ~7.4s process-startup floor independent of the registry — a
  local-rule-only scan of one trivial file still costs it (source: probe, 2026-08-17).
  This is why five invocations cost 29.8s and one costs 8.9s.
- Technical: semgrep parses and matches each target independently, with no cross-file
  resolution, so batching cannot change any per-file verdict (source: semgrep 1.166.0
  behaviour; contrast `tools/audit-requirements.py`, where pip-audit resolves all `-r`
  inputs into one environment — see `docs/specs/pip-audit-batching/spec.md`)
- Technical: semgrep reports paths relative to its working directory, which this script
  already pins to `REPO_ROOT` via `cwd=` (source: `tools/test-semgrep-argv-boundary.py:81`)
- Process: light mode is correct here because no risk trigger fires; the SAST gate's
  scan scope, suppressions, and blocking behaviour are untouched (source:
  `AGENTS.md` § *How we work* risk-trigger list)
