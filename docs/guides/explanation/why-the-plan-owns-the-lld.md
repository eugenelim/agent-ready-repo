# About the plan owning the low-level design

> Why the **low-level design** lives in `plan.md` rather than `spec.md`, and why
> the design's **stack is derived** instead of baked into the template. For the
> field-by-field description, see
> [Spec `Shape:` and the plan's `## Design (LLD)`](../reference/spec-shape-and-lld.md).

## The question this page answers

An enterprise feature carries a real low-level design — for a UI, the screen
states, component tree, navigation, and accessibility; for a backend, the data
model, sequence, resilience, security, and deployment order. Where should that
design live? It's tempting to grow the spec until it holds everything. This page
explains why the design belongs in the **plan**, and why the spec gains only a
light `Shape:` selector — and why the design names a stack the template never
ships.

## The shape of the answer

The split rests on a single distinction: **the spec is the contract; the plan is
the strategy.**

- The **spec** answers *what done means* — objective, boundaries, testing
  strategy, acceptance criteria. It is the stable thing a reviewer measures the
  implementation against. It changes when the *behaviour* changes.
- The **plan** answers *how we get there*. It is allowed to change as you learn.
  The low-level design is the most volatile part of "how" — the component you
  thought you'd reuse turns out to need splitting, the sequence reorders, a
  resilience strategy changes. That volatility belongs where change is expected.

So the design lives in the plan's `## Design (LLD)` section, built from nine
stack-neutral categories plus a tenth — rollout & deployment — realized by the
expanded `## Rollout`. The spec gains only the `Shape:` selector (which kind of
work this is) and sharper acceptance-criteria guidance: a user-visible UI state
becomes a criterion phrased *state / trigger / outcome*, and a non-functional
requirement with a pass/fail bar (WCAG-AA, a p99 latency) becomes a criterion.
The **observable** outcome rises to the contract; the **design** that produces it
stays in the plan.

Crucially, **no acceptance criterion lives in the design**. Instead each design
sub-section *traces back* to the criteria it satisfies and the contracts it
implements. The contract is never duplicated — it's referenced. That keeps a
single source of truth for "done" even as the design churns underneath it.

## Design choices and tradeoffs

Three alternatives were weighed and declined:

- **Grow the spec to hold the design.** Rejected: it blurs the contract. A spec
  that contains its own design drifts the moment the design changes, and
  reviewers can no longer tell the promised behaviour from the current plan for
  achieving it.
- **Add a third `design.md` tier.** Rejected: net new surface for every feature,
  another file to keep in sync, and a seam between plan and design that buys
  nothing. The plan already *is* the strategy document; the design is part of the
  strategy.
- **Ship a richer template with the stack already in it** (a UI template naming
  a component framework, a backend template naming a message bus). Rejected
  hardest: it would make the template useful for exactly one stack and wrong for
  every other. A universal template can only ship the *category names*.

That last point is why the stack is **derived, never baked**. The template ships
nine universal headings; the concrete stack is filled in per feature — conforming
to a reference-architecture document (`docs/architecture/reference.md`) when one
is present, degrading to detection from the repo's lockfiles and imports when it
isn't, and *asking* rather than guessing when the repo is greenfield or
ambiguous. The design is always stack-correct without the template ever
committing to a stack.

## How this differs from the spec's contract

A quick way to decide where something goes:

- *Could a reviewer verify it by reading the running system?* → acceptance
  criterion, in the **spec**.
- *Is it a choice about how the system is built that a different implementer might
  make differently?* → design, in the **plan's `## Design (LLD)`**.
- *Is it about how the change reaches production — infra, integration order,
  rollback?* → the plan's **`## Rollout`**.

## See also

- [Spec `Shape:` and the plan's `## Design (LLD)`](../reference/spec-shape-and-lld.md) — the precise field and category list.
- [Why a brief layer](why-a-brief-layer.md) — the layer above the spec, where product intent enters.
- [Product brief fields](../reference/product-brief-fields.md) — the brief's fields and the spec back-links.
