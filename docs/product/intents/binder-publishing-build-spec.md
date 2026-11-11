# Define the binder-publishing build contract

- **Slug:** `binder-publishing-build-spec`
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim

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

## Current state — checked 2026-11-05

`docs/architecture/binder-publishing/` is marked `STATUS: PLANNED`, no `packs/binder-publishing` exists, and the only spec, `binder-publishing-gate-propagation`, is Shipped with `Contract: none`. The design spans sixteen pages, and ADR-0073 fixes Zensical as the v1 renderer.

## Readiness

- **Route:** brief, but parked. Nothing here names a consumer or demand evidence, so do not decompose it until the owner names one.
- **Proposed slices when started, in dependency order:** (1) the `binder.toml` schema and the resolver that writes `binder-index.json`, standard library only; (2) the resolved-index contract and its validator; (3) the Zensical adapter, tested against recorded renderer output and never the live tool in a gate; (4) the security profile: fence neutralisation, path confinement, resource ceilings; (5) the skill, activation evals and pack wiring.
- **Agent-only proof for slice 1:** the unit coverage that `docs/architecture/binder-publishing/rollout.md` lists for configuration precedence, ordering, cycles and ambiguity.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
