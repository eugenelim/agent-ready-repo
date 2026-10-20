# Spec: Execution supervisor cutover

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** Platform Core
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0144, ADR-0064, ADR-0014
- **Brief:** brief:acceptance-centered-work-loop
- **Discovery:** none
- **Contract:** `contracts/jsonschema/loop-run-event.schema.json` (consumed unchanged); `contracts/jsonschema/loop-cohort-wave-decision.schema.json` (retired); `execution-supervisor-core`'s `run.json` fields (consumed)
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Protected semantic-policy contract.** `Contract`, `Scope and Non-goals`,
> `Durable Outputs`, `Agent Rules`, `Testing Strategy`, `Acceptance Criteria`,
> `Terminal Intent`, and `Accepted Risk` are approval-bound or explicitly
> review-authorized. A change follows its owning amendment, review, or risk
> decision. `Outcome`, `What Changes`, `Follow-ons`, and `Assumptions` are
> working material that may be corrected without changing accepted authority.

## Outcome

Adopters running full-mode `work-loop` reach the supervisor through the unchanged skill invocation, light mode never starts it, and the old phase engine, cohort writer, legacy review path, and wave-decision contract no longer exist anywhere in the catalogue. Success is a full code run that reaches readiness through the installed skill on POSIX and Windows with only the standard library, with every caller repointed and light mode's steps unchanged apart from command locations.

## What Changes

- `work-loop/SKILL.md` and its references route every action the old engine or cohort writer owned to a supervisor verb, and light-mode text only swaps command locations.
- `loop-engine.py`, `loop-cohort.py`, `_compat_facade.py`, `_review_compat.py`, `assets/state.json`, `references/full-mode-engine.md`, and the wave-decision schema leave the catalogue.
- The pre-PR hooks, `agentbundle`'s workspace bridge, CI, repository tools, guides, sibling packs, `new-spec`'s plan contract, and open backlog entries stop naming the old engine.
- The workspace bridge reads the run id, active signal, stage, and pending human gate from the supervisor's `run.json`.
- Slice 3's `delivery-fact-feed.py` reads each spec's committed `delivery/evidence.jsonl` instead of the shadow evidence log the cutover removes.
- Core ships the switched skill in its next major release.

## Scope and Non-goals

This spec owns the authority switch for full mode: the skill rewrite, removal of
the old engine, legacy review path, and wave-decision contract, repointing every
caller, the bridge's supervisor inputs, and the release. Tasks T2 and T3 merge
only after ADR-0144 is Accepted, Slice 3 has shipped, and all three of
`execution-supervisor-core`, `execution-supervisor-attempt-security`, and
`execution-supervisor-review-gate` have shipped; T1 may merge earlier.

