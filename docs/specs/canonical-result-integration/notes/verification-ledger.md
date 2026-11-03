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
