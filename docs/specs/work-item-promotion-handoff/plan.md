# Plan: Hand a captured item to its owner or close it, and record which

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `docs/specs/work-item-capture/spec.md` § D6 and § D10 — the stored-command rules, the stored-path set, and the merge-path disclosure this plan consumes; `packs/core/.apm/skills/work-intake/SKILL.md` § 4–5 — the classify table and the intake transaction the drain calls; `packs/core/.apm/skills/project-knowledge/scripts/knowledge_store.py` — the store API: partitions, event validation, the terminal-disposition writer and its identical-disposition no-op; `tests/roster/test_project_knowledge_capture_contract.py` — the repository-level test anchor pattern. Deviation: none.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (contract, scope and non-goals, durable outputs, agent rules,
> testing strategy, acceptance criteria, accepted risk) or its `Terminal
> Intent`. A change to tasks, tests, stubs, design, or approach needs none.
> Execution observations belong in
> `docs/specs/work-item-promotion-handoff/notes/verification-ledger.md`.

## Approach

One new module beside the store owns the executable half of the drain:
`packs/core/.apm/skills/project-knowledge/scripts/promotion_drain.py` — an
open-capture reader, the read-path prose re-run, the execution envelope, and
the per-item decision function, co-located with the store API and the capture
validator it re-uses. The work-intake skill gains the operator-facing
procedure that confirms, transacts, and commits dispositions. Tests drive the
module's seams directly under `tests/roster/`; the end-to-end drain is
verified over a fixture store, and one run over the real store is the smoke.
The riskiest part is the execution envelope — the only subprocess boundary in
the capability — so it lands first and alone.

## Constraints

- `docs/specs/work-item-capture/spec.md` § D6 — the stored-path set, the argv
  rules, and the case table the re-check drives against. Never re-implemented
  here; the re-check calls the write path's own validator.
- `docs/specs/work-item-capture/spec.md` § D10 — the merge-path disclosure the
  read-path prose re-run answers.
- [RFC-0106](../../rfc/0106-stop-registering-derivable-work.md) D1 — repo-origin
  artifacts materialize with no workspace entry; the drain registers nothing.
- `packs/core/.apm/skills/work-intake/SKILL.md` — the classify table is the
  routing authority; the drain adds only the shape-to-family map the spec's
  § D2 fixes.
- `tests/AGENTS.md` — repository-level assertions live in `tests/roster/`,
  anchored at the catalogue root.

## Construction tests

Cross-cutting, beyond the per-task tests below:

- End-to-end drain over a fixture store: offers → decisions → dispositions →
  replay-derivable counts (`AC-0001`, `AC-0002`, `AC-0019`, `AC-0020`
  together).
- Store replay after the fixture drain, goal-based: every disposition in the
  fixture store falls on exactly one side of the promoted-or-pruned split
  (`AC-0004`), and the item whose closure ground failed its test carries no
  terminal disposition (`AC-0003`).
- One drain over the real observation store completes and reports, whatever
  it holds.
- Repair round (review-sustained findings): the reader isolates a bad record
  through the store's own quarantine-collecting read path, the route
  transaction never deletes a prior committed artifact, a materialized
  captured-item file parses under the destination owner's grammar, and a
  closure's evidence rides the run report beside it.
- Manual verification: the spec's § D12 adjudicated sample, gated on capture
  traffic per the spec's Follow-ons.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Decision rationale (spec § Decisions this spec makes) | — the spec itself | gate approval | the owner's approval record |
| Current architecture (knowledge-capture entry) | T8, T23 | entry names the drain, the disposition, the envelope, and the no-dispatch hold | close-work reads the entry |
| Interface compatibility (store event shapes) | T1, T5, T6 | roster suites green over the fixture store | every drain-written disposition parses under the store's validators |
| Maintainer procedure (work-intake drain section) | T7, T19, T22 | source-text assertions | an operator reads the attended rule, the dispatch wiring, and the stale-lock recovery without the spec |
| Current product truth (work-item guide entry) | T8, T23 | guide names the routes, what closure means, and the non-dispatchable-member hold | cold-adopter check |
| Security (`docs/architecture/security.md`) | T8 | the § D10 prose residual recorded as settled by the read-path re-run | the gap list no longer carries it as unowned |
| Release history (core pack changelog) | T8, T23 | changelog entry | the entry leads the release |

