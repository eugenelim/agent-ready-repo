# Run a market and competitive analysis

**Use this when:** you need a defensible, committed read on internal position, competitive structure, macro forces, or portfolio mix — one artifact per question.
**Prerequisites:** `product-strategy` pack installed.
**Result:** one or more committed analysis artifacts in `docs/product/shaping/` — `swot-analysis.md`, `competitive-landscape.md`, `macro-environment.md`, or `portfolio-position.md` — each a standalone readable document.

You need a defensible picture of where the product stands — internal position,
competitive pressure, macro forces, portfolio mix — and you want each part
committed as an artifact a stakeholder can read, not a slide that evaporates.
Pillar 1 gives you four analysis frameworks, one per question. Run the ones the
situation warrants; you rarely need all four in the same week.

This guide assumes you have the pack installed and know what SWOT and Porter's
Five Forces are. It covers which framework answers which question, what each
writes, and where the analyses overlap.

## Pick the framework by the question

Each skill owns one question and writes one artifact to `docs/product/shaping/`.

| The question you're asking | Skill | Artifact |
| --- | --- | --- |
| Where are we strong and exposed, and what's open to us? | `run-swot` | `swot-analysis.md` |
| How much pressure is the competitive structure putting on us? | `run-porters-five-forces` | `competitive-landscape.md` |
| What macro forces are moving under us? | `run-pestle-analysis` | `macro-environment.md` |
| Where does each product sit in the portfolio? | `run-bcg-matrix` | `portfolio-position.md` |

Reach for the full reference table — every Pillar-1, -2, and -3 skill in one
place — at [Frameworks and artifacts](../reference/frameworks-and-artifacts.md).

## Run the internal-and-immediate read: SWOT

Start here when you need a fast, shared read on the product's own position.

> Run a SWOT for the payments product.

`run-swot` works the four quadrants — Strengths, Weaknesses, Opportunities,
Threats — and commits `swot-analysis.md`. Strengths and Weaknesses are internal
and present-tense; Opportunities and Threats are external and forward-looking.
The common failure is a SWOT that lists adjectives. Push each entry to a concrete
claim with a consequence: not "strong brand" but "brand recognition lets us
charge a 15% premium in the enterprise segment." A quadrant of vague nouns
produces a document nobody acts on.

## Run the competitive-structure read: Porter's Five Forces

Use this when the pressure is coming from the market's shape, not one rival.

> Run Porter's Five Forces on the market we're entering.

`run-porters-five-forces` assesses Supplier Power, Buyer Power, threat of New
Entrants, threat of Substitutes, and the intensity of Rivalry, and commits
`competitive-landscape.md`. It answers *how attractive is this market's
structure* — a different question from *who are our competitors*. Rate each force
and say what makes it high or low; a force marked "high" with no mechanism is an
assertion, not an analysis. Where Porter and SWOT overlap — Threats in the SWOT,
New Entrants and Substitutes in Porter — let the SWOT stay at the headline and
the Five Forces carry the structural detail. Don't duplicate the same paragraph
into both artifacts.

## Run the macro read: PESTLE

Use this when the forces that matter sit outside the market entirely.

> Run a PESTLE scan for the regulated-markets expansion.

`run-pestle-analysis` sweeps Political, Economic, Social, Technological, Legal,
and Environmental factors and commits `macro-environment.md`. The pitfall is
completeness theatre — filling all six categories evenly when only two actually
move your product. Weight the categories to the decision. A fintech expansion is
mostly Legal and Political; a consumer-hardware line is mostly Economic and
Environmental. Note the thin categories as thin rather than padding them.

## Run the portfolio read: BCG matrix

Use this when the unit of analysis is a set of products, not one product.

> Place our product line on a BCG matrix.

`run-bcg-matrix` positions each product across Stars, Cash Cows, Question Marks,
and Dogs on the growth-share grid, and commits `portfolio-position.md`. It needs
more than one product to be meaningful — a single-product company gets little
from it. Ground the placement in the two axes it actually uses (market growth and
relative share); a placement with no numbers behind it is a guess dressed as a
matrix.

## Sequencing and overlap

There is no fixed order, but a common flow is PESTLE and Porter to establish the
outside, then SWOT to fold that into the product's own position, then the BCG
matrix if a portfolio decision is on the table. Each artifact stands alone, so a
reader can open `competitive-landscape.md` without having read the SWOT. When two
frameworks touch the same fact, cite it once in the artifact that owns it and
reference across rather than copying — drift between two copies of the same claim
is worse than a cross-reference.

These four are the *analysis* half of Pillar 1. The forcing functions that turn
this picture into committed direction — the OKR cascade, the PRFAQ, stakeholder
synthesis — are the other half; see
[Cascade OKRs into the shaping queue](cascade-okrs-into-the-shaping-queue.md).

## See also

- [Run your first SWOT](../tutorials/run-your-first-swot.md) — the guided first pass at `run-swot`.
- [Cascade OKRs into the shaping queue](cascade-okrs-into-the-shaping-queue.md) — turn the picture into build-ready work.
- [Frameworks and artifacts](../reference/frameworks-and-artifacts.md) — the complete skill-to-artifact map.
- [Why strategy is its own seat](../explanation/why-strategy-is-its-own-seat.md) — why these artifacts sit upstream of the build packs.
