---
type: design-review
slug: team-orientation-heuristic-baseline
status: active
review_mode: authoring-time self-review
surfaces_reviewed: 2
principles: docs/design/principles/tech-site.md
aesthetic_reference: docs/specs/platform-site/aesthetic-direction.md
observed: live surfaces fetched 2026-09-04, plus source at 047bf0192
updated: 2026-09-04
---

# Baseline heuristic evaluation — both live surfaces

**24 findings: 1 catastrophic · 15 major · 6 minor · 2 advisory.** Plus 5
recorded passes where a commitment is met and should not be regressed.

**This is authoring-time self-review, not an independent pass.** The
`design-review` skill is explicit that a same-session critique marks its own
homework. The independent review is the forked-context `experience-reviewer`
agent, which runs at the Validate gate. Nothing here substitutes for it.

Every finding names the `tech-site.md` principle it violates, the quality-floor
commitment it breaches, or the Nielsen heuristic it fails. Findings that trace to
none of those sit in Director's notes, separated from the rated list.

## Step 0 — Surface inventory

| Surface | Genre | In this pass | Renderer |
| --- | --- | --- | --- |
| Marketing home, `/` | marketing (acquisition) | yes | Astro, `web/` |
| Documentation guides index, `/docs/guides/` | documentation | yes | Starlight, `docs-site/` |
| Pack catalogue, `/catalogue/`, `/packs/*` | marketing | no — separate pass needed | Astro, `web/` |
| Journey pages, `/journeys/*` | documentation-ish, generated | no — separate pass needed | Astro, `web/` |
| `/now/` | informational | no — separate pass needed | Astro, `web/` |

Both in-scope surfaces get their own genre rubric pass, not a merged one. The
cross-surface integration check runs after both.

**User and primary task.** The adoption champion (see
[personas](team-orientation-personas.md)), whose primary task is *understand the
operating model well enough to explain it to three other audiences*. Every
severity below is anchored to that task.

## Scope honesty — what this pass did not assess

Recorded so no reader mistakes silence for a pass:

- **Nav drawer behaviour on mobile** — full-width touch targets and the
  open/close state signal on the toggle. Not read.
- **Install and code block horizontal scroll on narrow viewports.** Not read.
- **The install task switcher's state set** — selected, focus, keyboard
  operation. Not read.
- **Hero top padding as a fraction of a small-phone viewport.** Token values not
  resolved.
- **Rendered contrast measurement.** Ratios below are taken from the values
  recorded in `tokens.css` and `aesthetic-direction.md`, not independently
  measured in a browser.
- **Any real assistive-technology run.** The accessibility findings are read from
  markup, which catches structure and misses behaviour.

A rendered-surface pass with a browser closes all six. It belongs at the Validate
gate, on the redesign, not here.

---

# Findings — worst first

## 🟥 4 — Catastrophic

### 1. Eleven internal gate codes are the visual entry point to the model
`heuristic` · Nielsen #2, match between system and the real world · violates
`tech-site.md` principle 1, durable application

**Observed.** The live page renders `G0`, `G1.5`, `G2`, `G3`, `G4`, `G5` eleven
times. Five in `ThreeLoops` — two in the pipeline chain, three opening each
loop's human-gate line. Six in `HumanGates`, where the code is set in the
heaviest weight at large body size in accent colour, making it the first thing
the eye lands on for six of seven cards.

**Why it costs the user.** The champion must learn a private notation to read a
public page, then either teach that notation to a budget holder or translate it
live. The principle states the reason directly: these are machine contracts, not
adopter copy. A champion who says "G4" to a CTO has lost the room; a champion who
must silently translate is improvising, which is the named worst moment.

**Severity factors.** Frequency: every reader, every visit. Impact: blocks the
core task of explaining the model. Persistence: never learned around, because the
mapping from code to decision is not on the page.

**Recommendation.** Remove all eleven. Substitute the decision phrasing, which
already exists in two places: `HumanGates`'s own `decide` field on each card, and
the P-path *ends at* fields in `guides/README.md`. The seventh gate card already
does this — its identifier is `Plan`, not a code — which is the proof the pattern
survives removal.

## 🟧 3 — Major

### 2. No element on the page shows how anything relates to anything
`heuristic` · Nielsen #6, recognition rather than recall · violates principle 1

**Observed.** Pack names appear in section 3. Loops appear in section 5. Decision
points appear in section 6. Nothing renders the relationship between them. The
one element that does encode a sequence — the `Discovery → Build → Release`
strip — is marked `aria-hidden` and carries gate codes rather than names.

**Why it costs the user.** The reader is asked to hold three separate
vocabularies in working memory across four screens of scrolling and construct
the mapping themselves. This is the owner's verdict, mechanically located.

