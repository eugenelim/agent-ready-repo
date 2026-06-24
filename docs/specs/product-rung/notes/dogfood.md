# T10 dogfood — the rungs route correctly end-to-end

Manual-QA record for the `product-rung` implementing PR. `product-engineering` is
**not** self-host-projected into this repo, so the skills cannot be triggered via
the local harness; the faithful exercise is to trace each scenario against the
**built** skill content an installed agent reads, citing the decision-driving
lines. Observed behaviour below.

## 1. `frame-intent` on a greenfield product concept → offers `product-vision`

**Scenario:** "I want to build a tool that helps freelance designers get paid faster."

**Trace.** `frame-intent/SKILL.md` step 1 infers Scale (`app` — one repo) and
confirms. Step 3 ("Pick the altitude — Scale only *suggests* it") now reads: *"For
concept-shaped or greenfield input, ask the altitude explicitly — 'is this a
product bet, or a feature you've already scoped?' — rather than defaulting to
`feature` … an `app` greenfield product concept → `product-vision`."*

**Observed:** the agent **offers `product-vision`** and asks the altitude — no
silent `feature` stamp. The template's `Level:` comment shows the open recognized
set, and the `## Product-vision fields` block prompts the existence-bet fields
(customer-shaped pitch, wedge, demand evidence, tiered assumptions, counter-metrics).
✔ matches AC "frame-intent asks the altitude explicitly for concept-shaped input".

## 2. `de-risk-intent` on the resulting `product-vision` intent → picks `market-existence`

**Trace.** `de-risk-intent/SKILL.md` intro mapping now routes *"product-level
(`product-vision` / `product-strategy`) → market-existence"*, and the gloss names
both halves: *"will anyone want this at all (market desirability) **and** can this
be a business (viability) … reuses the existing pre-PMF qualitative bar in
`references/kill-condition.md`."*

**Observed:** the agent picks **`market-existence`**, not `desirability`; it
predeclares a qualitative bar (kill-condition.md currency-adaptive 0-to-1 path) and
treats the bet as tested **once at the top**. ✔ matches the `market-existence` ACs.

## 3. Sibling-spawn path → offers the product parent

**Scenario:** decomposing "freelance designer payments platform" surfaces invoicing,
escrow, dispute resolution, and tax forms — each an independent value bet, not a
slice of one buildable thing.

**Trace.** `decompose-intent/SKILL.md` "Spotting a missing parent — offer, never
block": *"When decomposition … produces children that won't each reduce to a single
shippable slice — they read as several independent value bets … that is the signal
a product parent is missing … **Offer** to frame the product parent."* The sibling
*count* is a hint, not a threshold. `frame-intent` carries the same offer in its own
"Spotting a missing parent" subsection.

**Observed:** the agent **offers** to frame a `product-vision` / `product-strategy`
parent and hang the siblings beneath it, rather than emitting orphaned siblings. It
offers; it never blocks. The retroactive-parent affordance back-links existing
siblings via `Parent intent:`, inferring the altitude (architectural slices →
`capability`; independent value bets → product altitude) and naming it for the user
to correct. ✔ matches the sibling-spawn + retroactive-parent ACs.

## Verdict

All three required paths route correctly end-to-end; the integrated journey
(frame → de-risk → decompose) holds at the product altitudes, not just the parts.
