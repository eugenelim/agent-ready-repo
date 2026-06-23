# Product-rung survey — modeling the altitude above feature/capability

> Discipline: applied (practitioner-pattern survey)

Promoted grounding for **RFC-0043** (product rung above capability). Distilled
from an applied-mode `/research` run (two parts: prior art in an earlier internal
product toolkit + external best-practice across GStack/YC, Aha!, PR-FAQ, Lean/Business-Model Canvas,
Torres OST, Cagan/SVPG, North Star, JTBD). Confidence tags follow the applied-mode
overlay (GRADE minus the no-peer-review penalty; plus `survivorship bias` and
`stale prior art`); material claims triangulate ≥3 practitioner-independent sources.

---

**Question.** How should a "product rung" — the altitude *above* feature/capability,
where you shape and validate whether a product should exist, who it's for, and the
wedge — be modeled in our lightweight, prompt-only, markdown, file-per-artifact
product-engineering pack? Our current ladder is `capability → feature → spec`, with
a Scale axis (`app ↔ business-unit`) and a per-intent `de-risk-intent` step.

**Why now.** A greenfield product concept routed straight to a *feature* intent
(app-Scale default), with no rung for "should this product exist / who is it for /
what's the wedge." The level ladder tops out at `capability`, defined as
*architectural span*, not product altitude.

---

## Findings

### F1. A prior internal product toolkit already implements a product rung — as a vision artifact, gated on validated learnings `[high]`

An earlier internal product toolkit defines a 5-level,
phase-gated model that is a strict superset of what we have:

```
Strategic Intent → Opportunity Solution Tree → Assumption Map → Learning Memo
   → Vision → Initiative → Spec/Feature
```

- The **`Vision`** artifact is the "this product should exist" rung. It carries a
  *customer-shaped pitch*, *the change* (what changes for the customer),
  *what we believe and why* (evidence basis), *open assumptions tiered by risk*
  (`must-test-before-shipping | accept-as-bet | will-monitor-post-ship`),
  *counter-metrics*, and *predicted outcomes with a measurement plan*. It is
  **hard-gated**: it can only be authored once a `Learning Memo` with
  `status: survived` exists as its parent.
- The **`Assumption Map`** is the explicit "should this exist / who is it for"
  artifact: it enumerates bets across **five lenses — desirability, viability,
  feasibility, usability, ethical** — ranks them by `risk_if_wrong × evidence_today`,
  and names a single `riskiest_assumption`.
