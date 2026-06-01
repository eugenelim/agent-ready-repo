# Why a brief layer

Spec-driven delivery gives you a clean path from "we should build X" to "X is
shipped": `new-spec` writes one feature's contract, `work-loop` builds it. A
spec is sized to one feature, built in days or weeks. That shape is deliberate
— and it has an edge.

This page explains the edge, why a **brief** sits above the spec to cover it,
and why the brief looks the way it does. For how to use the brief, see
[Receive a product brief and decompose it into specs](../how-to/receive-a-product-brief-and-decompose-it-into-specs.md);
for the field list, see
[Product brief fields](../reference/product-brief-fields.md).

## The gap: there's no inbox for a handoff

Not every team authors all its own work. Where the product and engineering
functions are separate — most enterprises — engineering *receives* work:
someone hands over a product brief, a PRD, a solution document that spans
several features and months of effort.

A spec can't hold that. A spec is one feature, days to weeks, and `work-loop`
runs per spec. A multi-feature brief provably cannot be a single spec without
breaking both the sizing rule and the build loop. So a multi-feature handoff
*structurally forces* a layer above the spec — and without one, you're left
with two bad options:

- **Cram it into one oversized spec.** It breaks the sizing rule, and the build
  loop has nothing coherent to chew on.
- **Fire `new-spec` N times by hand.** Nothing records *why* the work exists,
  *how* it was decomposed, or *whether the whole thing is delivered*.

The brief is the missing inbox.

## The altitude: roadmap → brief → spec → AC

The brief slots into the document hierarchy between the roadmap and the specs:

```
roadmap   forward-looking themes        →  references briefs
  brief    one received outcome + the specs that deliver it
    spec   the engineering contract for one feature
      AC   the testable unit
```

The roadmap names themes. A brief records *one received outcome* and the specs
that deliver it. A spec is the contract for one feature. An acceptance
criterion is the testable unit. Each layer cites the one above it; none knows
about the layer below. The brief carries the *what/why* of the handoff; the
spec stays the *how*.

## Why these design choices

- **It executes — it isn't just a document.** The brief earns its place by
  *doing* something: `receive-brief` decomposes it into specs and hands each to
  `work-loop`. A brief that only described work would rot. One that spawns and
  tracks work stays alive.

- **Coverage is auto-derived, never hand-maintained.** The brief's Spec map
  rolls up from each spec's own `Status:` field via the `Brief:` back-links. A
  hand-written status drifts the moment a spec ships — so the coverage lint
  derives the truth and fails closed on a stale cell. "Is this brief
  delivered?" stays answerable for free.

- **It elicits; it doesn't mandate a schema.** Real briefs arrive half-formed.
  Rejecting them for missing a section would just push the friction back onto
  the person handing over the work. The skill insists only on the load-bearing
  fields (outcome, scope), offers the rest, and surfaces gaps.

- **It owns one repo's slice, not a coordination hub.** Coordinating an epic
  across repos is a tracker's job (a project board, an integration repo). The
  brief integrates with that via an optional `Epic:` pointer and stops there —
  building a hub would duplicate tools you already have and break the
  single-repo model.

- **Linkage is by reference, not nesting.** A spec names its brief with a
  `Brief:` field rather than living inside a brief directory. Specs stay flat,
  a spec can predate its brief, and one brief can gather specs authored over
  time — the same way many specs can reference one shared contract.

## What it deliberately is not

- **Not a portfolio layer.** One received brief is the ceiling. Rolling many
  briefs up into an initiative is a tracker's job, not this layer's.
- **Not a replacement for the roadmap or backlog.** The brief slots between
  them; both keep their jobs. The roadmap references briefs; backlog items roll
  up to them.
- **Not a new design tier.** The brief is *what/why*. The engineering *how* —
  including any low-level design — stays in the spec and its plan.

## See also

- [Receive a product brief and decompose it into specs](../how-to/receive-a-product-brief-and-decompose-it-into-specs.md)
- [Product brief fields](../reference/product-brief-fields.md)
- [The core pack as a system](core-pack.md) — where `receive-brief` sits among
  the other core skills.
