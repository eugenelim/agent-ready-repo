# Loop-contract item identity mechanism

- **Status:** Draft
- **Kind:** outcome
- **Level:** feature
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** work-loop-delivery-efficiency — [Work-loop delivery efficiency](work-loop-delivery-efficiency.md)

## Outcome

- **Steerable input:** Build the mechanism [ADR-0108](../../adr/0108-opaque-append-only-loop-contract-identifiers.md) and [the loop contract](../../architecture/loop-contract.md) §§ 3–4 decided and nothing implements: derive the single-homing pinned set from rule identifiers rather than a hand-declared tuple, fingerprint each identified item, and route a changed item's dependants into the next re-review's scope.
- **Lagging outcome:** A rule duplicated into a second authoring surface, or a criterion edited without its verifications following, is caught by a check rather than by whoever happens to read carefully.
- **Guardrail:** The suspect flag scopes what a review looks at and never decides whether a change may proceed. Blocking on a derived signal rebuilds the consequence-bound blocking already measured and killed in [work-loop review economics](work-loop-review-economics.md).

## Opportunity

Single-homing is enforced today by asserting that each of a hand-listed set of exact phrases appears in one authoring surface and not the other three. That leaves three gaps: a rule sentence nobody pinned is checked by nothing, a paraphrase in a second location is invisible, and a repeat inside one file is never counted. Identifiers close the first and third; fingerprints bound the second by flagging the next edit to either location.

Separately, four of the five findings in one review cycle were a criterion changed without its references following. That is the same mechanism from the other side: a fingerprint over an item's text is what makes its dependants suspect.

## Boundary

- Includes the identifier markers on shipped rule sentences, deriving the pinned set from them, per-item fingerprints and their baseline, and the edge from a suspect flag into re-review scope.
- Excludes detecting a paraphrase. A fingerprint compares identity, not similarity, so a reworded second home has its own fingerprint and is not recognised as a duplicate. That residue stays with review.
- Excludes any blocking behaviour.
- Excludes authoring guidance. [`docs/specs/acceptance-criteria-set-construction/`](../../specs/acceptance-criteria-set-construction/spec.md) owns which obligations become criteria, where a fact lives, and how a finding is answered; this intent owns only the checking mechanism beneath it.

## Owner

- eugenelim, Platform Core maintainer.

## Unresolved questions

- Does an identifier marker on shipped, adopter-facing rule prose cost more in readability than it returns in checkability?
- Is the fingerprint baseline committed beside the artifact, or derived from git history?
- Does the suspect flag surface in the review brief, in a lint, or both?

## Source

- Mode: repo-origin
- Locator: docs/specs/acceptance-criteria-set-construction/spec.md
- Authority: repo-origin
