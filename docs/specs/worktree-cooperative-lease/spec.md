# Spec: worktree-cooperative-lease

- **Status:** Draft
- **Owner:** repository maintainers
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Contract:** none <!-- no REST/event/RPC surface; the claim-file layout is coordination state held in code and tests, not a published interface -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Two commands operating on one worktree at the same time do not corrupt each
other's work, and one machine does not exhaust itself running more heavy builds
than it can hold. A maintainer running `clean --apply` while a peer's test suite
is mid-flight sees a refusal naming the holder rather than a deleted `node_modules`;
a maintainer whose gate is queued behind two others sees that it is queued rather
than a silent hang. Coordination is cooperative: a command that never participates
keeps working exactly as it does today.

This is the criterion deferred out of [`worktree-runtime-hygiene`](../worktree-runtime-hygiene/spec.md)
AC6 after it was built and then split under review. That spec's AC6 stated the
outcome in one sentence; three independent reviewers found failure modes it did
not enumerate, in a finished implementation with a green suite. The lesson shapes
this document: **every failure mode below is an acceptance criterion, not an
implementation note**, because a criterion that omits a failure mode cannot be
falsified by any test.

## Boundaries

### Always do

- Read the other role's claims and publish your own inside one indivisible step;
  a read taken outside that step is not a decision.
- Treat a claim payload as untrusted input, and treat liveness that cannot be
  determined as live.
- Give a refusal a reserved exit code, a greppable marker, and wording that says
  the command did not run.
- Seek a claim file to byte zero before locking or probing it, on every platform.

### Ask first

- Changing the default concurrency limit, the wait budget, or any age budget.
- Adding a claim role, or leasing a command not already named here.
- Making any lease failure able to fail a CI job.

### Never do

- Let a destructive command proceed on evidence it failed to obtain.
- Infer liveness, activity, busyness, or abandonment from anything other than a
  held lock; attachment is never liveness.
- Delete, or make deletable, the coordination state the lease depends on.
- Condition any behaviour on a CI environment variable.
- Wrap an aggregate make target whose recipe only prints a verdict, or change
  `ci`'s prerequisite list.

## Acceptance Criteria

- [ ] **AC1 — a claim's liveness is a held lock, observable on every supported
  platform.** A claim is live when its owner still holds the advisory lock it took
  for that claim's lifetime. Liveness is therefore an observation about a lock the
  operating system releases on the owner's death, never an inference from a
  recorded process identity, so a recycled identity cannot impersonate an owner
  and a killed run's claim is reclaimable at once. The recorded identity exists
  only to name a holder in a refusal.

  Both the publishing path and the probing path position the claim file at byte
  zero before locking. This is measured, not assumed: on Windows
  `msvcrt.locking` locks one byte at the current file position, so a publisher
  that writes a payload and then locks holds a different byte than a prober that
  opens at zero — and `tools/test_windows_lock_semantics.py` records on
  `windows-latest` that such a lock is **not** observable
  (`write-then-lock, probe at position 0 -> NOT blocked (LOCK INVISIBLE)`), while
  seeking both sides to byte zero makes it observable. An unobservable held lock
  is not a degradation: it makes every probe read not-live, so a live peer's claim
  is reclaimed and cleanup deletes under a running mutator. That job is wired into
  the Windows aggregate's required set by the change that satisfies this criterion,
  because something now depends on it.

- [ ] **AC2 — cleanup and mutating runs interlock, atomically.** A worktree carries
  an `activity` role held by mutating build and test entry points and an
  `exclusive` role held by `clean --apply`. Each participant's read of the other
  role and the publication of its own claim occur inside one uninterrupted hold of
  one shared decision lock; a scan taken outside that hold is not a decision, so
  two participants cannot each observe the other's absence and both proceed.
  `clean --apply` publishes `exclusive` before its first deletion, refuses
  immediately while any live `activity` claim exists, and holds the claim across
  every deletion. `clean` without `--apply` mutates nothing, publishes no claim,
  and does not create the store. When both roles contend at once **`activity` wins
  and `exclusive` retries**: a queued build is holding a person's attention, while
  cleanup is deferrable and can be re-run at no cost. A symmetric abort where
  neither proceeds is a defect, not an acceptable outcome, and a test asserts which
  participant won rather than that exactly one did.

