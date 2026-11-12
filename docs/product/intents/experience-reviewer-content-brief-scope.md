# Extend experience-reviewer to review content briefs

- **Slug:** `experience-reviewer-content-brief-scope`
- **Status:** Fulfilled
- **Fulfilled:** 2026-11-12 eugenelim: content briefs and current brand registers receive findings-only direction review with marketing exclusions preserved, proven by 40 targeted tests and two source-loaded reviews.
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Governed by:** [RFC-0062 OQ1](../../rfc/0062-content-design-and-copy-direction-skills.md)

## Outcome

`experience-reviewer` admits `type: content-brief` artifacts and current brand
registers identified by both `type: tone-of-voice` and `scope: brand-level`. It
reviews grounded direction and coherence through read-only findings.

## Opportunity

The reviewer’s description, introduction, and admission list omitted these
direction artifacts. Its marketing clarity lens already excluded them; that
exclusion must remain, even on a brief with `communication_mode: product-copy`.

## What this absorbs

### experience-reviewer-content-brief-scope

RFC-0062 OQ1 recorded this follow-on and suggested a further RFC. The accepted
Readiness decision chooses a direct-light reviewer-scope edit instead; no
follow-on RFC is part of this authorized slice. Both deferred producer handoffs
are replaced with fresh-context review handoffs. The scope includes current
brand registers as well as content briefs.

## Assumptions

- The shipped `content-design-skill` makes this reviewer-scope follow-on actionable.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 768c0a90b87e635220c3c784d7cdae67644d7e1d

## Readiness

Route: direct-light under the explicit implementation brief. Update the agent’s
description, introduction, admission list, and applicable direction lenses;
replace both deferred content-design handoffs, extend the eval and roster
contract, and document the scope in the pack README. Preserve marketing
exclusions, read-only findings, code/architecture exclusions, and finding anchors.
Do not include `xd-state-reviewer-doctrine`.

**Proof:** producer/reviewer content contracts and the pack’s creative-direction
and design-system suites. Live independent review of a product-copy content
brief and a current brand register must flag seeded direction/coherence defects
without rewriting or marketing-clarity findings. The declared agent proof is
review-list output plus manual dispatch; activation eval definitions alone do
not satisfy live review proof.

## Outcome note

End state: a content brief produced by `content-design` receives an experience review like any other design artifact.

## Non-goals

- Reviewing code, or architecture documents.
- Rewriting content briefs; the reviewer flags only.
- A follow-on RFC; this is a reviewer-scope edit.

**Riskiest assumption:** adding the content-brief type does not make the marketing-clarity lens fire on briefs. Tested agent-only by an eval case with a content brief that must not trigger that lens.
