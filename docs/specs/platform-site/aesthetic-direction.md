# Aesthetic Direction — agent-ready-repo platform site

**Surface:** responsive-web  
**Scope:** Full platform site — marketing anchor (`/`) + per-pack journey pages (`/journeys/`) + reference docs (`/docs/`). The marketing homepage is the primary surface; docs must be visually consistent but are a secondary surface.  
**Audience:** Senior engineers and engineering leads evaluating adoption of an AI operating model for their team.

---

## Surface treatment decision (Stage 1.5 — resolved)

**Alternating-band model.** Dark hero (product claim), light content sections (readable, enterprise-safe), dark footer (closure). Section transitions are hard-cut — not gradient fades. Confidence in the contrast is the design statement.

- **Hero and footer:** dark canvas `#0b0e12` (neutral-cool near-black — not warm-brown, not navy)
- **Content sections:** warm near-white `#fafaf9` (one-step warm offset, not clinical white)
- **Accent:** single chromatic — amber-gold family. Outside the indigo/blue/teal/purple cluster that saturates the developer-tool space. Amber reads as precision, craft, and signal — not danger, not consumer warmth.

This is the model Neo4j executes most successfully among the references studied. It serves both the IC (hero reads as precision tool) and the engineering lead (content sections are enterprise-readable).

---

## Named goals (ranked)

### 1. Precision authority *(dominant)*
The site reads like it was built by people who are exactly right about the problem — not selling, demonstrating. Every claim is specific and traceable. Trust is built the way good technical writing builds it: by being precise.

**Violated by:** Superlatives, vague claims ("AI-powered"), decorative chrome substituting for content, marketing inflection on technical claims, lorem ipsum or non-realistic placeholder copy.

- *Persona:* Senior engineering lead, 15-second scan, already skeptical of AI hype. Needs to feel: "this is the serious option, built by people who understand the problem."
- *Precedent:* Linear (real UI screenshots as proof, no illustration substitutes) — taking: specificity over illustration. Stripe developer docs — taking: zero decoration, total accuracy. Leaving: Stripe's pure-light treatment (our hero is dark).
- *Standards:* Nielsen information-scent, Hemingway iceberg rule (specifics over adjectives)
- *Platform conventions:* responsive-web — MDN layout and typography standards; no platform-specific constraints on content precision

### 2. Staged revelation
Above the fold makes one strong claim. Complexity earns its way in by scrolling — the human gate structure, per-pack journeys, and adapter matrix all surface after the first commitment is made.

**Violated by:** Fourteen packs presented as equal-weight choices before the visitor has decided to care; dense bullet lists above the fold; a nav with more than five items.

- *Persona:* Same lead, mid-scroll — now evaluating fit, not orienting. Needs the next question answered before the previous one has settled.
- *Precedent:* Linear (five product modules staged sequentially, each a full viewport section — not a grid). Cognee (one-breath headline → social proof → capability detail).
- *Standards:* Miller's Law (chunking), Hick's Law (fewer choices at decision points)
- *Platform conventions:* responsive-web — progressive disclosure is a first-class pattern; mobile-first means staged revelation is load-bearing, not optional

### 3. Grounded ambition
The visual language makes a product-platform claim, not a document claim. Display-scale type, alternating dark/light bands, full-bleed sections — it reads as a platform that has done the work, not a project with a site.

**Violated by:** MkDocs Material defaults visible on the marketing anchor; card-grid layouts in the hero; document-sized type (`h1 ≈ 2rem`); the generic indigo/slate palette from the current docs site leaking into the marketing surface.

- *Persona:* Any first-time visitor who has seen five AI-tool landing pages this week.
- *Precedent:* Neo4j (stat strip immediately below CTA, alternating text/screenshot sections, graph animation in hero). Vercel (negative letter-spacing on display type, monochrome commitment).
- *Standards:* Stage 1.5 surface-treatment rubric — dark hero = precision-tool claim; display type scale (`clamp(2.8rem, 5.5vw, 4rem)`) vs document scale (`h1 ≈ 2rem`)
- *Platform conventions:* responsive-web — `clamp()` is standard for responsive display type; `prefers-reduced-motion` required for any hero animation