## Design (LLD)

### Design decisions

- Disposition-last commit ordering with re-drain recovery (spec § D1): the
  store's identical-disposition no-op and the transaction's
  existing-artifact path make the sequence idempotent. Traces to `AC-0005`.
Owned by: T6
- The `-F` matcher is inserted by the envelope, never stored (spec § D9): it
  is the only matcher under which every admitted pattern is literal —
  verified by probe, `.` and `+` match literally under `-F` and as
  metacharacters under ERE. Traces to `AC-0022`.
Owned by: T3
- `rejected` designation with ground-coded reason codes (spec § D6): no
  vocabulary widening; the reason-code rule already admits
  `closed_overtaken`, `closed_falsified`, `closed_superseded`. Traces to
  `AC-0004`, `AC-0018`.
Owned by: T5
- One seam where command output crosses toward a durable sink, scanned there
  (spec § D8): no such sink ships in this delivery; the seam exists so the
  boundary is enforced and testable. Traces to `AC-0021`.
Owned by: T3

### Data & schema

The offer carries the capture record, the re-check verdict, the envelope
result (exit status, truncated output, capped flag), the prose re-run
verdicts, and the derived intake signals. Closure grounds ride in
disposition reason codes (`closed_overtaken`, `closed_falsified`,
`closed_superseded`); closure evidence and hold reasons ride in the drain's
run report — the store's disposition event carries no evidence field, and a
held item writes no disposition (§ D11). No schema change:
the store's v2 contract, event shapes, and terminal vocabulary are read and
written as-is. Traces to `AC-0004`, `AC-0019`.
Owned by: T1, T5

### Interfaces & contracts

`promotion_drain.py` exposes an open-capture reader (partition walk, no
mutation), an offer assembler (prose re-run, envelope, signals), a pure
decision function (offer → route proposal, hold, or closure verdict), and the
envelope runner. The work-intake procedure calls these plus the existing
`intake_transaction.py` and the store's disposition writer. Traces to
`AC-0001`, `AC-0006`.
Owned by: T1, T3, T5

### Component / module decomposition

