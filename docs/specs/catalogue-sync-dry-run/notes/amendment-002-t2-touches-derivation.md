# Amendment 002 — T2's `Touches` gains the decline-branch derivation

- **Date:** 2026-09-17
- **Run:** `b9900572-04c5-40b5-ac46-a02ea5b54bd5`
- **Raised at:** `CODE-IMPLEMENTATION`, wave 1, with **T2 started**. Wave 0 (T0)
  was complete and its evidence is in
  [`verification-ledger.md`](verification-ledger.md).
- **Owner authority:** the repository owner, in session, chose "amend T2's
  `Touches`" over adding a new task and over making the derivation
  function-agnostic, when the three routes were priced against each other. This
  file is that decision's repository record.

## The defect

T0 authored `notes/grounding/derive-decline-branches.py`, which locates decline
branches by matching one function name:

```python
if isinstance(node, ast.FunctionDef) and node.name == "_remove_stale_owned_paths":
```

T2's declared `Approach` then moves those branches out of that function:
"Split the per-entry loop into `_plan_stale_owned_paths(target, old_state,
current_paths)` … Reduce `_remove_stale_owned_paths` to calling the planner and
unlinking."

After T2's refactor the script exits 1 with `removal guard has no decline
branches` — the function still exists but holds zero. Measured independently:
`_plan_stale_owned_paths` carries **7** decline branches and
`_remove_stale_owned_paths` carries **0**.

T2's `Tests` field requires "equality between the fixture count and the
post-change § Grounding derivation". That obligation cannot run, so T2 cannot
legitimately close. The plan contained the conflict from the start: one task's
declared refactor invalidates another task's declared derivation, and no review
round caught it because each was consistent with the artifact on its own.

## Why this is an amendment and not a discovery refinement

§ Discovery channel admits a change to "the location and invocation mechanics"
of a Grounding script. This is neither: it changes which construct the script
inspects, which is the derivation's **oracle**. Amendment 001 narrowed the
pinning rule to keep a derivation's value and oracle amendment-only, precisely
so this case routes here. T2 is also a **started** task, and a started task's
section changes only through this path.

## Scope

Only `docs/specs/catalogue-sync-dry-run/plan.md`, and only T2's `Touches`:

```
  **Touches:** …/initialise_self_hosted.py,
               …/test_catalogue_tooling_self_hosted_init.py,
+              docs/specs/catalogue-sync-dry-run/notes/grounding/derive-decline-branches.py
```

No acceptance criterion changes. No task outcome, `Tests`, `Done when`, or
dependency edge changes. No other task's section changes. `spec.md` is
untouched and its approved hash must come back identical to `4d14dd64a131…`,
as it did across amendment 001.

The script's own change is then T2's work: match `_plan_stale_owned_paths`
instead, so the derivation measures the guard where the guard now lives.

## A second defect, fixed inside T2's existing bounds — no amendment needed

T2's inline proof for the decided/undecided partition cannot fail for one of
its two members:

```python
assert {"path-confinement-refused", "recorded-entry-unreadable"} == {
    f[4] for f in _STALE_DECLINE_FIXTURES if f[5] == "undecided"
} | {"recorded-entry-unreadable"}
```

The fixture table holds 6 entries with exactly one marked `undecided`, so the
right-hand side's second member is supplied by the union literal rather than
observed. Reclassifying `recorded-entry-unreadable` as decided leaves this
assertion passing, while spec AC-0013's "could not be compared" condition reads
that undecided set. The test file is already in T2's `Touches`, so this is
ordinary in-task repair.

## Bookkeeping consequence, recorded because it is otherwise invisible

`loop-cohort schedule` sets `current_wave_index = 0` unconditionally
(`loop-cohort.py:1469`), and re-approval after a plan edit requires a
re-schedule to re-hash the plan. Re-scheduling therefore resets the loop to
wave 0 even though wave 0 is complete.

The position is restored with the sanctioned `wave advance --from-index 0`
verb, which moves the index only. This is restoration of a recorded position,
not a fresh claim that wave 0's gates passed again — wave 0's evidence stands in
`verification-ledger.md`, and the engine's own history carries its
`wave-complete` and `wave-passed` transitions at sequences 18 and 19.

## Scoped review

§ Discovery channel requires the changed task and its declared dependants. The
changed task is T2; its declared dependant is T6 ("T5 — classification runs in
the command module; T2 — …"). T1 is unaffected: it shares the wave but not the
edge.