### 4. Identity specificity
The visual language is derived from the product's nature, not borrowed wholesale from a reference. The three supervised loops, mechanical gates, and human checkpoints are the product — the design language emerges from that structure.

**Violated by:** Looking like "yet another developer tool site" (the indigo/purple/teal cluster). Copying Vercel or Linear wholesale. Generic animated blob as the hero background treatment.

- *Persona:* Returning visitor or peer recommendation — the person who was told "check this out." Needs to remember it as distinct.
- *Precedent:* Neo4j's graph-visualization hero (concept = decoration, same object, no waste) — taking: identity derived from product structure. Leaving: Neo4j's enterprise-heavy customer-logo saturation strategy.
- *Standards:* Brand differentiation through constraint specificity; decoration justified by product metaphor or cut entirely
- *Platform conventions:* responsive-web — SVG/CSS animations are viable for the pipeline visualization; must degrade gracefully and respect `prefers-reduced-motion`

---

## Dominant goal for arbitration

**Dominant goal: Precision authority**

Resolved trade-offs:

| Tension | Winner | Reason |
|---|---|---|
| Precision authority vs. grounded ambition (dramatic hero obscures the claim) | Precision authority | One idea per viewport; the hero headline wins over visual spectacle |
| Staged revelation vs. precision authority (staging hides relevant info) | Precision authority | When a specific claim is more trustworthy visible than hidden, surface it |
| Identity specificity vs. grounded ambition (distinctive = unfamiliar) | Grounded ambition | The platform claim is more important than being unusual; specificity serves it, not the reverse |
| Any goal vs. quality floor (accessibility, contrast, motion) | Quality floor | Non-negotiable; the floor is not a trade-off |

---

## Color mode decision (researched)

**Alternating-band — not pure dark, not pure light.**

| Considered | Why rejected |
|---|---|
| Pure dark native (Linear, Resend, Warp) | High developer NPS; limits enterprise reach; harder to sustain over long-form journey content |
| Pure light (Cognee, many SaaS) | Generic; no product-platform claim in the hero; the existing MkDocs site already looks like this |
| Alternating bands | Serves both audiences; hero makes the product claim; content sections are enterprise-readable; scales to per-pack journey pages without the aesthetic breaking |

---

## Resolved decisions (formerly open questions)

- **Amber-gold on docs surface:** Resolved. `--ds-accent` (`#e8952b`) is never used as body-text color on light backgrounds — contrast ratio is ~3.2:1, which fails WCAG 4.5:1 for body text. `--ds-accent-deep` (`#8b5e0a`) is the text-safe variant on light (verified ~6.0:1). Full swap list: 6 targeted changes to `extra.css` documented in `.context/design-system-foundations.md`.

- **Hero pipeline visualization — static, not animated.** Rubric applied: ambient looping animations fail the cognitive-load test for task-focused audiences (Calabro 2024: 26% comprehension reduction; orienting reflex fires on every pulse cycle regardless of intent). The pipeline visualization is a static SVG with amber accent on gate nodes. One-shot on-load entrance (fade-in, 300ms) is acceptable; continuous looping is not. The amber radial glow in the hero background is static — not animated. `prefers-reduced-motion` still respected; the static treatment is already the canonical state.

- **Persona depth:** Confirmed by user — strategy and intended audience are established. Sketch (senior engineers and engineering leads evaluating adoption) is sufficient to ground all current decisions.

- **Journey page content:** Acknowledged as the largest unresolved content work item. Template and schema defined in `.context/journey-page-template.md`. Content authoring is a separate workstream; the platform site can launch Phase 1 (marketing homepage + pack catalogue) before journey content exists.
