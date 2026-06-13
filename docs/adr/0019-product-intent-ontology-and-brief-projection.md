# ADR-0019: Product shaping is a recursive level-tagged `intent` tree; a brief is a feature-intent projected onto one repo; contracts mature by stage

- **Status:** Accepted <!-- Proposed | Accepted | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-06-13
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0030 (the product-engineering pack — the decision this records) · ADR-0009 (the brief layer this reframes) · ADR-0008 + RFC-0017 + RFC-0018 (the contract-authoring seam this stages) · RFC-0019 (receive-brief)

## Context

RFC-0030 (Accepted 2026-06-13) introduces an opt-in `product-engineering` pack — the upstream the catalogue lacked, where product intent is shaped, de-risked, and decomposed into the specs `core` already builds. That pack needs a single artifact model, and several forces constrain it:

- **Scale spans two orders of magnitude.** The same discipline must serve a solo dev shaping one feature and a business unit shaping a capability that fans out across many distributed component repos. A model fixed to one altitude fails one end.
- **It must compose with what exists, not duplicate it.** `core` already owns the brief layer (ADR-0009) and `receive-brief` (RFC-0019); the contract-authoring seam already exists (ADR-0008, RFC-0017/0018). The pack must extend these, not fork them.
- **Trackers are heterogeneous and shallow.** Linear is lean (Initiative→Project→Issue, no Epic/Feature type); Jira Align is deep (Theme→Epic→Feature→Story). The *same* canonical unit lands at different levels in each; neither has a native home for "outcome" or "opportunity."
- **The AI-era build unit is the spec/vertical-slice, not the user story** — one feature maps neither 1:1 to value nor 1:1 to a story, so a model that reifies the epic→feature→story pyramid encodes a falsehood.
- **The repo boundary is the spec-context boundary** — an implementable spec needs its target component repo's full context (architecture, conventions, code, contracts), so a cross-component feature cannot be specced upstream; it must be sliced per repo and completed there.

## Decision

**We model product shaping as a recursive, level-tagged `intent` tree whose leaf is a shippable spec/slice; a brief is a feature-level intent projected onto a single repo; and the integration contract matures by SDLC stage rather than being pinned up front.**

Three parts:

1. **The `intent` ontology.** An `intent` is recursive and carries a `level` tag. It holds `{outcome, opportunity, assumptions}` as fields; its children are **either lower-level intents or, at the leaf, specs/slices**. A capability intent, a feature intent, and a PRD are therefore the *same artifact at different levels* (a PRD is a feature-level intent rendered as a document) — not three types. Decomposition is recursive (one level down at a time); assumptions are de-risked per intent at its own level. The tree is **deeper than any tracker** and projects **one-way** to trackers via per-mode profiles (a lean tracker collapses it, a deep tracker expands it); trackers are renders, never the source.

2. **A brief is a feature-level intent projected onto one repo.** At app scale the projection is identity (the intent *is* the brief, in the same repo). At BU scale it is a per-component slice (one brief per component repo). Because every repo receives its own projection regardless of whether the product pack is installed upstream, **`receive-brief` stays in `core`** as the universal receiver, and the product pack is only the optional upstream author/slicer. **`receive-brief` is level-agnostic by construction** — it always receives a brief *for its own repo* — so a brief carries **no `level:` field** and an app-scale feature intent *is* an ordinary `core` brief with no new field. The only ever-needed addition is an optional `parent-intent:` provenance back-pointer at **BU scale** (so a cross-repo slice can name its parent capability intent), carried like the existing `Epic:` coordinator pointer and never interpreted by `receive-brief`. `core` imports nothing from the pack and stands alone. *(This refines RFC-0030 §5's brief-field list — which named `level:` — per owner direction 2026-06-13: levels live in the intent tree, not in the brief.)*

3. **Contract maturity is staged.** behavioral intent @intent (example-shaped, no fields) → interaction/consumer-expectation contract @brief (CDC-shaped, not a full schema) → **detailed wire contract @spec** (design-first, reusing the ADR-0008 / RFC-0017/0018 `Contract:` seam at `new-spec` step 4b) → verify @build. The detailed contract is pinned at the spec stage, where full component context lives — not at intent.

This ADR records the decisions; the v1 spec (`docs/specs/product-engineering-pack/`) and the implementation follow. The business-unit, cross-component value-stream layer is deferred to a phase-2 spec (RFC-0030 Appendix A).

## Consequences

**Positive:**
- One model spans solo→BU; recursion handles arbitrary depth without new artifact types.
- Composes cleanly: the leaf spec *is* `core`'s `spec.md`; the brief *is* `core`'s brief; the wire contract reuses the existing seam — the pack is purely upstream and adds no duplication.
- Trackers become lossy projections of a canonical tree (the OpenAPI→codegen shape), so the tooling never dictates the product model, and Linear/Jira Align are both reachable from one source.
- `core` stays standalone (additive optional fields only), so pure-engineering repos are unaffected.
- Pinning the wire contract at the spec stage avoids both premature lock-in and late-integration surprises.

**Negative:**
- `intent` is a mildly-novel unifying noun (anchored to "strategic intent"); it is the one term adopters must learn.
- One-way projection means no round-trip tracker sync — status changes made in the tracker do not flow back (deliberate; bidirectional sync corrupts across mismatched hierarchies).
- The recursion adds conceptual surface over a flat work-item list.
- The pack is mined from `ai-product-kit` by hand, a standing manual-sync cost.

**Neutral / to revisit:**
- The BU-scale cross-component meta-repo (and the canonical home for a cross-repo shared contract) is deferred to phase 2; this ADR commits only to the projection/reference shape, not the authority location.
- The contract-authority home (meta-repo vs dedicated contracts repo vs schema registry) is org-specific and intentionally left open.

## Alternatives considered

- **Fixed work-item types (SAFe ladder: epic→capability→feature→story).** Rejected: the levels disagree across tools (a Jira "Epic" is a Jira Align "Feature"), and reifying the pyramid encodes the story=spec falsehood.
- **A flat fixed object set (e.g. outcome/opportunity/bet/spec/story).** Rejected: it can't express arbitrary decomposition depth, which the BU/platform case needs.
- **A tracker-native model (model the work in Linear or Jira Align directly).** Rejected: the tool dictates the product model, and neither tracker has a home for outcome/opportunity.
- **Pin the detailed wire contract at the intent stage.** Rejected: premature lock-in (Hyrum's Law / Postel tension) before the owning team has full context.
- **Bidirectional tracker sync.** Rejected: silent drift/corruption across mismatched hierarchies; one-way projection is the safe default.
- **Put the receiver (`receive-brief`) in the product pack.** Rejected: component repos always have `core` but may not have the product pack, so the receiver must be universal — it stays in `core`.

## References

- RFC-0030 — the accepted proposal, with the pressure-tested research and the Phase-2 appendix.
- ADR-0009 — the brief layer this reframes as a projection.
- ADR-0008, RFC-0017, RFC-0018 — the contract-authoring seam this stages.
- External anchors (per RFC-0030, author-verified): Backstage Domain→System→Component→API; Linear / Jira Align object models; design-first / contract-first.
