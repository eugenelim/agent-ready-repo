# Spec: semgrep-ratchet-integrity

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none — the change is confined to a self-test. No production
  script, no rule, and no gate invocation moves.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full (work-loop). Risk trigger that fired: compliance/governance/security
boundary — this file is the sole proof-of-life for the custom SAST rule that guards a
CWE-22/23 boundary, and a green result here is what licenses trusting the main scan's
silence (Makefile). Full mode is warranted even though the diff is one file and the
rule itself is untouched. Adversarial review is a NAMED SKIP (operator disabled
subagent dispatch); the spec-less self-review checklist and a mutation battery stand in
its place, and the mutation results are recorded in AC4 rather than asserted. -->

## Objective

`tools/test-semgrep-argv-boundary.py` is the only thing that proves
`tools/semgrep/argv-path-boundary.yml` still fires. The main `make sast` scan is
silent both when the rule works and when it has been broken into a no-op, so the
scan cannot distinguish them — the self-test is the discriminator.

That self-test re-declared the rule's `paths.include` as its own `FIXED_SCRIPTS`
constant, with nothing reconciling the two. The unchecked direction is the dangerous
one: a constant **shorter** than the rule's scope leaves a ratcheted script unscanned
while every assertion still passes.

Success: the rule file is the single definition of what is ratcheted, a shrunken or
mis-pointed scope is a named failure, and the assertions name the rule they claim to
prove rather than the file that contains it.

## Acceptance Criteria

- [x] **AC1 — the ratcheted scope is derived from the rule, not restated.**
  `FIXED_SCRIPTS` is gone. `ratcheted_scope()` parses
  `tools/semgrep/argv-path-boundary.yml` with `yaml.safe_load` and splits
  `paths.include` into concrete file entries (the production scripts to scan and
  assert) and glob entries (the fixtures directory, already covered by
  `unwired_fixtures`). The concrete list is what `main()` scans.

- [x] **AC2 — the drift that was already present is closed.**
  `packs/core/.apm/skills/work-loop/scripts/_loop_guards.py` was in the rule's
  `paths.include` and absent from `FIXED_SCRIPTS`, so it had never been scanned or
  asserted by this gate. It is now, and it is silent — verified independently by a
  direct `semgrep --config … -- _loop_guards.py` run reporting it scanned with zero
  findings, before the derivation was written, so the fix could not turn the gate red
  on arrival.

  The self-test goes from **5 assertions to 7**: the new coverage assertion plus
  `_loop_guards.py`.

- [x] **AC3 — an unscanned ratcheted path is a named failure.**
  `test_ratcheted_scope_is_covered` fails, by name, when any concrete
  `paths.include` entry is absent from semgrep's `paths.scanned`. Without it, the
  derivation would be decorative: "no findings" is satisfiable by semgrep never
  having looked, which is exactly how the shrinking list used to pass.

- [x] **AC4 — the control is proved able to fail.**
  A green self-test is worth nothing unless breaking what it guards turns it red.
  Measured, each mutation applied and reverted:

  | Mutation | Before | After |
  | --- | --- | --- |
  | `FIXED_SCRIPTS = []` | `2/2 passed`, **exit 0** | n/a — the constant no longer exists |
  | A `paths.include` entry mis-pointed to a nonexistent file | would pass silently | `5/7 passed`, **exit 1**, `FAIL [every ratcheted path in the rule was scanned]` naming the path |
  | `paths.include` reduced to globs only | would pass silently | **exit 1**, `paths.include has no concrete file entries … no production script would be asserted` |
  | A second rule added to the rule file | positive-fixture proof satisfiable by either rule | **exit 1**, `expected exactly 1 rule, found 2` |

  The first row is the defect this spec closes, reproduced before the fix.

- [x] **AC5 — findings are keyed by the rule, not only by path.**
  `scan_all` filters `payload["results"]` on
  `check_id.endswith("argv-path-without-boundary-validator")` before grouping.
  `--config` names a *file*, so previously any rule in that file could satisfy the
  positive-fixture proof-of-life while the rule under test was neutered.

  The report-consistency guard (a finding on a path semgrep did not list as scanned)
  stays **before** the filter: an inconsistent report is a defect whichever rule
  produced it.

  Honest scope: `ratcheted_scope()` now refuses a multi-rule file outright (AC4, row
  4), so this filter is belt to that brace and is unreachable today. Both are kept —
  the failure they prevent is a silently green ratchet, and the two guards fail on
  different mutations.

- [x] **AC6 — the optional-tool skip posture is unchanged.**
  `ratcheted_scope()` is called inside `main()`, *after* the semgrep-on-PATH check,
  and the derived list is threaded to the assertions as a parameter rather than a
  module global.

  This is deliberate and was corrected during implementation: an earlier revision
  derived the scope at import time, which made a malformed rule file exit 1 on a
  machine with no semgrep — a behaviour change this fix has no business making.
  Verified both ways: with `PATH` stripped of semgrep and a deliberately malformed
  rule, the script prints its `skip:` line and exits 0; with semgrep present, the
  same malformed rule exits 1.

## Boundaries

**Never do**

- Edit `tools/semgrep/argv-path-boundary.yml`. The rule is the subject under test;
  changing it to make the test pass inverts the gate. It is byte-identical in this
  diff (`git diff --stat` on it is empty).
- Add a path to `paths.include` for a script that has not adopted a boundary
  validator. The rule's own header states the expansion condition, and a premature
  entry reddens the gate on unrelated work.
- Widen the rule's scope to sweep the remaining ~68 argv→path sites. That is
  `pack-argv-path-boundary-sweep`, explicitly a migration rather than a fix.
- Reimplement a YAML parser to avoid the `yaml` import. That is the antipattern
  behind `ci-gate-parallelization-posture-test-yaml-parser`.

## Assumptions

1. **PyYAML is importable wherever this test runs.** Verified rather than assumed.
   `make sast` (Makefile) is the only invocation — the module docstring says so,
   because the test needs semgrep on PATH, and `docs.yml` names the file only as a
   `paths:` trigger. The CI job running `make sast` installs
   `tools/requirements-sast.txt`, whose `bandit` requires `PyYAML>=5.3.1`; pyyaml is
   also declared directly in `tools/requirements.txt` for local runs.

   This is a transitive guarantee, which is why the import carries a comment naming
   both manifests. If `bandit` ever drops PyYAML, this import is the second thing to
   break and the comment is what makes that diagnosable.

2. **`import yaml` in a `tools/` script is consistent with the repository.**
   AGENTS.md § *New tool scripts* requires *new additions* to `tools/` to be
   pure-stdlib; this is an existing file, and seven `tools/` scripts already import
   yaml, including the closest siblings `lint-ci-parity.py` and
   `test-ci-security-workflow.py`. `tools/lint-build.py`'s stdlib-import audit is
   scoped to `LINT_BUILD_DIR` (`packages/agentbundle/agentbundle/build`), not
   `tools/` — confirmed by reading it, and `lint-build.py` passes.

3. **`_loop_guards.py` scans clean.** Confirmed by direct invocation before the
   derivation was written (AC2).

## Residual — stated, not closed

Deriving the list guarantees *test scope == rule scope*. It does **not** guarantee
the rule's scope is complete: shrinking `paths.include` itself still shrinks coverage,
and the self-test will pass with fewer assertions. What is now impossible is the two
disagreeing, which is the defect
`sast-ratchet-scope-duplicated-fails-open` named and the only one this spec claims.

The rule's expansion is tracked separately as `pack-argv-path-boundary-sweep`. A
guard on the rule's own scope would need a roster of every script that has adopted a
validator — a different control, and a larger one.
