# Plan: worktree-cooperative-lease

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Why this plan exists separately from its predecessor

The lease was built once already, across five layers, and split out of
[`worktree-runtime-hygiene`](../worktree-runtime-hygiene/spec.md) under review
rather than landed. The implementation is preserved on branch
`eugenelim/worktree-hygience-c-lease-wip`; this plan rebuilds from it rather than
from nothing, and the known defects are enumerated in `workspace.toml`
`[backlog].open` under slug `worktree-cooperative-lease`.

The reason it was split is the reason this plan is shaped the way it is. Three
independent reviewers found failure modes the old criterion did not enumerate, in
a finished implementation with a green suite and 46 mutation proofs. The defect was
never in the code alone — it was that a one-sentence criterion cannot be falsified.
So each acceptance criterion in the spec now names a failure mode, and each task
below names the mutation that must redden it.

## Design (LLD)

**Two locks, two jobs, named so they cannot be confused.** A short-lived shared
*decision* lock makes read-other-role-then-publish-own indivisible. A long-lived
per-claim *ownership* lock answers liveness. The decision lock is never a claim's
own lock.

**Liveness is a held lock, positioned at byte zero.** Both the publishing and
probing paths seek to byte zero before locking. On POSIX `flock` covers the whole
open file description and position is irrelevant; on Windows `msvcrt.locking`
locks one byte at the current position, so a publisher that writes a payload then
locks holds a different byte than a prober opening at zero.

Measured on `windows-latest` by `tools/test_windows_lock_semantics.py`, which
landed ahead of this work for exactly this purpose:

```
MEASURED [win32 / os.name=nt] write-then-lock, probe at position 0
    -> NOT blocked (LOCK INVISIBLE)
```

All four cases passed, so the seek-to-zero invariant holds on Windows and
byte-range locking *can* carry liveness there. That measurement reversed the
design: the previous intent was to report `UNDETERMINABLE` on Windows —
surrendering the capability — purely because it could not be tested locally.

**Reclaim policy differs by role, and the difference is load-bearing.** Admission
roles (slot, ticket) are throughput counters: over-admitting by one costs memory
pressure, so they expire on a stated age budget. Worktree roles (activity,
exclusive) are safety interlocks: reclaiming a live one lets a mutator start under
an in-flight cleaner, so they never expire on age and their only path back is the
operator command. A previous round applied one rule to both and had to be split.

**The wrapper forwards the makefile, not the jobserver.** See the spec's
Limitations for the measurement and the three reasons.

## Tasks

Each task lands independently and leaves the repository working. Every new test
file gets its own Makefile pytest invocation.

### Task 1 — the claim primitive, positioned correctly

**Depends on:** none

Tests: `tools/test_coordination_lease.py` — atomic publish; a second publisher does
not overwrite; release removes only the caller's own claim; a `SIGKILL`ed holder's
claim is reclaimable using a real killed process; an unreadable payload is
undeterminable and counts as live; out-of-range identity, mismatched worktree and
out-of-window creation time each refused or clamped; digest keys do not collide for
`/mnt/a/b-c` versus `/mnt/a-b/c`; a symlinked store is refused; a claim path
escaping the store is refused; the decision lock serializes two real processes.

`Done when:` both the publish and probe paths seek to byte zero — asserted
structurally, because on POSIX the behaviour is identical either way and only
Windows can falsify it behaviourally.

### Task 2 — the two worktree roles and their interlock

**Depends on:** Task 1

Tests: `tools/test_worktree_lease_interlock.py` — `clean --apply` refuses while a
live `activity` claim exists and names the holder; proceeds when none exists and
holds `exclusive` across every deletion, observed during a real deletion; a dry run
publishes no claim and creates no store; a mutator with an unusable store warns and
proceeds while `clean --apply` refuses; **exactly one** participant wins a
contended tie, asserted as `== 1` so a symmetric abort fails; the atomicity of
read-then-publish asserted by observing the lock hold, not inferred from a race.

### Task 3 — admission, fairness, and the budgets

**Depends on:** Task 1

Tests: `tools/test_run_slot.py` — admission never exceeds the limit under real
contention; waiters admitted in registration order; a waiter whose ticket is
removed **re-registers** rather than waiting out its budget; an admission claim
expires on age while a worktree claim does not; invalid and below-one budget values
refused from the entry point that ships, not only the parsing helper; the clamp is
downward-only, host-independent in test, and reads a usable-memory figure with
headroom so the reference configuration is not clamped; the decision lock's budget
scales with the wait budget.

