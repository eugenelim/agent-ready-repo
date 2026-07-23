# Cascade OKRs into the shaping queue

**Use this when:** you have company objectives and need to turn the gaps they expose into typed shaping-queue entries the build loop picks up automatically.
**Prerequisites:** `product-strategy` pack installed and `workspace.toml` present in the repo.
**Result:** an `okr-cascade.md` in `docs/product/shaping/` and `{type = "strategy"}` gap entries appended to the initiative's shaping queue in `workspace.toml`.

You have company objectives, and you need them to become work the build loop
picks up — not a slide that stops at the leadership offsite. This guide covers
the three Pillar-1 skills that carry an objective from altitude down to a typed
shaping-queue entry: `run-okr-cascade`, `write-prfaq`, and
`synthesize-stakeholder-research`.

It assumes the pack is installed and that `workspace.toml` exists in the repo the
downstream product-engineering pack reads. Skip the OKR primer; this is about
wiring, not definitions.

## Cascade the objectives: `run-okr-cascade`

This is the skill that closes the gap between strategy and the build queue.

> Cascade our FY objectives down to the shaping queue.

`run-okr-cascade` walks company objectives down through team level and, at the
bottom, identifies the gaps that have no product answer yet. It commits two
things:

- `okr-cascade.md` in `docs/product/shaping/` — the readable cascade, company to
  team to gap.
- `{type = "strategy"}` entries appended to `["ini-NNN".shaping_queue].backlog`
  in `workspace.toml`.

The `workspace.toml` write is the load-bearing part. The product-engineering
pack's `frame-situation` reads that backlog as its shaping queue, so a
`{type = "strategy"}` gap becomes work the downstream pack shapes without anyone
copying it across by hand. Treat the cascade as the wire and `workspace.toml` as
the socket the build packs plug into.

Two things to get right:

- **Only real gaps become entries.** An objective already covered by in-flight
  work is not a gap. Cascading every objective into the backlog floods the queue
  and trains `frame-situation` to ignore it. Emit an entry only where there is no
  product answer yet.
- **The `ini-NNN` initiative must match** the one the downstream pack reads. A
  gap written under the wrong initiative id is invisible to `frame-situation` —
  it will sit in `workspace.toml` doing nothing.

## Force the altitude-0 commitment: `write-prfaq`

An objective survives contact with reality when someone commits to its outcome in
concrete terms. The PRFAQ is that forcing function.

> Write a PRFAQ for the objective we cascaded.

`write-prfaq` produces the press release plus FAQ — the artifact that states, at
altitude 0, what the world looks like when the objective has landed and answers
the hard questions in advance. It commits `prfaq.md` to `docs/product/shaping/`.
Run it against a cascaded objective and the vagueness surfaces fast: a PRFAQ you
can't write a credible press release for is an objective that isn't yet real. Use
it as the pressure test on the cascade output, not as a launch document.

## Fold in the stakeholder picture: `synthesize-stakeholder-research`

Objectives don't exist in a vacuum; stakeholders have already said things that
should shape the cascade.

> Synthesize the stakeholder research into a strategic narrative.

`synthesize-stakeholder-research` reads across stakeholder groups and builds a
strategic narrative by theme, committing `stakeholder-synthesis.md`. It
**consumes** existing research — desk-research pack outputs, interview notes you
already have — it does not run interviews. If you have no source material, this
skill has nothing to synthesize; gather first, then synthesize. Run it before the
cascade when stakeholder input should inform which gaps matter, or after it to
sanity-check that the cascaded gaps reflect what stakeholders actually raised.

## A working order

A common sequence: synthesize the stakeholder picture, cascade the objectives
against it, then PRFAQ the top gap to pressure-test it. But the skills are
independent — each commits its own artifact — so run only the ones the situation
needs. The one that changes downstream behaviour is `run-okr-cascade`; the other
two sharpen its input and output.

## See also

- [Run a market and competitive analysis](run-a-market-and-competitive-analysis.md) — the analysis half of Pillar 1 that frames the objectives.
- [Set UX and content strategy](set-ux-and-content-strategy.md) — the experience and content direction that runs alongside the cascade.
- [Frameworks and artifacts](../reference/frameworks-and-artifacts.md) — the complete skill-to-artifact map.
- [Why strategy is its own seat](../explanation/why-strategy-is-its-own-seat.md) — how the cascade wires strategy into the build loop.
