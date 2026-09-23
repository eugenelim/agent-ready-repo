# Brief: Digital Experience Doctrine completion

- **Slug:** `digital-experience-doctrine-completion`
- **Received:** 2026-09-03
- **Owner:** Repository maintainers (`ini-003`)
- **Status:** Draft
- **Authority:** [RFC-0071 § Implementation sequence](../../rfc/0071-digital-experience-doctrine.md)
- **Intent:** [Digital experience doctrine](../intents/digital-experience-doctrine.md)

## Outcome

One brief now coordinates the work left under Digital Experience Doctrine. It
keeps three groups apart: the seven intent outcomes, loose ends between packs,
and improvements inside one pack. Each item has one owner. Closed work can leave
the list, and pack craft cannot silently widen the doctrine.

## Success metrics

- Seven intents show the remaining outcomes.
- The dependency order is clear. It does not imply that an intent is ready for a spec or implementation.
- Every inherited seam gap points to a delivery owner or a route outside this brief.
- A fresh repository check can remove a stale row without losing its live follow-on.
- Product-strategy adoption and product-engineering shaping follow the shared contract as M2a and M2b.
- XD foundations and IA are M3b and M3c after M3a. State and reviewer doctrine is M3d after M3c.
- Cross-pack evaluation is M5 after M2–M4. Integrative guides are M6 after M5.

## Scope / Non-goals

**In scope**

