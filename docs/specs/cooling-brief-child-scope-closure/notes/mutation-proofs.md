# Mutation proofs

`plan.md` freezes at approval, so observations recorded after it go here. Each
row is an observed red: the engine was mutated, the suite run, and the failing
case names recorded from the run's own output. The harness restores the engine
from a byte-compared copy afterwards and the restore is asserted, so no mutation
can leak into the delivered file.

Suite: `tests/roster/test_cooling_brief_child_scope_closure.py`, 15 cases,
green unmutated. Run at base `6996a9840`.

| Mutation | Killed by | What it proves |
| --- | --- | --- |
| **M1** — the absent-key branch stops naming the entry | 6 cases: *absent parent is named*, *refuses a brief dependency*, *read from the entry not the body*, *the answer is per entry*, *does not refuse a non-brief dependency*, *a cooled brief is satisfied ahead of the refusal* | The undeclared case — the whole point of the delivery — is load-bearing in six independent places, not one. |
| **M2** — the unresolvable-value branch stops naming the entry | 1 case: *a declared parent resolving to no membership is unestablished* | That criterion is the only guard on the second unknown cause. Losing it is silent everywhere else, which is why the case exists. |
| **M3** — the refusal disjunct is dropped, so the finding is raised but nothing fails closed | 2 cases: *refuses a brief dependency*, *a cooled brief is satisfied ahead of the refusal* | The finding and the refusal are pinned **independently**. *An absent parent is named* stays green under this mutation, which is correct: a run that reports the problem without acting on it is exactly the half-fix this separation detects. |
| **M4** — the finding is raised at the brief's path instead of the entry's | 4 cases: *absent parent is named*, *resolving to no membership*, *read from the entry not the body*, *the answer is per entry* | The `path` is a contract, not a detail. A maintainer must be sent to the entry they can edit, not to the brief they cannot. |
| **M5** — a declared empty value is treated as unknown | 3 cases: *a declared empty parent marks nothing*, *the answer is per entry*, *refuses a brief dependency* | This mutation **is** the withdrawn conservative repair, which refused every brief dependency whenever any parentless spec cooled. That *A declared empty parent marks nothing* dies here is the proof that the escape hatch is real: without it this delivery would be the design ADR-0106 rejected. |

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
