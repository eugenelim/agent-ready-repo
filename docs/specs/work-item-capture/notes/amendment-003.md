# Amendment 003 — every task that changes the record contract gets the shared fixture

**Authorised by:** eugenelim, 2026-09-20 (same standing authority as 001/002;
this generalises what both were patching one task at a time)
**Against:** approved_plan_hash 902831032931

## The pattern, not the instance

Three amendments in two waves have the same root cause. The plan gives six
tasks `project_knowledge.py` — the validator that decides what a valid record
is — and gives only one of them
`packs/core/tests/skills/project-knowledge/knowledge_test_support.py`, the
module whose `valid_capture_request()` every other suite builds its fixtures
from. Changing what a record must be therefore reds that fixture, in a file
the changing task may not edit.

Measured at T3, not estimated: the § D6 argv change alone takes the suite
from 220 passed to **100 failed / 120 passed**, and every failure traces to
the shared fixture's string-valued `command`. The fixture is used across ten
files and twenty-two call sites, none of them in any task's `Touches:`.

Amendments 001 and 002 each fixed one task's instance of this. A third
instance is a class.

## The amendment

Add `packs/core/tests/skills/project-knowledge/knowledge_test_support.py` to
the `Touches:` of **every task that edits `project_knowledge.py`** — T2, T3,
T4, T5 and T7. T1 already has it.

Each task migrates the shared fixture to stay valid under the contract change
it makes, in the same task that makes the change. No criterion moves. No
task's behaviour changes. Wave placement is unaffected: T2, T3, T4 and T7 are
each alone in their wave, and T5 shares wave 5 only with T6, which touches no
Python under `project-knowledge`.

## What this does not license

Widening a shared *runtime* helper to make a fixture pass. That is what
amendment 002 records as the regression: `_expect_repo_path` and
`validate_capture_request` serve callers outside this feature, and the live
store holds records that a wide change makes unreadable. The fixture module
is test scaffolding; the helpers are not. A task may migrate the former
freely and must still stop at the latter.

## Standing instruction this produces

A task that changes what a valid record is owns the shared fixture that
constructs one. When a plan gives a task a validator, check in the same
breath which fixtures that validator's rules will red.
