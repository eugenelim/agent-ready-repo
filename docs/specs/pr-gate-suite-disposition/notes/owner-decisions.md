# Owner decisions: pr-gate-suite-disposition

Stable record of scope-owner decisions for this delivery. Referenced by
`loop-engine contract-amendment --owner-authority-ref`, which requires a
repository path: a conversation is not a reference.

## 2026-09-16 — Contract amendment approved: AC-0005 omits a coverage shape

**Decision.** Amend AC-0005 so its definition of "reaches" enumerates the three
shapes corroboration recognises for pull-request coverage, stated as recognised
rather than exhaustive. Owner authorised the controlled
amendment explicitly ("contract amendment approved").

**Defect.** AC-0005 as approved counts two shapes — a pytest operand of the step,
and any target `tools/repo/build_gate_chain.py` runs when the step invokes
`make build-check`. A third exists: a script invoked at a command position. Five
`run-test-suite` targets are gated exclusively that way, so the criterion as
frozen rejects five correct `PR_GATED` entries and thereby makes AC-0013 — the
lint exits 0 against the repository — unsatisfiable. The evidence, including the
five targets and their `build-check.yml` lines, is in
[`verification-ledger.md`](verification-ledger.md) § Specification error found.

**Amended wording.** "Reaches" counts, for the step in question:

1. a pytest operand of that step;
2. a script path at a command position in that step; and
3. any target `tools/repo/build_gate_chain.py` runs, when the step invokes
   `make build-check`.

These are stated as the shapes corroboration **recognises**, not as an exhaustive
account of how a step can run a suite. Review of the amendment found a fourth —
the `run_with_floor` shell wrapper at `build-check.yml:827` — whose two
directories are not `run-test-suite` targets. Teaching the check to read shell
wrappers is explicitly **outside** this amendment's authority.

**Why this shape and not a re-disposition.** Dispositioning the five as
`PR_GATED_IF` was considered and rejected by the owner: those five do run on every
pull request through `build-check.yml`, so calling them conditional would
understate real coverage, and it would give `PR_GATED_IF` two unrelated meanings
— "behind a path filter" and "invoked in a non-pytest shape".

**Scope.** No acceptance criterion is dropped, narrowed, or deferred, and no
follow-on is created: the amendment corrects an enumeration that was incomplete
when approved. AC-0013's outcome is unchanged; the amendment is what makes it
reachable.

## Earlier decisions, recorded during authoring

- Roster placement: extend `tools/lint-ci-parity.py` rather than add a new lint,
  because that module is already gated by a required pull-request check and a new
  lint would need wiring that lands ungated.
- `tools/test_local_ci_shared_test_deduplication.py`: PR-gate it despite 65.4s,
  against the measured cost of not doing so (red on `main` from PR #1313 to
  PR #1339, with PR #1336 merging green).
- Derive vs declare: follow `tools/lint-ci-parity.py`'s recorded precedent — a
  hand-declared roster as the anchor — over the defect entry's "derive" wording,
  with the disagreement recorded in `spec.md`.
- Roster scope: disposition all 114 targets, because the completeness arm cannot
  be switched on against a partial roster.
- Deletion pass: cut the criterion rejecting `PR_GATED_IF` on an unfiltered
  workflow, keeping the consequential direction only.
