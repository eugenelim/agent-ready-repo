# Spec: Durable cohort effects for engine transitions

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0125; ADR-0061 D5
- **Brief:** none
- **Discovery:** none
- **Contract:** none — this changes a repository-owned CLI and its run-local serialized state, not a mapped `contracts/` protocol
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects
> them in place as the work teaches, without an amendment and without a review
> round. A review finding against working material is advisory — it cannot block,
> because nothing gates the text it cites.

## Outcome

A work-loop controller can resume any transition with a cohort effect after an
interruption without asking a person whether that effect already landed.
Success is that each registered effect is applied exactly once and every event
outside the closed registry leaves cohort state unchanged.

## What Changes

- A short-lived `pending_transition` marker and one `transition_history` replace the amendment-only marker and history in cohort `state.json`.
- The engine classifies, applies, and records a registered cohort effect under the cohort lock before it writes engine state.
- One closed registry maps `contract-amendment`, `wave-passed`, `gates-failed`, `findings-remain`, and `reviewers-clean` to their cohort effects.
- Cohort state moves to schema version 2 while engine state stays at schema version 1; an in-flight run crossing the boundary is refused and reset, not migrated.
- Transition history drops its oldest entries to stay within the existing 1 MiB state ceiling instead of refusing after 20 entries.
- Work-loop execution and session-resumption guidance stops issuing separate cohort mutations for the five registered events.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | Applicable — § 1 is still marked planned and the infrastructure inventory describes four human recovery rows | `docs/architecture/loop-parallelism.md`, `docs/architecture/loop-infrastructure.md` | this spec's implementer | § 1 is marked implemented with its settled schema and authorization choices; the inventory describes engine-owned replay through `loop-cohort.py` | neither document describes a manual cohort-effect replay or an amendment-only durable protocol |
| Serialized-state contract | Applicable — keys, status semantics, retention, and the cohort/engine version split change | `packs/core/.apm/skills/work-loop/references/state-schema.md` | this spec's implementer | field table and invariants cover `pending_transition`, `transition_history`, the last-entry rule, truncation, and schema versions | the reference agrees with emitted assets and both status commands |
| Maintainer and recovery procedure | Applicable — four manual recovery branches and one human authorization gate disappear | `packs/core/.apm/skills/work-loop/references/session-resumption.md`, `packs/core/.apm/skills/work-loop/references/full-mode-engine.md`, `packs/core/.apm/skills/work-loop/SKILL.md` | this spec's implementer | ordinary and interrupted flows call the engine transition once; recovery relies on status plus replay, not a second cohort verb | no registered event instructs a person or agent to repeat its cohort mutation separately |
| Release history and user promise | Applicable — the `core` pack's CLI and durable state change | `packs/core/seeds/docs/product/changelog.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json` | this spec's implementer | one core patch above the fresh merge-base and a changelog entry naming automatic exactly-once recovery plus the reset boundary | all three version surfaces agree and projections carry the same changelog entry |
| Reusable learning | Applicable — `packs/AGENTS.md` requires an honest eval record for a non-cosmetic pack change | `packs/core/.apm/skills/work-loop/evals/evals.json` | this spec's implementer | an eval case exercises interruption and replay without treating the record as verification | the entry exists, parses, and states the expected durable behavior |
| Decision rationale | Applicable, discharged by citation — write authority and the registry boundary are already decided | ADR-0125 D1, D2, and D3 | architecture documents and code comments where needed | every claim writes the record number with the decision id | no text cites a bare ambiguous `D3` for this change |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off before
proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Derive one `transition_id` from `run_id`, the persisted pre-transition sequence, the event, and canonical event arguments; use that same value as the review operation id.
- Decide `applied`, `conflict`, and `absent` from transition history, then reclassify under the cohort lock before any effect.
- Persist `pre_transition_sequence` on both the marker and history entry, and write engine state only after the cohort effect and history entry are durable.
- Re-read and validate completed task sections in `plan.md` before classifying a `contract-amendment` replay as applied; use history alone for the other four events.
- Route every cohort mutation through `loop-cohort.py`, and edit `.apm` sources before regenerating `.claude/` and `.agents/` projections.

### Ask first

- Adding an event to the five-member effect registry or changing the effect associated with a member.
- Changing the destructive reset-pair rollout, the 1 MiB state ceiling, or the rule that the newest history entry is never discarded.
- Changing an existing wave-exit verdict, including the deliberate pass outcomes for unsupported schema (R2) and an absent receipts container (R4).

### Never do

- Write cohort `state.json` directly from `loop-engine.py`; ADR-0125 D3 keeps `loop-cohort.py` as the writer of record.
- Treat a missing marker as `absent`, compare the marker to decide `applied`, or clear history when the marker is cleared.
- Add per-event effect histories or retain `amendment_history` as a second source of replay truth.
- Implement plan width, the wave-decision contract, concurrent dispatch, or lift ADR-0061 D5.
- Change defect D's `workspace.toml` entry.

## Testing Strategy

