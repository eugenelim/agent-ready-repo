# Why strategy is its own seat

## About the strategy seat

Most catalogue packs answer *how do we build this*. This one answers a question
that comes before that: *what are we building, against whom, and why now*. It is
a distinct seat because the work has a distinct shape. A SWOT, a Porter's Five
Forces read, an OKR cascade — none of these produce code, and none of them are
downstream of a decision brief. They produce the situation the decision brief
argues from. Fold that work into the build packs and it quietly stops happening:
the shaping queue fills with features nobody traced to a market position.

The pack keeps that work visible by giving it its own artifacts, its own output
directory, and its own place in the pack chain. It installs to user scope so the
skills travel across every workspace — a strategist rarely lives in one repo.

## Three pillars, one seat

The seat covers three kinds of strategy that are usually done by different people
and usually done badly when merged.

**Market and competitive strategy** is the largest pillar. It holds the canonical
analysis frameworks — SWOT, Porter's Five Forces, PESTLE, the BCG matrix — plus
the forcing functions that turn analysis into commitment: the OKR cascade, the
PRFAQ, and stakeholder-research synthesis. Each writes a named artifact you can
point a stakeholder at. The frameworks are deliberately boring and canonical;
the value is in committing the output, not in inventing a new lens.

**UX strategy** is one skill, and it is not the same thing as design. It sets the
experience vision, the goals and measures, and the plan — the altitude at which
you decide *what kind of experience this product is* before anyone decides what a
screen looks like. It draws on the NN/g three-layer model, Jaime Levy's four
tenets, and the Gothelf/Seiden habit of linking UX outcomes to OKRs.

**Content strategy** is also one skill, and it lives above per-surface content
design. It is the organizational and governance layer — Halvorson's quad of
Purpose, Process, Structure, and Governance — that decides how content gets made,
kept true, and retired. It does not write the copy for any one surface. That is
the `content-design` skill in the experience-design pack, and the boundary
matters: strategy sets the system content lives in, design fills it.

## Why upstream of the build packs

The pack chain runs in one direction.

```
product-strategy (this pack)
        ↓                          ↓                      ↓
product-engineering          experience-design        content-design skill
(product-vision intent)  (journey → screen → services)  (experience-design)
```

Strategy sits at the top because everything below it needs a situation to react
to. `product-engineering` shapes intent and runs the discovery loop, but it
shapes intent *about something* — a market gap, an objective, a competitive
threat that strategy named first. `experience-design` maps journeys and draws
screens, but toward an experience vision that UX strategy set. Content design
fills surfaces whose governance content strategy defined. Run the build packs
without the strategy seat and each one invents its own missing context, silently
and inconsistently.

The seam that makes this concrete is the OKR cascade. `run-okr-cascade` does not
only write a document. It emits `{type = "strategy"}` gaps into the
`shaping_queue` backlog in `workspace.toml`, and the product-engineering pack's
`frame-situation` reads that backlog as its shaping queue. So a company objective
that has no product answer yet becomes a typed entry that the downstream pack
picks up as work to shape. The cascade is the wire; `workspace.toml` is the
socket. That is how an upstream strategy decision reaches the build loop without
a human copying it across by hand.

## What the seat deliberately excludes

A seat is defined as much by what it refuses. This one does not do growth
strategy — AARRR, product-led growth, PMF testing — which is a follow-on pack
concern, not a gap to paper over here. It does not produce primary research;
`synthesize-stakeholder-research` consumes desk-research outputs rather than
running interviews. It does not touch analytics or CRO tooling, which belong
downstream of the strategy the seat sets. Each exclusion keeps the seat sharp:
strategy names the situation and commits the direction, then hands off.

## See also

- [Frameworks and artifacts](../reference/frameworks-and-artifacts.md) — the full skill-to-artifact map.
- [Cascade OKRs into the shaping queue](../how-to/cascade-okrs-into-the-shaping-queue.md) — the upstream-to-build seam in practice.
- [Set UX and content strategy](../how-to/set-ux-and-content-strategy.md) — where the two smaller pillars live.
