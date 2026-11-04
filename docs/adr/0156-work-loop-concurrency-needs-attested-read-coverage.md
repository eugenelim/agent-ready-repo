# ADR-0156: Work-loop concurrency is admitted only on attested read coverage, and otherwise runs sequentially

- **Status:** Accepted
- **Date:** 2026-11-04
- **Areas:** work-loop, concurrency, security
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** ADR-0005 D3,D4; ADR-0061 D5; ADR-0144 D9; ADR-0154 D2
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0015; ADR-0005 D2,D5,D6,D7; ADR-0151; brief `acceptance-centered-work-loop` Slice 7; `docs/architecture/work-loop-result-integration.md`; `docs/architecture/runtime-security-primitives.md`

## Decision summary

- **Decision:** The execution supervisor may run `implement-task` attempts at the same time only when a host attestation it verifies itself proves each attempt's isolation and product reads, either by enforcing a read allowlist or by tracing every read. Admitted results then integrate one at a time, in the order the sequential floor would have issued them, through a pinned three-way apply onto the protected product ref. Everything else runs on the sequential floor.
- **Because:** two tasks that write different files can still break each other when one reads what the other writes. Only a proven read set shows that. Declared write sets, file disjointness, and safe categories cannot.
- **Applies to:** full-mode `code` runs of `work-loop`, and only their `implement-task` attempts for tasks with no stub fence. Not light mode, and not any other request kind.
- **Tradeoff accepted:** no shipped host can attest isolation or reads today, so every adopter keeps running sequentially until a verified containment adapter exists. The scheduler, admission, and integration code ship and are proven against a test-only attesting provider that cannot be selected outside the test corpus.
- **Revisit if:** a supported host can attest write confinement but not reads, and measured runs show read-free interference is rare enough to admit a weaker mode; or the permutation corpus finds a schedule whose product tree or verdict differs from the sequential one.

## Context

Full-mode `work-loop` issues one request at a time. The execution supervisor
owns that procedure (ADR-0144), and its result is a protected Git ref that only
it moves by compare-and-swap (ADR-0154). Four accepted decisions hold dispatch
sequential, and this record supersedes one clause of each:

- ADR-0061 D5 defers `doc` mode and parallel-wave orchestration. Only the
  parallel-orchestration clause is superseded. The `doc`-mode deferral stands.
- ADR-0005 D3 admits a parallel write only for a measured safe category
  (*cannot-collide*, *typed Group B*, *textual-loud*), and D4 adds a post-write
  `git merge-tree` file-disjointness check. Both are superseded. ADR-0005 D1,
  D2 (opt-in), D5 (parallel reads), D6 (merge-abort backstop), and D7 (worktree
  write isolation) stand.
- ADR-0144 D9 keeps ADR-0005's parallel-write gating as it is. Only that clause
  is superseded; its light-mode clause stands, and ADR-0154 already superseded
  its worktree clause.
- ADR-0154 D2 integrates a result only while the ref names its request's
  source commit, with no three-tree apply. Both clauses are superseded, and only
  for admitted concurrent results, which may land after the ref has moved and
  through an apply. Both still stand for every sequential result and every
  result without complete read proof. ADR-0154's *Revisit if* named this case.

ADR-0005's gate looks only at what tasks write. RFC-0015 showed what it misses:
two tasks editing different files can make incompatible implicit choices that
pass a textual merge and each task's own gates. A task reading a file its
sibling changes is that case. File disjointness cannot see it, and a safe
category is a judgment about a task, not a check of what it did.

Slice 7 of the acceptance-centred work-loop brief asks for concurrency that is
provider-neutral, admitted only with enforced read allowlisting or complete
tracing, and otherwise degrades to the sequential floor. Its exit proof is that
missing governance or read coverage serializes, undeclared reads are denied or
expand the attested set, and every schedule permutation yields the sequential
product tree and verdict with Pi absent.

Constraints:

- **Two attestation contracts already exist.** `containment-attestation.v1` is
  the launcher's guarantee about the mechanism. `access-attestation.v1` is the
  per-result record of reads. Only verified read coverage may support a
  complete access attestation (runtime security primitives § 4).
- **No host attests today.** Implementation workers are host subagents the
  supervisor's controls never contain. It records and enforces neither write
  roots nor network denial, and detects naive writes after the fact (runtime
  security primitives § 11).
