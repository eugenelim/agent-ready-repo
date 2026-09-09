# Intent: cross-module depth for the route-decision analysis

- **Level:** capability
- **Scale:** app
- **Owner:** eugenelim
- **Status:** Draft
- **Source:** split out of `docs/specs/distribution-route-registry/` during its
  post-gates review, 2026-09-04

## Outcome

`tools/check_distribution_route_decisions.py` reports a route decision made on a
contract-derived value **wherever it is written**, not only inside the module that
declares the route types — and every exemption it grants is derived from a declaration
in the tree and pinned by a mutation that fails without it.

## The opportunity

The distribution-route registry slice made every consuming surface read its route set
from `contracts/distribution-routes.toml`, and its checker proves no shared build-time
code decides by route. That checker is deliberately bounded: its value pass is
module-local, so a route value handed across a module boundary reaches its consumer
untainted and a decision made on it there is not reported. The checker's own `limits`
list records this.

That bound is real. During the slice's review a `declaration.identity == some_key`
comparison planted in `build/self_host.py` — using a value from the imported contract
reader, which is the shape every derived surface uses — passed `--check` with zero
findings. So AC2's second property is enforced where the route types are declared and
recorded as a limit elsewhere.

## Why this is its own slice

Depth was attempted inside the registry slice and taken back out. Five adversarial
review rounds produced 21, 14, 12, 9 and 10 findings, and by rounds 4 and 5 the dominant
source of new defects was the previous round's fixes rather than the original change.
Every round's findings concentrated in this one file. The production change — the
fifteen surfaces — was stable from round 1 onward and no round after the first found a
defect in it.

The cause is that each widening of the analysis surfaced legitimate contract-derived
code, which then needed an exemption, and each exemption became the next round's escape
hatch: a whole-function producer exemption that hid decisions in the resolver; a
single-route-module exemption mintable by any file; a `.get()` skip that let dispatch
through. Reaching sound cross-module analysis needs a contract of its own — what it must
detect, what it may exempt and on what derived evidence, and how each exemption is
pinned — rather than acceptance criteria written for a different problem.

## What a slice would carry

- Route values followed across module boundaries, including a reader called by a
  module-qualified name, which is how every production consumer spells it.
- A discriminator field set derived from the route types' own declarations rather than
  restated, so a field added to a route type cannot become an invisible decision surface.
- Per-route projector identities (`apm-package`, `claude-plugin`,
  `agent-plugin-root-manifest`) treated as discriminators, since they are what the
  registration seam matches on.
- Dispatch spelled as `mapping.get(route_value)` treated as `mapping[route_value]` is.
- An exemption for a module that serves exactly one route, derived from the registration
  collection the lookup actually resolves through, not from a file list or a bare
  factory definition.
- Every exemption enumerated in the recorded `limits`, and every one pinned by a
  mutation that fails when the exemption is removed.

Working code for all of the above existed and passed its gates; it was removed because
the review could not establish that it was *correct*, not because it was unfinished. It
is recoverable from this branch's history.

## What would make it worth doing

A measured answer to: how many route decisions could actually be reintroduced through
the module-local bound, given that the three route modules are the only place
route-specific code is permitted and the registry surfaces are now derived? If the
honest answer is "few, and each would fail a shipped behavioral test anyway", the
bounded checker plus its recorded limit may be the right permanent shape.

## Non-goals

- Whole-program typed data-flow, callback interpretation, or runtime code generation.
- Any change to the distribution-route contract or to the surfaces that read it.
