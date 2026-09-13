---
title: "Read the situation"
summary: "Establish what is true about the market and the organisation before committing to a direction."
pack: product-strategy
kind: how-to
order: 1
---

# Read the situation

**Step 1 of 3 — Read the situation**
<!-- rung: packs/product-strategy/JOURNEY.md -->

**What changes:** Opinion about the market becomes a committed situation artifact with evidence behind each claim.
<!-- rung: packs/product-strategy/JOURNEY.md -->

**What you need first:** A scope — which market, which part of the organisation, over what horizon — and any research you hold.
<!-- rung: authored -->

*Skipping costs:* Direction is set against an imagined market, and nothing downstream can tell which parts were evidenced.
<!-- rung: authored -->

**Concepts:**
<!-- rung: authored -->

- [Why strategy is its own seat](../explanation/why-strategy-is-its-own-seat.md) explains why this layer sits upstream of product discovery rather than inside it.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `synthesize-stakeholder-research` | Interview notes, surveys, or support transcripts | Convergent themes across stakeholder groups, with their sources. | Optional |
| `run-pestle-analysis` | A scope — market, region, time horizon | Political, economic, social, technological, legal and environmental forces, prioritised. | Optional |
| `run-porters-five-forces` | A defined industry boundary | The five forces assessed, and what they say about industry attractiveness. | Optional |
| `run-bcg-matrix` | The portfolio, and share and growth estimates | Each product placed by share and growth, with investment implications. | Optional |
| `run-swot` | The upstream analyses, if you ran them | Strengths, weaknesses, opportunities and threats, with the implications. | Required |

Prompts go into an AI agent session with this pack installed — the same session
throughout. Every artifact below commits to `docs/product/shaping/`, which is the
path downstream packs read by name, so the filenames are fixed rather than
project-specific.

<!-- rung: packs/product-strategy/JOURNEY.md -->

## Run `synthesize-stakeholder-research` — what people actually said

**You type:**
<!-- rung: packs/product-strategy/.apm/skills/synthesize-stakeholder-research/SKILL.md -->

```
Synthesize our stakeholder interviews into the themes that recur across groups, and say which group each came from.
```

**Agent returns:**
<!-- rung: packs/product-strategy/.apm/skills/synthesize-stakeholder-research/SKILL.md -->

> **Agent:** Done — I've written a synthesis naming each stakeholder group, the themes per group, and where they converge to `docs/product/shaping/stakeholder-synthesis.md`.

**You push back:**
<!-- rung: packs/product-strategy/.apm/skills/synthesize-stakeholder-research/SKILL.md -->

> **You:** You merged the sales and support themes into one voice. Keep them separate — they want opposite things, and that disagreement is the finding.
>
> **Agent:** I separated the two groups, kept the conflicting themes distinct, and named the disagreement as a convergent signal in its own right.

**Output varies** with how many groups you have research for and how much they disagree.
<!-- rung: packs/product-strategy/.apm/skills/synthesize-stakeholder-research/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (grounded):** Ask which input each theme came from; this surfaces themes assembled from the agent's expectations rather than from your research.
<!-- rung: packs/product-strategy/.apm/skills/synthesize-stakeholder-research/SKILL.md -->

**Watch out for:** A tidy synthesis flattens the disagreements that matter most. Notice a theme attributed to every group at once, and ask which group did not say it.
<!-- rung: packs/product-strategy/.apm/skills/synthesize-stakeholder-research/SKILL.md -->

**Where it lands:** `docs/product/shaping/stakeholder-synthesis.md`.
<!-- rung: packs/product-strategy/.apm/skills/synthesize-stakeholder-research/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
---
type: stakeholder-synthesis
---
# Stakeholder synthesis — <scope>

## <stakeholder group>

- **Theme:** <what this group said> — source: <interview, survey, ticket>

## Convergent signals

- <theme two or more groups reached independently>

## Divergent signals

