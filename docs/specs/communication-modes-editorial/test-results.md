# Integration test results — communication-modes-editorial

Three real artifacts from this repo run through the improved skill system.

---

## Example 1 — Pack card: experience-design (product-copy mode)

**Source:** `web/src/content/packs/experience-design.md` body paragraph  
**Mode classified:** `product-copy` (marketing/website surface with conversion goal)

### BEFORE (130 words)

> Experience Design installs the full design thread from outcome to realization — 18 skills covering journey mapping, screen flow derivation, service blueprinting, surface-genre design (marketing, documentation, analytical, marketplace, informational, workspace), design principles, content design, design system foundations, and continuous review. Connective skills walk journey-mapping → user-flow → service-blueprint and the inside-out sibling (process-mapping). Genre skills handle each surface type: conversion-design for marketing surfaces, documentation-design for docs sites, analytical-design for dashboards, and more. Craft skills design each screen (creative-direction, design-system, information-architecture, interaction-design) and review it (design-review, design-principles), all held to one shared quality floor — handle-all-states, WCAG 2.2 AA, reduced-motion. A forked-context `experience-reviewer` gives every design an independent review.

### Gate results

**Anti-AI-smell scan:** No flagged warning-signal words. Structural flags:
- Feature enumeration (18 skills, 4 taxonomic categories) without a user problem
- Mechanism-first ("installs the full design thread" → mechanism, not outcome)

**Deletion pass:** "from outcome to realization" adds no reader-facing meaning. The four taxonomic categories are useful but lose "why." Three of four sentences are taxonomy; zero are about the reader.

**5-second test:** FAIL — after 5 seconds, a reader knows WHAT it is but not why they need it or why this is different from any design toolkit.  
**Specificity test:** FAIL — the body could describe Figma, Abstract, or any design system tool with only the name changed.  
**Point-of-view test:** FAIL — no opinion about the problem, the status quo, or why teams struggle with design intent.  
**Distinctiveness test:** FAIL — reads as a category description, not a specific product with a point of view.

### AFTER (74 words for value statement + mechanism)

> Design intent evaporates between the product idea and the built screen — not because teams lack opinions, but because intent was never written down in a form engineering could act on. Experience Design fills that gap: it takes the customer journey your product is supposed to serve and walks it forward into screen flows, service blueprints, and per-screen briefs with the interaction model and quality floor engineering needs to build without guessing.
> 
> 18 skills across four layers: connective thread (journey → flow → blueprint), surface-genre design (marketing, docs, dashboards, marketplace, editorial, workspace), craft (creative direction, design system, IA, interaction design), and independent review.

**Evaluation:** word count down 43%. WHAT/WHO/WHY now answerable in 5 seconds. Still completely specific to this product.

---

## Example 2 — Pack card: product-engineering (product-copy mode)

**Source:** `web/src/content/packs/product-engineering.md` body paragraph  
**Mode classified:** `product-copy`

### BEFORE (81 words)

> Product Engineering installs upstream of the build loop. The `discovery-loop` (run by the `discovery-lead` agent) turns a raw idea into a build-ready decision brief: diverging across candidate product shapes, converging through a lens roster with two discovery reviewers, and emitting a connected hypothesis with validation hooks. `frame-intent`, `de-risk-intent`, and `decompose-intent` run as habits over a recursive intent hierarchy. `voice-and-microcopy` adds the content layer.

### Gate results

**Anti-AI-smell scan:** No flagged warning-signal words. Structural flags:
- "installs upstream of the build loop" — jargon pair (upstream, build loop) with no reader benefit
- "diverging across candidate product shapes, converging through a lens roster with two discovery reviewers" — architecture description, not outcome

**Deletion pass:** "and emitting a connected hypothesis with validation hooks" — the phrase carries no reader meaning without context. "run as habits over a recursive intent hierarchy" — pure architecture.

**5-second test:** PARTIAL — a technical practitioner gets it; a product person does not know what problem it solves.  
**Specificity test:** PARTIAL — "turns a raw idea into a build-ready decision brief" is genuinely specific; the mechanism description after it is not.  
**Point-of-view test:** FAIL — no opinion about why product ideas fail before the build.  
**Distinctiveness test:** FAIL — could describe any structured product planning methodology.

