# Amendment 0002 — owner authority

## Decision

The scope owner (`eugenelim`) authorized one controlled contract amendment to
`plan.md` on 2026-09-18, in session, choosing "Amend to add a task" from three
priced options after T5 reported `blocked`.

## What the owner was shown before deciding

T5's mutation sweep applied 34 mutations to the clauses T2 and T3 added. Thirty-
three reddened a named test. **One survived green**: the verb's usable-partition
check, `if not isinstance(waves, list) or not waves`, in `plan_dispatch_receipt`.

The controller reproduced the survival independently rather than accepting the
report — neutralising the clause leaves 266 tests passing at exit 0, with the
source restored to hash `1a221d9494cca78f` afterwards.

The cause is a non-discriminating assertion, not a missing case. Both driving
cases assert `expect=("schedule_waves",)`, a substring that three different
rows' messages all contain. With the clause removed, `waves == []` refuses on the
pointer row and `waves == "nope"` refuses on the wave row, so the case passes
either way. It is a control that cannot fail, which is the class T5 exists to
detect.

T5 walked the remedy against both arms rather than proposing it: a per-parameter
expectation pinned to the word each row owns gives 9 passed with the clause
present and 2 failed with it removed. Its first shape reddened three parameters
on the **unmutated** tree, because those rows correctly say "malformed" — a
remedy that fails on green is itself a false control — so it reshaped and
reverted rather than landing anything.

## Why a new task rather than the alternatives

T5's `Touches` is one file, the verification ledger. The repair is a test-file
edit. The plan's own `Approach` anticipated this — "a clause whose removal leaves
the suite green returns to T2 or T3 for a discriminating assertion" — but T2 and
T3 are complete, and the amendment rules state that a completed section cannot be
edited and that a correction is a new dependency-ordered unfinished task. So the
plan anticipated the survivor and its task graph cannot express the repair.

Widening a started task's `Touches` was rejected as worse form at the same cost.
Accepting the survivor was rejected because the clause would ship with no test
that can fail on it.

## Scope of the authority — three changes, and no others

1. **Add T7**, depending on T5: pin each malformed-partition case to the word its
   own row owns, re-run the survivor mutation, and supersede the ledger's green
   row with a caught row. Touches
   `packs/core/tests/skills/work-loop/test_loop_cohort.py` and the ledger.
2. **Re-point T6's dependency** from T5 to T7, so the release bump stays last.
   T6 is unstarted, so this edge is inside ordinary amendment scope.
3. **Narrow T5's `Done when`** from "no row reports a green survival" to
   requiring every green survival to be recorded together with the task that
   closes it. This is the one started-task edit. It is a narrowing to what a
   check can reach at T5's own time: T5 cannot close a survivor inside a
   one-file `Touches`, so the unnarrowed clause could not be discharged by the
   task that carries it. The obligation is not dropped — it moves to T7, which
   this amendment creates, and T6 now sits behind T7 so nothing ships before it
   is met.

Nothing else in `spec.md` or `plan.md` changes. No acceptance criterion is
added, removed or weakened. Neither settled owner decision recorded in the spec
is reopened. T1 through T4 are complete and their sections stay immutable; T5's
recorded mutation table stays as written, including the green row, because the
survival is the finding.

## Evidence bindings

The amendment gate derives completed tasks from `current_wave_index` plus
`schedule_waves`, not from `completed_task_ids`. At index 3 of a five-wave
schedule that is T2, T3 and T4, plus T1 preserved from amendment 0001. Each is
bound to the verification ledger, which holds its recorded observations.
