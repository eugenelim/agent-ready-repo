# The walk's handoff premise was false, and the evidence that settles it

Recorded 2026-09-11. This note exists because this spec's Objective deliberately
differs from the S7 row of
[`sdlc-guide-uplift-and-learning-paths.md`](../../../product/briefs/sdlc-guide-uplift-and-learning-paths.md),
and a reader is owed the reason without reconstructing it.

## The inherited claim

S6 shipped, and the brief's S7 row repeats, that the four packs form one
ordered sequence in which **each step hands a named artifact to the next**. The
row's acceptance language asks for "one worked example carries a real artifact
across **all three handoffs**". Two surfaces assert it today:
`guides/README.md:82` and `web/src/pages/journeys/index.astro`.

None of S6's criteria tested the claim against the packs' own contracts.

## What the packs actually promise

Read in sequence order from `packs/<pack>/JOURNEY.md` frontmatter:

| Seam | Upstream `youReceive` | Downstream `youProvide` | Agrees |
| --- | --- | --- | --- |
| desk-research → product-strategy | a confidence-graded synthesis brief | "any prior desk-research outputs" | yes, and the input is optional |
| product-strategy → experience-design | SWOT, PRFAQ, OKR gap entries, `ux-strategy.md`, `content-strategy.md` | "the feature, user, and intended outcome, plus any existing brand or design-system constraints" | **no** |
| experience-design → product-engineering | a complete, independently-reviewed design set | "a product idea or problem description" | **no** |

And `product-engineering`'s `youReceive` ends at "a build-ready decision brief",
while `guides/README.md:88` promises the reader "a change you approved before it
merged".

## Why the packs are right and the surfaces are wrong

Each of these was read directly, not taken from a reviewer's summary.

- **`docs/specs/discovery-loop/spec.md` — Shipped.** `product-engineering` is
  "a raw idea" converged into "a ratified, build-ready decision brief"; its
  AC32 wires the G3 handoff *out* to `work-loop`. Extending the pack through
  merge would contradict a Shipped contract.
- **`docs/specs/experience-pack/spec.md:49` — Shipped.** Every experience-design
  skill must be "standalone-useful (elicit its inputs inline when upstream
  product artifacts are absent)". A required strategy input contradicts it.
- **`packs/product-strategy/DESIGN.md:9`.** Strategy branches to *both*
  downstream packs: the OKR cascade feeds product-engineering's shaping queue,
  and `ux-strategy.md` plus `content-strategy.md` feed experience-design. It is
  a fork, not a link in a chain.
- **`packs/experience-design/DESIGN.md:263–274`.** The strategy inputs are
  "optional; the skills degrade gracefully when absent", and the downstream
  handoff is one artifact — `user-flow`'s per-screen state matrix — consumed by
  one skill in the product-engineering pack. A narrow skill-to-skill seam, not
  a whole-pack handoff.

  **The consuming skill is `ux-writing`, not the `voice-and-microcopy` this
  DESIGN.md names twice.** `packs/product-engineering/.apm/skills/ux-writing`
  exists and `voice-and-microcopy` does not. The design record is stale on the
  name; the seam it describes is real. Surfaces this slice writes name
  `ux-writing`, and repairing `packs/experience-design/DESIGN.md` is routed to
  that pack, because a pack source edit is a released pack change this slice's
  boundary excludes.
- **`guides/README.md:98–109`.** P3 already owns build and merge and already
  ends at "a merged change, and the decision to merge is yours".

## The correction, and its authority

Owner decision, 2026-09-11: **keep the four packs in their editorial order and
make the surfaces tell the truth**, rather than amend the packs to match the
surfaces.

The true relationships this spec's surfaces must state:

1. Desk-research evidence *may* feed product-strategy.
2. Product-strategy anchors are *optional* inputs to both experience-design and
   product-engineering.
3. The experience-design → product-engineering seam is the per-screen state
   matrix, read by `ux-writing`.
4. Product-engineering ends at an approved, build-ready decision brief.
5. Build, review and merge belong to P3 and the `core` build loop, which the
   walk routes onward to.

## What this forecloses, and what it does not

It forecloses describing the walk as three mandatory whole-pack handoffs. It
does **not** foreclose the four-pack membership or their recommended order,
both of which survive unchanged.

It also removes this slice's largest risk: no `packs/*/JOURNEY.md` changes, so
no version bumps, no changelog entry, no self-host or marketplace regeneration,
and no released pack change.

## Consequences for artifacts this slice does not own

- The brief's S7 row carries the false premise at line 225 and is narrowed by
  this slice under the owner decision above.
- [`s7-walkability-handoff.md`](../../../product/findings/s7-walkability-handoff.md)
  carries it too, and is marked superseded on that point rather than rewritten.