**Recommendation.** One artifact that renders the model whole, at the top. Not an
annotation on the current structure — a replacement for it.

### 3. Six of nine sections describe both lifecycles at once; none states either whole
`heuristic` · Nielsen #8, aesthetic and minimalist design · violates principle 1

**Observed.** The content inventory's lifecycle column returned "both" for six
sections and "team adopting" for three. No section describes only the work
lifecycle, and no section separates the two.

**Why it costs the user.** The ambiguity is distributed rather than localised, so
the reader never gets a clean read of either lifecycle. It also means adding a
diagram to the current page would not fix it.

**Recommendation.** Make one lifecycle dominant and nest the other inside it, so
position on the page answers "which one am I looking at".

### 4. The handoff sequence is available only to sighted users
`floor` · commitment 2, meaning never carried by one channel alone

**Observed.** `ThreeLoops` renders `Discovery —G3→ Build —G4→ Release` in a
`div` marked `aria-hidden="true"`, on the stated grounds that "the loop cards
below carry the real content". The cards each describe one loop. None of them
states the sequence or the handoff between them. The sequence exists only in the
hidden element.

**Why it costs the user.** A screen-reader user receives three independent loop
descriptions and no handoff chain — which is the product's central claim. The
`aria-hidden` reasoning is sound in form and wrong in fact: the decoration is
carrying unique meaning.

**Severity.** Accessibility floor breaches start at 3.

**Recommendation.** Either give the cards the sequence in text, or make the
sequence element a first-class accessible object rather than decoration. The
canvas must be designed to the second option from the start — a diagram that
carries the model cannot be `aria-hidden`.

### 5. Tweet test failure — the headline names a mechanism, not a reader's stake
`marketing` · tweet test · violates principle 1

**Observed.** *"The agentic build loop that cannot approve its own work."*

**Why it fails.** Shared alone, it describes a component and an anti-property. It
requires the reader to already know what a build loop is, and it names nothing
about a team, an outcome, or a job. For the champion — whose task is to make a
budget holder care — it is unusable as a standalone line.

**Recommendation.** Lead with what a team gets. The mechanism is the second
sentence, and it is a good one.

### 6. Five-second scan failure — "who is it for" and "should I care" are both absent above the fold
`marketing` · five-second scan · violates principle 1

**Observed.** Above the fold the reader can partially answer *what is this*. No
audience is named. No consequence of not caring is stated. The three numbers
below the CTAs size an install, not an operating model.

**Recommendation.** Name the reader and the stake above the fold. The engagement's
premise — this is for a team, not a person — is currently absent from the first
screen entirely.

### 7. Painkiller arrives third, after the product and the menu
`marketing` · painkiller-first structure · violates principle 1

**Observed.** Section order is hero (product identity), stat strip (product
scale), use-case menu (product inventory), *then* "An unattended loop makes
unattended mistakes" — the actual pain.

**Why it costs the user.** The reader is asked to choose from a menu before being
given the reason the menu exists. The aesthetic direction names this exact
failure under its Staged revelation goal.

**Recommendation.** Problem before menu. The problem statement is well written
and badly placed.

### 8. The five most load-bearing claims are the five with no evidence
`heuristic` · violates principle 2 directly

**Observed,** ranked by adoption weight: (1) `core` cannot approve its own work;
(2) unattended loops self-certify and require non-bypassable gates; (3) the
seven-gate human-control map is complete; (4) one install works across every
major agent; (5) three loops, seven adapters, one pip install. None has a
checkable artifact beside it. The sections that *do* carry evidence — per-pack
routes, runnable install commands, a command plus destination — carry the least
consequential claims.

**Why it costs the user.** The engineer persona checks claims and the budget
holder asks for proof. The page inverts evidence against importance.

**Recommendation.** For each of the five, place a real artifact beside it or
weaken the claim to what can be shown. Do not invent proof — principle 2's known
tradeoff already states that when the artifact cannot be shown, the surface names
the evidence boundary instead of substituting an invented example.

### 9. No social proof at any tier, for a product that needs a funded decision
`genre-rubric` (marketing item 5) · quality-floor-adjacent, principle 2

**Observed.** No customer quote, no logo, no metric, no third-party validation.
For a product whose unit of adoption is a funded cohort rollout, the budget holder
has nothing to anchor on.

**Recommendation.** The honest tier available here is evidence-by-artifact rather
than borrowed credibility: real gate output, a real review transcript, a real
adapter contract. That is what this product can earn today, and it satisfies
principle 2 rather than fighting it.

### 10. The specified hero visualization was never built
`taste` · contradicts named goal *Identity specificity*; spec drift

**Observed.** `aesthetic-direction.md` records a resolved decision: *"The pipeline
visualization is a static SVG with amber accent on gate nodes."* What shipped is a
row of HTML pill spans containing gate-code text, marked `aria-hidden`.