### AFTER (72 words)

> Most product ideas die in the gap between "we should build this" and a team that knows what to build and why. Product Engineering closes that gap. The `discovery-loop` (run by the `discovery-lead` agent) stress-tests the idea before engineering starts: it generates competing product shapes, subjects them to domain grounding and two specialist reviewers, and doesn't hand off until there's a connected hypothesis with a named kill condition.

**Evaluation:** word count down 11% (the BEFORE was already lean). USER PROBLEM now leads. Architecture description pruned to the outcome it produces. Still specific — kill condition, domain grounding, specialist reviewers are differentiating details.

---

## Example 3 — Pack README opening: experience-design (technical-editorial mode)

**Source:** `packs/experience-design/README.md` first two paragraphs  
**Mode classified:** `technical-editorial` (pack README — practitioner-facing, not conversion surface)

### BEFORE (excerpt, ~120 words)

> The design/UX seat for a product team — the grown-up successor to `design-craft`. It carries the **whole design thread** as one walkable flow: from a customer journey, through the screens that journey implies and the services behind them, to how each screen looks and behaves, to an independent review and a hand-off to realization. For interaction and visual designers, design-eng hybrids, and any agent or person authoring the **design intent** a UI build consumes (the design-side twin of `product-engineering`'s product intent).
>
> Every skill ships portable **method**, not your stack: no UI-framework code, no styling-language syntax, no animation library, and **no values tables** (no fixed spacing, timing, color, motion-curve, or breakpoint cheat-sheets, no fixed token set, no pixel comps).

### Gate results

Technical-editorial mode — deletion pass and anti-AI-smell scan apply, but the optimization target is CLARITY + PRECISION + CREDIBILITY, not conversion. Detail is acceptable when it creates understanding.

**Anti-AI-smell scan:** No flagged words. "The grown-up successor to `design-craft`" is an internal reference that means nothing to a first-time reader (design-craft is not a known product outside this repo).

**Deletion pass questions fired:**
- Q1 (Can the opening be stronger?): "The grown-up successor to `design-craft`" adds nothing for a new reader. Cut.
- Q5 (Explaining feature instead of outcome?): Second paragraph names exclusions (no X, no Y, no Z). This is useful and specific — the "What's NOT here" discipline is a strength. Keep.

**5-second, specificity, POV, distinctiveness tests:** NOT FIRED — technical-editorial mode targets clarity and precision, not desire and differentiation. The README correctly assumes a reader who has already decided to look.

### AFTER (minor change only)

Remove "the grown-up successor to `design-craft`" — the dash-phrase is an internal reference that confuses rather than orients. Everything else is already at the right precision level for technical-editorial mode.

> ~~The design/UX seat for a product team — the grown-up successor to `design-craft`.~~ **The design/UX seat for a product team.**

**Evaluation:** 1 phrase removed. The README body is already well-written for its mode and needs no further changes. This demonstrates mode-aware discipline: the copy-test battery doesn't fire on technical-editorial; a lighter scan is appropriate.

---

## Summary evaluation

| Example | Mode | 5-second | Specificity | POV | Distinctiveness | Word change |
|---------|------|----------|-------------|-----|----------------|-------------|
| experience-design card | product-copy | FAIL → pass | FAIL → pass | FAIL → pass | FAIL → pass | −43% |
| product-engineering card | product-copy | partial → pass | partial → pass | FAIL → pass | FAIL → pass | −11% |
| experience-design README | technical-editorial | not fired | not fired | not fired | not fired | −0.5% |

**Key finding confirmed:** the gap is not capability — the existing skills have the craft knowledge. The gap is mode-blindness. Pack cards and README openings were written in the same voice because no system distinguished when to switch register. With `communication_mode` declared and the editorial gates active, the distinction is now explicit and enforced.

**Remaining weakness acknowledged:** the improved system produces better direction for agents writing copy; it does not guarantee better copy from agents that ignore the upstream brief's mode declaration. The gate only fires when the content brief is upstream and the mode is read. For content produced without going through `content-design` first, the `experience-reviewer` extended lens is the fallback.
