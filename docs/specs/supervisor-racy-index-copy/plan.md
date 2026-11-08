# Plan: Supervisor racy-safe index copy

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_commit.py` (`_PrivateIndex._seed`, `_copy_index`); tests `packs/core/tests/skills/work-loop/test_supervisor_git.py` (the seeded-scan tests); evidence: a plain Git 2.56 reproduction where an index copy with a newer modification time misses a same-size rewrite that the original index and a time-preserving copy both see

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (contract, scope and non-goals, durable outputs, agent rules, testing
> strategy, acceptance criteria, accepted risk) or its `Terminal Intent`. A change
> to tasks, tests, stubs, design, or approach needs none: the controller makes it
> as an in-envelope working-plan change while no execution attempt is open, and
> the run continues with every finished task still finished. Execution
> observations belong in `docs/specs/<feature>/notes/verification-ledger.md` (or
> the adopter's equivalent). A genuine error in a protected section follows the
> controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads. `Design`, `Approach`, `Grounding` and `Risks` are working
> material the controller corrects in place, before or after approval, while no
> attempt is open. After approval, grounding for a seam or design means recorded
> as `implementation-discovered`, and each later correction, is a controller edit
> of the plan's `## Design (LLD)`, never a ledger line; a settled design decision
> that execution falsified is a plan error the owner agrees to, corrected the same
> way unless it reaches a protected section. A TDD task's `stub` fence is likewise
> written by the controller at task start, not carried in the approved plan.
> Treating working material as contract is how a review spends a round on prose
> no gate consumes — the measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

## Approach

One task: `_copy_index` returns the source index's file status, and `_seed` gives the copy that status's access and modification times before any Git command reads it. Git then treats entries written in the index's own second as racily clean, exactly as it does for the original index.

## Constraints

- ADR-0144 D2: standard library only, inside `work-loop/scripts/`.
- Every Git call goes through `_supervisor_git.py`.
- `packs/AGENTS.md`: the `.apm/` change bumps Core one patch above the merge base.

## Construction tests

**Integration tests:** none beyond T1.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Release history | T1 | Version bump | Changelog fragment |
| Verification record | Closeout | Ledger | Every AC row checked |

## Design (LLD)

### Design decisions

- **Keep the source index's times on the copy.** Git's racy-clean check compares each entry's modification time with the index file's; a copy written now would be newer than every entry. Setting the copy's times with `os.utime(..., ns=...)` from the source's `fstat`, at nanosecond precision and before the first Git command touches the copy, keeps the check identical to the original index's: Git reads the copy as racy and smudges racily clean entries when `_seed`'s `update-index` rewrites it, so the later `add -A` re-hashes them. Rejected: forcing a cold `read-tree HEAD` scan (loses the speed-up), or rehashing every entry (same).

Owned by: T1

## Tasks

### T1: The seeded scan sees a same-second, same-size rewrite

**Depends on:** none

**Tests:**
- AC-0001: `test_supervisor_git.py::test_a_same_size_rewrite_in_the_index_second_is_seen_by_the_seeded_scan` runs in the supervisor harness repository, whose tracked spec directory makes `_seed` rewrite the copy with `update-index`; it rewrites a tracked file within the index's second, waits into the next second without refreshing the real index, and asserts both scans name it; it fails without the fix.

**Done when:** `test_supervisor_git.py` and `test_supervisor_commit.py` pass under `WORK_SUPERVISOR_INTEGRATION=1` with zero skips, `make lint-ruff lint-mypy` is green, and Core is one patch above the merge base.

### T2: Close the first-round review findings

**Depends on:** T1

**Tests:**
- AC-0001: the T1 regression test still passes; the `_PrivateIndex` docstring names the index file's own modification time as trusted on the same terms as its entries.

**Done when:** `test_supervisor_git.py` and `test_supervisor_commit.py` pass under `WORK_SUPERVISOR_INTEGRATION=1` with zero skips, `make lint-ruff lint-mypy` is green, and the plan renders every section after `## Approach`.

## Rollout

- **Delivery:** one Core patch release; no setting or record changes.
- **Reversal:** reinstall the prior Core release.

## Risks

- A host whose filesystem cannot set times falls through to the existing cold-index fallback only if `os.utime` raises; the change treats that as a failed seeding.

## Changelog

- 2026-11-07: spec approved by eugenelim
- 2026-11-07: plan approved by eugenelim
