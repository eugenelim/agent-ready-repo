# Establish your repo's reference architecture

> Get a `docs/architecture/reference.md` — your repo's normative golden path —
> into a repo that doesn't have one yet. Assumes you know what `reference.md` is
> for; if not, read [Foundation vs. map](../explanation/foundation-vs-map.md)
> first.

You have a working codebase with real architecture decisions, and you want them
written down as a foundation that new work conforms to. There are three routes
in, depending on where your repo is.

## Route 1 — Harvest it from an existing codebase (most common)

When you already have code, let `adapt-to-project` propose a draft from what's
there. It detects the stack, the reusable building blocks, the recurring
component stereotypes, and the cross-cutting standards that already repeat across
the tree, fills the arc42 template, and presents the result as a per-section
proposal.

1. Run the `adapt-to-project` skill in your repo. (It also runs automatically
   after you install a pack — see [Adapt a pack to your project](adapt-to-project.md).)
2. When it offers a **reference-architecture** proposal, review it
   section by section. For each finding, **accept** what matches a decision your
   team has actually made, **edit** what's close, and **decline** anything it
   guessed at. Declined findings are recorded so they aren't re-proposed.
3. On confirmation, the draft is written to `docs/architecture/reference.md`.
   Commit it.

The harvest **proposes, never asserts** — nothing is written to
`docs/architecture/reference.md` until you confirm, and an existing
`reference.md` is never overwritten without an explicit accept (it's treated as
your living instance, like any other file you've already filled in).

**Pitfall — harvesting a thin repo.** If your codebase has no real decisions
yet (early prototype, one module, no recurring patterns), the harvest has
nothing to record and will say so. Don't force it — an invented foundation is
worse than none, because it manufactures "standards" nobody agreed to. Come back
when there are real decisions to hold work to.

## Route 2 — Pre-bake it with a stack pack

If your stack matches an opt-in stack pack, the pack ships a filled
`reference.md` for that stack as an ordinary seed. Install the pack and the
`reference.md` lands at `docs/architecture/reference.md`.

- If your repo has **no** `reference.md` yet, the pack's copy lands directly.
- If you **already have** one, the pack's copy arrives as a `.upstream`
  companion beside yours, and `adapt-to-project` walks you through merging the
  two — your file is never silently replaced.

After it lands, treat it as a starting point: edit it to match the decisions
your team has actually made. A pre-baked foundation still has to be *true* for
your repo. The delivery rules are specified in
[the stack-pack contract](../reference/reference-architecture.md#the-stack-pack-contract).

## Route 3 — Greenfield, at project bootstrap

A guided greenfield path — a bootstrap step that writes your first
`reference.md` as you stand up a new project — is **planned but not yet
available**. Until it ships, bootstrap a greenfield repo by copying the arc42
template into `docs/architecture/reference.md` by hand (the template ships inside
the `adapt-to-project` skill's `assets/` folder) and filling the sections you've
decided on. Follow [Create and use your `reference.md`](../tutorials/create-your-reference-architecture.md)
for the walkthrough.

## Verify

However you got there, you're done when:

- `docs/architecture/reference.md` exists and every section reflects a decision
  your team has actually made (no invented constraints).
- It names **no** stack specifics it doesn't really use.
- It sits beside `overview.md`, not in place of it — the two coexist (foundation
  and map).

## See also

- [Foundation vs. map](../explanation/foundation-vs-map.md) — why the two docs are separate.
- [`reference.md` sections and the stack-pack contract](../reference/reference-architecture.md) — the authoritative section list and contract.
- [Create and use your `reference.md`](../tutorials/create-your-reference-architecture.md) — the guided walkthrough.
