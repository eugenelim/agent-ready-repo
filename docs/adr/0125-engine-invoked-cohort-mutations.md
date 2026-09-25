# ADR-0125: Durable transitions make four cohort mutations engine-invoked

- **Status:** Accepted
- **Date:** 2026-09-25
- **Areas:** orchestration, work-loop
- **Reversibility:** high
- **Decision-makers:** @eugenelim
- **Supersedes:** none
- **Supersedes in part:** ADR-0061 D3, D4
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0061 (the record this supersedes in part — its D3 write clause and D4 invoker clause); RFC-0102 (the mutability classes that route this to a superseding record rather than an erratum)

## Decision summary

- **Decision:** We will let the engine apply a cohort effect as part of the transition that carries it, for a closed set of five events, while `loop-cohort.py` remains the sole writer of cohort state.
- **Because:** the crash windows for four of those events are closed today only by a recovery protocol a person executes by hand, which cannot be driven concurrently.
- **Applies to:** the events named in the effect registry of `docs/architecture/loop-parallelism.md` § 1, and no others.
- **Tradeoff accepted:** four mutations leave the skill's explicit control, so the skill alone no longer tells a reader what wrote cohort state.
- **Revisit if:** the effect registry needs an event whose effect is not a cohort mutation; or a direct engine write to `state.json` is proposed, which this record refuses.

## Context

ADR-0061 **D3** says the engine never writes cohort state and reads it only through five designated read-only verbs. **D4** says every cohort mutation is invoked explicitly by the skill.

Both already carry recorded drift. ADR-0061's 2026-09-22 erratum records that the guard layer reads `state.json` directly rather than through those verbs, and that the `contract-amendment` transition writes cohort state from inside the engine. That erratum describes what ships today; this record decides what changes, and does not restate it.

The present breach is narrow. One event writes: `cmd_transition` calls `apply_contract_amendment` on `contract-amendment`, at two call sites within that one function. The engine's other two reaches into the cohort module are a parse and a replay-status read, neither of which writes.

Durable transitions generalise the replay marker that one event already carries to every event with a cohort effect. Four more events gain one: `wave-passed` (wave advance), `gates-failed` (record-attempt), and `findings-remain` and `reviewers-clean` (review record). Each effect becomes part of its transition rather than a separate skill call, so the write breach widens from one event to five and four mutations move from skill-invoked to engine-invoked.

That reverses D3's write clause and D4 as written. RFC-0102 permits an erratum to clarify what a decision means and not to alter what was decided, so a third erratum on ADR-0061 cannot carry it.

**Why now.** The crash windows for those four events are closed today by a recovery protocol a person executes by hand. The `reviewers-clean` replay additionally requires explicit human authorization, because an unguarded replay double-counts a review round and overwrites a level of fingerprint audit history. A protocol that depends on a person at the moment a run has crashed does not survive concurrent execution, and concurrent execution is what the surrounding parallelism work exists to reach.

## Decision

> Write authority over cohort state stays with `loop-cohort.py`, and the set of mutations the engine may invoke as a transition effect widens from one event to five.

ADR-0061 D3's "never writes cohort state" and D4's "invoked explicitly by the skill" no longer hold as written. D3's read-channel clause is unaffected by this record; its drift is already recorded in ADR-0061's 2026-09-22 erratum.

- **D1:** An event carrying a cohort effect may have that effect applied by the engine as part of the transition, rather than by a separate skill call.
- **D2:** The eligible set is closed and enumerated by the effect registry in `docs/architecture/loop-parallelism.md` § 1. An event outside that registry gains no write authority from this record.
- **D3:** `loop-cohort.py` remains the writer of record for cohort state. The engine reaches it through that module and never around it; this record grants no direct engine write to `state.json`.

## Consequences

**Positive:**

- The four events stop depending on a person executing a recovery table at the worst possible moment.
- One replay rule replaces the per-event conventions, so classification no longer differs by event.
- The authority question is settled before § 1's implementation begins, rather than discovered during it.

**Negative:**

- Four mutations leave the skill's explicit control, so a reader can no longer tell from the skill alone what wrote cohort state.
- ADR-0061's D3 and D4 stop being readable as current. The mirrored supersession field is the only thing that tells a reader so.

**Neutral:**

- ADR-0061 **D1** and **D2** are unaffected. The engine still owns legal phase ordering and guard enforcement; `loop-cohort.py` still owns execution state, counters, fingerprints and waves.
- This record decides authority, not schema. The marker shape, the unified transition history, its retention rule, and whether the `SCHEMA_VERSION` bump moves one constant or three belong to `docs/architecture/loop-parallelism.md` § 1. Specifying them here would create a second home that drifts from the first.

**Revisit if:** the effect registry needs an event whose effect is not a cohort mutation; or a direct engine write to `state.json` is proposed, which this record refuses.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** every engine call that mutates cohort state corresponds to an event in § 1's effect registry, and no engine code writes `state.json` outside `loop-cohort.py`.
- **Owner:** @eugenelim

## Alternatives considered

- **Leave the four events on the manual recovery protocol:** rejected. It depends on a person at exactly the moment a run has crashed, and it cannot be driven concurrently — which is the condition the rest of the parallelism work is built for.
- **Re-align the code to D3 instead of superseding it**, moving `apply_contract_amendment` back out of the engine: rejected. It would reopen the crash window that marker exists to close, and would have to be reversed again the moment the other four events need one.
- **Record it as a third erratum on ADR-0061:** rejected. RFC-0102 reserves errata for clarifying what a decision means; this reverses two clauses, which is a decision.
