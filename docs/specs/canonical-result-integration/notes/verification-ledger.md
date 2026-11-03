# Verification ledger: canonical result integration

Execution observations for the approved plan. This file records how tasks are
verified, not new obligations.

## Knowledge capture at spec-approved

`project-knowledge --capture --producer-profile work-loop --semantic-gate
spec-approved` refused with `map_mismatch`, which project-knowledge marks as
environmental. The owner chose on 2026-10-30 to record the refusal and start the
run; the gate captured nothing.

## Knowledge capture at plan-locked

The `plan-locked` capture was not attempted: it uses the same producer profile
and store that refused `spec-approved` with `map_mismatch`.

## T1: a sibling worktree's push refused the attempt

While T1's `implement-task` attempt was open, another worktree session of this
repository pushed a branch, and Git appended its `[branch …]` tracking entry to
the shared common-directory `config`. The supervisor's attempt check digests
that file, so `next` answered `attempt-residue` on `common:config`. With the
owner's agreement on 2026-10-30, the controller removed only that 3-line entry,
the supervisor re-issued the request, the result was reported, and the entry
was restored byte for byte. Captured as
`docs/product/captured/supervisor-common-config-residue.md`, and fixed by the
`supervisor-config-tracking-keys` spec in core 4.0.6 (#1668).

## T1: gates of record

Lint and mypy pass (157 files). Supervisor suites: 526 passed and 2 failed; the
two `test_supervisor_effects.py` rebase tests did not answer the new
`history-adoption` decision, were updated to answer it as the owner would, and
the suite then passed 35 of 35. Crash corpus: 187 passed in four shards of
about 24 minutes each. Roster schema and parity suites: 18 passed.

## T1: how it shipped

T1's first supervisor run admitted the task, then its review rounds ran in a
separate worktree outside that run, because each fix round rewrote the
supervisor the run had pinned. T1 shipped as core 4.0.7 in #1676 after fourteen
rounds of adversarial, security, and quality review. Its gates of record were
819 supervisor suite tests, the 187-case crash corpus, and 97 roster tests on
the merged tree, plus every PR CI check, Windows included. The first run is
not resumed: a run left by an earlier release counts its tasks incomplete, so
T2 and T3 run in a fresh run on `main` after #1676.

## T1: VI-0513's regenerate crossing

VI-0513 builds the "run with no recorded product ref" state by deleting the ref
and its run-store record, rather than by a real crossing from a run pinned to
the previous Core. The first run never reached `regenerate`, so no real
crossing was observed.

## T2: architecture review

The design reviewer reviewed T2's architecture pages in five rounds. Round 1
returned MAJOR REWRITE: the execution-supervisor page lacked the product-ref
procedure, still said a rebase converges on its own, and five pages gave three
reversal routes. The rounds that followed fixed those findings. They also fixed
the classification table's order, the crash-recovery wording, and ADR-0154's
correction, which the owner chose to record as a dated `## Errata` entry. Round
5 returned SHIP IT. Security was clean from round 2, and the adversarial and
quality reviewers were clean on their last code-bearing round.

## T2: the regenerate crossing found a defect

The second run's `regenerate` was the real crossing the T1 entry above had not
observed. The rebuilt install had to be committed by the controller. Under the
product ref, that commit was foreign history: leaving it uncommitted answered
`uncommitted-changes`, and restoring it answered `supervisor-changed`. On
2026-11-03 the owner adopted the controller's commit once (`reanchor`), and
chose to fix the defect in this slice as T4.

## T4: a regenerated install lands as a supervisor step

T4 makes the next `next` after a `regenerate` admission commit the pack source's
own entries at every copy of the skill that counts, as one recorded step. It
took five review rounds, which fixed steerable copy roots, a check-then-commit
gap, mode changes, staged versions, and the index after adoption. The run's own
second regenerate proved it: the supervisor committed both installs
(`.claude/` and `.agents/`) as one `regenerate` step, with no adoption, and
`HEAD` and the product ref named the same commit. Gates of record: 857
supervisor suite tests, the 203-case crash corpus, 97 roster tests, and every
PR CI check on #1678, Windows included.

## T3: closeout

VI-0531 is met by the closeout commit on #1678: the spec is `Shipped` with
every criterion checked, the plan is `Done`, and `lint-spec-status.py` passes.
The brief's Spec map already lists this spec.