### Task 4 — the wrapper, the status and release commands, and the make wiring

**Depends on:** Task 2, Task 3

Tests: `tools/test_with_lease_cli.py` — exit-code integrity in both directions;
both claims released on every exit path; an unusable store warns and runs the
child; a live `exclusive` claim refuses with the reserved code and marker; a
missing command refused; verbatim argv with no shell; only the nesting marker
added; a nested invocation through a **real recursive make** completes rather than
deadlocking; a queued caller reports that it is queued; `lease-status` mutates
nothing, prints no absolute path, and prints the identifier `release-claim`
requires; `release-claim` refuses a live claim, has no override, and releases an
undeterminable one — the success path asserted, not only the refusals.

Wire `lock-semantics-windows` into `build-check-windows`'s `needs` in this task,
because from here something depends on it.

### Participant matrix

The previous plan claimed `bootstrap.py` published a claim and it never did, and
that plan froze at `Done` with the wrong statement in it. So every entry point is
listed with its disposition, and each participating one carries a dropped-wrapper
mutation.

| Entry point | Disposition | Mutation that must redden |
|---|---|---|
| `make test` | wrapped | remove the wrapper; the target's own guard reddens |
| `make build-check` | wrapped | remove the wrapper; also remove the `-f` forwarding, which must redden `assert-sast-chain-reachable` |
| `make sast` | wrapped | remove the wrapper; the target's own guard reddens |
| `make ci` | **not** wrapped — its recipe only prints a verdict, and `lint-ci-parity` derives 31 dispositions from its prerequisite list | add a wrapper; the parity guard reddens |
| `frontend_runtime.py gate` | publishes an `activity` claim, takes **no** slot | remove the claim; its own test reddens |
| `tools/repo/bootstrap.py` | **not** participating. It runs `npm ci --prefix` only, which is per-worktree and concurrently safe; the globally destructive `pip install -e` is a documented manual step in a Makefile comment and has no code path to lease | none — asserted by a test that `bootstrap.py` imports no lease module, so a future claim added here is a deliberate act |

### Clause-to-mutation ledger

Task 4 does not close until every clause of every AC appears in this ledger with a
named mutation and the check that catches it. Structural clauses — "exactly one
implementation", "single-homed", "positioned at byte zero" where the platform makes
position irrelevant — take goal-based source checks, because a runtime assertion
cannot falsify them. AC3's clauses take predecessor-regression mutations
(conditionalise a shipped guard, drop the pre-delete recheck, move the store, give
it a deletable suffix). AC9's takes the mutated-makefile proof. The ledger is a
deliverable, not a description: a clause with no entry is an unfinished task.

### Windows enforcement lands in Task 1

Wiring `lock-semantics-windows` into `build-check-windows`'s `needs` is **not
sufficient to gate it**: that aggregate is `if: ${{ always() }}` and its script
checks only the AgentBundle and CredBroker results, so a failing lock job would be
ignored. Task 1 therefore adds the job to `needs`, threads its result into the
aggregate's env, and extends the script's condition — and runs the real
coordination publisher and prober on Windows rather than only the synthetic
semantics fixture, since the fixture proves the platform and not the code.

### Not changing

`scan`'s JSON schema and its pinned key set; the deletion safety predicate, which
is reused rather than modified; `ci`'s recipe and prerequisite list; the port
lease's observable behaviour and its aged-reclaim policy; `docs/CONVENTIONS.md`;
`docs/product/changelog.md`, because nothing here bumps a released artifact's version and `tools/repo/**` is repository-only.

### Tempted and declined

- Forwarding the jobserver. Declined for the three reasons in the spec's
  Limitations; the decisive one is that this wrapper holds descriptors open for the
  claim locks and would risk handing a sub-make a lock instead of a token.
- Reporting `UNDETERMINABLE` on Windows. Declined because it was measured
  unnecessary; that would have surrendered a capability to cover a blind spot.
- Making the two reclaim policies consistent. Declined: the asymmetry is the
  contract, and a future round tempted to tidy it should change the criterion first.
- Reporting lease state inside `scan --json`. Declined: it bumps `SCHEMA_VERSION`
  and breaks a pinned key set for diagnostics `lease-status` already provides.
