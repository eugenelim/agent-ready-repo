# Plan: Hand a captured item to its owner or close it, and record which

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing
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
- Manual verification: the spec's § D12 adjudicated sample, gated on capture
  traffic per the spec's Follow-ons.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Decision rationale (spec § Decisions this spec makes) | — the spec itself | gate approval | the owner's approval record |
| Current architecture (knowledge-capture entry) | T8 | entry names the drain, the disposition, and the envelope | close-work reads the entry |
| Interface compatibility (store event shapes) | T1, T5, T6 | roster suites green over the fixture store | every drain-written disposition parses under the store's validators |
| Maintainer procedure (work-intake drain section) | T7 | source-text assertions | an operator reads the attended rule without the spec |
| Current product truth (work-item guide entry) | T8 | guide names the routes and what closure means | cold-adopter check |
| Security (`docs/architecture/security.md`) | T8 | the § D10 prose residual recorded as settled by the read-path re-run | the gap list no longer carries it as unowned |
| Release history (core pack changelog) | T8 | changelog entry | the entry leads the release |

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
procedure section). Unchanged: the store, the transaction, the router. Traces
to `AC-0016`.
Owned by: T3, T4, T7

### State & control flow

Per item: read offer → decide → confirm → transaction (materialize,
dispatch) → terminal disposition. Crash windows: before the transaction
(nothing happened), inside it (the transaction's own rollback), after it
before the disposition (capture open; the re-drain completes the sequence),
after the disposition (complete). Traces to `AC-0005`, `AC-0012`.
Owned by: T6

### Behavior & rules

The decision function implements spec § D2 (shape → family), § D10
(readiness), § D5 (closure grounds and tests), § D6 (disposition mapping),
and § D11 (attended-only). The rules live in the spec; the function is their
single executable home. Traces to `AC-0003`, `AC-0006`, `AC-0007`,
`AC-0008`, `AC-0009`, `AC-0010`, `AC-0011`, `AC-0018`.
Owned by: T5

### Failure, edge cases & resilience

Envelope refusals (confinement, re-check, caps) and prose re-run refusals
produce holds, never partial effects. Crash recovery is the re-drain. A
repeated identical disposition is the store's no-op. Traces to `AC-0005`,
`AC-0013`, `AC-0014`, `AC-0015`, `AC-0023`.
Owned by: T3, T6

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

## Rollout

Pure addition: one new module, one skill-procedure section, documentation
surfaces. No migration, no vocabulary change, no contract version bump.
Rollback is deletion of the module and the procedure section; the store is
untouched by a rollback.

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
