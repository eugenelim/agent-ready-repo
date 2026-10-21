# ADR-0144: Work-loop procedure and review authority: a skill-shipped supervisor over the phase engine, cohort writer, and legacy review gate

- **Status:** Accepted
- **Date:** 2026-10-11
- **Areas:** orchestration, work-loop
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** ADR-0125
- **Supersedes in part:** ADR-0061 D1,D2,D8; ADR-0064 D1,D2,D5,D6
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0028 (the TDD stub vehicle this keeps — stubs still live in the plan's task `Tests:`, and the guard here enforces what that RFC left to prose); ADR-0014 (light mode runs no engine — unchanged here); ADR-0005 (parallel-write gating — untouched; Slice 7 owns it); ADR-0042 / ADR-0047 (which reviewers run — unchanged in meaning, now expressed as review-policy data); FEAT-0036 (the review-gate cutover this record absorbs); ADR-0115 (the telemetry exporter — unaffected, because it reads the same event file shape)

## Decision summary

- **Decision:** We will make a supervisor that ships inside the `work-loop` skill the single owner of delivery procedure, replacing the phase engine, the cohort writer, the whole-plan lock, and the legacy review gate, with no legacy compatibility layer.
- **Because:** procedure can then change tasks inside the reviewed envelope without approval, while criteria, evidence, and structured review facts become the only authority for completion.
- **Applies to:** full-mode `code` and `spec-plan` runs of `work-loop`; not light mode, parallel writes, or canonical result integration.
- **Tradeoff accepted:** an in-flight run started under the old engine is re-derived by the loop rather than read by a compatibility adapter, and reversal means reinstalling the prior Core release.
- **Revisit if:** an adopter population appears that cannot tolerate a re-derived in-flight run, or a supported host cannot run a standard-library script from the installed skill directory.

## Context

`work-loop` procedure is split across two path-loaded scripts inside the skill.
`loop-engine.py` owns legal phase order (ADR-0061 D1), and `loop-cohort.py`
owns waves, counters, and `state.json` (ADR-0061 D2), with the engine allowed
to apply five registered cohort effects through it (ADR-0125 D1–D3). An
approved plan is pinned by a whole-artifact hash. Any later edit is refused,
and the only way back is `contract-amendment` or a reset.

Four facts make this the wrong owner for the acceptance-centered loop:

- **The lock forbids the replanning the brief requires.** The accepted brief
  `acceptance-centered-work-loop` needs task order, decomposition, test shape,
  and local method to change after initial review without approval, as long as
  the reviewed execution envelope and terminal intent stay fixed. Slice 1
  already ships the envelope projector, the change classifier, and the
  `initial-plan-review.v1` record. Nothing consumes them as authority.
- **Two guards exist only as prose.** The `spec-plan` no-artifact boundary is a
  table row, and red-before-green with byte-identical stubs (RFC-0028) is a
  reference document. No script checks stub bytes or records red.
- **Review authority sits on the wrong side of the boundary.** Slice 2 ships
  structured review facts — selected obligations, current typed reports,
  actual-failure assessments, and dispositions — beside the legacy path, but
  the gate still decides from `loop-cohort.py review raw-classify` and the
  adjudication grammar. The skill also carries reviewer-specific procedure:
  role conditions, adjudication grammar, retry caps, and session mechanics.
  FEAT-0036 proposed switching that gate on its own, keeping the old plan lock
  and cohort writer, which would mean building that switch twice.
- **Nothing handles an unknown external effect.** The engine has no operation
  keys and no record of a human decision about an effect whose outcome cannot
  be queried. ADR-0061 D8 deferred durable side-effect semantics until their
  prerequisites existed, and this record now supplies them.

Two constraints shape how the authority moves:

- **Adopters receive only what the skill ships.** `tools/` and
  `packages/agentbundle/` do not install with a pack, and Slice 1 already
  refused any `packages/agentbundle/` home for delivery services. The skill
  loads its `_*.py` siblings by path today.
- **Distribution is small.** The owner judged on 2026-10-11 that compatibility
  adapters, reverse readers, and dual-write parity cost more than re-deriving
  the few in-flight runs, which the loop can do from durable facts.

## Decision

We will make a supervisor that ships inside the `work-loop` skill the single
owner of delivery procedure, replacing the phase engine, the cohort writer, the
whole-plan lock, and the legacy review gate, with no legacy compatibility layer.

- **D1:** `work-supervisor.py` and its `_supervisor_*.py` siblings in
  `work-loop/scripts/` own procedure for full-mode runs: task projection,
  ordering, dispatch, leases, recovery, and terminal handling. `loop-engine.py`
  phase order and `loop-cohort.py` cohort state stop being authorities, and no
  other script writes procedure state.
- **D2:** The supervisor runs from the installed skill directory on the Python
  standard library alone, on every platform full mode supports today, Windows
  included. It never imports or executes anything from `tools/`, `packages/`, or
  another installed package at runtime.
- **D3:** An accepted `initial-plan-review.v1` bound to the current
  reviewed-execution-envelope fingerprint and terminal intent admits execution.
  The whole-plan hash lock is removed. A working-plan or task change that leaves
  both unchanged reprojects tasks without approval and cancels only
  unintegrated attempts. A change to either refuses dispatch and names the
  owning amendment or plan-review authority.
- **D4:** `spec-plan` terminal intent ends after initial review with no task
  projection, no execution request, and no repository test or implementation
  write.
- **D5:** In `code` intent, no production change for a TDD task that declares
  stubs is admitted until the supervisor itself has observed those exact stub
  bytes fail. Red proof belongs to the task and its stub bytes; the supervisor
  records it when it admits the stub, or itself when the stubs are already
  committed and still fail. A task with a `no stub` disposition needs no red
  proof. Missing or mismatched proof refuses.
- **D6:** Effect intents and receipts are durable records. An external effect
  whose outcome the source cannot establish is never repeated automatically; it
  waits for a durable named-human `effect-resolution.v1` decision: confirmed, do
  not retry, or one authorized retry claimed under lock and compare-and-swap.
  An effect the source shows never happened may be dispatched again, at most
  three times in all, before a human decides.
- **D7:** No compatibility adapter, reverse reader, or dual-write path to the
  old engine ships. A run whose durable state predates the supervisor is
  re-derived from the spec, plan, Git history, evidence, and review facts, and
  reversal is reinstalling the prior Core release.
- **D8:** Review closure derives only from structured review readiness:
  every selected obligation has a current typed report, every finding has a
  current actual-failure assessment, and every supported finding is disposed.
  All reviewer roles switch at once. The `raw-classify` and adjudication-grammar
  gate no longer decides full-mode code-review closure; pre-approval and
  light-mode adjudication keep that classifier on a surviving command.
  Reviewer-specific procedure leaves the skill: which roles run becomes
  review-rules data, and how a reviewer works stays inside the reviewer.
- **D9:** Light mode (ADR-0014), parallel-write gating (ADR-0005), and the
  worktree as the product result boundary stay as they are.
- **D10:** The supervisor is the only producer of `.loop-run/events.jsonl`. It
  appends one line per supervisor step in the existing
  `loop-run-event.schema.json` envelope, with supervisor step names in `from`,
  `event`, and `to`, and keeps the lines crash-consistent by deriving them from
  its own commits. The bridge reads the run id and active signal from the
  supervisor's `<spec>/.supervisor/run.json` instead of `engine-state.json`;
  its tail, filter, and reset rules (ADR-0064 D3, D4, D7) are unchanged.
- **D11:** Worker attempts — implementer and reviewer subagents — are
  untrusted: a change during an attempt to a trusted file (the spec, its plan,
  the records it cites, or the installed skill), to Git control state, or to
  committed `delivery/` records refuses its result, and `HEAD` may advance only
  by commits the supervisor itself made. The controller, the agent following
  `SKILL.md`, is trusted as it is today. A named-human decision (approval,
  accepted risk, effect resolution) is recorded with its authority reference,
  not cryptographically enforced.

## Decision drivers

- **Replanning freedom:** in-envelope task change needs no human approval.
- **One owner per mechanism:** procedure has one writer, and completion stays
  with criteria, evidence, and review facts.
- **Adopter reach:** everything that runs must install with the skill.
- **Cut before adding:** no mechanism earns a place unless the slice's
  acceptance boundary needs it.

## Consequences

**Positive:**

- Tasks can be reordered, split, or replaced after initial review with no
  approval and no reset.
- The `spec-plan` boundary and red-before-green become checked refusals rather
  than prose.
- A new reviewer joins through one `review-rules.json` entry and a typed report; no skill procedure or supervisor code changes.
- Journal loss can no longer repeat an external effect silently.
- Slice 8 shrinks: no compatibility adapter or reverse reader exists to retire.

**Negative:**

- An in-flight run under the old engine does not resume in place. The loop
  re-derives it, and a run that cannot be re-derived restarts from its approved
  spec.
- Reversal is coarse. Reinstalling the prior Core release discards supervisor
  records that release cannot read.
- `loop-infrastructure.md`, `loop-contract.md`, the work-loop skill and its
  review references, and the engine and review test corpus all change in one
  delivery, which makes it a large review.
- The authority-migration design's reverse-reader and dual-read gates no longer
  apply to this cutover. Its Slice 4 rows need an amendment to match.

**Revisit if:** an adopter population appears that cannot tolerate a re-derived in-flight run, or a supported host cannot run a standard-library script from the installed skill directory.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:** a clean-environment test runs the installed skill's
  `work-supervisor.py` with only the standard library importable and fails on
  any import outside the skill directory. A test fails if any script other
  than the supervisor writes procedure state. A reviewer joins through a
  `review-rules.json` entry and a typed report: a synthetic reviewer closes a
  review obligation with only that entry added and a `review-report.v1` returned.
- **Owner:** Core pack maintainers

## Alternatives considered

- **Keep the engine and cohort writer, and relax the plan lock in place:**
  rejected on one owner per mechanism. It leaves phase state and wave state as
  competing authorities beside criteria and evidence, which the brief rules out.
- **A single-file supervisor built by `tools/build-work-supervisor.py` from a
  manifest:** rejected on adopter reach and cut before adding. The builder never
  reaches adopters, and the skill already ships path-loaded siblings that need
  no build step.
- **Home the journal, effect-resolution store, and provider selector in
  `packages/agentbundle/`:** rejected on adopter reach. That package is not
  installed with the skill.
- **Switch the review gate separately (FEAT-0036) while the engine keeps
  procedure:** rejected on cut before adding. It builds a gate switch and a
  reversal path into an engine this record retires.
- **Ship compatibility adapters, reverse readers, and dual-write parity before
  the switch:** rejected on cut before adding, by the owner on 2026-10-11. The
  distribution is small enough for the loop to re-derive in-flight runs.

## References

- `docs/product/briefs/acceptance-centered-work-loop.md` (Slice 4 row)
- `docs/architecture/work-loop-execution-supervisor.md`
- `docs/architecture/work-loop-authority-migration.md` (rows this record satisfies and amends)
- `docs/product/intents/FEAT-0036-review-authority-cutover.md` (absorbed)
- `docs/specs/structured-review-boundary/spec.md` (the review facts D8 decides from)
- `docs/specs/execution-supervisor-core/spec.md`, `execution-supervisor-attempt-security/spec.md`, `execution-supervisor-review-gate/spec.md`, and `execution-supervisor-cutover/spec.md` (the deliveries that implement it)
