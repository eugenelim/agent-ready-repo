# Close tracker write-back receipt and result contracts

- **Slug:** `tracker-writeback-result-contracts`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Parent intent:** capability:external-tracker-projection

## Outcome

Tracker write-back boundaries reject receipt-shaped impostors and expose deliberate, closed result-code vocabularies for each processor result type.

## Opportunity

The guarded-write boundary accepts a structurally matching receipt without a shared runtime identity, and processor result `code` values remain unconstrained strings.

## What this absorbs

### tracker-refresh-receipt-runtime-identity

- **Authority:** [spec/tracker-refresh-writeback AC25](../../specs/tracker-refresh-writeback/spec.md)
- The Jira guarded-write receipt check verifies status, action, and target structurally rather than by runtime class identity, so an in-process caller can supply a receipt-shaped object.
- Make the check exact through a shared receipt runtime identity, using the same design required by the cross-loaded store.

### tracker-refresh-processor-result-vocabulary

- **Authority:** [spec/tracker-refresh-writeback AC24](../../specs/tracker-refresh-writeback/spec.md)
- `RefreshResult` is closed through `RESULT_CODES` and the `refresh-result.schema.json` enum, but each processor result still has no closed result-code set, allowing typos to ship silently.
- A single shared `frozenset` would falsely authorize codes an adapter cannot return. Close each result type's vocabulary and define a deliberate shared base as a multi-file public-result-contract change.
- Processor-result types are `RemoteReceiptWriteResult` and `GuardedWriteResult` in `packs/core/.apm/skills/work-intake/scripts/refresh.py`, and `WriteBackResult` in each of the `jira-refresh` and `jira-align-refresh` processors under `packs/atlassian/.apm/skills/`. Each carries an unconstrained `code: str`.
- The work was deferred to avoid widening the reviewed surface after adversarial review round 2.

## Assumptions

- Every processor-result type (`RemoteReceiptWriteResult`, `GuardedWriteResult`, and each Jira processor's `WriteBackResult`) carries an unconstrained `code: str`.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

## Current truth

Verified 2026-11-05: `RemoteReceiptWriteResult` and `GuardedWriteResult` in `refresh.py` each carry an unconstrained `code: str`; `RefreshResult` validates against `RESULT_CODES` at construction.

## Readiness

- **Route:** new-spec. Two independent parts, one session each if the owner prefers.
- **First slice:** a closed code set per result type, validated at construction like `RefreshResult`, covering the core types and each Jira processor's `WriteBackResult`.
- **Second slice:** receipt runtime identity, tested with a receipt-shaped impostor.
- **Agent-only proof:** unit tests; a typo code raises.
- **Manual dependency:** none.

## Non-goals

- A single shared result-code set across result types; it would authorize codes an adapter cannot return.
- Tracker transport changes and the `RefreshResult` vocabulary, which is already closed.

## Riskiest assumption

**Riskiest assumption:** a per-type closed set covers every code each adapter actually returns today. Tested agent-only by collecting the codes each result type emits across the existing test suites and the source, and asserting each is in its set before the set is enforced.
