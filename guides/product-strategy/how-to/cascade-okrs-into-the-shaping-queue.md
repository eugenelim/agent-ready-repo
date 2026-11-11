---
title: Cascade OKRs into the shaping queue
summary: Convert objective gaps into traceable strategy gap files ready for product shaping.
pack: product-strategy
kind: how-to
---

# Cascade OKRs into the shaping queue

**Use this when:** you have company objectives and need to turn the gaps they expose into strategy gap files the build loop picks up automatically.
**Prerequisites:** `product-strategy` pack installed.
**Result:** an `okr-cascade.md` in `docs/product/shaping/` and one gap file per gap under `docs/product/captured/`.

You have company objectives, and you need them to become work the build loop
picks up — not a slide that stops at the leadership offsite. This guide covers
the three Pillar-1 skills that carry an objective from altitude down to a strategy
gap file: `run-okr-cascade`, `write-prfaq`, and
`synthesize-stakeholder-research`.

```text
Run an OKR cascade for our company goal of reducing enterprise churn.
```

It assumes the pack is installed. Skip the OKR primer; this is about
wiring, not definitions.

## Cascade the objectives: `run-okr-cascade`

This is the skill that closes the gap between strategy and the build queue.

> Cascade our FY objectives down to the shaping queue.

`run-okr-cascade` walks company objectives down through team level and, at the
bottom, identifies the gaps that have no product answer yet. It commits two
things:

- `okr-cascade.md` in `docs/product/shaping/` — the readable cascade, company to
  team to gap.
- One file per gap at `docs/product/captured/<gap-slug>.md`, with `Status: Open`,
  `Kind: intent`, and `Type: strategy`.

The gap files are the load-bearing part. The product-engineering pack's
`frame-situation` shapes each gap file whose `Type:` is `strategy`, so a gap
becomes work the downstream pack shapes without anyone copying it across by hand.
Treat the cascade as the wire and the gap file as the socket the build packs plug
into. A gap is just its file: nothing is added to `workspace.toml`.

Two things to get right:

- **Only real gaps become files.** An objective already covered by in-flight
  work is not a gap. Cascading every objective into gap files floods the shaping
  list and trains `frame-situation` to ignore it. Write a file only where there is
  no product answer yet.
- **Close a gap in its file.** When a gap is settled, set `Status: Closed` and add
  `Resolution:` to the same file, so nothing else needs editing.

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

## What you have now

You have an `okr-cascade.md` that connects company objectives to team-level
work and identifies real gaps. Each gap is its own file under `docs/product/captured/`, so
product engineering can pick them up for further shaping.

## See also

- [Run a market and competitive analysis](run-a-market-and-competitive-analysis.md) — the analysis half of Pillar 1 that frames the objectives.
- [Set UX and content strategy](set-ux-and-content-strategy.md) — the experience and content direction that runs alongside the cascade.
- [Frameworks and artifacts](../reference/frameworks-and-artifacts.md) — the complete skill-to-artifact map.
- [Why strategy is its own seat](../explanation/why-strategy-is-its-own-seat.md) — how the cascade wires strategy into the build loop.
