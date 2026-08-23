# ADR-0093: OKF reference corpora remain governed build-time sources within their owning pack

- **Status:** Accepted
- **Date:** 2026-08-21
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0087; ADR-0071

## Decision summary

- **Decision:** We will author inert OKF reference corpora inside their owning pack and compile them at build time into ordinary same-pack Skill references.
- **Because:** progressive knowledge disclosure must remain portable, deterministic, and usable from a user-scope pack install without adding runtime or cross-pack authority.
- **Applies to:** reference-only OKF bundles using `agentbundle-okf/v1`, beginning with the architect pack's `architecture-lenses` corpus and the existing security-checklists pilot.
- **Tradeoff accepted:** canonical source and generated delivery files coexist in the catalogue, and every source change requires deterministic regeneration.
- **Revisit if:** an accepted use case requires cross-pack composition, runtime knowledge retrieval, executable Playbooks, or a public OKF runtime contract.

## Context

RFC-0087 introduced OKF as an experimental authoring and deterministic
projection format. Its original cost-engineering and security-checklists pilots
proved compiler behavior, adapter preservation, routing observations, and
cross-platform check-mode verification. The architect assessment work added a
larger reference-only pilot: 47 concepts arranged behind nine progressive
indexes and consumed by assessment, design, and review workflows.

The architect pack must remain useful when installed alone at user scope. Moving
the corpus into `core`, or resolving it dynamically from another pack, would
make the new workflows depend on content an architect-only installation does
not receive. Copying the knowledge into each workflow would preserve
installation independence but restore the duplication and routing drift that
the corpus is intended to remove.

The pilot evidence supports a narrow build-time knowledge-source decision. It
does not establish a need for runtime OKF discovery, remote retrieval,
executable Playbooks, or a new adapter primitive.

## Decision

**We will keep each reference-only OKF corpus as a governed canonical authoring
source inside its owning pack and compile it at build time into ordinary
same-pack Skill references.**

For each admitted corpus:

- canonical concepts and indexes live under the owning pack's `okf/<bundle>/`
  tree;
- the pack manifest declares the bundle and its generated router ownership;
- the catalogue compiler produces a router, hierarchical indexes, reference
  copies, and a managed-output manifest under that same pack;
- workflow Skills consume the generated same-pack reference surface through
  bounded progressive routing rather than loading the whole corpus;
- generated output is replaceable build output and is never edited directly;
- installed workflows use the compiled Skill references and require no runtime
  compiler, OKF loader, core-pack lookup, or cross-pack knowledge resolution;
- reference corpora remain inert: they may inform reasoning but cannot declare
  tools, executors, attesters, remotes, or Playbook authority.

`agentbundle-okf/v1` remains a governed catalogue authoring profile. This
decision accepts its reference-only build-time use; it does not create a public
runtime API, general remote-discovery contract, or automatic right to publish
other OKF content types.

## Decision drivers

- Keep a user-scope pack install self-contained.
- Give multiple same-pack workflows one maintained knowledge source without
  giving knowledge content workflow authority.
- Preserve progressive disclosure for large, nested corpora.
- Make projection deterministic, reviewable, and fail-closed in CI.
- Avoid adding runtime dependencies, network retrieval, or adapter behavior for
  an authoring-time concern.

## Consequences

**Positive:**

- Architect assessment, design, and review can share neutral architecture
  knowledge without a core or cross-pack dependency.
- Maintainers update one canonical concept and regenerate every same-pack
  consumer surface deterministically.
- Installed workflows receive ordinary portable Skill files and need no special
  runtime support.
- Generated ownership, path validity, and prohibited authority can be checked
  mechanically.

**Negative:**

- Canonical source and generated reference copies both occupy the catalogue.
- A concept change is incomplete until the owning pack is regenerated and its
  compiler, routing, and consumer-parity gates pass.
- The pattern deliberately does not deduplicate knowledge across independently
  installed packs; a genuinely shared corpus would require a separate decision.
- Runtime freshness and organization-specific context remain the responsibility
  of the consuming workflow's authorized evidence surfaces, not the OKF bundle.

**Revisit if:** an accepted use case requires cross-pack composition, runtime knowledge retrieval, executable Playbooks, or a public OKF runtime contract.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:** compiler check mode is clean; generated-path ownership and pack-dependency gates pass; frozen routing and consumer-parity tests resolve only owning-pack paths; user-scope pack metadata declares no knowledge dependency on another pack.
- **Owner:** maintainers of each pack that declares a reference-only OKF bundle

## Alternatives considered

**Place reusable reference corpora in `core`.** Rejected because an
architect-only user-scope installation cannot rely on core content and the
result would introduce a cross-pack delivery dependency.

**Resolve OKF bundles dynamically at runtime.** Rejected because it adds a new
runtime, versioning, failure, and trust boundary when static build-time
projection already satisfies the accepted use cases.

**Keep hand-authored copies in every workflow.** Rejected because duplicated
concepts drift, weaken progressive routing, and make provenance and lifecycle
maintenance inconsistent across consumers.

**Project executable Playbooks alongside references.** Rejected because the
pilots prove inert knowledge routing, not execution authority. Playbook
projection would require its own security and governance decision.

## References

- RFC-0087: OKF knowledge projection and its pilot evidence requirements.
- [`docs/rfc/0087-notes/pilot-results.md`](../rfc/0087-notes/pilot-results.md)
- [`packs/architect/okf/architecture-lenses/`](../../packs/architect/okf/architecture-lenses/)
- ADR-0071: `.apm/` is the runtime export boundary and pack tests remain pack-owned.