New: `packs/core/.apm/skills/project-knowledge/scripts/promotion_drain.py`,
loaded beside `knowledge_store.py` and `project_knowledge.py` as sibling
modules. Edited: `packs/core/.apm/skills/work-intake/SKILL.md` (the drain
procedure section, and § 5's lock paragraph under T22),
`packs/core/.apm/skills/work-intake/scripts/intake_transaction.py` (the
lock acquisition, under T22), and the release surfaces under T23
(`packs/core/pack.toml`, the plugin manifest, the changelog fragment, the
CI workflow's named steps, `tools/lint-ci-parity.py`). Unchanged: the
store, the router. Traces
to `AC-0016`.
Owned by: T3, T4, T7, T22, T23

### State & control flow

Per item: read offer → decide → confirm → transaction (materialize,
dispatch) → terminal disposition. Crash windows: before the transaction
(nothing happened), inside it (the transaction's own rollback), after it
before the disposition (capture open; the re-drain completes the sequence),
after the disposition (complete). The follow-up hardening adds the
no-dispatch gate ahead of the transaction (hold before any effect) and the
recovered-lock acquisition inside it (atomic publication, stale-owner
recovery, identity re-verification). Traces to `AC-0005`, `AC-0012`,
`AC-0025`, `AC-0028`.
Owned by: T6, T19, T22

### Behavior & rules

The decision function implements spec § D2 (shape → family), § D10
(readiness), § D5 (closure grounds and tests), § D6 (disposition mapping),
and § D11 (attended-only). The rules live in the spec; the function is their
single executable home. The follow-up hardening adds: § D1's no-dispatch
hold (no wired dispatch → held before any effect), § D3's classify-member
gate (non-member or non-dispatchable → held), and § D5's superseded
citation check (absent, non-resolving, escaping, or non-existent →
refused). Traces to `AC-0003`, `AC-0006`, `AC-0007`,
`AC-0008`, `AC-0009`, `AC-0010`, `AC-0011`, `AC-0018`, `AC-0025`,
`AC-0026`, `AC-0027`.
Owned by: T5, T19, T20, T21

### Failure, edge cases & resilience

Envelope refusals (confinement, re-check, caps) and prose re-run refusals
produce holds, never partial effects. Crash recovery is the re-drain. A
repeated identical disposition is the store's no-op. The follow-up
hardening adds: the no-dispatch gate holds before any effect; a
non-member or non-dispatchable classification holds as unroutable; a
refused citation (absent, non-resolving, escaping the repository root, or
non-existent) holds the closure; and lock acquisition fails closed —
live and pid-less owners never taken, removal re-verifies identity, and
an orphaned acquisition temporary never blocks a later acquisition.
Traces to `AC-0005`,
`AC-0013`, `AC-0014`, `AC-0015`, `AC-0023`, `AC-0025`, `AC-0026`,
`AC-0027`, `AC-0028`.
Owned by: T3, T6, T19, T20, T21, T22

### Quality attributes (NFRs)

The envelope is the security boundary: blessed confined-file reads for store
access, no shell, no inherited environment, resource caps. Traces to
`AC-0013`, `AC-0014`, `AC-0015`, `AC-0021`.
Owned by: T3

## Tasks

### T1: Open-capture reader

**Depends on:** none

**Tests:** unit, per the spec's Testing Strategy.
- A fixture store holding open, dispositioned, and envelope-only records: the
  reader yields exactly the open captures with their records, so every count
  the run reports derives from the store alone (`AC-0019`).
- A malformed merged record is quarantined under the store's existing read
  rules rather than silently offered.

**Done when:** the roster suite drives the reader over a fixture store and
passes, and no store file is modified by a read.

### T2: Read-path prose re-run

**Depends on:** T1

**Tests:** unit, per the spec's Testing Strategy.
- A merged record carrying a bearer-token-shaped string, a `/Users/…` path,
  and an instruction-shaped line in each scanned field in turn: each is
  refused by the named control and the offer reports the refusal
  (`AC-0023`).
- A clean merged record — free text carrying none of the refusal patterns —
  passes all three re-run controls and is offered (`AC-0023`).
- The scanned set is asserted equal to the set the capture spec's
  free-text-scan criterion (`docs/specs/work-item-capture/spec.md` §
  Acceptance Criteria, "Every free-text field a `work-item` record carries")
  derives from the schema, not a hand-written list.
- A dispatch spy over the classification presentation: record prose appears
  inside the data delimiter and never in instruction position (`AC-0024`).

**Done when:** the three re-run controls run at offer assembly and the roster
suite drives each refusal.

### T3: Execution envelope

**Depends on:** none

**Tests:**
- A stored path that is a repository-relative symlink pointing outside the
  repository — final element, non-final element, and
  `verification_route.path` — is refused after resolution (`AC-0013`).
- A command run with a poisoned ambient environment (`PATH`, `GIT_*`,
  `HOME`) and a poisoned repository configuration inherits none of it;
  standard input is closed; `LC_ALL=C` is pinned (`AC-0014`).
- A command exceeding 10 seconds wall clock is terminated; one whose output
  exceeds 64 KiB is truncated; each holds the item rather than reporting it
  verified (`AC-0015`).
- A stored `grep` pattern containing `.` and one containing `+` match exactly
  the lines containing those literals under `-F`; the matcher is inserted by
  the envelope, never stored (`AC-0022`).
- Output carrying a credential-shaped string is scanned at the durable-write
  seam before any write, and reaches the presentation layer as delimited
  data (`AC-0021`).

**Approach:** real subprocesses, not mocks, for confinement, environment,
and caps — these are runtime properties; the fixture commands come from the
§ D6-admitted shapes.

**Done when:** the integration suite runs each refusal and cap against real
subprocesses and passes.

### T4: Pre-execution re-check

**Depends on:** T3

**Tests:** unit, per the spec's Testing Strategy.
- The re-check calls the capture validator — `project_knowledge.py`'s § D6
  function, the same one the write path uses — asserted by identity, not by
  re-implemented behavior (`AC-0016`).
- Every row of the capture spec's § D6 case table drives the re-check: each
  refused row refuses, each admitted row admits (`AC-0017`).
- A merged record carrying a string `command`, and one carrying argv
  `["bash", "-c", "…"]`, are each refused at the re-check (`AC-0016`).

**Done when:** the case-table driver passes unchanged when a row is added
upstream.

### T5: Decision function

**Depends on:** T1, T2, T3, T4

**Tests:**
- Routing table: a ready defect routes; a defect failing § D10's readiness
  holds (`AC-0008`); a governance item holds while a non-governance item in
  the same offer set routes (`AC-0007`); an unroutable item holds
  (`AC-0006`); a stored path refused by the envelope holds the item
  (`AC-0009`); an untrusted-classified field is refused as input and carried
  unexecuted (`AC-0010`).
- An unattended run holds every item and writes no disposition (`AC-0011`).
- Closures: each ground with its test passing records the ground
  (`AC-0002`); each ground with its test failing is refused (`AC-0003`).
- Every disposition falls on exactly one side of the promoted-or-pruned
  split, and a closure lands on the pruned side (`AC-0004`, `AC-0018`).

**Done when:** the pure-function suite over the routing and closure tables
passes.

### T6: Drain assembly and recovery

**Depends on:** T5

**Tests:** unit, per the spec's Testing Strategy.
- A crash injected at each effect boundary — before the transaction, inside
  it, after it before the disposition, after the disposition: a crash before
  the disposition leaves the capture open, and the re-run drain completes
  without a second artifact or a second terminal event (`AC-0005`,
  `AC-0012`).
- A crash on the closure path, where the terminal disposition is the only
  effect: a crash before the disposition leaves the capture open, and
  re-driving a closure whose disposition already exists is an
  identical-disposition no-op — no second terminal event (`AC-0005`).
- After a fixture drain with routed, held, and closed items: the
  store-derived counts and the run report agree member for member
  (`AC-0001`, `AC-0002`, `AC-0019`, `AC-0020`).

**Approach:** the crash driver injects at the seams the transaction and the
disposition writer already expose; no new failure hook.

**Done when:** the crash-recovery suite passes over the fixture store.

### T7: Work-intake drain procedure

**Depends on:** T6

**Tests:**
- Source-text assertions over the new SKILL.md section: it states the
  attended rule — every route and closure confirmed, unattended reports and
  holds (`AC-0011`) — and the disposition-last ordering (`AC-0005`); it
  routes through the existing classify and transaction seams and registers
  nothing.

**Done when:** the source-text suite passes and the section is readable
without the spec.

### T8: Durable surfaces and smoke

**Depends on:** T7

**Tests:**
- Goal-based checks: the work-item guide entry names the routes and what
  closure means; the architecture entry names the drain, the disposition,
  and the envelope; `docs/architecture/security.md` records the § D10 prose
  residual as settled by the read-path re-run; the changelog entry leads the
  release.
- One drain over the real observation store completes and reports.

**Done when:** each surface check passes and the real-store drain run is
recorded in the verification ledger.

## Repair tasks

Findings the review round sustained, each repaired under its own task. They
land after the original eight; most land in the store's own surfaces — the
pending-read quarantine, the transaction helper's artifact discipline, the
captured-item grammar, and the run report — while T22 lands in work-intake's
shared transaction helper and T23 in the release surfaces.

### T9: Collision-safe, non-destructive route transaction

**Depends on:** none

**Tests:** unit, per the spec's Testing Strategy.
- Two defect captures whose statements share the first sixty slug
  characters: both confirmed routes commit, both artifacts exist afterward,
  and each target is named for its own capture — the capture id rides the
  filename (`AC-0005`).
- A pre-existing byte-differing file at a route's target: the transaction
  fails and the item is held, and the pre-existing file is neither deleted
  nor modified — the rollback removes only the transaction's own partial
  artifact, the `.tmp` file (`AC-0005`).
- Re-drive idempotency retained: a re-driven route over its own
  already-committed artifact leaves it as it is (`AC-0005`).

**Done when:** the roster suite drives the collision and the
  pre-existing-target case and passes, and the crash-recovery suite still
  passes unchanged.

### T10: Per-record isolation in the open-capture reader

**Depends on:** none

**Tests:** unit, per the spec's Testing Strategy.
- A fixture store holding one clean capture and one dirty merged record
  (a journal line whose free text carries a privacy-violating string,
  identity fields recomputed over it): the reader returns the clean capture
  plus the quarantined record with the store's own reason code, and the
  drain completes — it offers the clean item and reports the quarantined
  record as held with the refusing control named (`AC-0023`, `AC-0011`).
- The reader reads through the store's own quarantine-collecting pending
  path, never a second validation implementation — asserted by identity, the
  same way the re-check task asserted the write-path validator.
- The existing reader suite (open, dispositioned, envelope-only records;
  no store file modified by a read) still passes over the new return shape.

**Done when:** a dirty merged record no longer aborts the drain, and the
  roster suite drives the mixed store end to end.

### T11: Grammar-conforming materialization

**Depends on:** none

**Tests:** unit, per the spec's Testing Strategy.
- A confirmed defect route's materialized file parses valid under
  work-loop's own captured-item parser: `Kind` inside the closed vocabulary,
  `Detail` a repository-relative path — the capture's own journal partition
  (`AC-0001`).
- A confirmed question route materializes no captured-item file: the route
  dispatches through the seam with the classification riding the decision,
  and `docs/product/captured/` holds nothing the question route wrote
  (`AC-0001`).
- The drain-run suite's routed-question expectations update to the
  dispatch-only shape and still pass.

**Done when:** every artifact the drain materializes parses valid under the
  destination owner's own parser, and the roster suite proves it.

### T12: Closure evidence rides the run report

**Depends on:** none

**Tests:** unit, per the spec's Testing Strategy.
- A confirmed closure's run-report entry carries the operator's evidence
  verbatim beside the ground (`AC-0002`).
- The counts still agree member for member with the store-derived
  dispositions (`AC-0019`).

**Done when:** a closed item's report entry names its ground and its
  evidence, and the roster suite drives it.

### T13: A refused disposition write holds the item, not the run

**Depends on:** none

**Tests:** unit, per the spec's Testing Strategy.
- The T10 mixed-store fixture, attended: the drain completes, the clean
  capture whose disposition write the store refuses is held with the
  refusing reason named, and no exception escapes the run (`AC-0005`).
- A closure whose disposition write is refused holds the item the same
  way (`AC-0005`).
- A clean store's disposition writes are unchanged: routes and closures
  still record their terminal dispositions (`AC-0001`, `AC-0002`).

**Done when:** one quarantined record can no longer abort an attended
  drain at the disposition boundary, and the roster suite drives the
  mixed store end to end.

### T14: One read path — dispositions through the store's own exclusion reader

**Depends on:** none

**Tests:** unit, per the spec's Testing Strategy.
- The T10 mixed-store fixture: `store_terminal_dispositions` returns the
  clean dispositions and raises nothing, using the store's own
  per-record-exclusion reader — never a second validation implementation
  (`AC-0019`, `AC-0020`).
- A clean store's dispositions are unchanged by the switch.

**Done when:** the module's two read paths agree on the mixed store, and
  the counts comparison the run report makes can be made.

### T15: The captured-item filename stays inside the owner's grammar

**Depends on:** none

**Tests:** unit, per the spec's Testing Strategy.
- A defect whose statement carries non-ASCII alphanumeric characters
  (é, ü, CJK) materializes a filename matching the owner's
  `[a-z0-9][a-z0-9-]*\.md` grammar, and the owner's own listing sees the
  item (`AC-0001`).
- An ASCII statement's filename is unchanged by the fix.

**Done when:** every artifact the drain materializes is visible to the
  destination owner's listing.

### T16: The work-intake dispatch rides the transaction's failure shape

**Depends on:** none

**Tests:** unit, per the spec's Testing Strategy.
- Two confirmed question items whose first dispatch raises: the drain
  completes, the failed item is held with the failed stage named, and the
  second item is still offered and routed (`AC-0006`).
- No exception text from the processor escapes the drain — the held
  entry carries a reason code, never the exception's message.

**Done when:** both route families expose the same dispatch-failure
  shape, and the roster suite drives the failing dispatch.

### T17: Named CI steps for the nine roster suites

**Depends on:** none

**Tests:** the repository's own parity linter.
- Each of the nine `tests/roster/test_promotion_drain_*.py` files gets a
  named step in `.github/workflows/build-check.yml`, placed above the
  bulk `python -m pytest tests/ -q` step with the standard guard, and a
  matching `LOCAL("test-after-build-check")` disposition in
  `tools/lint-ci-parity.py`; the linter exits 0 over the amended
  workflow.

**Done when:** `python3 tools/lint-ci-parity.py` (with PyYAML available)
  reports every step dispositioned, and the nine steps sit above the
  bulk roster step.

### T18: The dispositions reader carries its quarantine collector through partition enumeration

**Depends on:** none

**Tests:** unit, per the spec's Testing Strategy.
- A fixture store holding one clean dispositioned capture plus a misnamed
  partition file (a name the store's partition validator refuses): the reader
  quarantines the partition, the drain completes, and
  `store_terminal_dispositions` returns the clean dispositions without raising
  (`AC-0019`, `AC-0020`).
- A clean store's dispositions are unchanged.

**Done when:** the module's two read paths agree on a store holding a
  misnamed or non-regular partition file, and the roster suite drives it.

### T19: A route with no dispatch wired holds the item

**Depends on:** none

**Tests:** unit, per the spec's Testing Strategy.
- The drain run with defaults — no `transact` override, no
  `dispatch_processor` — over a routable question and a ready defect: each
  is held with the missing dispatch named in the reason, and
  `store_terminal_dispositions` returns no terminal event for either
  (`AC-0025`).
- The hold precedes every transaction effect: a spy over the transaction
  runner and the lock acquisition records zero invocations — the AC-0010
  zero-calls pattern — and no captured-item artifact is materialized for
  the held defect (`AC-0025`).
- `transact_route` called directly with `dispatch_processor=None` on both
  route branches returns the hold shape and attempts no disposition.
- A drain with a real dispatch wired still routes and records `routed`;
  the existing routed-outcome suites are updated to wire one — a real
  dispatch or a dispatch-carrying `transact` override — including
  `test_promotion_drain_repair.py`'s direct `transact_route` assertions
  and the attended-drain routed counts, and `test_promotion_drain_run.py`'s
  AC-0005 crash-boundary suite and its re-drive, which currently assert
  `routed` through the no-dispatch default (`AC-0005`, `AC-0001`).
- A source-text assertion, the T7 pattern, over work-intake `SKILL.md` § 8:
  the wiring note names `dispatch_processor` and states that a drain without
  it holds every routable item.

**Done when:** `drain()` with defaults can no longer record `routed`, the
  hold leaves no artifact and no lock, and work-intake `SKILL.md` § 8 records
  how the operator wires the dispatch at invocation.

### T20: A classification is one of the six classify-table members

**Depends on:** none

**Tests:** unit, per the spec's Testing Strategy.
- A question classified with an output that is not one of the six members
  § D3 names is held as unroutable (`AC-0026`).
- A question classified with `remember` or `incomplete` — the
  non-dispatchable members — is held the same way (`AC-0026`).
- A question classified with each dispatchable member still routes, with
  the classification riding the report item unchanged (`AC-0001`).
- The member set is a module constant whose members spec § D3 enumerates,
  referenced there rather than restated here, and a source-text assertion —
  the T7 pattern — pins the constant to work-intake `SKILL.md` § 4's
  classify table, so a table row added or renamed fails the suite until the
  constant follows.

**Done when:** no non-empty string can route a question, the constant and
  the classify table cannot drift apart silently, and the roster
  suite drives each member and one non-member.

### T21: The superseded closure ground's test runs in the drain

**Depends on:** none

**Tests:** unit, per the spec's Testing Strategy.
- A superseded closure whose cited capture id resolves in the seeded store
  closes and records the disposition (`AC-0002`).
- A superseded closure whose citation is a capture id that resolves
  nowhere, or a path that does not exist, escapes the repository root
  lexically (`..` traversal or absolute form), or resolves outside the
  root through a symlink, or is absent — the closure input carries no
  `citation` field — is refused by the drain
  itself, the item stays open, and the refusal names the failed citation
  (`AC-0027`).
- The citation rides the closed item's run-report entry beside the
  evidence, and a superseded closure that closes carries its citation in
  that entry (`AC-0002`, `AC-0027`).
- A superseded closure whose citation resolves but whose operator verdict
  is false is refused — the verdict is a veto on every ground (`AC-0027`).
- Overtaken and falsified closures are unchanged: the operator's verdict
  still decides them, with the evidence riding the report (`AC-0003`).

**Done when:** a superseded closure cannot commit on a citation that
  resolves nowhere, is a path that does not exist, or is absent, and the
  other two grounds are byte-for-byte their current behavior.

### T22: A stale workspace lock is recovered

**Depends on:** none

**Tests:** unit, per the spec's Testing Strategy.
- A workspace lock holding a pid that no longer exists: the transaction
  recovers it — liveness probe, identity re-verification, removal, one
  retry — and completes, where the same state previously returned
  `LOCK_BUSY` forever (`AC-0028`).
- Concurrent recovery: a fresh lock taken at the same path between the
  probe and the removal is refused, not removed — the re-verification sees
  a different inode or payload and returns lock-busy (`AC-0028`).
- A workspace lock holding the running process's pid is still refused
  (`AC-0028`).
- A lock whose pid is owned by another live process (probe raises
  `PermissionError`) is treated as live and refused.
- A file at the lock path that is not a regular file — a symlink, a
  FIFO, a device — is never probed and never removed, and the payload
  read is no-follow, non-blocking, and bounded (`AC-0028`).
- A lock whose payload carries no parseable pid is never removed, and the
  transaction's own acquisition publishes the lock atomically — the
  `_acquire_claim` pattern: write the pid to a temporary file, then
  `os.link` it into place, so the lock never exists without its pid. The
  test drives the seam: fault-inject the link step (a raising `os.link`)
  and assert no lock file exists at the lock path (`AC-0028`). The
  temporary's identity and lifecycle are asserted with it: its name is
  unique to its holder — pid and a random token — created fresh on every
  acquisition so concurrent acquirers never collide and a killed creator's
  orphan never blocks a later acquisition; it is unlinked immediately
  after publication and on link failure, and an orphaned temporary is
  inert garbage, never a lock (`AC-0028`).
- Work-intake `SKILL.md` § 5's lock paragraph — "If another writer holds
  the lock, the transaction returns `lock_busy` without mutating either
  side" — is updated to state the stale-owner recovery and its limits
  (dead owner removed after identity re-verification; live, pid-less, and
  alien non-regular files at the lock path never taken, probed, or
  removed), asserted by a T7-style source-text check.

**Done when:** the drain's re-run recovery path survives a hard-killed
  predecessor without ever removing a live writer's lock, and the
  intake-transaction suite drives every lock state. The recovery lands in
  the shared `_acquire_workspace_lock`, so every `run_intake_transaction`
  caller gains it (`AC-0028`).

### T23: Release mechanics for the hardening

**Depends on:** T19, T20, T21, T22

**Tests:** goal-based check.
- `packs/core/pack.toml` and the plugin manifest carry the next patch
  version, with a changelog fragment naming the four hardening fixes.
- `make build-self FORCE=1` projects every changed `.apm` file into both
  adapter trees, and the self-host check is clean.
- Every new or changed roster suite has its named CI step above the bulk
  step in `.github/workflows/build-check.yml` and its
  `LOCAL("test-after-build-check")` disposition in
  `tools/lint-ci-parity.py`.
- The acquisition temporary's root glob
  (`.workspace-repair.lock.*.tmp`, the repository's own convention for
  such temporaries) is added to `.gitignore` beside
  `.workspace-repair.lock`, and to the adopter-facing seed copy at
  `packs/core/seeds/.gitignore` beside its own lock entry — the shipped
  `intake_transaction.py` creates the temporary in adopter trees too —
  each asserted by a source-text check over its file.
- The two durable surfaces the hardening falsifies are updated and pinned:
  `docs/architecture/knowledge-capture.md`'s confirmed-route sentence gains
  the no-dispatch hold, and `docs/guides/reference/work-item-capture.md`'s
  question-routing sentence gains the hold on non-dispatchable members;
  `tests/roster/test_promotion_drain_surfaces.py` extends to pin both, and
  its changelog-fragment assertion — one fragment matching "promotion
  drain", pinned to the released version — moves to the hardening's
  fragment and version.

**Done when:** the local gate chain — ruff, mypy, changelog,
  lint-ci-parity, self-host check, the touched suites — is green.

## Rollout

The original delivery was a pure addition — one new module, one
skill-procedure section, documentation surfaces. The follow-up hardening is
a behavior change in a shared concurrency primitive: `drain()`'s default
outcome flips from `routed` to held, the shared transaction's lock
acquisition gains atomic publication and stale-owner recovery reaching
every `run_intake_transaction` caller, two routed-outcome suites rewire to
a real dispatch, and the release surfaces (pack version, changelog,
`.gitignore`, CI steps, lint-ci-parity) update alongside. No migration, no
vocabulary change, no contract version bump. Rollback of the hardening is
a revert of those edits — the module and procedure section remain; the
store's event shapes are untouched by either direction.

## Risks

- The envelope's caps may refuse legitimate verification commands on large
  repository files (`cat` over 64 KiB). The hold-and-report outcome is safe,
  and the first refusal is the revision trigger the spec records.
- The real well may hold no items at delivery, leaving the § D12 adjudicated
  sample gated. The fixture-driven suites cover the mechanics; the spec's
  Follow-ons records the gate.
- A repeated dispatch after a crash in the dispatch-to-disposition window
  starts a second processor run over the same artifact. Accepted by spec
  § D1 as bounded and visible.

## Changelog

<!-- Approvals only. Each approval is an entry, one per gate, with a real
date and the approver's own handle. -->

- 2026-11-04: spec approved by eugenelim, with the four defaulted
  assumptions ratified as defaulted (disposition-last ordering, `rejected`
  for closures, 10 s / 64 KiB envelope caps, attended-only operation).
- 2026-11-04: plan approved by eugenelim as the initial strategy, safety,
  dependency, scope-alignment, and terminal-intent review; tasks remain
  mutable.
