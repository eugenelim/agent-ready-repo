---
name: conversion-design
description: "Use when designing a marketing surface — a landing page, product homepage, pricing page, or acquisition flow — where the primary goal is to convert a visitor into a lead, trial user, or customer. Triggers on 'design the landing page', 'structure the homepage', 'what goes above the fold', 'convert visitors', 'design the pricing page', 'product marketing surface'. Produces IA and structural specifications for conversion surfaces. Do NOT use for product UI design (use user-flow + interaction-design), documentation surfaces (use documentation-design), or analytical dashboards (use analytical-design). Surface genre: marketing."
---

# Skill: conversion-design

Converts the content brief and design-principles artefact into a **structural specification for a marketing surface** — the above-fold contract, the scroll story, and the social-proof architecture that carries a visitor from "not sure" to "ready to act." This skill is IA and structure; it does not write copy (that is `content-design` and `tone-of-voice`) and does not derive tokens or color (that is `design-system` and `creative-direction`).

## When to invoke

Confirm all three before specifying:

1. **The surface goal is acquisition or conversion** — the primary measure is whether a visitor takes a defined next action (trial, sign-up, purchase, demo request). If the primary goal is informational, use `informational-design`.
2. **A content brief exists or can be elicited** — `content-design` defines what each section must accomplish; conversion-design defines where each section sits and what the visitor's eye should hit first.
3. **Design principles exist** — the principles arbitrate structural choices (which hero type, which proof tier) so decisions are grounded, not gut-feel.

## Hero approach selection (5 types)

Choose one hero type based on the product's awareness stage and the dominant buyer psychology:

1. **Statement hero** — leads with a conviction statement the reader immediately agrees or disagrees with. Best when product category is understood; awareness is medium-high. Risk: vague statements read as noise.
2. **Problem-agitation hero** — leads with the reader's pain, amplified. Best when awareness is low and the category needs creating. Risk: must name a pain the reader actually feels, not the pain the company imagines.
3. **Social-proof hero** — leads with a credibility signal (customer count, recognizable logo wall, compelling testimonial). Best when the product is in a crowded category and trust is the primary objection.
4. **Demo-first hero** — leads with a live or animated product demo. Best when the product's interface IS the differentiator and seeing beats reading. Risk: requires the product to be visually legible without context.
5. **Narrative hero** — leads with a story or scenario the reader recognizes as their situation. Best for complex products where the category is unfamiliar or the use case requires imagination.

**IC-first principle:** whichever hero type is chosen, the reader's identified pain, goal, or situation must appear before the product's name or features. A hero that opens with the product's name fails the IC-first check.

## Above-fold 6-element spec

The above-fold zone carries exactly these six elements; their absence or conflation is a structural finding:

1. **Headline (≤10 words)** — the conviction statement; what the product does and for whom, in reader-benefit language.
2. **Subheadline** — one sentence expanding the headline: the mechanism or proof that makes the headline believable.
3. **Primary CTA** — one action, one label, one next state. Label names the reader's outcome, not the system's action ("Start building" not "Submit").
4. **Secondary CTA** — the lower-commitment option (watch a demo, see pricing, read a case study). Present only if the primary CTA asks for meaningful commitment.
5. **Proof signal** — one credibility element visible without scrolling: a recognizable customer logo, a specific number (not "thousands"), or a third-party rating.
6. **Friction microcopy** — one line that removes the dominant objection to clicking the primary CTA ("No credit card required" / "Cancel anytime" / "Takes 2 minutes").

## Scroll story — 7-zone structure

Each zone has exactly one job; assign content to zones before designing sections:

| Zone | Job |
|------|-----|
| 1. Above fold | Conviction + CTA (the 6-element spec above) |
| 2. Problem amplification | Name the cost of not solving the problem |
| 3. Solution fit | Show how the product solves specifically for the declared audience |
| 4. Proof | Social proof at the appropriate tier for the product's maturity stage (see Social proof hierarchy) |
| 5. How it works | Remove the "but how does it actually work" objection — process, not feature list |
| 6. Objection handling | Address the dominant objections before the CTA repeats |
| 7. Bottom CTA | Repeat the primary CTA for visitors who scrolled; add any final urgency or risk-reversal |

**One-job-per-zone rule:** a zone that does two jobs (proof AND objection handling) dilutes both. If content doesn't fit one zone's job, it needs its own zone or it is cut.

## Social proof hierarchy — by maturity stage

Tier the social-proof selection to the product's market maturity:

| Maturity stage | Primary proof tier | Secondary |
|----------------|-------------------|-----------|
| Pre-PMF / early | Specific outcomes from beta users; named case study; founder credibility | Number of users (if non-trivial) |
| Growth | Customer logos (recognizable in category); quantified outcomes | Press mentions in respected outlets |
| Scale | Analyst recognition; industry certifications; customer count with specificity | Net Promoter Score (if exceptional) |

Higher-tier proof on a lower-maturity product reads as fabricated. Match the tier to the actual stage.

## Numbered product tour spine

When a product tour section is warranted (zone 5), structure it as a numbered spine:

1. **Trigger** — what event or decision point causes the user to turn to this product?
2. **First action** — what does the user do first?
3. **Intermediate result** — what do they see after the first action that confirms they're on track?
4. **Primary outcome** — what does the finished state look like?

Each step names the product capability serving it; none reprints UI labels. The spine reveals the workflow, not the feature list.

## Canonical aesthetic reference tier (study subjects, not prescriptive tools)

For grounding creative-direction on a marketing surface, study how these sites handle conversion structure: Evil Martians (developer tools aesthetic), Linear (enterprise SaaS clarity), Vercel (demo-first product confidence). Internalize the structural philosophy — information hierarchy, proof placement, CTA legibility — not the surface treatment.

## Anti-patterns to refuse

- **Feature-list hero.** Lists of features above the fold are not a conviction statement; they assume the reader already cares. Move features to zone 3 (solution fit) where they answer a question the reader now has.
- **"We" language in the headline.** "We help companies do X" centers the company. "Do X faster" centers the reader. The headline belongs to the reader.
- **Proof without specificity.** "Trusted by thousands of teams" is noise. "Used by 12,000 engineering teams at Shopify, Stripe, and Notion" is proof. Specificity is the signal; vagueness is the absence of proof.
- **Above-fold without friction microcopy.** If the primary CTA asks for commitment (sign-up, trial, purchase) and there is no risk-reversal line, the dominant objection ("what am I committing to?") is unhandled.