- [ ] **AC3 — the deletion safety proof is unchanged and unconditional.** The
  per-candidate predicate of `worktree-runtime-hygiene` AC5, and its re-assertion
  immediately before each deletion, are untouched. No check becomes conditional on
  holding a claim. The claim narrows the concurrent-mutation window; it does not
  replace the proof. The store lives under the Git common directory and its files
  carry a suffix the deletion predicate already refuses, so no cleanup run can
  delete the coordination state it depends on.

- [ ] **AC4 — claim payloads are untrusted, and no claim is unreleasable.** An
  out-of-range identity, a recorded worktree disagreeing with the claim's own
  location, and a creation time outside the file's own creation window are each
  refused or clamped rather than trusted. The scheduler orders waiters by a value a
  writer cannot forge downward, so a backdated claim cannot become permanently the
  oldest waiter.

  Liveness that cannot be determined counts as live, because that is the safe
  answer for a destructive caller. It is reached without an adversary: the module's
  own bound is that advisory locks are undependable on a network mount, and an
  unreadable claim file — another user's, or one left `000` — answers the same way.
  Because that answer is *permanent*, every role needs a documented path back, and
  **the paths differ by role for a reason that must not be tidied away**:

  An **admission** claim is a throughput counter. Reclaiming one from a still-live
  owner over-admits by one run: more memory pressure, self-correcting, recoverable.
  So an admission role expires against a stated budget that no legitimate holder
  outlives, and a wedged slot or ticket cannot block every gate indefinitely.

  A **worktree** claim is a safety interlock. Reclaiming an `exclusive` claim from a
  still-live owner lets a mutator start while a cleaner is deleting, which is
  corruption and is not recoverable. So the worktree roles never expire on age, and
  their only path back is the explicit operator command.

  That asymmetry is deliberate. A previous round applied one rule to both and had
  to be split; a future round tempted to make them consistent should change this
  criterion first, not the code.

  **The recovery model is stated per observable state, because two earlier
  formulations of it were false.** Claiming "no claim is unreleasable" and "the only
  path back is the operator command" cannot both hold: a hung but observably-live
  holder is refused by that command, and its actual recovery is external. There are
  four states and they do not share an answer:

  | Claim state | Recovery |
  |---|---|
  | Absent, or lock observably free | Reclaimed automatically; no operator action |
  | Undeterminable (unreadable file, unmapped lock errno, network mount) | The operator command releases it — and this **is** an override, because the claim may in fact be live. It is offered because the alternative is a permanent wedge, and it is the operator accepting a risk the tool cannot evaluate |
  | Observably live, holder hung | **No tool-side recovery.** The command refuses it, correctly. Recovery is terminating the named holder and re-probing. The refusal names the holder so that is actionable |
  | Live, holder healthy | Not a fault. Wait, or use the status command to see who holds it |

  So the honest contract is narrower than "no claim is unreleasable": every claim has
  a documented path back, but for one state that path leaves the tool, and for
  another it requires the operator to accept a risk. The command states which case
  it is in rather than implying the release was safe.

  Releasing a waiter's ticket must not strand it: AC5's re-registration retains the
  waiter's original queue position, which is what makes this escape hatch safe.
  Neither clause is complete without the other, and both name the coupling.

- [ ] **AC5 — heavy runs are admitted against a common-directory-wide limit, and a
  waiter is not overtaken.** At most a configured number of heavy build and test
  runs are admitted at once across every worktree sharing one Git common
  directory. Admission prunes, counts and publishes inside one hold of the shared
  decision lock. A waiter registers once and is admitted in registration order,
  and its ticket scan shares the lock hold with its own claim, so two waiters
  cannot each observe no older ticket and both admit. A waiter whose registration
  is lost re-registers **retaining its original position**, so an operator removing
  a ticket (AC4) cannot send that waiter to the back of the queue repeatedly and
  starve it.

  The limit is **soft across an admission expiry, and that is stated rather than
  implied**: when AC4's age budget reclaims a slot whose owner may still be live,
  the live count can briefly exceed the configured limit by the number of expired
  slots. That is the accepted cost of not wedging every gate forever, and it is
  bounded — over-admission costs memory pressure, which is recoverable, where a
  permanent wedge is not. A criterion promising a hard cap and an expiry policy at
  once would be unsatisfiable.
  The limit is common-directory-wide, not machine-wide: a second clone is a second
  scope, processes outside these worktrees hold no claim, and no output may imply
  that the machine is governed.