- <where groups want opposite things — kept apart, not merged>
```

*Section shape only, taken from the skill's own procedure. This pack ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Run `run-pestle-analysis` — the macro forces

**You type:**
<!-- rung: packs/product-strategy/.apm/skills/run-pestle-analysis/SKILL.md -->

```
Run a PESTLE for our market over the next three years, and prioritise by impact and time horizon.
```

**Agent returns:**
<!-- rung: packs/product-strategy/.apm/skills/run-pestle-analysis/SKILL.md -->

> **Agent:** Done — I've written the six PESTLE dimensions assessed for your scope, prioritised by impact and time horizon to `docs/product/shaping/macro-environment.md`.

**You push back:**
<!-- rung: packs/product-strategy/.apm/skills/run-pestle-analysis/SKILL.md -->

> **You:** Most of these are global trends that apply to everyone. Cut anything that would not change a decision we are about to make.
>
> **Agent:** I removed the generic entries and kept the four forces with a named consequence for a decision in your horizon.

**Output varies** with the scope you set, the region, and how regulated the market is.
<!-- rung: packs/product-strategy/.apm/skills/run-pestle-analysis/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (falsifiable):** Ask what decision each force would change; this surfaces a list of things that are true but inert.
<!-- rung: packs/product-strategy/.apm/skills/run-pestle-analysis/SKILL.md -->

**Watch out for:** Six headings invite six paragraphs whether or not there is anything to say. Notice a dimension filled in for completeness, and delete it rather than let it dilute the prioritised set.
<!-- rung: packs/product-strategy/.apm/skills/run-pestle-analysis/SKILL.md -->

**Where it lands:** `docs/product/shaping/macro-environment.md`.
<!-- rung: packs/product-strategy/.apm/skills/run-pestle-analysis/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
---
type: macro-environment
---
# Macro environment — <industry>, <geography>

Horizon: <0–18mo | 18mo–3yr | 3yr+>

## Political
- <named policy or regulatory signal> — impact: <tailwind | headwind | neutral>
## Economic
- <indicator currently moving, and its direction>
## Social
## Technological
## Legal
## Environmental

## Priority forces

| Force | Horizon | Direction | Why material |
| --- | --- | --- | --- |
```

*Section shape only, following the PEST/PESTLE scan (Aguilar, 1967, extended). Variant names split the same core six differently. This pack ships no template — confirm the shape against what you get back.*

## Run `run-porters-five-forces` — the competitive structure

**You type:**
<!-- rung: packs/product-strategy/.apm/skills/run-porters-five-forces/SKILL.md -->

```
Assess the five forces for this industry and tell me where the structural profit pressure actually sits.
```

**Agent returns:**
<!-- rung: packs/product-strategy/.apm/skills/run-porters-five-forces/SKILL.md -->

> **Agent:** Done — I've written the five forces assessed against your industry boundary, with a synthesis of where the pressure sits to `docs/product/shaping/competitive-landscape.md`.

**You push back:**
<!-- rung: packs/product-strategy/.apm/skills/run-porters-five-forces/SKILL.md -->

> **You:** You drew the industry boundary around our product category, which makes substitutes look weak. Redraw it around the customer need and reassess.
>
> **Agent:** I redrew the boundary around the job the customer is hiring for; substitute threat moved from low to high and I reassessed rivalry with it.

**Output varies** with where you draw the industry boundary — the single choice that moves the result most.
<!-- rung: packs/product-strategy/.apm/skills/run-porters-five-forces/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (testable):** Redraw the boundary one level wider and ask which force changes; this surfaces an assessment resting on a flattering boundary.
<!-- rung: packs/product-strategy/.apm/skills/run-porters-five-forces/SKILL.md -->

**Watch out for:** The boundary is chosen before the analysis and decides most of it. Notice a boundary drawn around what you sell rather than what the customer is trying to get done.
<!-- rung: packs/product-strategy/.apm/skills/run-porters-five-forces/SKILL.md -->

**Where it lands:** `docs/product/shaping/competitive-landscape.md`.
<!-- rung: packs/product-strategy/.apm/skills/run-porters-five-forces/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
---
type: competitive-landscape
---
# Competitive landscape — <industry>, <geography>

## Supplier power — <High | Medium | Low>
<Concentration, switching cost, forward-integration threat.> Evidence: <fact>
## Buyer power — <rating>
## Threat of new entrants — <rating>
## Threat of substitutes — <rating>
## Competitive rivalry — <rating>

## Industry attractiveness — <High | Medium | Low>

Determining forces: <one or two>. Strategic implication: <move>.
```

*Section shape only, following Porter (HBR, 1979). Five forces exactly — the "sixth force" belongs to a different model. This pack ships no template — confirm the shape against what you get back.*

## Run `run-bcg-matrix` — where to invest

**You type:**
<!-- rung: packs/product-strategy/.apm/skills/run-bcg-matrix/SKILL.md -->

```
Map our portfolio on a BCG matrix and name the one investment decision it implies.
```

**Agent returns:**
<!-- rung: packs/product-strategy/.apm/skills/run-bcg-matrix/SKILL.md -->

> **Agent:** Done — I've written each product placed by relative market share and market growth, with the investment implication for each quadrant to `docs/product/shaping/portfolio-position.md`.

**You push back:**
<!-- rung: packs/product-strategy/.apm/skills/run-bcg-matrix/SKILL.md -->

> **You:** Two of these are estimates with no source. Mark them as estimates on the chart, because the quadrant boundary is where they sit.
>
> **Agent:** I marked both as estimated and noted that one sits close enough to the boundary that its quadrant depends on the estimate.

**Output varies** with how many products you have and how well you can estimate share and growth.
<!-- rung: packs/product-strategy/.apm/skills/run-bcg-matrix/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (grounded):** Ask what share and growth figures placed each product and where they came from; this surfaces a quadrant assigned by intuition.
<!-- rung: packs/product-strategy/.apm/skills/run-bcg-matrix/SKILL.md -->

**Watch out for:** A product near a boundary reads as firmly in one quadrant once it is drawn. Notice placements with estimated inputs, and treat their implications as provisional.
<!-- rung: packs/product-strategy/.apm/skills/run-bcg-matrix/SKILL.md -->

**Where it lands:** `docs/product/shaping/portfolio-position.md`.
<!-- rung: packs/product-strategy/.apm/skills/run-bcg-matrix/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
---
type: portfolio-position
---
# Portfolio position — <portfolio>

Thresholds: relative share <1.0> · market growth <10%>
Data basis: <measured | proxy — directional only>

| Offering | Rel. market share | Segment growth | Quadrant |
| --- | ---: | ---: | --- |
| <name> | <0.4> | <22%> | Question Mark |

## Investment implications

- **Stars** — <invest to hold leadership>
- **Cash Cows** — <harvest to fund Stars>
- **Question Marks** — <invest or divest>
- **Dogs** — <divest unless strategically held>

## Top reallocation decision
```