**Why it matters.** The direction's fourth named goal is that the visual language
be derived from the product's structure — *"the three supervised loops, mechanical
gates, and human checkpoints are the product"*. The approved mechanism for that
goal is missing, and its placeholder is the page's worst accessibility and
vocabulary offender at once.

**Recommendation.** This is good news for the engagement: the SVG centrepiece is
an *already-approved* aesthetic decision, including that it be static with at most
a one-shot entrance. `creative-direction` amends rather than re-litigates.

### 11. The direction's own named violation is present on the page
`taste` · contradicts named goal *Staged revelation*

**Observed.** The goal's stated violation is *"Fourteen packs presented as
equal-weight choices before the visitor has decided to care."* Seven equal-weight
outcome cards, each listing pack names, are the third section — before the problem
statement.

**Recommendation.** Move the reason above the menu. The cards themselves are
well-built and outcome-led; their position is the defect.

### 12. Precision authority is the dominant goal and the unevidenced claims contradict it
`taste` · contradicts dominant named goal *Precision authority*

**Observed.** The goal's stated violations include *"vague claims"* and
*"marketing inflection on technical claims"*. The arbitration table in the same
document makes precision authority win every recorded tension except against the
quality floor. Finding 8's five claims are therefore contradicting the goal the
direction says wins.

**Recommendation.** Treat finding 8 as the highest-priority taste finding too,
not only a principle-2 finding.

### 13. Documentation navigation is two tiers below what its page count requires
`genre-rubric` (documentation items 1 and 3)

**Observed.** 207 guide markdown files plus 22 pack pages — roughly 229 published
pages. The rubric's tiers put anything over 200 pages in search-first. The actual
navigation is a flat sidebar, and item 3 states that for over-200-page sites
*"search must be persistent and prominent — a top-right corner widget does not
meet the search-first requirement."* Starlight's search is a header widget.

**Why it costs the user.** Every reader, every visit, permanently.

**Recommendation.** Raise search to a first-class element of the documentation
landing page, and group the sidebar by job so browsing remains viable for the
reader who does not know the search term.

### 14. All 21 guide areas sit in one sidebar group, placed last, after "Other"
`genre-rubric` (documentation item 1) · Nielsen #2 · violates principle 1

**Observed.** `tools/build-site.py` generates the sidebar as one group per pack
`group`, then appends every guide as a single final group. Live order: Get
Started, Pack Catalogue, Foundation, Agent workflows, Engineering, Integrations,
Content and design, Catalogue operations, Other, **Guides**. `site.toml` records
that the group order is declaration history: *"Appended so no existing group
moves."*

**Why it costs the user.** The nav asks the reader to pick a pack, which is the
question they came to the documentation to answer. It is the marketing surface's
pack-menu failure repeated one level down.

**Recommendation.** Re-group by reader job. Authored in `site.toml
[[guide_groups]]`, consumed by `generate_sidebar_config`. Never edit
`docs-site/src/content/docs/guides/` — it is a build projection of `guides/`.

### 15. The documentation landing page fails two of the three hub jobs
`genre-rubric` (documentation item 3)

**Observed.** Job 1, a "Start Here" entry point — one link, one promise, above the
fold: **fail.** The page opens with *"Choose the pack and guide that matches your
outcome"* and the ordered paths sit below it. Job 2, content-type entry points
named by what the reader accomplishes: **partial.** "Choose what you want to
achieve" and "Choose by role" are both job-named and good; there are no
Diátaxis-typed entry points. Job 3, search above the fold with a placeholder
naming a real example query: **fail.**

**Recommendation.** Promote P1 to a single above-the-fold "Start here" with one
promise. The content already exists; only its position and framing are wrong.

### 16. The best content on either surface is below the fold on a page most readers never reach
`heuristic` · Nielsen #10, help and documentation · violates principle 1

**Observed.** P1 through P6 are ordered, prerequisite-declaring, time-costed
paths that each end at a handoff rather than a document — and each states a
concrete first value. They are the highest-quality explanatory content in the
project. Twenty-one of twenty-two guide areas have no direct route from marketing, and the guides index itself has none.

**Recommendation.** Route marketing into the paths, and lead the index with them.

## 🟨 2 — Minor

### 17. Content typing is inconsistent for hub pages
`genre-rubric` (documentation item 2). Several pack `README.md` files carry
`kind: explanation` while functioning as navigation indexes. The page structure
does not match the declared type. Retype the hubs or add a hub type.

### 18. The first path costs three times the tutorial TTFV budget
`genre-rubric` (documentation item 4). The rubric scopes a tutorial to ≤20
minutes of active work; P1 is stated at ~1 hour. Prerequisites *are* stated,
which is the harder half done. Either split P1's first value out as a ≤20-minute
on-ramp or stop presenting it as the tutorial entry point.

