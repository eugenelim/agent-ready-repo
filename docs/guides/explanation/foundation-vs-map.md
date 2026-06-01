# About foundation vs. map

> Why your repo keeps **two** architecture documents — `reference.md` (the
> foundation) and `overview.md` (the map) — and why they must not collapse into
> one. For the section-by-section description of `reference.md`, see
> [`reference.md` sections and the stack-pack contract](../reference/reference-architecture.md).
> To create one, follow [Create and use your `reference.md`](../tutorials/create-your-reference-architecture.md).

## The question this page answers

Both files live under `docs/architecture/`. Both describe "the architecture."
So why two? Because they answer two different questions, for two different
moments, and merging them produces a document that does neither job well.

`overview.md` answers **"where is everything?"** It is a *map*: a description of
how the code is organized *today*. You read it to find the package that owns
billing, to learn that inbound requests land in one place and persistence in
another. It is descriptive — it reports what is, and when the code moves, the
map is updated to match. A map that disagrees with the territory is simply a
bug in the map.

`reference.md` answers **"how should new work be shaped?"** It is a
*foundation*: the golden path — the stack, the reusable internal building
blocks, the component stereotypes, and the cross-cutting standards that new code
is expected to conform to. You read it before you design a feature, to learn
which building blocks to reuse and which standards to follow. It is normative —
it prescribes what *should* be, and when a design wants to deviate, the
deviation is what needs a reason.

## Descriptive vs. normative — why the split matters

The two roles pull in opposite directions, and that is the whole point of
keeping them apart.

A map must follow the code. If you refactor three packages into one, the map
changes the same day — it has no opinion about whether the refactor was wise; it
just reports the new shape. A map with opinions baked in gets stale the moment
reality and preference diverge, and then you can't trust it to tell you where
things *are*.

A foundation must lead the code. Its job is to be the thing a pull request is
held to: "this new component is a handler, so it follows the handler
stereotype's error-handling standard." If the foundation simply described
whatever the code currently does, it would have no power to steer anything —
every inconsistency in the codebase would instantly become "the standard,"
and the document would ratify drift instead of resisting it.

Put one sentence of each kind in the same document and they fight. The
descriptive half rots the prescriptive half (now the "standard" is whatever got
merged last), and the prescriptive half makes the descriptive half untrustworthy
(is this section reporting reality or aspiration?). Separating them lets the map
stay honest about the present *because* it doesn't also have to be a statement
of intent — the same reason a project keeps decision records separate from its
current-state docs.

## Why a template, instantiated on demand — not a pre-placed file

`reference.md` is **not** shipped to you as an empty starter file. It begins as
a template carried inside the `adapt-to-project` skill, and a real
`docs/architecture/reference.md` appears in your repo only when you instantiate
it. Two reasons:

- **A thin repo has no golden path yet.** Early on, there are no real
  architecture decisions to hold work to — only choices nobody has committed to.
  A pre-placed empty `reference.md` would invite someone to fill it with
  invented constraints, manufacturing a "standard" out of guesses. Leaving it
  un-instantiated says the honest thing: *you don't have a foundation yet, and
  that's fine.*
- **A stack pack can deliver a filled one without a fight.** Because the core
  product never pre-places a `reference.md`, an opt-in pack tuned to a particular
  stack can ship a fully filled `reference.md` as an ordinary seed, and — since
  there is nothing in core to collide with — it just lands. If you have *also*
  written your own, the two are reconciled through the normal companion-merge
  path rather than one silently clobbering the other. The mechanics of that
  contract are in the
  [reference page](../reference/reference-architecture.md#the-stack-pack-contract).

## How the foundation gets used

A feature's low-level design (in its plan) reads `reference.md` as steering: it
names the building blocks it reuses and the standards it follows, and it
justifies anything it does differently. That is the foundation paying off — the
design doesn't re-litigate the stack or reinvent error handling; it inherits
them. For how the design consumes it, see
[Spec `Shape:` and the plan's `## Design (LLD)`](../reference/spec-shape-and-lld.md).

## See also

- [`reference.md` sections and the stack-pack contract](../reference/reference-architecture.md) — the authoritative section list and contract.
- [Create and use your `reference.md`](../tutorials/create-your-reference-architecture.md) — the guided first walkthrough.
- [Establish your repo's reference architecture](../how-to/establish-reference-architecture.md) — the task recipe, with variations.