*Section shape only, following the BCG growth-share matrix (Henderson, 1970). Both axes are relative — share against the largest competitor, not absolute share. This pack ships no template — confirm the shape against what you get back.*

## Run `run-swot` — the situation, committed

**You type:**
<!-- rung: packs/product-strategy/.apm/skills/run-swot/SKILL.md -->

```
Synthesize this into a SWOT for our situation, and reference the PESTLE and five-forces work where it applies.
```

**Agent returns:**
<!-- rung: packs/product-strategy/.apm/skills/run-swot/SKILL.md -->

> **Agent:** Done — I've written strengths, weaknesses, opportunities and threats with the evidence for each, plus the strategic implications to `docs/product/shaping/swot-analysis.md`.

**You push back:**
<!-- rung: packs/product-strategy/.apm/skills/run-swot/SKILL.md -->

> **You:** The strengths are things we like about ourselves. Keep only the ones a competitor could not claim as well.
>
> **Agent:** I cut the four that any competitor could claim and kept the three that rest on something specific to you, with the evidence for each.

**Output varies** with which upstream analyses exist and how much evidence sits behind each entry.
<!-- rung: packs/product-strategy/.apm/skills/run-swot/SKILL.md -->

**You decide:** Approve the situation before direction is set — the pack's `approve-strategy-situation` gate. Everything downstream treats this as settled.
<!-- rung: packs/product-strategy/JOURNEY.md -->

**Check (falsifiable):** Ask which competitor could claim each strength; this surfaces a generic capability list dressed as a position.
<!-- rung: packs/product-strategy/.apm/skills/run-swot/SKILL.md -->

**Watch out for:** A SWOT is the easiest artifact to fill with plausible sentences. Notice entries with no cited evidence and no upstream artifact behind them.
<!-- rung: packs/product-strategy/.apm/skills/run-swot/SKILL.md -->

**Where it lands:** `docs/product/shaping/swot-analysis.md`.
<!-- rung: packs/product-strategy/.apm/skills/run-swot/SKILL.md -->

**What it looks like:**
<!-- rung: docs/product/pack-walks/samples/product-strategy/swot-analysis.md -->

```markdown
---
type: swot-analysis
---
# SWOT — Northwind Logistics, freight-booking product line

**Scope:** the freight-booking product line, not the whole company
**Horizon:** medium-term (12–24 months)
**Competitive reference point:** venture-funded digital freight brokers

## Strengths

- **Carrier density in the Midwest corridor.** 4,100 contracted carriers against
  the nearest competitor's ~900 in the same lanes. A competitor would need years
  of contracting to match it, not a product release.
- **Existing EDI integrations with 14 of the top 20 shippers.** Already built,
  already certified; new entrants quote 6–9 months per integration.
- **Pricing data from eight years of settled loads.** The dataset is the moat,
  not the pricing model built on it.

## Weaknesses

- **No mobile surface for drivers.** Every status update is a phone call to a
```

*A real artifact, not a section list: the opening of one produced by running the skill against a fictional scenario. Yours will differ in content and follow the same form.*

## Where this leads

**Done with this step:** You can move on when every SWOT entry cites evidence or an upstream artifact, and no strength is one a competitor could equally claim.
<!-- rung: authored -->

Stage 1 of three, and the pack's first human gate. Everything below treats this as settled.

**Next:** [Set the direction](set-the-direction.md).
<!-- rung: authored -->

**Go deeper:** [the `product-strategy` frameworks and artifacts reference](../reference/frameworks-and-artifacts.md) — every framework this step runs, and the artifact it commits.
<!-- rung: authored -->
