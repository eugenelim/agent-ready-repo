# Close tracker write-back receipt and result contracts

- **Status:** Draft
- **Level:** feature

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
- The named `WriteBackResult` type no longer exists. Current processor-result types include `RemoteReceiptWriteResult` and `GuardedWriteResult`, both with unconstrained `code: str`; the gap remains while the old type name is stale.
- The work was deferred to avoid widening the reviewed surface after adversarial review round 2.

## Assumptions

- The processor-result premise changed: `WriteBackResult` has been replaced by `RemoteReceiptWriteResult` and `GuardedWriteResult`, each retaining unconstrained `code: str`.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