- The **`Learning Memo`** enforces a **predeclared-threshold discipline**: a
  `predeclared_at` timestamp that *must precede* experiment results, enforced by an
  `assumption-threshold-lock` hook (described as "the single most important guard in
  the kit"). This is our `de-risk-intent` kill-condition idea, made mechanical.
- Mechanism is **exactly our target shape**: every artifact is a `.md` file with YAML
  frontmatter, slash commands draft them, parent-links (`parent_intent`,
  `parent_opportunity`, …) form a traceable chain, and "files as memory" is a named
  principle. No DB, no SaaS.
- It explicitly routes the existence question to **human-only ownership** ("Should we
  enter this market? Is this problem important enough to solve?" are non-delegable).

**Caveat / what NOT to lift wholesale:** that toolkit is *heavy* — ~84 object types,
5 levels, write-time hooks, a 23-section handoff packet, and a validation phase that
was **largely unshipped** at the time of review. Our pack's whole value
proposition is the opposite: one recursive `intent` shape, prompt-only, minimal
ceremony. The lift is **selective** — take the *concepts* (a vision-shaped product
rung; the desirability-bet framing; tiered open-assumptions), not the 5-level ontology.

*Source: a prior internal product toolkit's own design docs and templates (all primary).*

### F2. Across every external framework, the product-rung artifact converges on the same four elements: a job/problem, a who defined by circumstance, a wedge, and existence-evidence `[high]`

Triangulated across four independent lineages (Christensen/Ulwick, Maurya, Tan/YC,
Amazon) — no shared vendor or employer:

- **JTBD (Christensen / Ulwick ODI)** — the *job statement* + the **struggling
  moment** (the context where current solutions break down) is the wedge and the
  existence test. "Who" is **circumstantial, not demographic** ("morning commuter in
  a car", not "25–35 professional"). Competing "hires" name the real competition.
- **Lean Canvas (Maurya)** — the **Early Adopters** sub-field (inside Customer
  Segments) *is* the wedge; the **Existing Alternatives** sub-field (inside Problem)
  is the existence test ("if nothing exists, the problem may not be urgent enough to
  pay for"). UVP must be written *for the early adopter*.
- **GStack `/office-hours` (Garry Tan / YC)** — six forcing questions that are
  directly file-serializable: Demand Reality (evidence of payment/behavior, not
  interest) · Status Quo · Desperate Specificity (name the actual human) · **Narrowest
  Wedge** (smallest version someone pays for *this week*) · Observation & Surprise ·
  Future-Fit. This is the single most liftable external artifact — six discrete prompts.
- **Amazon PR-FAQ** — the one-page constraint + the *customer quote written before the
  product exists* is the existence diagnostic; the "so what? — is it meaningfully
  better than what exists?" gate kills most PR-FAQs before build (treated as a feature).

The convergence is the design signal: a product rung needs **{problem/job, who-by-
circumstance, wedge, existence-evidence}** — and our existing JTBD opportunity field
already covers *part* of this but at the feature altitude, not above it.

*Sources: Christensen Institute, Strategyn (primary); leanstack/Maurya (primary);
GStack repo + gstacks.org (primary); About Amazon + Commoncog/Bryar (primary/secondary).*

### F3. The product-level validation bet is *desirability / value risk* ("will anyone want this at all") — categorically distinct from our feature-level de-risk `[high]`

Our `de-risk-intent` names one riskiest assumption + a kill condition, and the
intent-model says feature-level assumptions are *desirability* and capability-level are
*architectural/adoption*. But the **product-existence** bet is a different question than
"do users want *this feature*": it asks whether the problem is real and urgent enough
that anyone will hire *any* solution.

- **Cagan/SVPG four risks** — *Value* ("will anyone want it?"), Usability, Feasibility,
  **Viability/business** (legal/finance/sales/channel fit). Our model maps cleanly to
  value + feasibility; **viability risk is the gap** least covered today.
- **Torres OST assumption testing** adds two mechanics worth lifting *selectively*: an
  **assumption map 2×2** (importance × evidence) to prioritize *which* assumption to
  test first, and **three solution candidates per opportunity** for compare-and-contrast
  rather than a binary pass/fail. The OST *tree* itself largely duplicates our
  `capability → feature → spec` + JTBD opportunity — don't re-import it.

*Sources: roadmap.one/SVPG, mindtheproduct/Cagan, timwoods.io (primary/secondary);
producttalk.org Torres (primary).*

### F4. North Star and metric-decomposition frameworks are *alignment* tools, not existence validators — they presuppose the product exists `[high]`

North Star (Amplitude/Cutler/Ellis) — one NSM + 3–5 input metrics + guardrails + the
work — is a prioritisation/alignment causal tree. It explicitly *does not* answer
"should this exist / who is it for." Useful at the product rung only for **metric
discipline** (name the value metric + its input drivers), additive to a JTBD frame.
Do not make it the existence gate. Same verdict for **Aha! Roadmaps'**
Foundation/Market/Imperatives → Goals → Initiatives → … → Features hierarchy: it is an
*organizational/linkage* schema (liftable as naming + parent-link structure) but its
"should this exist" content lives in an *optional* Lean Canvas model, never a forced gate.

*Sources: amplitude.com books/blog, productfolio (primary/secondary); Aha! support docs
+ blog (primary, vendor — flagged).*

### F5. Of the document-shaped artifacts, PR-FAQ and Lean Canvas are the two liftable into a prompt-only file; Business Model Canvas is the wrong altitude `[high]`

- **PR-FAQ** — stronger on narrative/vision; 10 discrete promptable press-release
  sections + customer/internal FAQ; forces written proof of customer clarity before
  any build. Closest analogue to the prior toolkit's vision artifact.
- **Lean Canvas** — stronger on hypothesis-mapping; 9 short boxes, explicit wedge
  (Early Adopters) and existence (Existing Alternatives) sub-fields; maps directly onto
  a de-risk experiment queue.
- **Business Model Canvas (Osterwalder)** — designed for *established* businesses; no
  early-adopter field, no existence test. Maurya forked it into Lean Canvas precisely
  for this reason. Wrong altitude for a "should this exist" gate.

*Sources: Commoncog/Bryar & Carr (secondary/primary); leanstack/Maurya, Strategyzer,
Wikipedia BMC (primary/tertiary).*

---

## What this means for the RFC (synthesis)

`[synthesis]` The convergent, liftable design — calibrated to our prompt-only,
one-recursive-`intent` philosophy, *not* a heavyweight 5-level toolkit's weight:

1. **Add one product rung to the level ladder**, above `capability`. Candidate name:
   `product` (or `vision`). It is the *same recursive `intent` artifact*, one `Level:`
   higher — consistent with our "same shape at every level" model. It does **not**
   require a new artifact type, file layout, or hook.
2. **Decouple Level from Scale.** The bug that sent the user to a feature intent is the
   hardwired `app → feature` / `business-unit → capability` default. Make Level and
   Scale orthogonal: an `app`-Scale (one-repo) greenfield concept can legitimately
   start at `product` level. Scale stays "how many repos"; Level stays "altitude".
3. **Give the product rung a product-shaped field set** drawn from the F2 convergence,
   not a generic outcome+opportunity. Minimum liftable set:
   - *Job + struggling moment* (JTBD) — the problem and its urgency.
   - *Who, by circumstance* — the early adopter / wedge segment (Lean Canvas Early
     Adopters; GStack "name the actual human").
   - *Existing alternatives* — what they do today badly (Lean Canvas; existence test).
   - *Narrowest wedge* — smallest version someone pays for now (GStack).
   - *Demand evidence* — behavior/payment, not stated interest (GStack Demand Reality).
   - These are all prose/short-field, agent-promptable, single-markdown-file.
4. **The product-rung de-risk bet is the desirability/value bet**, and our existing
   `de-risk-intent` already fits — just teach it that at `product` Level the riskiest
   assumption is "will anyone want this at all," and add **viability risk** (F3 gap) to
   the kinds it considers. Optionally lift Torres' importance×evidence 2×2 for
   prioritizing which assumption to test first.
5. **Greenfield becomes a mode, not just a subtraction.** Today greenfield only means
   "skip current-state inputs." At the product rung, greenfield should *add* the
   product-shaping fields (problem/wedge/demand), since that's exactly when they're
   load-bearing.
6. **Wire the seam to `init-project`.** `frame-intent → de-risk → decompose` should hand
   its leaf into core's `init-project` as a recognized discovery shape (today
   `init-project` only names research/PRD/`receive-brief`; it never names
   `frame-intent`). This closes the "greenfield product concept falls between the two
   skills" gap.

`[inference]` Borrow the prior toolkit's *concepts* but keep our minimalism: the vision
field set (customer-shaped pitch, tiered open-assumptions, counter-metrics) and the
predeclared-threshold discipline are the high-value, low-weight lifts. Skip the large
fixed-type ontology, the mandatory phase-gates, the write-time hooks, and the
multi-section handoff packet — those contradict our charter's prompt-only, low-ceremony posture.

---

## Known unknowns

- **Known-unknown:** Does adding a `product` Level break `decompose-intent`'s
  tracker-projection table (which maps `top/capability → Initiative/Epic`)? Would be
  closed by: reading `decompose-intent/references/tracker-projection.md` and checking
  whether a level above capability has a tracker home or collapses.
- **Known-unknown:** Is `product` the right name vs. `vision`, given our "intent is one
  artifact" framing and that the prior toolkit separates a Rumelt-style strategic-intent
  (diagnosis/policy/actions) from a vision artifact? Would be closed by: deciding whether
  our rung is the *strategy* altitude or the *product-existence* altitude — these are
  arguably two distinct rungs (the design later resolved to two).
- **Known-unknown:** Does our `de-risk-intent` already handle viability risk, or only
  desirability + feasibility? Would be closed by reading its `references/`.
- **Unknowable (for now):** Whether adopters actually want a product rung or will find
  it ceremony — only adoption telemetry / user feedback settles it. The user hitting the
  gap is n=1 (strong, but one signal).

---

## Sources (primary unless noted)

**Prior art:** an earlier internal product toolkit (held privately, not cited by name
or URL here) — its README, charter, phase-guide, handover contracts, object inventory,
human/AI-ownership doc, and its vision + assumption-map templates (all primary).

**GStack/YC:** [garrytan/gstack](https://github.com/garrytan/gstack),
[office-hours SKILL.md](https://github.com/garrytan/gstack/blob/main/office-hours/SKILL.md),
[gstacks.org](https://gstacks.org/),
[YC essential startup advice](https://www.ycombinator.com/blog/ycs-essential-startup-advice).

**Aha!:** [strategy intro](https://support.aha.io/aha-roadmaps/support-articles/strategy/strategy-introduction),
[hierarchy report](https://www.aha.io/blog/hierarchy-report) (vendor — flagged).

**PR-FAQ / canvases:** [About Amazon culture/process](https://www.aboutamazon.com/news/workplace/an-insider-look-at-amazons-culture-and-processes),
[Commoncog PR-FAQ](https://commoncog.com/putting-amazons-pr-faq-to-practice/),
[Working Backwards (Bryar & Carr)](https://www.amazon.com/Working-Backwards-Insights-Stories-Secrets/dp/1250267595),
[Maurya fill-order](https://medium.com/lean-stack/what-is-the-right-fill-order-for-a-lean-canvas-f8071d0c6c8c),
[Strategyzer BMC](https://www.strategyzer.com/library/the-business-model-canvas).

**Discovery/metrics:** [Torres OST](https://www.producttalk.org/opportunity-solution-trees/),
[Torres assumption testing](https://www.producttalk.org/assumption-testing/),
[SVPG four risks](https://roadmap.one/blog/posts/blog6-6-svpg-product-risks/),
[Cagan vision/strategy](https://www.mindtheproduct.com/product-vision-and-strategy-marty-cagan-on-the-product-experience-part-1-of-2/),
[Amplitude North Star](https://amplitude.com/books/north-star/about-north-star-framework),
[Christensen Institute JTBD](https://www.christenseninstitute.org/theory/jobs-to-be-done/),
[Strategyn ODI](https://strategyn.com/jobs-to-be-done/).
