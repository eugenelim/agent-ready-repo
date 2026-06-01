# `reference.md` sections and the stack-pack contract

> Authoritative description of the `docs/architecture/reference.md` document: its
> four arc42 sections and the contract governing how an opt-in stack pack
> delivers a filled one. For *why* this is separate from `overview.md`, see
> [Foundation vs. map](../explanation/foundation-vs-map.md). For the task of
> creating one, see
> [Establish your repo's reference architecture](../how-to/establish-reference-architecture.md).

`reference.md` is the normative golden path a feature's low-level design conforms
to. It is filled only when a repo has real architecture decisions to record; a
thin repo has none and leaves the template un-instantiated.

## Sections

`reference.md` follows the arc42 sections that carry normative steering. Each
section is present when there is a real decision to record under it, and omitted
otherwise. The sections, in order:

### Constraints

What the architecture must respect regardless of the feature: the languages and
runtimes in play, the platforms that must be supported, regulatory or
contractual obligations, performance or availability targets, and the team
conventions that outrank local preference. These are the boundaries a normal
change does not renegotiate.

### Solution strategy

The top-level approach — the few decisions that explain most of the codebase:
the architectural style, the load-bearing technology choices (each with the
one-line reason it won over the obvious alternative), and the architectural move
that delivers each top-priority quality goal.

### Building-block view / component catalogue

The reusable internal building blocks and the component stereotypes new code is
expected to reuse rather than reinvent. Contains: the recurring *kinds* of
component and the responsibility each owns (so a design can say "this is a new
handler" and inherit that stereotype's rules); the shared internal libraries,
base types, and clients a feature should reach for first; and the composition
rules — allowed dependency directions and boundaries that must not be crossed.

### Crosscutting concepts / standards

The standards every component conforms to regardless of what it does: error
handling, observability (logging, metrics, tracing), security and data handling
(authn/authz, secrets, input validation at trust boundaries), configuration and
environments, and the expected test shape per component stereotype.

## The stack-pack contract

A `reference.md` can be authored by hand, proposed by the `adapt-to-project`
harvest, or pre-baked by an opt-in **stack pack** — a pack tuned to a particular
stack that ships a filled `reference.md`. The contract governing stack-pack
delivery has four clauses:

| Clause | Rule |
| --- | --- |
| **Delivery path** | A stack pack ships a filled `reference.md` as an ordinary seed at `seeds/docs/architecture/reference.md`. |
| **Sole producer** | When the stack pack is the only producer of `reference.md`, it lands with no collision — the core product never pre-places a `reference.md`, so there is nothing to collide against. |
| **Two producers** | When a `reference.md` already exists (you wrote your own, or two packs each ship one), the incoming copy is delivered as a `.upstream` companion beside the existing file, and the two are reconciled through the `adapt-to-project` companion-merge path — never a silent overwrite. |
| **Never `overview.md`** | A stack pack ships only `reference.md` (the normative foundation), never `overview.md` (the descriptive map). The map is specific to your codebase and is not something a pack can pre-write. |

A consequence of the first two clauses: **no bundler override field exists or is
needed.** The sole-producer case has nothing to collide with, and the
two-producer case is handled by the existing `.upstream` companion plus merge —
so there is no "this pack's `reference.md` wins" switch to configure.

## See also

- [Foundation vs. map](../explanation/foundation-vs-map.md) — why `reference.md` is normative and `overview.md` is descriptive.
- [Create and use your `reference.md`](../tutorials/create-your-reference-architecture.md) — a guided walkthrough.
- [Establish your repo's reference architecture](../how-to/establish-reference-architecture.md) — the task recipe.
- [Spec `Shape:` and the plan's `## Design (LLD)`](spec-shape-and-lld.md) — how a feature's design reads `reference.md` as steering.
