# RFC-0043: A product rung — two product-shaping altitudes above capability, and Level decoupled from Scale

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-23
- **Date closed:** 2026-06-23
- **Related:** ADR-0019 (intent ontology — **refined by a follow-on ADR this RFC produces**, since ADRs are immutable) · RFC-0030 (the product-engineering pack) · RFC-0019 (receive-brief) · core `init-project` (greenfield front door) · promoted research survey `0043-notes/survey-product-rung.md`

## The ask

**Recommendation (BLUF).** Add a **product rung** to the `product-engineering`
intent ladder — two seeded-but-open altitudes above `capability`:
**`product-vision`** (why this product should exist · who, by circumstance · the
wedge · demand evidence — the *existence* bet) sitting above **`product-strategy`**
(central challenge · guiding policy · coherent actions · problem/segment sequence —
the *path*). **Decouple `Level` from `Scale`** so a one-repo greenfield concept can
start at a product altitude instead of being coerced to `feature`. The mechanism is
prompt-only: a `Level:` enum extension, framing/decomposition prompts, seeded field
sets, and one new de-risk assumption-kind. **No engine, hook, or new skill.**

**Why now (SCQA).** *Situation:* RFC-0030 / ADR-0019 shipped a recursive,
level-tagged `intent` whose levels are deliberately **not** a fixed ladder.
*Complication:* the shipped v1 collapsed the ladder to `capability | feature` and
`scale-intake.md` hardwired `app → feature` / `business-unit → capability`, so a
greenfield *product concept* routes straight to a feature intent — there is no rung
for "should this product exist, for whom, what's the wedge." A user hit exactly this.
*Question:* how do we give the product altitude a home without betraying the
pack's prompt-only, low-ceremony charter?

**Decisions requested:**

1. **Add two product rungs, keeping `Level` open.** `product-vision` above
   `product-strategy` above `capability`; the field stays open-valued (per ADR-0019),
   these two are the *recognized, seeded* product altitudes. · *why:* the v1 enum
   over-narrowed an intentionally open ontology. · decide-by: RFC accept (default:
   adopt).
2. **Decouple `Level` from `Scale`.** Scale = "how many repos"; Level = altitude; the
   old Scale→Level mapping becomes a *suggested starting level*, never silently
   stamped. · *why:* this is the root cause of the misroute. · decide-by: RFC accept
   (default: adopt).
3. **Either rung authorable directly; skipping allowed but observable.** Add a
   *sibling-spawn detector* and a *retroactive parent* affordance (below). · *why:*
   the LLM fans a product concept into multiple feature intents anyway; the rung's job
   is to anchor and consolidate, not to gate. · decide-by: RFC accept (default: adopt).
4. **De-risk gains one product-level assumption-kind** — `market-existence` (will-anyone-
   want-this-at-all + viability), a **distinct token** from the feature-level
   `desirability` kind, reusing the existing pre-PMF qualitative-bar. · decide-by:
   RFC accept (default: adopt).
5. **Wire the `frame → de-risk → decompose` seam into core's `init-project`.** ·
   *why:* the greenfield product loop and the greenfield repo front door don't connect
   today. · decide-by: RFC accept (default: adopt).

## Problem & goals

**Diagnosis.** Two coupled defects in the shipped pack, not one:

1. **The ladder tops out at `capability`**, which `intent-model.md` defines as
   *architectural span* ("spans several features / components") with a
   *architectural/adoption* de-risk kind. A greenfield product concept is neither a
   feature nor an architectural span — it is a bet about whether a product should exist
   at all, for whom, and through what wedge. That altitude has no rung.
