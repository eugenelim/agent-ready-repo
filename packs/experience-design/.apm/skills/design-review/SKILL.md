---
name: design-review
description: "Evaluate an existing screen, flow, or mockup with a severity-rated findings list using a three-pass structure: Pass 1 cold-read (audience, job, rendered state only); Pass 2 primary task and one unhappy path (desktop, tablet, mobile, keyboard, focus, zoom, reduced-motion); Pass 3 contract review (quality-floor, heuristics, marketing clarity, taste). Triggers on 'critique this design', 'review this screen', 'what is wrong with this mockup', 'do a heuristic eval', 'is this usable', 'does this fit our aesthetic', 'does this page convert', 'is this copy compelling', 'tweet test'. Do NOT use to name a felt direction (use creative-direction), to derive tokens (use design-token-taxonomy), or to structure hierarchy (use information-architecture). Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register."
---

# Skill: design-review

Runs a structured, three-pass evaluation of a screen, flow, or mockup and returns a **prioritized, severity-rated findings list** — each issue mapped to the recognized usability principle or aesthetic reference it violates, with one concrete, portable recommendation. The list is the artifact: it turns "this feels off" into something a stakeholder can argue and a builder can act on.

> **Authoring-time self-review.** This skill is an **interactive, authoring-time** tool — it runs in the session, with the author. It is **not** a fresh-context pass and **not** an adversarial reviewer; a same-session critique marks its own homework. The genuine fresh-context UX review is the forked-context **`experience-reviewer`** agent — invoke it for an independent pass after the authoring session.

## Severity tiers

Every finding carries one of three tiers. Apply these tiers consistently across all three passes.

| Tier | When to use | Rules |
|---|---|---|
| **Blocker** | The surface cannot ship with this finding unresolved. | Use for: any WCAG failure at the required conformance level; any missing state that leaves a user with no path forward (empty loading/error/permission states, blocked or destructive-confirmation states absent); marketing above-fold failures that prevent the reader from determining fit; contract violations that contradict the Digital Experience Contract. **Never** downgrade an accessibility failure to Concern or Suggestion. |
| **Concern** | The finding meaningfully degrades the experience but does not prevent task completion. | Use for: heuristic violations at severity 2–3; states missing but with a degraded fallback; copy that is weak but not misleading; contrast that is close to but not at the floor. |
| **Suggestion** | A documented improvement opportunity with low urgency. | Use for: severity 0–1 heuristic findings; preference-backed aesthetic observations with a grounded warrant; polish opportunities. **Never** present a pure aesthetic preference (one not grounded in the aesthetic reference or a recognized platform convention) as a Suggestion — it goes in Director's notes instead. |

## When to invoke

Confirm all three before drafting; if any fails, resolve it first.

1. **There is something concrete to review** — a screen, flow, mockup, or described surface. A vibe with no artifact isn't ready; route to `creative-direction`.
2. **You know whose task you're judging** — a critique needs a user and a goal. Without them, severity is unanchored guesswork; draw out the primary task first.
3. **You're evaluating, not creating** — the ask is "is this good," not "make this." If it's deriving values or structuring a layout, hand to `design-token-taxonomy` or `information-architecture`.

## Rendered evidence

When the surface under review has a rendered form (a live page, a built screen, a high-fidelity mockup at a specific viewport), **you must obtain rendered evidence before rating any finding**. Evidence means: a described observation from the actual rendered state at the viewport in question ("at narrow-phone width the hero CTA is below the fold"), a screenshot observation, or an explicit note that the rendered state was examined. A finding rated against code or a spec alone — without the rendered form — is marked `⚠ unverified` and is not a Blocker.

> If the session has no access to the rendered surface (design-only session, no build available), say so explicitly at the top of the findings list and mark all severity-3+ findings `⚠ unverified` — the independent `experience-reviewer` will pick them up when a rendered form exists.

## Procedure

