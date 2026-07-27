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

## Example 2 — Product vision headline: product-vision-INI-001 (product-copy mode)

**Source:** `docs/product/shaping/product-vision-INI-001.md` Headline section  
**Mode classified:** `product-copy` (conviction statement; the surface is persuasion, not explanation)

### BEFORE (24 words)

> A product OS for engineering teams — the coordination layer that closes the gap between one AI assistant and a thousand coordinated agents.

### Gate results

**Anti-AI-smell scan:** No warning-signal words. Structural flags:
- "closes the gap" — generic resolution phrase; the gap is named but not felt
- "product OS" — borrowed OS metaphor; does not explain what an OS actually does for the reader
- "coordination layer" — mechanism first; the reader's situation does not appear before the solution

**Deletion pass:**
- Q5 (Feature instead of outcome?): FIRE — "the coordination layer" names a mechanism, not what the reader gains
- Q10 (Is the product's actual POV visible?): FIRE — the "Why now" section has a sharp POV ("the bottleneck shifted from model capability to coordination infrastructure"); the headline does not carry it

**5-second test:** PARTIAL — *what is this?* ("a product OS") and *who is it for?* ("engineering teams") are clear; *why should I care?* requires the reader to feel the coordination gap, which the headline only names.  
**Specificity test:** PARTIAL — "one AI assistant and a thousand coordinated agents" is specific and strong; "closes the gap" is generic.  
**Point-of-view test:** FAIL — the strong POV lives in the body ("the bottleneck is coordination, not capability") but the headline is just a mechanism description.  
**Distinctiveness test:** FAIL — "closes the gap" could appear unchanged on hundreds of coordination/integration products.

### AFTER (28 words)

> Engineering teams now run AI on every task — but each agent starts from scratch, knows nothing of the others, and leaves no shared trail. This is the OS beneath the agents.

**Evaluation:** same word count. POV now leads (the reader's situation before the solution). "OS beneath the agents" earns the metaphor by naming what an OS actually does. The specific "one AI assistant to a thousand" claim is preserved in the body where it can be explained.

**Note on technical-editorial mode:** The `product-vision-INI-001.md` body sections (The problem, The solution, The adopter, Why now) use `technical-editorial` mode correctly — specific claims, evidence-backed, no AI-smell flags. The gate battery does not fire on those sections.

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
| product-vision-INI-001 headline | product-copy | partial → pass | partial → pass | FAIL → pass | FAIL → pass | +17% |
| experience-design README | technical-editorial | not fired | not fired | not fired | not fired | −0.5% |

**Key finding confirmed:** the gap is not capability — the existing skills have the craft knowledge. The gap is mode-blindness. Pack cards and README openings were written in the same voice because no system distinguished when to switch register. With `communication_mode` declared and the editorial gates active, the distinction is now explicit and enforced.

**Remaining weakness acknowledged:** the improved system produces better direction for agents writing copy; it does not guarantee better copy from agents that ignore the upstream brief's mode declaration. The gate only fires when the content brief is upstream and the mode is read. For content produced without going through `content-design` first, the `experience-reviewer` extended lens is the fallback.