2. **`Level` is welded to `Scale`.** `scale-intake.md` sets `app → feature`,
   `business-unit → capability`, and `frame-intent` step 3 nudges hard ("At `app` Scale
   most intents are `feature`-level"). So "one repo" is treated as proof you already
   know your feature. Scale (how many repos) and Level (altitude of the bet) are
   orthogonal; fusing them mis-routes every single-repo product concept.

The consequence observed in practice: a product concept fed to `frame-intent` either
becomes a single feature intent (altitude lost), or the agent fans it out into
**multiple feature intents with no shared parent** — sibling bets that each silently
re-assume the product should exist, and whose product-level "does anyone want this"
question gets tested piecemeal at feature level (validation theatre) or not at all.

**Goals.**

- Give the product altitude a home as the *same recursive `intent`*, one or two
  `Level`s higher — no new artifact type, file layout, hook, or skill.
- Make `Level` and `Scale` orthogonal so an `app`-Scale greenfield concept can start at
  a product altitude.
- Make rung-skipping safe *and* observable: anchor orphaned sibling feature intents
  under a product parent, and consolidate the existence de-risk to one test at the top.
- Seed concrete, agent-promptable field sets for both rungs.
- Connect the product loop to core's greenfield front door.

**Non-goals** (could-have-been-goals, deliberately dropped):

- **Importing a heavyweight product-ops toolkit's machinery** — a large fixed-type
  ontology, mandatory phase gates, write-time hooks, and a multi-section handoff packet
  (the mass that prior-art product toolkits tend to accrete). We lift *concepts and field
  sets*, not infrastructure; hooks fail Charter Principle 3.
- **A fixed product→strategy→capability→feature→story ladder.** ADR-0019 rejected fixed
  SAFe ladders; we keep `Level` open and merely *seed* two named product altitudes.
- **Live tracker API integration** for the new rungs — projection stays one-way and
  by-hand, per RFC-0030 / `tracker-projection.md`.
- **Mandating either rung.** Neither is required; a feature-first repo never sees them.

## Proposal

### D1 + D2 — two open, seeded rungs; Level orthogonal to Scale

`Level:` becomes an **open** field (string), with a *recognized set* documented in
`intent-model.md`: `product-vision` › `product-strategy` › `capability` › `feature`.
"Open" means an adopter may name an intervening altitude; "recognized" means these are
the ones the skills prompt for and the templates seed. This honors ADR-0019's
"no fixed ladder" decision while closing the top of the ladder.

`scale-intake.md` carries **two** roles for Scale today (`scale-intake.md:29-30`):
it sets the *default Level* **and** it sets the *leaf-projection* (`app` → a same-repo
brief; `business-unit` → a per-component slice). This RFC changes **only the first**:
the Scale→Level *stamp* becomes a *suggested starting altitude*; the Scale→leaf-projection
role is **preserved unchanged** (it is load-bearing for `app` vs `business-unit` leaf
shape — see the spike note in Evidence). After the change, Scale still infers/confirms
(how many repos), but `frame-intent` **asks the altitude explicitly when the input is
concept-shaped or greenfield**, rather than defaulting to `feature`. Suggested starting
points: `app` greenfield concept → offer `product-vision`; `app` known feature →
`feature`; `business-unit` → `product-strategy` or `capability`. A suggestion the user
overrides in one word, not a silent stamp.

**Semantics.**

- **`product-vision`** — the existence bet. *Why this product should exist, for whom,
  through what wedge.* Aspirational/narrative; the altitude where "should we build this
  at all" lives.
- **`product-strategy`** — the path. *Given the vision, which problems do we solve, in
  which segment, in what order, under what guiding policy.* This is where a multi-feature
  product gets its sequencing and its coherent first move.

Vision sits above strategy (a strategy serves a vision); both sit above `capability`.

### D3 — either rung direct; skip allowed but observable

The recursion already produces "the next level down" and already supports child intents
at any lower `Level` (`recursive-decomposition.md`). So entering at any rung, or
skipping, needs no mechanism change — only two prompt-only behaviors in
`frame-intent` / `decompose-intent`:

- **Sibling-spawn detector.** *Trip condition (qualitative, not a fixed count):* the
  intent being framed **won't reduce to a single shippable slice** — framing it keeps
  forcing more than one sibling that each ship and test independently. The sibling
  *count* is a signal, not a threshold; the test is the shippability test
  `decompose-intent` already applies. When it trips, the agent **says so and offers** to
  frame the product parent, instead of silently emitting orphaned siblings. It offers,
  never blocks — "either rung directly" still holds.
- **Retroactive parent — with an altitude rule.** When a rung was skipped and multiple
  intents already exist, the agent reconstructs a parent and back-links the siblings via
  the existing `Parent intent:` field (`intent-template.md:14`), reusing
  `decompose-intent`'s upward-feedback edge. **The reconstructed parent's altitude is
  inferred, not assumed to be a product rung:** if the siblings are *architectural
  slices of one buildable thing*, the parent is a `capability`; if they are *independent
  value bets that together constitute one product*, the parent is `product-vision`/
  `product-strategy`. The agent names the inferred altitude and lets the user correct it
  — decoupling Level from Scale (D2) removes the old altitude anchor, so this inference
  is explicit and confirmable rather than silent. Skipping never traps you; the parent
  is reconstructable.

The decomposition boundary becomes explicit: the product→capability→feature cut is where
multi-feature fan-out belongs, and the sibling-spawn signal marks it.

### D4 — one new de-risk assumption-kind

`de-risk-intent` maps the dominant assumption *kind* to the intent's level
(`capability → architectural/adoption`; `feature → desirability`). Add one row with a
**distinct token, not the word "desirability" again**:
**`product-vision`/`product-strategy` → `market-existence` = will-anyone-want-this-at-all
(market desirability) + can-this-be-a-business (viability)** — closing the Cagan
viability risk we don't cover today. This is **categorically distinct from the
`feature → desirability` row** (per survey F3): feature desirability asks "do users want
*this feature*"; `market-existence` asks "is there a product here at all." Naming them
with one token is exactly the conflation that produces validation theatre, so the kinds
get different tokens and D-prose says so. It reuses the **existing pre-PMF
qualitative-bar** machinery in `kill-condition.md` ("proceed only if ≥ 4 of 6 target
users complete the task unaided") — no new de-risk mechanism. The `market-existence` bet
is tested **once at the top**, not re-litigated N times across sibling features.

### D5 — field sets (seeded)

`frame-intent`'s `assets/intent-template.md` gains two level-conditional field blocks,
filled only when the intent is at that rung:

- **`product-vision`:** customer-shaped pitch · the change (what's different for the
  customer) · the job + struggling moment · who, by circumstance (early adopter, not
  demographic) · existing alternatives (what they do today, badly) · narrowest wedge
  (smallest version someone pays for now) · demand evidence (behavior/payment, not
  stated interest) · open assumptions, tiered (`must-test-before-shipping` /
  `accept-as-bet` / `will-monitor-post-ship`) · counter-metrics.
- **`product-strategy`:** central challenge (diagnosis) · guiding policy · coherent
  actions (3–5) · problem/segment sequence (which, in what order, why now) · horizon.

These are prose/short-field, agent-promptable from a single markdown file.

### D6 — the init-project seam

Core's `init-project` stage 2 ("value gate") consumes *fed-in discovery* from three
named sources (`research` output, a PRD, a `receive-brief` brief) and never names
`frame-intent`. Add `frame-intent`/`intent` as a **fourth recognized discovery source**,
and document that `frame → de-risk → decompose` hands its leaf into `init-project`. This
closes the seam where a greenfield product concept falls between the product loop and
the repo front door.

**This is a cross-package, by-reference-only edit, and it is treated as structural — not
a changelog one-liner.** `init-project` composes other skills strictly *by reference,
never by import* (`init-project/SKILL.md:145-146`) and forbids *performing discovery
itself* (`:128`). The seam respects both: it names `intent` as one more upstream
discovery shape that `init-project` *receives*, importing nothing from
`product-engineering`; `init-project` still performs no discovery. Because this adds a
named cross-pack reference (a structural change under `docs/CONVENTIONS.md`'s risk
triggers), the `core` follow-on **records the reference in its ADR/spec**, not merely a
changelog line.

### Migration

No data migration. Existing intents are `capability`/`feature` and stay valid (the
recognized set is a superset). The `Level:` enum widens; the Scale→Level *stamp* becomes
a *suggestion*. `decompose-intent`'s tracker-projection table gains rows for the two
rungs (see Open questions OQ1). Pack bumps: `product-engineering` 0.5.1 → **0.6.0**
(additive levels + field sets + de-risk kind), `core` a patch/minor for the
`init-project` seam doc.

## Options considered

**Axis: where the product altitude lives in the model** — exhaustive over {nowhere,
inside an existing rung, a new rung as the same artifact, a new *separate* artifact
type}. These cover every structural choice: don't model it · overload `capability` ·
extend the recursive intent · introduce a parallel type.

| Option | What | Trade-off | |
| --- | --- | --- | --- |
| **A. Do nothing** | Tell users to stamp `Level: capability` by hand | Zero work; but `capability` is *architectural span* with the wrong de-risk kind, the Scale→Level stamp still misroutes, and orphaned siblings persist. Cost of delay: every greenfield product concept keeps misrouting. | |
| **B. Overload `capability`** | Redefine `capability` to also mean product altitude | One fewer rung; but conflates architectural-span and product-existence — two different de-risk kinds — and still leaves no vision/strategy distinction. | |
| **C. New rung(s), same recursive `intent`** ★ | `product-vision`/`product-strategy` as higher `Level`s of the existing artifact | Matches ADR-0019's "same artifact at every level"; prompt-only; reuses recursion + de-risk. Cost: two new field blocks + enum widening. | |
| **D. New parallel artifact type** | A distinct `vision.md`/`strategy.md` type (separate per-rung templates, as heavier product toolkits use) | Cleaner per-type fields; but breaks the "one recursive artifact" model, needs new layout/discovery/decompose wiring, and trends toward heavyweight-toolkit mass. | |

★ **Recommended: C.** It is the only option that closes the altitude gap *and* the
Scale↔Level coupling while staying inside the one-recursive-`intent`, prompt-only model.

**Sub-axis (conditional on choosing C): how many product rungs** — {one merged product
rung · two (vision/strategy) · N-deep fixed ladder}. This sub-axis only arises *after*
the main axis selects "a new rung" — it is not a fourth main-axis option. One rung loses
the well-attested vision-vs-strategy distinction (Cagan; common across product-ops toolkits); the **N-deep
arm is precisely the fixed ladder ADR-0019 rejected and this RFC lists as a Non-goal**
(see Non-goals) — so the rejection lives in exactly one place and this sub-axis defers to
it rather than re-deciding it. **Two seeded rungs over an open `Level` field** is the
middle that prior art supports and the charter tolerates.

## Risks & what would make this wrong

**Pre-mortem.**

- *It ships and adopters feel ceremony.* Failure mode: the rungs read as mandatory PM
  bureaucracy on a solo project. **Mitigation:** neither rung is mandatory, either is
  authorable directly, levels are skippable; you pay only for the rung you choose. The
  sibling-spawn detector *offers*, never blocks.
- *The two rungs blur in practice.* Failure mode: users can't tell vision from strategy
  and fill both with the same content. **Mitigation:** distinct field sets and a
  one-line "vision = why it should exist; strategy = the path" cue; if they still blur,
  the open field lets a user collapse to one.
- *Tracker projection has no home for the rungs.* **Mitigation:** see OQ1 (open, with a
  proposed default) — to keep the mapping in one place, it is not restated here.

**Key assumptions (falsifiable).**

- *The recursion already supports N levels above feature, so this is enum+prompt work, no
  engine change.* Falsifiable by finding a hardcoded two-level assumption in
  decompose/de-risk. **Checked — see Evidence.**
- *The pre-PMF qualitative-bar already covers the product-existence bet's currency.*
  Falsifiable if product-existence needs a de-risk currency `kill-condition.md` can't
  express. **Checked — the 0-to-1/pre-PMF qualitative bar fits.**
- *Adopters want a product altitude.* Falsifiable by adoption telemetry / feedback. Signal
  is currently n=1 (the reporting user) — see Open questions.

**Drawbacks.** Two more recognized levels widen the surface every product-engineering
skill reasons about (frame, de-risk, decompose, tracker-projection, the guide). The
`init-project` seam couples `core` doc to a product-engineering concept by *name* (not by
import) — a small narrative coupling. And "open `Level` field" trades enum-tidiness for
flexibility, so lint can't enforce a closed set.

## Evidence & prior art

**Spike / de-risk result (riskiest assumption: no engine change needed).** Three distinct
claims, each verified separately against the shipped pack — they are *not* the same claim:

1. *The decomposition recursion needs no change.* `recursive-decomposition.md:14` states
   "**Above feature level → produce child intents at the next lower `Level:`**" —
   N-levels-above-feature already works. **Confirmed.**
2. *The Scale→Level change is a stamp→suggestion edit, and it must NOT sever
   Scale→leaf-projection.* `scale-intake.md:29-30` gives Scale **two** roles — the
   default Level (which becomes a suggestion) *and* the `app`-brief / `business-unit`-slice
   leaf-projection (which is **preserved**). D2 edits only the first; the second is
   load-bearing for leaf shape and is explicitly kept. **Confirmed and scoped.**
3. *The `market-existence` de-risk reuses existing machinery.* `kill-condition.md` already
   carries a **"0-to-1 / pre-PMF → qualitative bar"** mode that fits the `market-existence`
   currency. **Confirmed.**

The change therefore reduces to: the `Level:` enum (`intent-template.md:11`), the
framing/decompose prompts, two field blocks, one de-risk-kind row, the tracker table, and
the by-reference `init-project` seam doc — **no engine, no hook, no new skill. Spike passes.**

**Repo precedent.**

- **ADR-0019** (Accepted 2026-06-13) — the intent ontology this RFC refines via a
  follow-on ADR (ADRs are immutable, so the decision is recorded in a new, superseding/
  refining ADR rather than edited in place). It
  **explicitly rejected fixed work-item ladders** ("the levels disagree across tools…
  reifying the pyramid encodes the story=spec falsehood"), establishing that `Level` is
  open by design. The shipped `capability | feature` enum over-narrowed it; this RFC
  realigns the implementation with the decision.
- **RFC-0030** — the pack's founding RFC. Its steel-thread already names a
  **"vision/intent root"** above outcome that "gives the taste-led mode a home" (§ spine);
  v1 collapsed it to capability/feature. This RFC ships the root RFC-0030 anticipated.
- `frame-intent/references/scale-intake.md` — the hardwired Scale→Level default (root
  cause). `decompose-intent/references/{recursive-decomposition,tracker-projection}.md`
  and `de-risk-intent/references/kill-condition.md` — the reused mechanisms.
- core `init-project/SKILL.md` stage 2 — the three discovery sources the seam extends.

**External prior art** (full survey + citations: `0043-notes/survey-product-rung.md`;
applied/practitioner mode). Each fetched and confirmed to contain the borrowed claim:

- **A prior internal product toolkit** implements the same shape — a vision artifact
  gated on validated learnings, a Rumelt-style strategic-intent
  (diagnosis / guiding-policy / coherent-actions), and a multi-lens assumption map.
  Confirms the two-rung split and seeds the field sets. We borrow concepts/fields freely,
  **not** the hooks/fixed-type-ontology/phase-gates (too heavy for our charter).
- **Convergent existence-test elements** across four independent lineages — JTBD
  *struggling moment* (Christensen), Lean Canvas *Early Adopters* + *Existing Alternatives*
  (Maurya), GStack `/office-hours` *narrowest wedge* + *demand reality* (Tan/YC), Amazon
  *PR-FAQ* "so what?" gate — all point at {job, who-by-circumstance, wedge,
  demand-evidence}, which is the `product-vision` field set.
- **Cagan/SVPG four risks** supply the de-risk kind: value + **viability** (the one of the
  four we don't cover). **North Star / Aha!** are alignment tools that *presuppose* the
  product exists — explicitly **not** used as the existence gate (a finding, not a lift).

**Promoted research.** The full applied-mode survey — findings F1–F5, per-finding
confidence tags, Known unknowns, and all citations — lives in the companion
`docs/rfc/0043-notes/survey-product-rung.md`; summarized above, not duplicated here.

## Open questions

- **OQ1 — Tracker-projection rows for the two rungs.** Default: map both to a
  higher/intervening tier (Jira Align Theme/Strategy tier; Linear → Initiative/label;
  `none` → markdown, unchanged), settled at spec time. owner: eugenelim · decide-by: spec.
- **OQ2 — `product-strategy` at `app` scale.** Default: available at any Scale, mandatory
  at none (covered by "either rung directly"). A solo greenfield repo will often author
  only `product-vision`. owner: eugenelim · decide-by: spec.
- **OQ3 — Adopter demand beyond n=1.** Default: ship behind the pack's normal opt-in and
  watch for feedback; the design's optionality means a low-cost bet even if uptake is
  thin. owner: eugenelim · decide-by: post-ship review.

## Follow-on artifacts

Filled in on acceptance:

- **ADR refining ADR-0019** (a new, superseding/refining ADR — ADR-0019 itself is
  immutable) — record the open-`Level` recognized set + the Level/Scale decoupling.
- **Spec** `docs/specs/product-rung/` — the `frame-intent` / `de-risk-intent` /
  `decompose-intent` edits, field-set templates, sibling-spawn + retroactive-parent
  behaviors, tracker-projection rows, and the `init-project` seam. `product-engineering`
  0.5.1 → 0.6.0; `core` bump for the seam.
- **Guide touch-up** — `product-engineering` Diátaxis explanation/reference: the new rungs
  and the Level-vs-Scale model.
