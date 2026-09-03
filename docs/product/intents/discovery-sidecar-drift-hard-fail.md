# Discovery sidecar drift hard fail

- **Status:** Draft
- **Level:** feature
- **Authority:** [RFC-0048 Decision 7](../../rfc/0048-autonomous-product-team-operating-model.md)

## Outcome

Traceability lint rejects a discovery sidecar whose on-disk edge set drifts from `_state/traceability.json`.

## Opportunity

The sidecar cross-check is warn-only with exit 0 because the `traceability.json` matrix schema was previously RFC-0048 doctrine rather than a pinned implementation contract.

## What this absorbs

### sidecar-drift-hard-fail

Promote matrix-to-artifact sidecar drift from warn-only to a hard violation now that the discovery-loop sidecar schema is reported as pinned at version 0.1. Update the traceability-lint contract and tests that still describe the schema as unpinned. The current cross-check compares `_state/traceability.json` with the on-disk edge set and stays warn-only with exit 0 because a hard failure against an undefined schema would be dead code or a false-positive generator. The recorded fix is to promote sidecar drift from warn to hard violation with exit 1 in `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py` once the RFC-0048 Decision-7 spike pins the `traceability.json` schema. Unblocks when the sidecar schema is pinned by the RFC-0048 Decision-7 spike and the hard-failing check, contract, and tests land.

## Assumptions

- Local evidence is needed to establish that the RFC-0048 Decision-7 spike landed, that it pins the schema at version 0.1, and which traceability-lint contract and tests still describe it as unpinned.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