- [Product strategy adoption doctrine](../intents/product-strategy-adoption-doctrine.md)
- [Product engineering shaping doctrine](../intents/product-engineering-shaping-doctrine.md)
- [Design system foundations](../intents/xd-design-system-foundations.md)
- [Information architecture archetypes and objects](../intents/xd-ia-archetypes-objects.md)
- [Experience state and reviewer doctrine](../intents/xd-state-reviewer-doctrine.md)
- [Cross-pack experience evaluation](../intents/cross-pack-experience-eval.md)
- [Digital product integrative guides](../intents/digital-product-guides-update.md)
- Coordinating the three seam candidates in [Completion inventory](#completion-inventory): frontend experience composition, an executable handoff resolver, and repair of the contract journey pages.

**Non-goals**

- Proposing specs or plans for any of these intents.
- Growth operations, unrelated packs, and changes to discovery-loop, work-loop, or new-spec logic. RFC-0071 places them outside its scope.
- Expanding craft inside `experience-design` or `frontend-engineering` just because a repository review found a gap. [Adjacent work](#adjacent-work) routes those items, and they do not count toward this brief.
- Reopening [`tech-site-completion`](tech-site-completion.md) or forcing the
  documentation and marketing sites to share tokens.

## Completion inventory

This is the doctrine queue. It records the next decision and links to the file
that owns changing facts. It does not repeat lifecycle status.

| Candidate | Durable evidence | Remaining outcome | Next decision |
| --- | --- | --- | --- |
| Seven-intent doctrine family | [Parent intent](../intents/digital-experience-doctrine.md#the-family-this-parents) and the seven intent files listed above | Shape the remaining RFC-0071 outcomes without fabricating spec readiness | Continue each intent through its own shaping gate |
| Frontend experience composition | [`frontend-experience-composition`](../../specs/frontend-experience-composition/spec.md) and its canonical `workspace.toml` entry | Give XD and frontend engineering one state-coverage map and proportional depth ladder | Confirm whether this existing spec is a delivery slice of this brief; if so, add the reciprocal `Brief:` link and the Spec map entry together |
| Executable design-handoff resolution | [`design-handoff-read` follow-ons](../../specs/design-handoff-read/spec.md#follow-ons) | Replace prose-only path resolution with one executable resolver; close the unbounded reserved-tree set, add a product discriminator, and measure the waived control families including matching-type replacement | Decide whether these residuals form one independently shippable slice; the four files under `docs/design/direction/`, including the invalidated `type: design-system` record, are current evidence for the product-discriminator case rather than a separate queue item |
| Contract journey projections | [`digital-experience-contract` criteria](../../specs/digital-experience-contract/spec.md#acceptance-criteria) and the parent intent's recorded assumption | Make the three journey projections tell the truth about the Digital Experience Contract | Route as a bounded repair: the criteria require the phrase in `product-strategy.md`, `experience-design.md`, and `core.md`, while the current files contain no hit |

## Repository re-check — 2026-09-22

| Incoming row | Finding | Queue effect |
| --- | --- | --- |
| `design-handoff-read` | The spec owns the delivery state; only its resolver and identity follow-ons remain unowned | Drop the delivery row; retain only its live residual |
| S3 frontend truth-up | The current artifacts no longer contain the listed stale claims or literal eval paths; the 16-case `test_public_claims_match_shipped_behaviour.py` suite pins the README, five-gate procedure, CWV boundary, example output, and notification-panel route | Remove |
| S5 XD half | [`aesthetic-style-direction`](../../specs/aesthetic-style-direction/spec.md) contains the direction sheet, fifteen axes, counterfactual gate, and divergence audit | Remove the XD half; route only the frontend half below |
| S4, S5 frontend half, and S6/S7 | The named motion primitives, cross-build fingerprinting rules, modern primitives, and pack-local runnable inspection harness remain absent | Route outside this brief to the frontend-craft and rendered-evidence candidates below |
| S8a reference deduplication | Re-measurement remains 31 files / 24 hashes: containment 5/1; layout 12/9; editorial gates 3/3; interrogation 3/3; four other pairs 2/2 | Route outside this brief to reference reconciliation below |
| S9 post-launch marketing | Conversion measurement operations, pricing-specific doctrine, experimentation, and SEO remain outside RFC-0071 | Route to [`growth-strategy-pack-charter`](../intents/growth-strategy-pack-charter.md) |
| Floating site work | `StatStrip` is absent; the homepage receives `/now/` through shared navigation; the docs palette is intentionally self-contained, so token divergence and a web-only `--ds-focus-ring` are not sync defects | Remove; reopen only on a demonstrated emitted-site failure |

## Adjacent work

These are intake candidates, not delivery slices. Each needs its own admitted
intent. None affects this brief's coverage or closure.

| Candidate owner | Absorbs | Decision discriminator |
| --- | --- | --- |
| `frontend-experience-craft-completion` | S4 motion/emotion; the frontend half of S5 anti-sameness/composition; absent modern CSS and native-platform primitives from S6 | Decide whether these gaps produce one user outcome or need separate motion, composition, and platform-capability intents |
| `frontend-rendered-evidence-runtime` | The raw browser snippet without a pack-local runnable harness, plus the authority needed for an independent experience reviewer to inspect rendered output | Decide whether a portable harness can improve execution without adding a required browser dependency or weakening the named-skip path |
| `experience-design-reference-reconciliation` | S8a's eight duplicate-basename families | Reconcile meaning, not filenames: only identical semantics should share a source; the 31/24 measurement rules out a mechanical dedup sweep |

S9 already has an owner in
[`growth-strategy-pack-charter`](../intents/growth-strategy-pack-charter.md).
The `docs/design/direction/` collision supports the handoff discriminator and
resolver. It is not a fourth adjacent item.

## Constraints / Appetite

- Keep the seven-intent family and at most three seam candidates here. Route work inside one pack elsewhere.
- Do not create a spec until its slice can ship on its own and a human confirms it.
- Do not copy changing status or proof into prose. Link to the owning intent, spec, workspace entry, or test.
- Prefer one candidate per outcome. A shared folder or similar wording is not enough to merge work.

## Assumptions / Risks

- Another session is editing the `frontend-experience-composition` spec, plan, and workspace entry. This brief does not touch them or treat the edits as approved.
- The motion, anti-sameness, modern-CSS, and harness rows are gaps, not accepted product intents. Their user outcome and bounds still need framing.
- Reference reconciliation needs judgment. Equal names do not prove equal contracts. Unequal hashes do not prove useful differences.
- The journey-page mismatch is a contract defect, not a new doctrine outcome. Its repair should stay inside the owning projection path.

## Ready gaps (Draft only)

- Confirm or reject the three seam candidates in the Completion inventory.
- If `frontend-experience-composition` belongs here, update its `Brief:` field and this Spec map together. Wait for the other session's edits to settle.
- Admit, merge, or reject the three adjacent candidates. Do not carry raw S-labels for the long term.
- Run a revision-bound shaping review after those decisions.

## Governance references

- [RFC-0071 Digital Experience Doctrine](../../rfc/0071-digital-experience-doctrine.md)
- [Digital experience doctrine intent](../intents/digital-experience-doctrine.md)
- [`design-handoff-read`](../../specs/design-handoff-read/spec.md)
- [`digital-experience-contract`](../../specs/digital-experience-contract/spec.md)

## Proposed slices

The three rows in Completion inventory are candidates only. Recording them does
not confirm the cut.

## Spec map

Empty. A candidate enters only after a separate slice decision and a link back
from the spec.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