0. **Surface inventory (multi-surface platforms only).** If the review subject is a multi-surface platform (e.g., marketing site + documentation site, or app + marketing + docs): (a) enumerate every surface and label its genre (marketing / documentation / analytical / etc.); (b) confirm which surface is under review in this pass; (c) note which other surfaces exist — they will need separate passes; (d) flag: cross-surface integration check required (see the marketing genre rubric for copy voice continuity and the information-architecture skill for cross-surface wayfinding). If the review subject is a single surface, skip to Pass 1.

---

### Pass 1 — Cold-read

**Run this pass first, in isolation, before examining code, briefs, or internal notes.** Look only at the rendered surface (or described screen state) as a first-time visitor would.

1. **Name the audience and job.** From the rendered surface alone, answer: who is this for, and what are they trying to do? If you cannot answer both questions from the first screen without scrolling, that is a finding. Do not consult the brief yet.
2. **Record what you see above the fold.** Describe the headline, primary CTA, proof signal, and navigation — exactly as a first-time visitor encounters them.
3. **First-impression finding.** State one sentence: what this surface communicates in the first five seconds, and whether it matches the audience and job you named.

Pass 1 produces a short observation block, not a findings list. Findings from it are carried into Pass 3.

---

### Pass 2 — Primary task and one unhappy path

**Walk the primary task and one unhappy path across three viewport widths and four accessibility modes.**

1. **Choose the primary task** from the brief (or, if the brief is absent, from the most prominent CTA on the surface).
2. **Choose one unhappy path** — the most likely failure: no results, a network error, a gated action, or a destructive confirmation.
3. **Walk the task and the unhappy path** at each of:
   - Desktop (wide viewport)
   - Tablet (mid viewport)
   - Mobile (narrow viewport)
   Then at each of:
   - Keyboard-only navigation (tab order, focus indicator, action completability)
   - Focus management (where does focus land after a state change? is it predictable?)
   - 200% zoom (does layout reflow? are controls still reachable?)
   - Reduced-motion (are animations replaced by instant or cross-fade transitions?)
4. **For each combination**, record: task completable (yes / partial / no); specific friction or block; which state from the quality-floor is missing or broken.

Pass 2 produces a structured observation table. Findings from it are carried into Pass 3.

---

### Pass 3 — Contract review

**Run the full contract review using all evidence from Passes 1 and 2.** This pass produces the final findings list.

1. **Frame the surface and load design-principles.** Name the user, the primary task, and each step under review. Also load the `design-principles` artefact at `docs/design/principles/<slug>.md` if one exists for this surface — every finding in this review must be mapped to the principle it was judged against. When a finding cannot be traced to any principle, route it to one of three places: (a) a **quality-floor commitment** it breaches (these are always valid regardless of whether principles exist — the floor applies unconditionally), (b) a recognized **heuristic** from the evaluation in step 3, or (c) a **new-principle decision** — flag it to the team as a gap in the design-principles artefact, not as a finding in this review. Pure aesthetic preferences with no principle backing and no floor/heuristic grounding go in a **Director's notes** section at the end of the findings list, clearly separated from the severity-rated findings. **This is a mandatory procedure step** — a design-review that skips design-principles integration does not produce a traceable findings list.
2. **Apply the shared floor first.** Run the `quality-floor` checklist at `references/quality-floor.md` against the surface — handle all 18 states, the accessibility floor, the reduced-motion principle. Each miss is a finding mapped to the floor commitment it breaches; accessibility misses are Blockers. Then apply the surface-specific mobile checklist for the surface's genre:

   *Marketing surface mobile:* primary CTA — and secondary CTA if present — is visible above the fold on a small-phone viewport without scrolling; hero top padding does not consume more than one-fifth of a common phone-height viewport before any content appears; navigation drawer items are full-width touch targets — compact inline chips in a vertical list are not acceptable; drawer has an explicit open/close state signal on the toggle icon; stat/feature strip dividers reset correctly when items reflow to multiple rows; tab bars scroll horizontally or wrap without a broken 3+1 layout; grid minimum accounts for the narrowest target viewport usable width minus horizontal padding on both sides; install/code blocks scroll horizontally rather than clipping.

   *Documentation surface mobile:* code blocks scroll horizontally (not clip); full-bleed sections that extend to the viewport edge must not produce a horizontal scrollbar on systems where scrollbars occupy layout space; sidebar collapses correctly and navigation is accessible without it at narrow-tablet widths and below; single-column reading width stays within a comfortable reading range; search is accessible from the mobile header without opening the sidebar.

