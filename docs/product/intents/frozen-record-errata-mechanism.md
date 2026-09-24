# Correct frozen records through a licensed errata mechanism

- **Slug:** `frozen-record-errata-mechanism`
- **Status:** Fulfilled
- **Level:** feature
- **Owner:** eugenelim
- **Accepted:** 2026-09-24 by eugenelim, on an owner waiver rather than an independent shaping review. This intent reached a delivered state without ever passing `Draft` → `Accepted`, so the ratification is taken now rather than reconstructed from a review that never ran; the owner waived the intent-mode review that gate names, for this one-off migration only. Basis: `docs/specs/lifecycle-transition-contract/notes/migration-record.md`.
- **Fulfilled:** 2026-09-24 by eugenelim, on an independent fulfilment verification against the repository rather than against this artifact's own account. The ADR errata mechanism is shipped and machine-checked, not merely described: `new-adr/SKILL.md` licenses `## Errata` as the append-only correction section on an accepted ADR, the template's zone table names it, and `new-adr/scripts/lint-adr-shape.py` enforces the heading as rule `ADR-S015`. Record written by the 2026-09-24 corpus migration; the date is the verification's, because the artifact records no delivery date of its own.

## Outcome

Maintainers can add dated, additive corrections to frozen ADRs and related frozen records without rewriting historical bodies, and classify the maintained lifecycle of distribution adapters.

## Opportunity

The repository freezes ADR bodies and only licenses `## Errata` for RFCs, leaving known false references and discharged-deferral pointers without a permitted correction shape.

## What this absorbs

### adr-errata-convention

- **Authority:** [spec/pack-test-boundary-remaining-packs](../../specs/pack-test-boundary-remaining-packs/spec.md)
- ADRs have no errata mechanism. `docs/CONVENTIONS.md` freezes the body, and the shipped `new-adr` template says only the Status line moves, while `## Errata` is RFC-scoped in `packs/governance-extras/.apm/skills/new-rfc/SKILL.md`.
- ADR-0071 names deleted `packs/core/tests/pack/test-runtime-boundary.py` at line 74 and says a migration is partial when it is complete. Two other frozen records have the same staleness.
- Extend the errata convention to ADRs by amending `new-adr`'s `SKILL.md` and template plus `docs/CONVENTIONS.md`, bumping governance-extras, and filing the ADR-0071 erratum.
- This is a governance change and needs its own PR.
- **Unblocks when:** picked up.

### distribution-adapters-lifecycle-class

- **Authority:** [spec/frozen-doc-supersession-annotations](../../specs/frozen-doc-supersession-annotations/spec.md)
- `docs/specs/distribution-adapters/spec.md` is now explicitly `Shipped` with a Status-line supersession annotation. Commit `5fd1b93b2` (`docs(specs): annotate the frozen documents that relied on a superseded decision (#987)`) made that annotation.
- The original premise that its lifecycle remains undecided is stale. The document remains demonstrably maintained because adapter PRs amend its Changelog and projection table.

## Assumptions

- The lifecycle premise changed: `distribution-adapters` is explicitly Shipped with a Status-line annotation, not undecided.
- ADR-0083's comparison table at line 72 and deferred-items list at line 201 have a 2026-08-18 dangling pointer to shipped `spec/npm-dependabot-wiring`, whose `[backlog].open` entry was deleted; this is the second concrete errata instance.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