It keeps the reusable `spec-approved` and `plan-locked` knowledge-capture
gates that Slice 3 retained, under those gate names; removing them belongs to
Slice 8 once delivery facts are written by default, which this cutover makes
true. It does not change light mode's steps or gates; change the supervisor's
procedure, security checks, or review selection; ship a compatibility adapter,
reverse reader, or dual-write path (ADR-0144 D7); or give adopters their own
review rules.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | The switch needs its governing record accepted. | `docs/adr/0144-work-loop-supervisor-owns-procedure.md`; mirrors on ADR-0125, ADR-0061, ADR-0064 | Platform Core decision-maker | ADR shape lint | ADR-0125 is `Superseded`. |
| Interface compatibility | The wave-decision contract is retired. | `contracts/jsonschema/`, `contracts/README.md`, `.workspace-prune-protected.toml` | `agentbundle` contract maintainers | AC-0008 | The schema and its registry rows are gone. |
| User and maintainer procedure | Adopters drive full mode through the skill. | `work-loop/SKILL.md`; `references/` (a supervisor reference replacing `full-mode-engine.md`, carrying `execution-supervisor-attempt-security`'s unsupported Git settings list; `state-schema.md`, `session-resumption.md`, `delivery-contract-lifecycle.md`, `supervisor-mode.md`, `finding-adjudication.md`, `pre-execute-review.md`, `review-verdict-record.md`, `reviewer-roster.md`, `light-mode.md`); `evals/evals.json`; `profiles/work-loop.toml` | Core pack maintainers | Skill evals and link checks | Every action AC-0001 lists names its supervisor verb. |
| Planning contract | Tasks inside the envelope change without amendment. | `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md`, `new-spec/assets/plan.md` | Core pack maintainers | new-spec evals | Both state which plan changes need an amendment and which do not. |
| Current architecture | The authority map changes. | `ARCHITECTURE.md`; `packs/core/DESIGN.md`; `docs/architecture/` `loop-infrastructure.md`, `loop-contract.md`, `loop-parallelism.md`, `work-loop-execution-supervisor.md`, `work-loop-authority-migration.md`, `work-loop-review-disposition.md`, `acceptance-centered-work-loop.md`, `telemetry.md`, `verification-graph.md`, `README.md`, `workspace-mcp/design.md` | Platform Core | Architecture review | None describes a removed script, `legacy-result-ack.v1`, a `tools/` supervisor builder, or a `packages/agentbundle/` supervisor home as current. |
| Knowledge architecture | The delivery fact feed's source moves from the shadow log to committed evidence. | `docs/architecture/work-loop-knowledge-handoff.md`, `docs/architecture/knowledge-capture.md` | Platform Core and project-knowledge maintainers | Architecture review | Both name `delivery/evidence.jsonl` as the feed source and the retained capture gates as Slice 8's to remove. |
| Guides and sibling packs | They name the removed commands. | Files under `guides/` and `packs/` found by AC-0007's search | Owning pack maintainers | AC-0007 | No hit remains. |
| Release history | Behavior changes, and in-flight runs re-derive. | Core manifests and `docs/product/changelog.md` | Core pack release maintainers | Version parity | T1's 3.x release and the next major each carry a changelog entry; the major names the in-flight-run consequence. |
| Product coordination | Backlog entries target removed scripts, and the slice closes. | `workspace.toml` and the brief's Spec map | Platform Core | Workspace reconcile and brief-coverage lint | Each backlog entry naming a removed script is retired through `close-work` or rewritten, with its disposition in the ledger. |

## Agent Rules

### Always do

- Rewrite every reference from a repository-wide search, outside history
  paths, taken at the start of the work, not from a remembered list.
- Keep shipped skill text free of this repository's internal record citations.
- Get a security-reviewer pass on T1 and T2 before merge.

### Ask first

- Choosing a Core version other than the next major.

### Never do

- Ship a compatibility adapter, reverse reader, or dual-write path to the old
  engine.

## Testing Strategy

- **Skill switch, light mode, and removal (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010):**
  goal-based tree, search, run, and diff checks, because these are facts of the
  tree and of whole runs.
- **Runtime (AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016):** goal-based
  installed-skill runs on POSIX and the Windows CI job, plus bridge and
  upgraded-adopter fixtures.
- **Hooks (AC-0017, AC-0018):** goal-based hook runs.
- **Knowledge (AC-0019, AC-0020, AC-0021):** goal-based runs against
  project-knowledge's capture path, the fact feed, and a skill copy with
  project-knowledge absent.

## Acceptance Criteria

### Definitions

- **Engine-owned actions.** Run initialization, phase transitions, plan
  approval and locking, scheduling, wave advance, attempt and dispatch
  recording, full-mode review recording, status, identity, and reset.
- **Light-mode text.** `references/light-mode.md`, `SKILL.md`'s `Select: light
  or full mode` section, and every other `SKILL.md` instruction light mode
  follows.
- **Command swaps.** `loop-cohort.py review <verb>` or a bare `review <verb>`
  becomes `review-artifact.py <verb>` for `classify`, `raw-classify`, `inspect`,
  and `record`; any other mention of `loop-cohort` or `loop-engine` becomes "the
  supervisor".
- **History paths.** Every file named `CHANGELOG.md` or `changelog.md`,
  `docs/adr/`, `docs/rfc/`, `docs/specs/`, `docs/knowledge/`,
  `docs/product/research/`, and `.context/`; in `workspace.toml`, comments and
  `path` or `ref` values that point into a history path; and in
  `docs/product/briefs/` and `docs/product/intents/`, text describing past
  delivery.

### Criteria

Skill switch, light mode, and removal

- [ ] **AC-0001.** In `SKILL.md` and its references, every engine-owned action
  names a `work-supervisor.py` verb.
- [ ] **AC-0002.** No file in the skill other than `review-rules.json` and
  `references/light-mode.md` contains a table row or list item that names a role
  from `review-rules.json` together with its condition or boundary text.
- [ ] **AC-0003.** A direct-light run and a durable light-mode run invoke no
  `work-supervisor.py` command and create no `<spec>/.supervisor/`.
- [ ] **AC-0004.** Light-mode text differs from its pre-change text only by the
  command swaps and by qualifiers that limit a clause shared with full-mode
  code review to light mode and pre-approval, and no shipped skill line names a
  bare `review <verb>` without `review-artifact.py`.
- [ ] **AC-0005.** `packs/core/tests/skills/work-intake/test_direct_light_no_writes.py`
  and `packs/core/tests/skills/work-loop/test_work_intake_dispatch.py` pass with
  no change other than the command swaps.
- [ ] **AC-0006.** `loop-engine.py`, `loop-cohort.py`, `_compat_facade.py`,
  `_review_compat.py`, `assets/state.json`, and `references/full-mode-engine.md`
  are absent from the skill source and its generated copies.
- [ ] **AC-0007.** Outside history paths, no file in `packs/`, `tools/`,
  `packages/`, `tests/`, `guides/`, `contracts/`, `.github/`,
  `docs/product/intents/`, `docs/product/briefs/`, `Makefile`, `.snyk`, or
  `workspace.toml` names `loop-engine`, `loop-cohort`, `engine-state.json`,
  `full-mode-engine`, or a cohort `state.json`.
- [ ] **AC-0008.** `contracts/jsonschema/loop-cohort-wave-decision.schema.json`
  is absent, and no file outside history paths names it.
- [ ] **AC-0009.** No remaining script in `work-loop/scripts/` was invoked only
  by removed files.
- [ ] **AC-0010.** `SKILL.md`'s close step names the explicit close-time
  `work-item` capture.

Runtime

- [ ] **AC-0011.** The installed skill's `work-supervisor.py` completes a
  synthetic full code run to readiness with only the standard library and the
  skill's `scripts/` directory importable.
- [ ] **AC-0012.** The Windows CI job runs the same synthetic run to readiness.
- [ ] **AC-0013.** The workspace bridge binds a supervisor run's id and active
  signal from `run.json`.
- [ ] **AC-0014.** The bridge marks a gate pending with its question while
  `run.json` reports an open `human-decision`, and clears it once that request
  resolves.
- [ ] **AC-0015.** The bridge shows a gate question only through Slice 1
  content-safety inert framing.
- [ ] **AC-0016.** In a repository whose ignore rules omit `.supervisor/` and
  `.loop-run/`, a full run reaches readiness and no supervisor commit touches
  either.

Hooks

- [ ] **AC-0017.** `packs/core/.apm/hooks/pre-pr.py` and `tools/hooks/pre-pr.py`
  run `work-supervisor.py status --check` for each spec holding
  `delivery/approvals.jsonl`, and fail when any such run exits non-zero.
- [ ] **AC-0018.** The hooks' supervisor check adds no failure when every such
  run exits 0, including a terminal run that reached the retry cap, or when no
  spec holds `delivery/approvals.jsonl`.

Knowledge

- [ ] **AC-0019.** The rewritten skill still requests a reusable capture at the
  `spec-approved` gate before `start` and at the `plan-locked` gate at `start`,
  under those gate names, and project-knowledge accepts each exactly as Slice
  3's AC-0006 fixtures require.
- [ ] **AC-0020.** `delivery-fact-feed.py` reads each spec's committed
  `delivery/evidence.jsonl` with no shadow-services setting, and returns a
  candidate for a supervisor run's review-failure receipt.
- [ ] **AC-0021.** A full code run reaches readiness with project-knowledge
  absent.

## Follow-ons

none

## Terminal Intent

`code` — switch the skill, remove the old engine, repoint callers, and release.

## Accepted Risk

A run started under the old engine is re-derived from durable facts rather than
resumed in place (ADR-0144 D7): its tasks count as incomplete until the loop
re-runs or replans them. The Platform Core decision-maker accepted this risk on
2026-10-11 because distribution is small.

## Assumptions

- **The engine and the supervisor read `Depends on:` lines differently (found 2026-10-19 in `execution-supervisor-core`).** Both use the shared task-section walk and value parse in `_loop_guards.py`. But `loop-cohort.py` finds the line only when it is unbulleted and exact-case (`**Depends on:** T1`). The supervisor's projector also accepts a bulleted or differently cased line (`- **Depends on:** T1`), and this repository's plans use bullets. So on today's plans the engine schedules no dependency where the supervisor orders tasks. After the cutover, the supervisor's reading becomes the only one, and plans that relied on the engine ignoring their bulleted dependencies will start to see them ordered. Evidence: `docs/specs/execution-supervisor-core/notes/verification-ledger.md`, the "plan parser moved to `_loop_guards.py`" entry.
