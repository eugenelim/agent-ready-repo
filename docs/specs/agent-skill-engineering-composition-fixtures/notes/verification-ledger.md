# Verification ledger — Agent Skill Engineering Composition Fixtures

Observations produced by execution. The spec and plan are pinned at approval;
this file is where anything measured during the build is recorded.

## Base

- **Base commit:** `d44484b29d1ba0f56cb0baf42fd79b1348e26a58`. Every "before this
  slice" comparison set — AC3's declared-case set, AC5's marker set, AC8's
  payload digests, AC12's inherited records, AC22's milestone string — is read
  from this commit with `git show d44484b29:<path>`.
- **Base freshness:** `check-base-freshness.py` returned
  `{"status": "ok", "message": "head is current", "target": "origin/main"}` on
  2026-09-09, before the first edit. The branch tip and `origin/main` were the
  same commit, so the base commit above is also the merge-base.
- **Base milestone,** recorded because AC22 compares against it:
  `M3 · slice 4 consumer integrations shipped; 3c and 3e are unblocked and
  parallel, 3d needs 3c, 5 needs 3c, 6 closes — see the brief's slice table`

## T1 — lifecycle roll

Completed 2026-09-09 in one commit. Evidence, in the order the task names it:

- **Registration moved, not appended.** `workspace_status.py explain` reports
  this spec in `collection=work.active` with `findings=[]`. Neither
  `duplicate_membership` nor `impossible_transition` is emitted for it. The
  `.queue` entry is gone rather than duplicated — the defect the round-3 review
  caught in the task's original wording.
- **AC22, all three conditions, measured against the base commit.** The
  milestone differs from `git show d44484b29:workspace.toml`: `True`. It
  contains "in flight": `True`. It no longer offers 3e as unblocked or parallel:
  `True`. New string: `M3 · slice 3e composition behavior fixtures in flight;
  slice 4 consumer integrations shipped; 3c unblocked, 3d needs 3c, 5 needs 3c,
  6 closes — see the brief's slice table`.
- **Brief Spec-map row (AC24), confirmed by reading.**
  `lint-brief-coverage.py --root .` exits 0 and resolves the row as
  `agent-skill-engineering-composition-fixtures: Implementing`. Exit 0 is not
  the evidence — the lint exits 0 on an unresolved back-link too — the resolved
  line is.
- **Brief prose reconciled.** The *Not yet started* paragraph no longer asserts
  that 3e has no spec, plan, or workspace entry; 3e moved to a new *In flight*
  paragraph and the remaining list reads "3c, 3d, 5 and 6".
- **Roster gates.** `tests/roster/test_workspace_status_projection.py` and
  `tests/roster/test_status_projection_and_context_exclusion.py`: 104 passed,
  12 subtests passed, 27.49s.
- **Status pair.** `spec.md` `Implementing`, `plan.md` `Executing`, both in the
  same commit as the registration move and the milestone rewrite.

## T2 — declare, pin, grade, reconcile

Recorded when the task completes. Required entries: every inherited verdict that
moved with its prior and measured value; each exemption's authority fields; each
enumeration's mutation proof; the per-assertion floor-requirement readings; the
per-verdict transcript readings; the round attestation; the payload-defect
reading; the bare-identity reading.

## T3 — publish and close

Recorded when the task completes.

## Observed gate failures

None yet.
