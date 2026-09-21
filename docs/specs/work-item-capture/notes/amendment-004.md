# Amendment 004 — a task that must prove something owns somewhere to prove it

**Authorised by:** eugenelim, 2026-09-20 (same standing authority as 001-003)
**Against:** approved_plan_hash 0d49e15a45f8

## What happened

T6's `Tests:` section requires a test comparing the close-time branch table
in the shipped skill against the spec's own table. T6's `Touches:` listed the
skill file and its references directory — **no test location at all**. The
implementer wrote the test into `packs/core/tests/skills/work-loop/`, which
T7 owns, and flagged the crossing in its report rather than hiding it.

Crossing was the wrong call — the boundary exists so the plan's defects
surface instead of being absorbed — but the plan is what put it in that
position, and the test it wrote is correct and passing.

## The audit, run before amending

Every task was checked for the same shape: does a task whose `Tests:` section
demands an assertion own a path where a test can live? Two do not:

- **T6** — demands the branch-table comparison, owns no test path.
- **T8** — demands documentation and release checks, owns no test path.

The other six each own a test location. This is the same class as amendment
003: the plan assigned an obligation and withheld the surface needed to
discharge it. Fixing one instance and waiting for the next is what amendments
001 and 002 did, at the cost of two round trips.

## The amendment

Add `packs/core/tests/skills/work-loop/` to **T6**'s `Touches:`. That
retroactively legitimises the test already written and makes the plan honest
about who owns it. T6 and T7 are in different waves, so no concurrent edit.

**T8 is left as it is, deliberately.** Its checks are goal-based — a guide
names the three shapes, the architecture entry describes the record class,
the changelog entry leads the release, the self-host check is clean. Those
are verified by running commands and reading the artifacts they name, not by
a new test module. If T8 finds it needs one, that is a fifth amendment and a
signal the check was mis-specified as goal-based.

## Standing instruction this produces

When a plan gives a task an obligation to prove something, check in the same
breath that it owns a place to put the proof. Three of four amendments in
this run have been a task holding an obligation without the surface to
discharge it.