- [ ] **AC6 — the budgets are strict, single-homed, and calibrated to a
  measurement.** The concurrency limit and the wait budget each parse as whole
  numbers, reject values below one, and refuse invalid input rather than falling
  back to a default, so a malformed value cannot silently disable the limiter —
  and that refusal is reachable from the entry point that ships, not only from the
  parsing helper. A refusal is the operator's-error path and is distinct from the
  store-unavailable path; the two are never caught by one handler.

  The values are named here, not left to the implementation, because the previous
  round's calibration defect is reachable by redefining an unnamed term:

  | Quantity | Value | Why |
  |---|---|---|
  | Default concurrency limit | **2** | Memory-bound, not core-derived: a unit suite measured 178.9 s wall against 56.4 s CPU, so a run is mostly waiting and cores are the wrong denominator. On the 10-core 32 GiB reference host `cpu_count() // 2` gives 5, which is the concurrency that exhausted swap at load 135 |
  | Wait budget | **5400 s** | Sized by queue depth times hold time over the limit, not by one run: at limit 2 with five waiters and 25-minute holds the last waiter needs 50-75 minutes |
  | Memory per concurrent run | **12 GiB** | The reference host is 32 GiB and judged safe at 2. A divisor of 16 GiB left **no headroom** and, because the platform reports *usable* rather than nominal pages, clamped that very host to 1 — the defect this row exists to prevent. 12 GiB leaves the reference configuration at 2 and still clamps a 16 GiB machine to 1 |
  | Admission claim age budget | **6 h** | Above any legitimate run; a full suite is 15-25 minutes |
  | Decision-lock acquisition budget | **at least one twentieth of the wait budget, and never below 30 s** | A proportional budget alone still conforms while being uselessly small, so a floor is stated too |

  The clamp reads the usable-memory figure, applies only to the default, and never
  raises it. An explicit override is the operator's decision about their own
  hardware and is never clamped away. A platform whose memory cannot be measured is
  left unclamped rather than guessed at.

  The decision lock's own acquisition budget scales with the wait budget rather
  than being a fixed second, because it is otherwise the first thing to exhaust
  under exactly the contention the limiter exists to bound — and exhausting it
  must never degrade the limiter to a no-op.

- [ ] **AC7 — one wrapper, one child runner, and a refusal no caller can mistake
  for a verdict.** A wrapper command holds the worktree `activity` claim and one
  admission slot for exactly one child's lifetime, releasing both on normal exit,
  non-zero exit, interrupt and spawn failure, and forwarding termination signals to
  the child's process group. It uses the single child runner already shipped rather
  than a second copy, spawns from a verbatim argument vector with no shell and no
  interpolation, refuses an empty command, and adds only the nesting marker to the
  child's environment. Neither publishing nor releasing a claim can alter the
  child's exit code, in either direction: a failing release cannot redden a passing
  child, and a succeeding release cannot mask a failing one.

  Every refusal — mutator, cleanup, wrapper and gate alike — exits **75**
  (`EX_TEMPFAIL`), prints the literal marker `WORKTREE_LEASE_DID_NOT_RUN` alone on
  its own line, and says the command did not run. Both values are stated here so a
  test can assert the literals from this contract rather than by reading the
  implementation's own constant, which is the tautology that left the previous
  round's marker with no guard at all.

  **75 is not, and cannot be, a code no child returns.** The wrapper runs a verbatim
  argument vector, so a child may return any code including 75; a criterion
  promising otherwise is unsatisfiable. The marker is therefore the authoritative
  discriminator and the exit code is a convenience for callers that cannot read
  stderr. A caller distinguishing contention from a gate verdict greps the marker;
  one that sees 75 without the marker is looking at a child's own status.

  A refusal names process ids and worktree base names only, never a payload or an
  absolute path. A queued caller reports
  that it is queued and behind whom, rather than waiting in silence, because a long
  queue and a deadlock are otherwise indistinguishable from outside. A status
  command reports claims and occupancy, mutates nothing, and prints the identifier
  the release command requires.

