# Run your first SWOT

**What you'll build:** a committed `docs/product/shaping/swot-analysis.md` — a four-quadrant read of one product's position in the shaping surface.
**Prerequisites:** `product-strategy` pack installed and a repo with (or happy to create) a `docs/product/` tree.
**Time:** 20–30 minutes from standing start to committed artifact.

By the end you'll have a committed `docs/product/shaping/swot-analysis.md` —
a four-quadrant read of one product's position — and you'll have seen where it
lands in the shaping surface the downstream build packs read. One skill,
`run-swot`, from a standing start to a committed artifact.

You need the `product-strategy` pack installed. It installs to user scope, so the
skill loads in whatever workspace you're in.

## 1. Pick the product and open the workspace

Work in a repo that has a `docs/product/` tree, or where you're happy for one to
be created. Have one product in mind — the thing the SWOT is about.

You should see a normal working repo. Nothing has happened yet; this step only
sets where the artifact will land.

## 2. Ask for the SWOT

In your agent, say what you want in plain language:

> Run a SWOT for our payments product.

`run-swot` activates. It works one quadrant at a time — Strengths, Weaknesses,
Opportunities, Threats.

You should see the skill begin the SWOT and start on the first quadrant, naming
the product you gave it.

## 3. Answer for the internal quadrants

The skill works Strengths and Weaknesses first. These are internal and
present-tense — what's true about the product today.

Give concrete claims, not adjectives. "Brand recognition lets us charge a 15%
premium with enterprise buyers" is a Strength; "good brand" is not.

You should see each internal quadrant fill with specific, present-tense entries
about the product itself.

## 4. Answer for the external quadrants

The skill moves to Opportunities and Threats. These are external and
forward-looking — what the market opens or threatens.

You should see the two external quadrants fill with forward-looking entries
pointed at the market, distinct from the internal claims above them.

## 5. Review the assembled analysis

The skill shows you the full four-quadrant SWOT before it writes anything.

Read it as a whole. Check that every entry is a claim with a consequence, not a
lone noun. If a quadrant reads thin or vague, say so and the skill reworks it.

You should see all four quadrants together, and you should be asked to confirm
before it commits.

## 6. Commit the artifact

Approve. The skill writes `swot-analysis.md` into `docs/product/shaping/`.

You should see a new file at `docs/product/shaping/swot-analysis.md` containing
the four quadrants you reviewed.

## 7. See where it landed

Open `docs/product/shaping/`. Your `swot-analysis.md` sits alongside whatever
other strategy artifacts the pack has produced. This directory is the shaping
surface — the committed strategy artifacts the downstream product-engineering and
experience-design packs draw on.

You should see `swot-analysis.md` in `docs/product/shaping/`, committed and ready
for a reviewer to open on its own.

## What you did

You took one product from a standing start to a committed, four-quadrant strategy
artifact in the shaping surface — the same surface every other Pillar-1 skill
writes to. The next market picture usually needs more than a SWOT: the
competitive structure, the macro forces, the portfolio position. Reach for those
in [Run a market and competitive analysis](../how-to/run-a-market-and-competitive-analysis.md).

## See also

- [Run a market and competitive analysis](../how-to/run-a-market-and-competitive-analysis.md) — the other three Pillar-1 analysis frameworks.
- [Frameworks and artifacts](../reference/frameworks-and-artifacts.md) — every skill and the file it writes.
- [Why strategy is its own seat](../explanation/why-strategy-is-its-own-seat.md) — why this artifact sits upstream of the build packs.
