# Mutation proofs

`plan.md` freezes at approval, so observations recorded after it go here. Each
row is an observed red: the engine was mutated, the suite run, and the failing
case names recorded from the run's own output. The harness restores the engine
from a byte-compared copy afterwards and the restore is asserted, so no mutation
can leak into the delivered file.

Suite: `tests/roster/test_cooling_brief_child_scope_closure.py`. The M1-M5 run
below covered **15** cases at base `6996a9840`, all green unmutated. The suite
has grown since and the table is not a claim about the cases added after it:
`test_the_shipped_command_emits_the_finding` was added by T4, and the AC9, AC10
and membership-form cases were added after review. Those four are covered by the
M6-M9 run recorded below rather than by M1-M5.

| Mutation | Killed by | What it proves |
| --- | --- | --- |
| **M1** — the absent-key branch stops naming the entry | 6 cases: *absent parent is named*, *refuses a brief dependency*, *read from the entry not the body*, *the answer is per entry*, *does not refuse a non-brief dependency*, *a cooled brief is satisfied ahead of the refusal* | The undeclared case — the whole point of the delivery — is load-bearing in six independent places, not one. |
| **M2** — the unresolvable-value branch stops naming the entry | 1 case: *a declared parent resolving to no membership is unestablished* | That criterion is the only guard on the second unknown cause. Losing it is silent everywhere else, which is why the case exists. |
| **M3** — the refusal disjunct is dropped, so the finding is raised but nothing fails closed | 2 cases: *refuses a brief dependency*, *a cooled brief is satisfied ahead of the refusal* | The finding and the refusal are pinned **independently**. *An absent parent is named* stays green under this mutation, which is correct: a run that reports the problem without acting on it is exactly the half-fix this separation detects. |
| **M4** — the finding is raised at the brief's path instead of the entry's | 4 cases: *absent parent is named*, *resolving to no membership*, *read from the entry not the body*, *the answer is per entry* | The `path` is a contract, not a detail. A maintainer must be sent to the entry they can edit, not to the brief they cannot. |
| **M5** — a declared empty value is treated as unknown | 3 cases: *a declared empty parent marks nothing*, *the answer is per entry*, *refuses a brief dependency* | This mutation **is** the withdrawn conservative repair, which refused every brief dependency whenever any parentless spec cooled. That *A declared empty parent marks nothing* dies here is the proof that the escape hatch is real: without it this delivery would be the design ADR-0110 rejected. |

## What no mutation could kill

None. Every mutation attempted was killed by at least one case, and each was
killed by the criterion that owns it rather than by an unrelated case failing
for a side reason.

## The one asymmetry worth naming

M3 leaves *An absent parent on a cooled entry is named* green. That is by
design, and it is the reason the spec states the finding and the refusal as two
criteria rather than one: a single criterion asserting "it is named and refused"
would have passed a mutant that names without refusing in the half of the
observation it checked first.

## M6-M9 — the post-review run, at base `02742751a`

Three independent reviews found `brief_membership_paths` wrong in three
directions at once. The predicate is now kind-based and collection-agnostic over
canonical and legacy memberships together. These four mutations test that fix
and the two criteria that previously had no case at all.

Suite at this run: 19 cases, green unmutated.

| Mutation | Killed by | What it proves |
| --- | --- | --- |
| **M6** — revert to the collection-based predicate, the shipped defect | 1 case: *a brief registered in any membership form resolves* | The fix has a criterion that can fail. Before this case existed, reverting the predicate was undetectable by the suite. |
| **M7** — keep the kind filter but drop legacy memberships, the partial fix | 1 case: the same | The legacy half is independently pinned, so a later simplification that drops it cannot pass. |
| **M8** — suppress the brief's own violation repository-wide | 15 cases, including *unestablished scope reports itself and suppresses nothing* | The suppression rail this delivery deliberately did **not** touch. AC9 had no case before review, so this mutation was previously invisible; it is the exact mutation the withdrawn design would have shipped. |
| **M9** — attribution stops suppressing | 2 cases: *an attributed cooled child still suppresses its parent's violation* and AC9's | AC10 now has a criterion. The shipped behaviour this delivery inherits is pinned rather than assumed. |

The engine was restored from a byte-compared copy after each mutation and the
restore was asserted, as in the M1-M5 run.

**What the two runs together say about the first one.** M1-M5 all passed and all
were killed, and the delivery still shipped three fail-open and fail-closed
defects in the same predicate. Every M1-M5 fixture varied the *child's*
declaration; none varied what was registered in a brief queue, and none
registered a brief in `[backlog].open` or as a legacy string. A mutation run
only reaches the axes its fixtures vary, so a clean sweep bounds nothing outside
them — which is why three reviewers each found a different direction of the same
error that five killed mutations had not.
