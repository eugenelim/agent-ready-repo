# Define the binder-publishing build contract

- **Status:** Draft
- **Level:** feature

## Outcome

The planned binder-publishing design has an implementation build specification beyond its existing gate-propagation contract.

## Opportunity

`docs/architecture/binder-publishing/` is planned, while `docs/specs/binder-publishing-gate-propagation/spec.md` only covers gate propagation and states that `binder-publishing` has no implementation or published interface change.

## What this absorbs

### binder-publishing-build-spec

- **Authority:** [binder-publishing architecture](../../architecture/binder-publishing/README.md)
- **Authority:** [RFC-0090 D3](../../rfc/0090-change-sizing-and-decomposition.md)
- The planned binder-publishing design has no build spec. The only existing spec is `docs/specs/binder-publishing-gate-propagation/spec.md`, whose line 8 says: `Contract: none — binder-publishing has no implementation, so no published interface changes here.`
- Apply RFC-0090's tail-triage lane to this design as the likely decomposition lens, given its size.
- **Unblocks when:** someone applies the tail-triage lane.

## Assumptions

- None.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