- **Replay status and retention (AC-0001, AC-0002, AC-0005, AC-0006, AC-0013, AC-0014): TDD at the module and CLI surfaces.** Table-driven tests walk `absent`, `applied`, and `conflict`, including a cleared marker, an amended completed task, more than 20 small entries, and a newest entry that alone exceeds the byte ceiling.
- **Effect registry (AC-0003, AC-0004, AC-0015): TDD at the integration surface.** Each of the five registry members is driven through the same transition-effect entry point and asserts its observable cohort mutation; every event outside that registry, derived from the engine transition table, is asserted to skip the entry point and preserve cohort state.
- **Crash safety (AC-0007, AC-0008): TDD exercised end to end.** For every registry row, an injected crash after the cohort commit but before the engine-state write is followed by the same engine transition; the final cohort state proves an effect count of exactly one. A second injection after marker creation but before the effect proves recovery from the other side of the critical section.
- **Writer and lock rails (AC-0009, AC-0010): goal-based static checks.** AST/source-shape checks prove the engine reaches the closed registry through `loop-cohort.py`, never writes cohort `state.json`, and reclassifies plus records while the cohort lock is held.
- **Schema and guard compatibility (AC-0011, AC-0012, AC-0016, AC-0018): TDD at CLI and guard surfaces.** Mixed cohort/engine schema cases refuse with the reset pair while the existing wave-exit R2 and R4 cases still pass; the emitted initial asset carries only schema-2 unified transition keys.
- **Published operating flow (AC-0017, AC-0019): goal-based checks plus one manual E2E smoke.** The built source and both projections contain no separate registered cohort-effect call after an engine transition; a temporary real spec run demonstrates one registered transition, one interrupted replay, and a clean status.

## Acceptance Criteria

- [x] **AC-0001.** For a valid pending or replayed transition, status is `applied` exactly when the last `transition_history` entry has its `transition_id` and every artifact pinned by that event still matches; it is `conflict` when the last entry has the same `pre_transition_sequence` under a different id or a pinned-artifact check fails; it is `absent` when no history entry has that sequence.
- [x] **AC-0002.** Clearing `pending_transition` after a successful cohort commit does not change that transition's status from `applied`, and replaying it does not apply its effect again.
- [x] **AC-0003.** The effect registry contains exactly `contract-amendment`, `wave-passed`, `gates-failed`, `findings-remain`, and `reviewers-clean`; every event outside that registry, as derived from the engine transition table, leaves cohort state byte-identical during the cohort-effect phase.
- [x] **AC-0004.** Each registered event performs the effect named by `loop-parallelism.md` § 1 with arguments derived from the source named there: completed-task amendment evidence, `last_event_context.completed_wave_index`, or the persisted pre-transition sequence.
- [x] **AC-0005.** A `contract-amendment` history match is not `applied` after a completed task section in `plan.md` changes; each of the other four history matches is `applied` without re-reading an unpinned artifact.
- [x] **AC-0006.** `pre_transition_sequence` is present on every marker and history entry, and a replay after engine state has advanced reads that persisted value rather than deriving a new key.
- [x] **AC-0007.** For each of the five registry members, a crash after marker persistence but before effect commit followed by replay yields one cohort effect and one matching history entry.
- [x] **AC-0008.** For each of the five registry members, a crash after cohort effect/history commit but before engine-state commit followed by replay yields one cohort effect and one matching history entry.
- [x] **AC-0009.** The engine applies registered effects only while holding its engine lock and the cohort lock in that order, reclassifies after acquiring the cohort lock, clears the marker in the same cohort-state commit as the history append, releases the cohort lock, and writes engine state last.
- [x] **AC-0010.** `loop-engine.py` makes no direct write or unlink of cohort `state.json`; every registered mutation is dispatched through a closed registry owned by `loop-cohort.py`.
- [x] **AC-0011.** New cohort state is stamped `schema_version: 2`, new engine state remains stamped `schema_version: 1`, and each component validates the version of the state file it owns or consumes without treating the two constants as one shared value.
- [x] **AC-0012.** An in-flight run with a cohort schema from the other side of the version-2 boundary refuses before mutation and names `loop-cohort reset` followed by `loop-engine reset` as the recovery; neither direction attempts migration.
- [x] **AC-0013.** Transition history may exceed 20 entries and is trimmed oldest-first only when needed to keep the compact UTF-8 serialization of the whole cohort state at or below 1,048,576 bytes; the entry whose append first exceeds the ceiling is retained by discarding older entries, while an entry that cannot fit even as the sole history member refuses without changing state.
- [x] **AC-0014.** Every replay classification reads only the last history entry to decide `applied`; a test that changes the implementation to accept an older matching entry fails.
- [x] **AC-0015.** The review operation id for both `findings-remain` and `reviewers-clean` equals their `transition_id`, so an engine replay and review-record idempotency use the same key and no human authorization gate remains for a matching `reviewers-clean` replay.
- [x] **AC-0016.** The existing wave-exit verdict rows for unsupported schema (R2) and absent receipts container (R4) still pass, with no overlap and no uncovered row introduced if the verdict implementation is touched.
- [x] **AC-0017.** Work-loop execution and session-resumption instructions issue no separate `wave advance`, `record-attempt`, or `review record` mutation for a registered event after requesting its engine transition.
- [x] **AC-0018.** The emitted initial cohort-state asset uses `pending_transition` and `transition_history` and contains neither `amendment_pending` nor `amendment_history`.
- [x] **AC-0019.** The source, `.claude/`, and `.agents/` work-loop copies are byte-equivalent after the repository build.

## Follow-ons

- Plan width in `loop-parallelism.md` § 3, the wave-decision contract in § 4, and any change to ADR-0061 D5 remain separate decisions and deliveries.
- The remaining durable-state part of defect D and its `workspace.toml` entry remain unchanged.

## Assumptions

none
