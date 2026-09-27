# Verification ledger: Frame-intent experience handoff

## Published-skill invocation — 2026-09-27

**Mode:** Read-only consumer invocation of the canonical published skill at
`packs/product-engineering/.apm/skills/frame-intent/SKILL.md`.

**Request:**

> Frame a feature intent for changing the subscription-upgrade confirmation so
> account owners can immediately see the effective plan, final price, billing
> date, and a server-issued confirmation reference after purchase. The current
> journey ends on an ambiguous loading state. Use only verified billing facts,
> and do not claim savings unless evidence supports it.

**Observed result:** A separate Codex CLI consumer completed successfully and
emitted the optional Product-to-experience handoff. Its output named the
post-purchase confirmation, first success across all four verified facts, the
server-issued reference as product proof, the billing response as evidence,
and constraints against inferred facts or unsupported savings claims.

**Product-fact groups observed:** All five: affected journey or surface; user
outcome and first-success behavior; product mechanism or proof; evidence for
user-visible claims; and constraints, prohibited claims, and material unknowns.

**Decision boundary:** The consumer selected no engagement mode, visual
direction, typography, color, layout, motion, first-viewport composition,
signature interaction, or implementation approach.

**Downstream invocation:** None. The consumer used only the canonical
`frame-intent` skill.

**Unexercised scope:** Owner and scale confirmation, domain-source validation,
current-state maps, roadmap checks, baselines, de-risking, and decomposition.
The complete captured run is retained at
`.context/frame-intent-experience-handoff/frame-intent-qa.log`.

## Fresh Codex consumer invocation — 2026-09-27

**Mode:** A fresh Codex subagent independently applied the canonical published
`frame-intent` skill read-only. It wrote no file and called no downstream skill.

**Request:** The same subscription-upgrade confirmation request recorded above.

**Observed result:** The feature qualified because it materially changes the
upgrade journey's visible success state and what that state must prove. The
consumer emitted the optional Product-to-experience handoff with these facts:

- **Affected journey or surface:** The post-purchase subscription-upgrade
  confirmation, replacing the ambiguous loading state.
- **User outcome and first-success behavior:** The account owner can confirm the
  effective plan, final price, billing date, and confirmation reference. First
  success is all four verified facts appearing for a completed purchase.
- **Product mechanism or proof:** A server-issued confirmation reference tied
  to the completed upgrade and its verified billing response.
- **Evidence for user-visible claims:** The completed-upgrade response supports
  the plan, price, billing date, and reference. No evidence was supplied for a
  savings claim.
- **Constraints, prohibited claims, and material unknowns:** Show only verified
  billing facts; do not claim savings without supporting evidence. Recovery
  behavior for a delayed or incomplete confirmation remains unknown.

**Decision boundary:** The result chose no engagement mode, visual direction,
typography, color, layout, motion, first-viewport composition, signature
interaction, or implementation approach.

**Downstream invocation:** None. The canonical skill supplied the product facts
without invoking or requiring Experience Design.

**Unexercised scope:** Scale and owner confirmation, current-state maps,
billing-domain sources, roadmap checks, baselines, quantified targets,
de-risking, decomposition, and optional independent shaping review.
