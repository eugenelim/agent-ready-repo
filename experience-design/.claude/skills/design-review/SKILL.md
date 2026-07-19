---
name: design-review
description: "Evaluate an existing screen, flow, or mockup with a severity-rated findings list: quality-floor pass (states, a11y, motion), heuristic eval (Nielsen's 10), marketing clarity pass (tweet test, five-second scan, painkiller-first — fires on above-fold copy with a persuasion goal), and taste critique (grounded aesthetic reference + platform fit). Triggers on 'critique this design', 'review this screen', 'what is wrong with this mockup', 'do a heuristic eval', 'is this usable', 'does this fit our aesthetic', 'does this page convert', 'is this copy compelling', 'tweet test'. Do NOT use to name a felt direction (use creative-direction), to derive tokens (use design-system), or to structure hierarchy (use information-architecture)."
---

# Skill: design-review

Runs a structured evaluation of a screen, flow, or mockup and returns a **prioritized, severity-rated findings list** — each issue mapped to the recognized usability principle or aesthetic reference it violates, with one concrete, portable recommendation. The list is the artifact: it turns "this feels off" into something a stakeholder can argue and a builder can act on.

Four modes, always run in this order:

1. **Quality-floor pass** — mandatory; checks all states, accessibility, and reduced-motion.
2. **Heuristic evaluation** — walks the surface against recognized usability principles.
3. **Marketing clarity pass** (when the artifact includes above-fold copy with a persuasion/conversion goal — a landing page, marketing page, or product announcement) — checks the copy against the tweet test, five-second scan, and painkiller-first structure. Does **not** fire for internal tools, forms, settings screens, or content pages with no conversion goal.
4. **Taste critique** (when a grounded aesthetic reference is present) — checks the screen against the grounded aesthetic reference and platform fit.

> **Authoring-time self-review.** This skill is an **interactive, authoring-time** tool — it runs in the session, with the author. It is **not** a fresh-context pass and **not** an adversarial reviewer; a same-session critique marks its own homework. The genuine fresh-context UX review is the forked-context **`experience-reviewer`** agent — invoke it for an independent pass after the authoring session.

## When to invoke

Confirm all three before drafting; if any fails, resolve it first.

1. **There is something concrete to review** — a screen, flow, mockup, or described surface. A vibe with no artifact isn't ready; route to `creative-direction`.
2. **You know whose task you're judging** — a critique needs a user and a goal. Without them, severity is unanchored guesswork; draw out the primary task first.
3. **You're evaluating, not creating** — the ask is "is this good," not "make this." If it's deriving values or structuring a layout, hand to `design-system` or `information-architecture`.

## Procedure

1. **Frame the surface and load design-principles.** Name the user, the primary task, and each step under review. This anchors every severity call that follows. Also load the `design-principles` artefact at `docs/design/principles/<slug>.md` if one exists for this surface — every finding in this review must be mapped to the principle it was judged against. When a finding cannot be traced to any principle, route it to one of three places: (a) a **quality-floor commitment** it breaches (these are always valid regardless of whether principles exist — the floor applies unconditionally), (b) a recognized **heuristic** from the evaluation in step 3, or (c) a **new-principle decision** — flag it to the team as a gap in the design-principles artefact, not as a finding in this review. Pure aesthetic preferences with no principle backing and no floor/heuristic grounding go in a **Director's notes** section at the end of the findings list, clearly separated from the severity-rated findings. **This is a mandatory procedure step** — a design-review that skips design-principles integration does not produce a traceable findings list.
2. **Apply the shared floor first.** Run the `quality-floor` checklist at `references/quality-floor.md` against the surface — handle all states, the accessibility floor, the reduced-motion principle. Each miss is a finding mapped to the floor commitment it breaches; accessibility misses start at major.
3. **Run the heuristic evaluation.** Walk the surface against the recognized usability principles in `references/heuristics.md`. For each problem, record what you observed before you judge it.
4. **Map and rate.** Map each finding to the single best-fit principle (or floor commitment) and assign a 0–4 severity, naming the frequency × impact × persistence factors that set it. See `references/heuristics.md`.
5. **Run the marketing clarity pass** (when the artifact includes above-fold copy with a persuasion/conversion goal). For each of the three criteria, record what you observed, then map and rate:
   a. **Tweet test** — can the headline or tagline stand alone as a conviction statement? If you shared just that line with no surrounding context, would it communicate what this is and why it matters to the target reader? Failure: the line only describes the product, names a category without a reader benefit, or requires the page for meaning.
   b. **Five-second scan** — after 5 seconds on the above-fold, can a first-time visitor answer: *what is this / who is it for / should I care?* All three must be answerable from the visible content alone, not inferred. Failure: one or more answers are absent, ambiguous, or below the fold.
   c. **Painkiller-first structure** — does the copy lead with the reader's problem, pain, or desired outcome before naming the product's features? A painkiller solves a known hurt; a vitamin is a nice-to-have. Failure: copy leads with the author's feature list or product identity rather than the reader's recognized need.
   
   Map each finding to the criterion it violates and assign a 0–4 severity using the frequency × impact × persistence rubric, where **impact** means conversion/persuasion cost — how badly the miss hurts the reader's ability to determine fit and take the intended action. (This is a deliberate application of the same rubric to a persuasion-cost dimension; it is not a separate scale.) Label source mode `marketing`. A settings screen or internal tool that is out of scope for this pass produces no findings with this label.
