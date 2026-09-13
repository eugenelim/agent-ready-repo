# Walk — `desk-research`, `product-strategy`, `product-engineering`, `core`

Walked 2026-09-12 against the rendered site: 15 steps, 45 skills.
Method and owner routing in [README.md](README.md). The
`experience-design` walk, which established the method, is
[here](experience-design.md).

These four were authored *after* the method existed, so most of what the first
walk found was designed out rather than discovered. What remained is below.

## Findings

| # | Dimension | Owner | Finding | State |
| --- | --- | --- | --- | --- |
| 1 | Human vs agent | guide | `product-engineering` declares four gates and the guidebook carried three — `approve-decision-brief` had no decision point anywhere in the walk | Fixed — it sits on `place-bet`, where the bet is still cheap to change |
| 2 | Human vs agent | guide | `desk-research` showed `set-research-scope-and-depth` twice, reading as two decisions | Fixed — the two are alternative routes, and the second now says so |
| 3 | Orientation | guide | `core` walks 10 of its 18 skills and `desk-research` 11 of 12, with the omissions unmentioned. A reader who knows the pack has eighteen assumes the walk lost eight | Fixed — both entry pages name what is off the path and why |
| 4 | Handover | guide | Four guidebooks ended by pointing at the guides hub and saying the work "is picked up by" the next pack, naming no page | Fixed — ten cross-pack edges, each stated at both ends |
| 5 | Artifact | skill | `define-content-strategy` cited "the Halvorson content strategy quad (Brain Traffic, 2018 revision)" for sections that appear in neither published quad | Fixed in the pack — the citation was wrong, the sections are unchanged |
| 6 | Artifact | guide | 21 of 45 skills ship no output template, so their previews were section lists | Partly fixed — three now excerpt a real artifact produced by running the skill; the rest remain shape-only |

## What the method caught that authoring did not

Finding 1 is the one worth keeping. The step *prose* said "the pack's third
gate", so reading the page left the impression the gate was covered. Only
counting `You decide` markers against the journey's declared gate list showed
that no skill carried it. A walk that reads for sense would have missed it; the
count is what found it.

Finding 3 is the same shape: nothing on the page was wrong, and the omission was
invisible without comparing the walked set against the published set.

## Two things the checks caught during the walk, not after

- Adding a table of non-walked skills inside `## What you will run` made those
  rows read as step-map rows, and the lint refused them. Correctly: pack-level
  scope is not step-level information, and it moved to the entry pages.
- `guides/core/` already held a cross-kind reading thread at orders 9–12.
  Authoring a guidebook beside it made the whole directory a guidebook under the
  scoping rule of the time, and 90 findings were reported against pages that had
  done nothing wrong. The rule now takes two signals.

## Open, routed out of the guide

- **18 of 45 skills still have no output template** (finding 6). Each one is a
  place where the guide shows a shape it cannot verify. Running the skill and
  keeping the artifact closes one at a time; three are done.
- **The journey contract still has no field for run order** — carried over from
  the first walk, and the reason a guidebook's skill sequence is authored rather
  than projected.
