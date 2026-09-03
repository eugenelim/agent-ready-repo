# Replicate authoring doctrine and reseal shaping gates

- **Status:** Draft
- **Level:** feature
- **Authority:** [RFC-0099 §7](../../rfc/0099-cut-before-adding-and-artifact-shaping.md); [spec/shaping-review-contracts follow-ons](../../specs/shaping-review-contracts/spec.md)

## Outcome

Maintainers can govern authoring contracts through evidence-backed, RFC-0099-compliant rules.

## Opportunity

The evidence-home hypothesis was reverted before replication, and the current work-loop re-drafting route does not yet carry the RFC-0099 shaping gate or its two remaining execution-side errata.

## What this absorbs

### spec-criteria-grounding-evidence-home

This is a hypothesis, not accepted work. Acceptance criteria may attract a third content category: evidence that a mechanism is correct, such as a control's arity, a field nothing else reads, or the measurement a bound came from. The two-way outcome/mechanism split gives that evidence no home, so it can be duplicated in the criterion and plan task and drift. The proposed home is `Assumptions`, with a source cited by the criterion.

The idea was spiked on 2026-09-01 in core 2.22.0 at `7478c8d25` and reverted the same day. On the abandoned `work-loop-next-projection` contract, 12 of 16 findings were single-clause drift. Applying the split cut criteria prose 21% and raised the criterion count from 29 to 37 because grounding left and hidden conjunctions came apart. The spike did not earn doctrine: `n=1`; the subject was abandoned days later for an unrelated deeper defect; sustained findings after the split were 21, 17, and 18; blockers were 6, 8, 5, and 3; the causal claim “no home, therefore duplicated” was inferred rather than tested; an 18k-word contract pair may duplicate facts regardless of a home; the split introduced absent or wrong assumption citations needing a mechanised check; and the shipped worked example came from the abandoned contract with a line-number citation no reader could follow. The spiked text is in history at `7478c8d25`; it was reverted at `d73597ae2`'s successor.

Re-spike only after before/after measurement on two or three unrelated specs authored by different sessions, with at least one reaching approval; a test of the causal step rather than correlation; and a worked example grounded in a shipped, stable artifact with no line-number citation. The original inspection was indeterminate because required rule lookup was refused; current evidence that settles the hypothesis is the stated replicated measurement and causal test.

### rfc0099-execution-side-errata

Implement the two remaining execution-side RFC-0099 errata from `docs/specs/shaping-review-contracts/spec.md#follow-ons`: a root-cause-cluster checkpoint after adjudication, and a touched-seam cleanup versus neighbouring-module boundary across work-loop, implementer, adversarial review, and quality review. Claim minimization has shipped. Re-measure `CAT-S003` headroom first; `work-loop/SKILL.md` is currently 832 lines. The original inspection was indeterminate because required rule lookup was refused; a current measurement of that headroom and the named follow-ons settles scope.

### amendment-redraft-shaping-gate

RFC-0099 section 7 puts `shaping-reviewer` at step 2 of drafting, so a post-seal correction re-entering that sequence owes a shaping pass. The work-loop drives `SPEC-PLAN-DRAFTING` in-loop rather than through `new-spec`; therefore the gate added to `new-spec` in PR #1171 does not cover it. `references/delivery-contract-lifecycle.md` has zero occurrences of `shaping`. Until this lands, an amendment reseals without the cold contract review RFC-0099 requires. This was re-homed from archived `docs/specs/sealed-baseline-replacement/`; it carries no state, schema, or transition change and belongs to the next change touching the work-loop re-drafting path. Any `work-loop/SKILL.md` addition must respect `CAT-S003` body-line headroom. The original inspection was indeterminate because required rule lookup was refused; direct inspection of those paths and RFC-0099 section 7 settles it.

## Assumptions

- The evidence-home premise needs a dated replication across two or three unrelated specs, including one approved spec, plus a causal test before authoring doctrine changes.
- The RFC-0099 execution and amendment premises need a current `CAT-S003` measurement and inspection of the named execution paths because the earlier rule lookup was refused.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