6. **Run the taste critique** (when a grounded aesthetic reference from `creative-direction` is available). See `references/taste-critique.md` for the full method. In brief:
   a. **Check aesthetic alignment** — for each named goal in the grounded reference, ask whether the screen advances, is neutral to, or contradicts it. Ground each verdict in the recorded referent (persona + precedent + standards), never in a fresh opinion.
   b. **Check platform fit** — verify the screen respects the platform surface's (responsive-web / iOS / Android / cross-platform) conventions; point to the platform standard as the warrant, never reprint its values.
   c. **Map and rate taste findings** — each taste finding maps to the aesthetic goal it contradicts or the platform convention it violates; rate 0–4 by the same severity rubric (frequency × impact × persistence), with 0 reserved for genuine disagreement where the referent does not clearly resolve the call.
7. **Prioritize and recommend.** Merge all findings from all modes. Sort worst-first across modes, lead with a count-by-severity headline, and give each finding one concrete, portable recommendation expressed as design intent — never a stack-specific implementation. Label the source mode (`floor` / `heuristic` / `marketing` / `taste`) so the reader knows which lens each finding came from.

## Genre-specific rubrics

After the quality-floor and heuristic passes, route to the genre-specific rubric that matches the surface's `surface-genre:` declaration (from the per-screen brief). If no genre is declared, elicit it — genre rubrics are not optional for genre-bearing surfaces; they surface issues the generic passes miss.

Each rubric is a numbered checklist. Work through it in order; a "no" is a finding, mapped to the genre rubric item that failed it. Rate each finding with the standard 0–4 severity (frequency × impact × persistence). Label source mode `genre-rubric`.

### Documentation genre rubric

1. **Navigation tier match** — does the navigation strategy match the page count tier? (≤30 pages: flat nav; 30–200: hub-and-spoke; >200: search-first.) A flat-nav structure on a 400-page docs site fails this item.
2. **Content typing** — is every piece of content typed (tutorial / how-to / reference / explanation)? Does the page structure match its declared type? (A tutorial that contains a full API reference mid-step is typed incorrectly.)
3. **Landing page orientation** — does the docs landing page serve orientation (Start Here entry point + content-type entry points + search above the fold) rather than marketing copy? A landing page that leads with product benefits rather than reader navigation fails this item.
4. **TTFV reachability** — is the first-value moment achievable from the tutorial entry point? (Tutorial is scoped to ≤20 minutes of active work; prerequisites are stated before the reader starts; code samples work as pasted.)
5. **Machine-readability by design** — are machine-readability requirements built into the IA? (Code blocks typed with language identifiers; API tables with consistent column structure; heading hierarchy that reflects content type.) These should be design decisions, not implementation afterthoughts.

### Marketing genre rubric