- [ ] **AC8 — nesting is identity-bearing, and cannot be forged or leaked.** An
  acquisition nested inside an already admitted run is a no-op, and so is its
  release, so an inner run cannot hand back a slot it never took. Nesting is
  recognised only when the inherited marker names a claim still live in the same
  scope; a marker naming no live claim counts as absent, so a stale export or a
  crashed run's leftover cannot silently disable the limiter. The marker is not
  echoed where it becomes a bypass anyone can copy. The receipt states when a run
  is nested and whose claim it inherited, so an inert limiter is visible.

- [ ] **AC9 — the lease cannot fail a CI job, and the make wiring survives it.**
  An unusable store, an unresolvable worktree, or a platform that cannot lease
  warns and runs the child; only genuine contention refuses, and only
  `clean --apply` fails closed, because only it deletes.

  A recursive make invocation introduced by the wrapper forwards the makefile
  currently in use, so a self-test that proves its own guard by running a *mutated*
  copy still executes the mutation. Without that forwarding the sub-make re-reads
  the real makefile and such a guard silently stops proving anything while still
  reporting success.

  It does **not** forward the jobserver; see Limitations. Every existing guard that
  reads a wrapped target's recipe keeps working, and each wrapped target is itself
  guarded, so a dropped wrapper reddens something.

## Limitations

A wrapped make target loses the jobserver, so `make -j` prints
`warning: jobserver unavailable: using -j1` and runs serially. This is a stated
limitation rather than a defect to fix, and the reasoning is recorded because the
obvious fix is worse than the symptom.

Measured on macOS with GNU Make 3.81: a direct `$(MAKE)` reports
`MAKEFLAGS=[ --jobserver-fds=3,4 -j]` with those descriptors open, while the same
invocation through the wrapper reports `MAKEFLAGS=[]` with none. `MAKEFLAGS`
propagates through the environment; the **descriptors** do not. Make's own
suggested remedy — prefixing the recipe line with `+` — was tried and does not
help: it marks the line recursive for `-n` purposes without restoring descriptors.
Explicit `pass_fds` forwarding does work.

It is not adopted for three reasons. The jobserver is three different mechanisms —
inherited descriptors on make 3.81 through 4.3, a named pipe on 4.4 and later, a
named semaphore on Windows where `pass_fds` is unsupported — so forwarding means
version-sniffing a format that has already changed twice. Its failure mode is a
build that **hangs** rather than warns, because a token not returned to the pipe
leaves make waiting forever, nondeterministically and under load. And this wrapper
is the process most likely to get it wrong: its whole purpose is to hold
descriptors open for the claim locks, so forwarding numeric descriptors risks
handing a sub-make a claim lock instead of the jobserver.

No workflow passes `-j`, so nothing in CI is affected. A caller who needs
parallelism should invoke the unwrapped target directly rather than have the
wrapper forward a mechanism it cannot forward safely.

## Testing Strategy

Real processes, real locks, real filesystems. The prior round's dominant failure
was guards that were written correctly and could not fail — six of them, none
visible in a green suite — so every criterion here names what mutation must
redden it, and no mutation proof is accepted without observing the baseline green
first.

Four rules follow from specific defects that reached review last time.

Never mock the call a branch dispatches on. Every disposition test in the prior
round patched `os.killpg`, which is how a real defect reached a green suite; kernel
and filesystem behaviour must be exercised unmocked at least once per claim.

Never assert against the constant the code emitted. That comparison is a tautology:
mutating the constant changes both sides and the test still passes, which is how a
required refusal marker ended up with no guard at all.

A test whose name claims concurrency, atomicity or ordering has two participants
and a deterministically widened window. A single-actor body is a sequential test
whatever it is called, and one such test passed with its mutual-exclusion lock
removed entirely. Where a third mechanism serialises the participants, assert the
property directly rather than inferring it from a race outcome.

Budgets for real process startup are generous and single-homed. A two-second wait
produced a failure that read exactly like a logic defect on a host that has run at
load 160.

Windows behaviour is verified on the `windows-latest` runner, not reasoned about.
Anything that cannot be verified there is stated as unverified rather than
asserted.

## Assumptions

1. All linked worktrees of one checkout share one Git common directory, which is
   therefore the coordination scope. A second clone is a second scope.
2. Advisory locks are dependable on a local filesystem. A common directory on a
   network mount is outside what this mechanism promises, and a claim whose lock
   cannot be evaluated is treated as live rather than guessed at.
3. The platform reports a physical-memory figure through a documented interface, or
   reports none; where it reports none the clamp does not apply.