- **Shared Git state.** Linked worktrees share one common directory: objects,
  every shared ref, config, worktree admin folders, and the supervisor's run
  store. Only `HEAD`, `refs/worktree/`, and `refs/bisect/` are per worktree.
- **Git floor.** A three-way apply that writes a tree without a checkout needs
  `git merge-tree --write-tree`, Git 2.38. The supervisor's floor is 2.32.
- **Merge-time code.** The hardened Git helper does not neutralize
  `merge.<name>.driver`, and attributes such as `merge=union` can turn a
  conflict into a clean merge.
- **Portability.** Core imports no runtime-specific adapter, and Pi stays an
  optional external consumer.

## Decision

> The supervisor admits concurrent implementation attempts only when an
> attestation it verifies proves each one's isolation and reads, and their read
> and write sets do not interfere. Results land one at a time in sequential
> order. Otherwise the work runs one task after another.

- **D1:** Exactly three execution modes exist. `sequential` is the floor and is available on every host. `enforced-allowlist` needs a host that denies every read outside the attempt's declared read set. `complete-trace` needs a host that records every read. Both concurrent modes also need the host to confine the attempt's writes to a fresh, never-reused tree of its own; to deny it the Git common directory, every shared ref, the run store, `delivery/`, and every sibling's tree; to deny all network access; and to deny inter-process channels between siblings. An attestation that does not cover all of this is incomplete. No other signal admits concurrency: not `Depends on:`, not `Touches:`, not a declared write set, not a task category, and not a model's judgment.
- **D2:** Admission fails closed to the floor. A task's attempt runs concurrently only when all of these hold: the run's pinned policy opts in (ADR-0005 D2 stands); the task declares both a read set and a write set; it has no stub fence; its dependencies are complete; its reprojection bound (D6) is not spent; Git is at least 2.38; and a verified `containment-attestation.v1` (D3) covers it before it runs any repository code. If any one is missing, the attempt waits and runs sequentially: it is issued only while no other attempt is open, and no attempt opens while it runs. A finished result waiting for its turn (D5) is not an open attempt, so an earlier floor task can still run, and the held result is then checked under D4 against that task's changes. A missing condition never refuses the run and never weakens a guarantee. The concurrent path ships only in a release made after this record is accepted.
- **D3:** The supervisor verifies every attestation itself, never by trusting a value carried through `report` or any channel a worker can write. The trust root is a launcher identity the owner approves and the run pins at `start`. Each attestation is bound to the run, the attempt, its issued grant, and a fresh nonce, and each result's `access-attestation.v1` is bound by fingerprint to its `execution-result.v1`. A copied, replayed, foreign, or broader attestation is unverifiable. The test-only attesting provider cannot be selected or installed outside the test corpus. An unverifiable attestation sends the task to the sequential floor.
- **D4:** A read includes a lookup of a path that does not exist and a listing of a directory. A write includes a deletion, both ends of a rename, and a mode or type change. A lookup of a missing path meets a write that creates it. A listing of a directory meets a write that adds, removes, or renames an entry directly in it. A recursive walk or a glob meets any write under its root. Any other read meets a write to the same path. At admission, two tasks may overlap only when neither one's declared read set or write set meets the other's declared write set. At integration, a result's attested read and write sets are checked against every path changed on the product ref between the result's source commit and the observed tip. In `enforced-allowlist` an undeclared read is denied. In `complete-trace` it joins the attested read set before the check. A meeting refuses the result. A result without a complete, verified access attestation integrates only on exact source equality (ADR-0154 D2).
- **D5:** Results integrate one at a time under one cross-process integration lock, in the order the sequential floor would have issued their tasks; a finished later result waits for earlier ones. Under the lock the supervisor reads the tip once and uses that read for the attempt's authority, the D4 check, the apply, the compare-and-swap's expected value, and the run-store write. The apply runs only through the hardened Git helper with a pinned algorithm (`git merge-tree --write-tree`, default strategy, no strategy options). Attributes come from a pinned source no attempt controls, any non-default merge attribute refuses, and `start` refuses a repository that configures a merge driver. An apply that changes a path outside the result's write set refuses. A content conflict, stale authority, or lost compare-and-swap leaves the ref unchanged, records `integration-conflict.v1` under the integration-diagnostic content profile with product paths only and no file contents, and reprojects the task from the new tip. That conflict is ADR-0005 D6's backstop.
- **D6:** Each concurrent attempt has its own manifest and residue record over its own tree and the shared control state, and no open attempt relaxes another's trusted-file, control-state, or `delivery/` checks. Controller replans and stub-fence revisions still wait until no attempt is open (ADR-0151). A failure has task blast radius: a refused, conflicting, or failed attempt reprojects only itself and any running sibling whose sets meet its own. Cancelling an attempt ends its attested process tree and confirms the end before the task reprojects onto a fresh tree; an unconfirmed end sends the task to the floor. A cancelled attempt's result is never admitted. Each task has a reprojection bound, after which it runs sequentially, and every reprojection is journaled and shown by `status`.
- **D7:** Given the same attempt outputs, every admitted schedule gives the same product tree and the same acceptance verdict as the sequential order. Evidence, gates, and reviews read only integrated trees. This record admits concurrency for no other request kind, and leaves read concurrency to ADR-0005 D5. Admission reads the attestation contracts and the pinned launcher identity, never which runtime is in use. Core ships no attesting adapter, and every proof of this record runs with Pi absent.