1. **Hero approach fit** — does the hero approach match the product's position and reader's awareness level? (Vision for underfunded markets; social-proof for mature markets; job-to-be-done for buyers who know the pain but not the product.) An approach mismatch is a conversion-strategy finding, not a cosmetic one.
2. **Above-fold spec completeness** — are all six above-fold elements present: headline (≤10 words), sub-headline, primary CTA, secondary CTA (or social proof inline), proof signal, and friction microcopy? A missing friction microcopy or a headline over 10 words fails this item.
3. **Scroll-story zone integrity** — does each zone in the scroll story have a single job? A zone that simultaneously introduces a feature, shows a testimonial, and prompts a second CTA has no job — it has three, and does none of them well.
4. **Social proof tier calibration** — is the social proof at the right tier for the product's maturity stage? (Early: named customer quotes; Growth: logos + metrics; Scaled: independent validation.) A startup listing analyst rankings it hasn't earned fails this item.

### Analytical genre rubric

1. **Business-question traceability** — does every widget trace to at least one of the 3–5 named business questions? A widget that answers no named question is a candidate for removal; flag it.
2. **Tier 1 KPI ceiling** — are Tier 1 KPIs ≤9 and above the fold without scrolling? Does each KPI have a visible comparison baseline (not just a primary value)? "1,247 active users" with no comparison baseline fails this item.
3. **Filter adjacency** — do filter controls live adjacent to the data they filter? A date range filter in a sidebar while the charts it controls are in the center creates a spatial mismatch; fails Shneiderman's zoom-and-filter principle.
4. **Widget state completeness** — does every widget have a designed loading state, empty state, error state, and stale-data state? A widget designed only in its "populated" state fails this item.

### Informational genre rubric

1. **Line-length constraint** — is the reading column width constrained to produce 45–75 characters per line at the chosen type scale? A full-width text block on a wide viewport fails this item.
2. **Reading-pattern consistency** — does the chosen pattern (F for dense/reference-heavy, Z for conversational/single-topic) apply consistently to heading placement, first-sentence construction, and layout decisions across the page?
3. **"What's next" intent clarity** — does the post-article zone serve a defined reader intent (related topic / deeper dive / action / discovery) at a clear visual priority? A zone with four equal-weight "what's next" categories at identical visual weight serves no intent.

### Marketplace genre rubric

1. **Card hierarchy decision weight** — is the card hierarchy ordered by decision weight (primary identifier → key attribute → social proof signal → secondary attributes → CTA)? An attribute that drives the match decision (price, availability, compatibility) buried below secondary details fails this item.
2. **Filter architecture + buyer behavior match** — is the filter architecture appropriate to the declared buyer behavior? (Browse-first: chip-based filters, immediately visible; Search-first: sidebar filters, complex taxonomy.) A browse-first surface with a sidebar-only filter fails this item.
3. **Transaction bridge context** — does the transaction flow (cart, checkout, booking) keep marketplace context visible throughout? A checkout screen that shows only the cart line items, with no reference to the listing the buyer selected, fails this item.

### Workspace genre rubric

1. **Last-location landing** — does the surface land returning users at their last working context? A workspace that greets returning users with a generic dashboard instead of their last location fails this item.
2. **Interrupt escalation respect** — is the interrupt escalation ladder respected? (Ambient for non-urgent; focal — modal, sound, motion overlay — only for time-sensitive + action-required.) A workspace that uses focal interrupts for non-urgent notifications fails this item.
3. **Agentic output review surface** — for any agentic output (generated content, proposed code change, automated action), is there a review surface between the output and its application? An agent that applies output without a review step fails this item.

---

## Anti-patterns to refuse

- **Claiming to be a fresh-context reviewer.** This skill is authoring-time self-review. The genuine fresh-context UX review is the forked-context `experience-reviewer` agent — it runs independently, between sessions, and does not mark its own homework.
- **Reprinting the aesthetic reference values.** The taste critique points to the grounded referent; it never reprints palette entries, type scales, spacing values, or any literal from the reference. See `references/taste-critique.md`.
- **Unrated opinions.** A finding without a severity and a violated principle or aesthetic goal is taste, not a critique. Map it or drop it.
- **Skipping the floor.** The `quality-floor` pass is mandatory, not optional polish. A surface can clear all ten heuristics and still fail the floor.
- **Prescribing the stack.** Recommendations name the *what* and *why* as design intent. The moment you reach for a framework, value, or property, you've left the method.
- **Burying the catastrophe.** A flat or alphabetized list hides the blocker. Worst-first, always, with the headline up top.
