# Loop-contract item identity mechanism

- **Slug:** `loop-contract-item-identity-mechanism`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Kind:** outcome
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:work-loop-delivery-efficiency

## Outcome

- **Steerable input:** A rule duplicated into a second authoring surface, or a criterion changed without its verifications following, is flagged by a check, and the set of single-homed rules follows from the rules themselves rather than from a hand-kept list.
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

## Riskiest assumption

**Riskiest assumption:** the pinned set derived from rule identifiers equals the hand-declared set of 30 rules with no loss of coverage. Tested agent-only: the existing 57 tests pass on the derived set, and deleting any one identifier marker fails a named test.

## Non-goals

- Detecting a paraphrase: a fingerprint compares identity, not similarity.
- Any blocking behaviour.
- Authoring guidance, which `acceptance-criteria-set-construction` owns.
- Fingerprints and the suspect flag until a measured miss shows the derived set is not enough.

## Readiness

**Route:** new-spec, one slice, the cheap half only.

**First slice:** derive the single-homing pinned set from rule identifiers. Today `packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py` holds a hand-declared `RULES` tuple of 30 (name, surface, phrase) rows, and its 57 tests pass. The slice moves those names into identifier markers on the shipped sentences and builds the tuple from them.

**Agent-only proof:** the same 57 tests pass on the derived set, and a mutation that deletes one marker fails a named test. A rendered-page diff shows markers cost no visible text.

**Answers.** Markers go in HTML comments, which costs no readability. A fingerprint baseline and the suspect flag are not built: the evidence is one review cycle, and `docs/architecture/loop-contract.md` § 4 keeps them `STATUS: PLANNED`. Revisit them only after a measured miss that the derived set did not catch, and then commit the baseline beside the artifact and surface the flag in the review brief only.

## Source

- Mode: repo-origin
- Locator: docs/specs/acceptance-criteria-set-construction/spec.md
- Authority: repo-origin