3. **Run the heuristic evaluation.** Walk the surface against the recognized usability principles in `references/heuristics.md`. For each problem, record what you observed before you judge it.
4. **Map and rate.** Map each finding to the single best-fit principle (or floor commitment) and assign a severity tier (Blocker / Concern / Suggestion), naming the frequency × impact × persistence factors that set it. See `references/heuristics.md`.
5. **Run the marketing clarity pass** (when the artifact includes above-fold copy with a persuasion/conversion goal). For each of the three criteria, record what you observed, then map and rate:
   a. **Tweet test** — can the headline or tagline stand alone as a conviction statement? If you shared just that line with no surrounding context, would it communicate what this is and why it matters to the target reader? Failure: the line only describes the product, names a category without a reader benefit, or requires the page for meaning.
   b. **Five-second scan** — after 5 seconds on the above-fold, can a first-time visitor answer: *what is this / who is it for / should I care?* All three must be answerable from the visible content alone, not inferred. Failure: one or more answers are absent, ambiguous, or below the fold.
   c. **Painkiller-first structure** — does the copy lead with the reader's problem, pain, or desired outcome before naming the product's features? A painkiller solves a known hurt; a vitamin is a nice-to-have. Failure: copy leads with the author's feature list or product identity rather than the reader's recognized need.
   
   Map each finding to the criterion it violates and assign a severity tier (Blocker / Concern / Suggestion), where **impact** means conversion/persuasion cost. Label source mode `marketing`. A settings screen or internal tool that is out of scope for this pass produces no findings with this label.
6. **Run the taste critique** (when a grounded aesthetic reference from `creative-direction` is available). See `references/taste-critique.md` for the full method. In brief:
   a. **Check aesthetic alignment** — for each named goal in the grounded reference, ask whether the screen advances, is neutral to, or contradicts it. Ground each verdict in the recorded referent (persona + precedent + standards), never in a fresh opinion.
   b. **Check platform fit** — verify the screen respects the platform surface's conventions; point to the platform standard as the warrant, never reprint its values.
   c. **Map and rate taste findings** — each taste finding maps to the aesthetic goal it contradicts or the platform convention it violates; rate using the severity tiers (Blocker is rare for taste; Concern for clear contradictions; Suggestion for grounded preference differences with no clear warrant).
7. **Prioritize and recommend.** Merge all findings from all passes and modes. Sort Blockers → Concerns → Suggestions, lead with a count-by-severity headline, and give each finding one concrete, portable recommendation expressed as design intent — never a stack-specific implementation. Label the source pass (`pass-1` / `pass-2` / `pass-3`) and mode (`floor` / `heuristic` / `marketing` / `taste`) so the reader knows which lens each finding came from.

## Genre-specific rubrics

After the quality-floor and heuristic passes, route to the genre-specific rubric that matches the surface's `surface-genre:` declaration (from the per-screen brief). If no genre is declared, elicit it — genre rubrics are not optional for genre-bearing surfaces; they surface issues the generic passes miss.

Each rubric is a numbered checklist. Work through it in order; a "no" is a finding, mapped to the genre rubric item that failed it. Rate each finding with the standard severity tier (Blocker / Concern / Suggestion). Label source mode `genre-rubric`.

**Multi-surface routing:** When the subject includes both a marketing surface and a documentation surface, the marketing genre rubric and the documentation genre rubric must each be run as separate passes. Do not collapse them into a single pass. Each pass gets its own findings list; the cross-surface integration check (copy voice continuity, cross-surface wayfinding) runs after both surface passes are complete.

### Documentation genre rubric