### 19. Two parallel generated hierarchies with no stated division of labour
`heuristic` · Nielsen #4, consistency and standards. Pack reference and guides
cover overlapping ground and appear as sidebar peers. State which answers which
kind of question, at the point of choice.

### 20. The above-fold proof signal is a scale claim, not proof
`genre-rubric` (marketing item 2, element 5). Three numbers — three loops, seven
adapters, one pip install — sit adjacent to the CTAs, and the rubric asks for a
specific number, recognisable logo, or third-party rating. These are specific but
self-reported and unverifiable, so they read as scale rather than proof.

### 21. The primary CTA optimises for the wrong commitment
`marketing`. *"Try the supervised build loop"* is good outcome language for an
individual trial. The engagement's premise is that the commitment worth earning is
a cohort decision. The CTA and the page's thesis disagree.

### 22. Grid minimum may exceed the narrowest target viewport
`floor` · marketing mobile checklist. The use-case grid uses a 280px column
minimum. At a 320px viewport minus horizontal padding on both sides this may
overflow. **Not verified** — the padding token was not resolved. Check at 320px.

## ⚪ Advisory

### 23. Cross-surface copy voice splits on the model's own vocabulary
`genre-rubric` (marketing item 4). Marketing describes the handoffs with gate
codes; documentation describes the same handoffs with human decision phrasing.
One model, two vocabularies, and a reader crossing the seam loses the mapping.
Rated advisory only because findings 1 and 16 already carry the fix; it is listed
so the cross-surface check is on the record.

### 24. Crossing from documentation back to marketing has no route at all
`heuristic` · Nielsen #3, user control and freedom. A reader who has understood
the model in the documentation surface and now needs to sell it internally has
nowhere to go. See the [seam artifact](team-orientation-seam.md).

---

# Recorded passes — do not regress these

Stated explicitly because a redesign is where working controls get lost.

1. **Reduced motion is handled correctly.** The hero's one-shot 300ms fade is
   guarded by `prefers-reduced-motion: no-preference`, and the content is fully
   visible without it. The aesthetic direction's resolved decision against
   looping animation — grounded in a cited comprehension study — is honoured.
   Floor commitment 3, met.
2. **The accent contrast hazard the direction flagged is not present.** Every
   `color: var(--ds-accent)` in the codebase sits in a dark zone — hero, stat
   strip, nav, footer, terminal, install block, dark section. The ~3.2:1
   accent is never body text on light; `--ds-accent-deep` is used there instead — measured at **5.43:1**, not the
   ~6.0:1 the aesthetic direction records.
3. **The focus-ring system is careful, deliberate, and documented.** Two scoped
   `--ds-focus-ring` overrides handle amber-filled controls on a dark carrier
   and dark zones generally, with measured ratios recorded in `tokens.css` and
   an explicit note about which controls must *not* be swept in. An early count
   in this engagement misread these as a duplicate defect. They are not. Leave
   them alone.
4. **The adapter matrix is the best-built element on the page.** Focusable
   scroll region with an accessible name, per-cell visually-hidden Yes/No text
   so meaning is not carried by a glyph alone, and a documented `position:
   relative` fix that stopped hidden labels widening the page body.
5. **The stat strip reflows correctly.** Divider rules reset on the two-per-row
   mobile grid rather than leaving orphaned vertical rules — the exact item the
   marketing mobile checklist calls out.

---

# Director's notes

Not rated. No principle, floor commitment, or heuristic decides these.

- The problem statement — *"An unattended loop makes unattended mistakes"* — is
  the best single line on either surface. It passes the tweet test that the
  headline fails. It is worth considering whether it should be the headline.
- The whitespace treatment on the problem section, with no card and no icon, is
  the most confident piece of art direction on the page.
- The `Plan` gate card, alone among seven, uses a human label. It reads better
  than its six neighbours, which is the argument for finding 1 made visually.

# Handoff

**To `conversion-design`:** findings 5, 6, 7, 20, 21 set the above-the-fold
contract. Findings 2, 3, 11 set the scroll story.

**To `documentation-design`:** findings 13, 14, 15, 16, 17, 18, 19.

**To `information-architecture`:** findings 14 and 24, plus the route-identity
cost of re-grouping 21 sidebar groups, which principle 3 requires be argued
rather than absorbed.

**To `creative-direction`:** findings 10, 11, 12 — all three are contradictions
of already-named goals, so the amendment is small.

**To `interaction-design`:** finding 4 is the canvas's hardest constraint. The
diagram carries the model, so its accessible equivalent must carry the nesting
and the one-way tracker edge, not a flattened alt string.

**To the Validate gate:** the six unassessed items listed at the top need a
rendered-surface pass with a browser, against the redesign.