## Decision drivers

- A concurrent result must equal the sequential one.
- A missing proof costs throughput, never correctness.
- Admission is mechanical and provider-neutral.
- No value a worker can write is trusted as proof.
- The record reuses the shipped product ref and attestation contracts rather
  than adding a second integration point.

## Consequences

**Positive:**
- The silent interference ADR-0005 accepted inside its safe categories is
  closed: a read of a sibling's write is proven absent, or the work serializes.
- Admission no longer depends on a task category a human or model assigns.
- Sequential results keep ADR-0154's exact-source rule unchanged.

**Negative:**
- No host ships a verified attestation today, so every adopter keeps the
  sequential floor. The concurrent path is proven only against a test-only
  attesting provider until a containment adapter exists.
- The concurrent path raises its Git floor to 2.38; older Git runs sequentially.
- A plan must declare read and write sets for anything to run concurrently, and
  an under-declared read costs a denied attempt.
- TDD tasks with a stub fence always run sequentially.
- Holding finished results for sequential order gives up some of the speed-up.
- A permutation corpus, a three-way apply, per-attempt manifests, and sibling
  cancellation are new supervisor code to build and maintain.

**Revisit if:** a supported host can attest write confinement but not reads, and measured runs show read-free interference is rare enough to admit a weaker mode; or the permutation corpus finds a schedule whose product tree or verdict differs from the sequential one.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:** the Slice 7 corpus in `packs/core/tests/skills/work-loop/` shows that a run missing any D2 condition dispatches nothing concurrently; that a forged, replayed, or foreign attestation serializes; that an undeclared read is denied or joins the attested set; that a read-after-write, a same-line conflict, and a merge-driver or attribute attempt leave the ref unchanged; and that every permutation of an admitted schedule equals the sequential product tree and verdict. Every case runs with Pi absent.
- **Owner:** Core pack and `agentbundle` maintainers, with security maintainers for D3

## Alternatives considered

- **Keep ADR-0005's safe categories and disjointness gate:** rejected against "a concurrent result must equal the sequential one". The gate sees writes only, so a read of a sibling's write passes it.
- **Admit concurrency from declared write sets or `Touches:`:** rejected against the same driver. RFC-0015 found about 45% file overlap among 55 declared-independent waves, as a lower bound, and tasks under-name what they touch.
- **Integrate in completion order:** rejected against the same driver. When a later task finishes first and reads an earlier task's write, the integrated tree is not the sequential one and cannot be undone.
- **Trust an attestation returned with the result:** rejected against "no value a worker can write is trusted as proof".
- **Stay sequential and keep ADR-0061 D5:** rejected against "admission is mechanical and provider-neutral". It leaves no route to concurrency when a host can prove isolation.
- **Let each host's runtime decide:** rejected against the same driver. Results and merge behaviour would vary by runtime.
- **Refuse the run when proof is missing:** rejected against "a missing proof costs throughput, never correctness". The sequential floor is always correct, so refusing only adds a stop.

## References

- RFC-0015 (the experiments behind ADR-0005, and the overlap measure).
- Bernstein, *Analysis of Programs for Parallel Processing*, IEEE Trans.
  Electronic Computers, 1966 (the read and write set conditions D4 applies).
- `docs/architecture/work-loop-result-integration.md` §§ 2–8 (the planned
  integration design this record makes admissible).
