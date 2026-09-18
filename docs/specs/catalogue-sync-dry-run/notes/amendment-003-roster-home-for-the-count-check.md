# Amendment 003 — T2's `Touches` gains the repo-only roster tree

- **Date:** 2026-09-17
- **Run:** `b9900572-04c5-40b5-ac46-a02ea5b54bd5`
- **Raised at:** `CODE-IMPLEMENTATION`, wave 1 (`[T1, T2]`), with **T2 started**.
- **Owner authority:** the repository owner, in session, chose "move it to the
  repo-only tree" over skip-guarding it in place and over dropping the
  subprocess comparison. This file is that decision's repository record.

## The defect

T2's repaired fixture-count check reads the § Grounding derivation by running
it, which is what makes the comparison independent of the implementation it
checks. It resolves the script repo-relatively and without a guard:

```python
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
_DECLINE_BRANCH_DERIVATION = (
    REPOSITORY_ROOT / "docs/specs/catalogue-sync-dry-run/notes/grounding/derive-decline-branches.py"
)
```

`packages/agentbundle/tests/` is a **published** tree: `gate-export-boundary`
builds an sdist of `agentbundle` and runs the shipped suite inside it, and that
environment has no `docs/`, no `packs/`, and no `workspace.toml`. So the check
cannot run where it is currently homed, and would fail rather than skip.

Demonstrated rather than inferred: with the derivation held aside, the test
fails with `assert 2 == 0` and
`[Errno 2] No such file or directory`. One defect of this shape has previously
reddened three checks at once — `gate-export-boundary`, `build-and-smoke`, and
`make build-check` as its aggregator.

The precedent for the fix is established: two integration tests that read the
repository were moved out of the published tree into the repo-only roster tree
for exactly this reason.

Cause note: T2's brief required the comparison to read the derivation's output
rather than re-derive it, which is right, but did not say that the test tree is
published. The obligation was sound and its home was not.

## Scope

Only `docs/specs/catalogue-sync-dry-run/plan.md`, and only T2's `Touches`,
which gains the roster path **and the wiring `tests/AGENTS.md` requires for it**:

```
  **Touches:** …/initialise_self_hosted.py,
               …/test_catalogue_tooling_self_hosted_init.py,
               …/notes/grounding/derive-decline-branches.py,
+              tests/roster/test_catalogue_sync_decline_branch_alignment.py,
+              .github/workflows/build-check.yml,
+              tools/lint-ci-parity.py,
+              .workspace-prune-protected.toml
```

### Correction — this amendment was first scoped to one file, and that was wrong

`tests/AGENTS.md:29-37` states that adding `tests/roster/test_x.py` "obliges
three further edits, each guarded separately":

1. a step in `.github/workflows/build-check.yml` naming the file — "without it
   the suite runs on no pull request at all, and stays green by never
   executing";
2. a matching `STEP_DISPOSITION` entry in `tools/lint-ci-parity.py`, where
   `LOCAL("test-after-build-check")` is the right value for roster, because that
   target's `run-test-suite` includes `pytest tests/ -q`;
3. an entry in `.workspace-prune-protected.toml`, required "when the test names
   a `docs/specs/<slug>` path as a literal" — which this test does, since that
   is how it reaches the derivation.

`tests/AGENTS.md` also warns that moving a test out of a suite orphans the
imports only it used, and that `ruff check .` must be run afterwards because the
repository lint targets do not cover it.

Root `AGENTS.md` § Rule lookups obliges reading every scoped `AGENTS.md` on the
path to a file being changed. `tests/AGENTS.md` governs `tests/roster/` and was
not read before this amendment was first scoped or before the route was priced
for the owner, so the owner's choice rested on a cost of one file when the real
cost is five and touches two gate-chain surfaces. The corrected cost was put
back to the owner, who confirmed the move with full wiring. Recorded here
because a decision taken on wrong pricing must show the correction, not just the
outcome.

No acceptance criterion changes. No task outcome, `Tests`, `Done when`, or
dependency edge changes. No other task's section changes. `spec.md` is
untouched; its canonical `approved_spec_hash` has been `4d14dd64a131…` across
every approval in this run and must stay so.

The move itself is then T2's work: the fixture-count-versus-derivation check
relocates to the roster tree, while every per-branch reason fixture, the
pairwise token distinctness, and the decided/undecided partition stay in the
published unit file, because those read only `agentbundle` and are legitimate
adopter tests.

## Note on why the obligation still holds after the move

T2's `Tests` field requires "equality between the fixture count and the
post-change § Grounding derivation". That obligation is a delivery-time check
on this change, not a standing adopter test — the derivation it reads is part of
this spec's working material and is not shipped. The roster tree is where a
repo-reading check belongs, so the move satisfies the obligation rather than
weakening it. The fixture table it compares against stays in the unit file, so
the roster test imports it rather than duplicating it; a second copy of the
table would be a control that agrees with itself.

## Bookkeeping, recorded because the last amendment got it wrong

`loop-cohort schedule` builds waves over **unfinished** tasks and infers
completion from the previous `current_wave_index`, then resets the index to 0.
At amendment 002 this turned an 8-wave schedule whose wave 0 was `[T0]` into a
7-wave schedule whose wave 0 was `[T1, T2]`. Restoring the remembered index of
1 pointed the engine at `[T3]` and skipped the in-progress wave; that was
caught, and recovered with a cohort-only reset that brought T0 back into the
schedule.

For this amendment the position is re-established by **reading the persisted
wave array and locating the wave that contains `T1` and `T2`**, not by
restoring a remembered number. If the re-schedule again omits the completed
`T0`, index 0 is the correct answer and no advance is owed.

## Scoped review

The changed task is T2; its declared dependant is T6. T1 shares the wave but
not the edge.
