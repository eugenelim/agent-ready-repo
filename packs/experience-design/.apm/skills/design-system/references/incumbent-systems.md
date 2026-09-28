# Working with a system that already exists

Load this on `inherit`, `extend`, and `refine`, and on `originate` whenever you
are not certain the product is genuinely greenfield. Most products are not.

## Find the source of visual truth before deciding anything

A product usually has more than one place that looks like a design system, and
they usually disagree. Find which one the interface actually reads from.

Look for: a token or theme source the interface imports; a variables or
constants module the components reference; a component library with its own
internal values; a design-tool library; and a document describing a system
nobody wired up. The last two describe intent; only the first three decide what
renders.

Then judge coherence honestly, because the route turns on it:

- **Coherent** — one source, roles named by job, values referenced rather than
  retyped, and the interface broadly obeys it. Route `inherit`.
- **Partial** — a real source exists but does not cover everything, or parts of
  the interface bypass it. Extend its best-supported pattern rather than
  declaring the product greenfield. Which route this is depends on the gap, not
  on the partiality: a gap sitting inside a scale the system already has is
  `inherit` and fill; only a capability the system cannot express is `extend`.
- **Absent or contradictory** — no source the interface reads from, or several
  that disagree with no winner. Say which you found and ask which is
  authoritative before routing; do not pick for the product.

Record what you found and where. A later reader needs to know whether "no
incumbent system" was a finding or an assumption.

## Inherit before extend, extend before replace

The order is the rule, and each step needs a reason the previous one could not
serve.

**Inherit** takes the incumbent values as given. Identify only the gaps the
current work actually needs — not every gap the system has. A gap the current
work does not need is not this run's business, and filling it grows the system
for nobody.

**Extend** adds what the incumbent system lacks. Three constraints:

- Extend the existing scale rather than starting a second one. A new step
  belongs on the incumbent ratio, at the incumbent naming.
- Follow the incumbent naming and binding convention exactly, including the
  parts you would have done differently. A system with two conventions is two
  systems.
- Add the fewest new primitives and roles that close the gap, and record what
  each new one relates to in the incumbent system.

**Replace** changes an incumbent value or relationship. It needs an approved
direction that actually commits the axis being changed. A tidier model is not a
reason, and neither is a convention you prefer.

## Never rename for tidiness

Do not rename incumbent tokens, restructure their layering, or reorganise their
groups to match a more elegant taxonomy. Renaming touches every consumer, risks
a partial sweep, and buys nothing the product asked for. A token whose name is
literal rather than semantic is worth noting as a finding; it is not worth
changing under a run that was asked for something else.

## Never create a parallel system

The failure to avoid is a second set of values sitting beside the first, each
correct on its own terms, with the interface drifting between them. It happens
by accident: a run cannot find the incumbent source, or finds it and decides a
fresh start is cleaner, and writes a complete system that competes with one
already shipping.

If you have resolved values that the incumbent system also resolves, and you
did not intend to replace them, you have built the parallel system. Go back and
inherit.

## Record what moved, in three groups

Whenever a route changes an incumbent system, the artifact separates:

- **Retained** — incumbent values and relationships carried unchanged. Name
  them; a reader cannot tell "kept" from "overlooked" otherwise.
- **Extended** — what was added, on which incumbent scale, at which naming.
- **Replaced** — what changed, what it was, and which approved commitment
  required the change.

A change with nothing in the retained group is a replacement wearing an
extension's name.

## Bind to the architecture the project already has

The system's shape is the project's decision, not this skill's. Follow what is
already there:

- **A layered token system.** Keep primitive, semantic, and component tiers
  separate and keep the dependency one-way. Bind consumers to semantic roles.
- **A flat custom-property file.** Resolve into properties in the same
  namespace and naming style already in use. Do not impose a layering the
  project never adopted.
- **A theme object in code.** Follow its structure and its key names.
- **A platform token source.** Follow the platform's own conventions for
  naming and grouping.
- **A small constants module.** Some products need nothing more. A handful of
  well-named constants is a complete design system for a product of that size.
- **A design-only artifact.** Where the binding happens later or elsewhere,
  resolve values and relationships without naming how they will be bound at
  all.

Where the project has no convention yet, prefer separating primitives from
semantic roles, because it is what lets a direction change land without a
rename. Prefer it; do not require it. A two-tier structure imposed on a product
that wanted six constants is overhead the product will route around.

Name no product, framework, styling language, or pipeline as the required
binding. The system must be implementable in whatever the project already uses.