1. **Navigation tier match** — does the navigation strategy match the page count tier? (≤30 pages: flat nav; 30–200: hub-and-spoke; >200: search-first.) A flat-nav structure on a 400-page docs site fails this item.
2. **Content typing** — is every piece of content typed (tutorial / how-to / reference / explanation)? Does the page structure match its declared type? (A tutorial that contains a full API reference mid-step is typed incorrectly.)
3. **Landing page orientation and hub structure** — does the docs landing page serve orientation rather than marketing copy? Verify all three hub jobs are present: (1) "Start Here" entry point — one link, one promise, above the fold; (2) content-type entry points — one section per Diátaxis type (tutorial / how-to / reference / explanation), named by what the reader accomplishes, not by content-type label; (3) search above the fold with a placeholder naming a real example query. A landing page that leads with product benefits rather than reader navigation fails this item. For >200-page sites (see item 1, navigation tier match), search must be persistent and prominent — a top-right corner widget does not meet the search-first requirement.
4. **TTFV reachability** — is the first-value moment achievable from the tutorial entry point? (Tutorial is scoped to ≤20 minutes of active work; prerequisites are stated before the reader starts; code samples work as pasted.)
5. **Machine-readability by design** — are machine-readability requirements built into the IA? (Code blocks typed with language identifiers; API tables with consistent column structure; heading hierarchy that reflects content type.) These should be design decisions, not implementation afterthoughts.

### Marketing genre rubric

1. **Hero approach fit** — does the hero approach match the product's position and reader's awareness level? (Vision for underfunded markets; social-proof for mature markets; job-to-be-done for buyers who know the pain but not the product.) An approach mismatch is a conversion-strategy finding, not a cosmetic one.
2. **Above-fold spec** — verify all six elements are present and correctly placed: (1) Headline: ≤10 words, IC-first (reader pain/goal before product name); (2) Subheadline: conviction-building (outcome or benefit), not a second problem statement; (3) Primary CTA: outcome language, not system action ("Install the core loop" not "Submit"); (4) Secondary CTA: only if primary asks meaningful commitment — absent is valid; (5) Proof signal: specific number, recognizable logo, or third-party rating, positioned adjacent to the CTAs; (6) Friction microcopy: one line removing the dominant objection to clicking the primary CTA ("No credit card", "Reversible", "1 command to try, 1 to remove") — absence is a blocker if the primary CTA implies commitment. **Tone collision check:** if the headline is a Statement, the subheadline must stay conviction-building — not pivot to problem-agitation (that belongs in a separate section below the fold).
3. **Scroll-story zone integrity** — does each zone in the scroll story have a single job? A zone that simultaneously introduces a feature, shows a testimonial, and prompts a second CTA has no job — it has three, and does none of them well.
4. **Cross-surface copy voice continuity** (only when a documentation surface is in scope for the same platform) — does the marketing copy voice carry through to the docs surface? Flag as minor: marketing uses precision/technical register but docs uses casual/tutorial register without explanation. Flag as major: marketing makes product claims the docs surface contradicts or doesn't support. This check requires reading at minimum the docs landing page and one how-to page alongside the marketing surface.
5. **Social proof tier calibration** — is the social proof at the right tier for the product's maturity stage? (Early: named customer quotes; Growth: logos + metrics; Scaled: independent validation.) A startup listing analyst rankings it hasn't earned fails this item.

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
- **Unrated opinions.** A finding without a severity tier and a violated principle or aesthetic goal is taste, not a critique. Map it or drop it.
- **Skipping the floor.** The `quality-floor` pass is mandatory, not optional polish. A surface can clear all heuristics and still fail the floor.
- **Prescribing the stack.** Recommendations name the *what* and *why* as design intent. The moment you reach for a framework, value, or property, you've left the method.
- **Burying the catastrophe.** A flat or alphabetized list hides the blocker. Worst-first, always, with the headline up top.
- **Skipping Pass 1.** The cold-read is not optional. Skipping it removes the only unbiased audience-and-job check in the sequence — the one most likely to catch architecture-first heroes and inventory-first pack pages.
- **Rating without rendered evidence.** When the surface has a rendered form, findings rated against code or specs alone are unverified. Mark them `⚠ unverified` and note that the `experience-reviewer` will confirm after render.
- **Softening an accessibility failure to Suggestion.** An a11y failure at the required conformance level is a Blocker. Severity tiers are not for negotiation on the floor.
