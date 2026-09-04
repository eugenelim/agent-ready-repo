---
title: "Establish your repo's reference architecture"
summary: Create a normative `reference.md` from settled repository decisions so later designs and reviews follow a real golden path.
pack: architect
kind: how-to
---

# Establish your repo's reference architecture

**Use this when:** Your repo lacks a normative golden path and you want current architecture that assessment can compare with evidence and that designs, diagrams, and reviews can follow.
**Prerequisites:** A working codebase with real architecture decisions (harvesting route); or `adapt-to-project` for harvest, a stack pack for pre-bake, or `init-project` for greenfield.
**Result:** A committed `current-architecture` artifact at the repository's resolved destination, reflecting decisions your team has actually made with no invented constraints.

:::note
Put a `reference.md` golden path at the adopter-owned `current-architecture` destination. `docs/architecture/reference.md` is the catalogue fallback, not a universal path. Assumes you know what the artifact is for; if not, read [Foundation vs. map](../../core/explanation/foundation-vs-map.md) first.
:::

You have a working codebase with real architecture decisions, and you want them written down as a foundation that new work conforms to. There are three routes in, depending on where your repo is.

```text
How should we establish a reference architecture for our existing payments platform?
```

Once it exists, the four architect workflows can use it. Assessment treats it as
reported intent to compare with implementation; proposals, drawings, and
critiques measure against the same golden path:

```text
                         ┌──────────────────────────────┐
                         │ resolved current architecture │
                         │  (your repo's golden path)    │
                         └───────────────┬──────────────┘
                                         │ steers
         ┌───────────────┬───────────────┼───────────────┬───────────────┐
         ▼               ▼               ▼               ▼
 architect-assess architect-design architect-diagram architect-review
 compares intent   proposes against draws against     measures the artifact
 with evidence     your stack        your stack        against it
```

## Route 1 — Harvest it from an existing codebase (most common)

When you already have code, let `adapt-to-project` propose a draft from what's there. It detects the stack, the reusable building blocks, the recurring component stereotypes, and the cross-cutting standards that already repeat across the tree, fills the arc42 template, and presents the result as a per-section proposal.

1. Run the `adapt-to-project` skill in your repo. (It also runs automatically after you install a pack — see [Adapt a pack to your project](../../core/how-to/adapt-to-project.md).)
2. When it offers a **reference-architecture** proposal, review it section by section. For each finding, **accept** what matches a decision your team has actually made, **edit** what's close, and **decline** anything it guessed at. Declined findings are recorded so they aren't re-proposed.
3. Resolve `current-architecture` through Core. On confirmation, write the draft
   only to its confined writable repository destination. An external destination
   needs a separately approved adapter; otherwise the skill renders a handoff.
   Commit the local result when applicable.

The harvest **proposes, never asserts** — nothing is written until you confirm,
and an existing golden path is never overwritten without explicit acceptance.

**Pitfall — harvesting a thin repo.** If your codebase has no real decisions yet (early prototype, one module, no recurring patterns), the harvest has nothing to record and will say so. Don't force it — an invented foundation is worse than none, because it manufactures "standards" nobody agreed to. Come back when there are real decisions to hold work to.

## Route 2 — Pre-bake it with a stack pack

If your stack matches an opt-in stack pack, the pack ships a filled
`reference.md` as catalogue seed material. Its packaged
`seeds/docs/architecture/reference.md` location is a delivery default, not
repository routing authority. Resolve `current-architecture` before accepting
or merging that content into the adopter's destination.

- If your repo has **no** `reference.md` yet, the pack's copy lands directly.
- If you **already have** one, the pack's copy arrives as a `.upstream` companion beside yours, and `adapt-to-project` walks you through merging the two — your file is never silently replaced.

After it lands, treat it as a starting point: edit it to match the decisions your team has actually made. A pre-baked foundation still has to be *true* for your repo. The delivery rules are specified in [the stack-pack contract](../reference/reference-architecture.md#the-stack-pack-contract).

## Route 3 — Greenfield, at project bootstrap

When you're standing up a brand-new repo from an idea, the `init-project` skill is the front door, and writing your first `reference.md` is its **foundation** step. It walks you through choosing the stack, recording the rationale as an ADR, and instantiating `reference.md` from the arc42 template — filled forward from your decision rather than harvested from existing code.

1. Run the `init-project` skill in your new repo.
2. At the foundation step, decide the load-bearing stack choices. The skill
   resolves `decision-record` and `current-architecture` independently, then
   hands each artifact to its existing method. See [Decide and record your
   foundation during inception](../../core/how-to/record-your-foundation-during-inception.md)
   for that step on its own.

For the whole greenfield flow end to end — idea through walking skeleton — follow [From idea to a walking skeleton](../../core/tutorials/start-a-new-project.md).

## Register the artifact

After the architecture artifact exists, register it in `workspace.toml` so a
downstream brief or spec can name it as a hard dependency:

```toml
{ path = "docs/product/design/payment-routing.md", kind = "design", source = { mode = "repo-origin" }, summary = "How payment routing splits across the two providers", needs = [] },
```

Then add the artifact to the downstream work's `needs` array. That work remains
blocked until the design artifact lands:

```toml
needs = [
  { type = "local", kind = "design", path = "docs/product/design/payment-routing.md" },
]
```

## Verify

However you got there, you're done when:

- The resolved current-architecture artifact exists and every section reflects a decision your team has actually made (no invented constraints).
- It names **no** stack specifics it doesn't really use.
- It remains a normative golden path rather than replacing a descriptive map;
  the roles coexist even when their resolved locations are not siblings.

## What you have now

You have a committed, truthful reference architecture at the destination your
repository resolved for `current-architecture`. Register a downstream design as
a dependency when it must land before a brief or spec can proceed.

## See also

- [Assess a repository and turn evidence into action](assess-a-repository.md) — test the implemented architecture without turning the foundation into proof.
- [Foundation vs. map](../../core/explanation/foundation-vs-map.md) — why the two docs are separate.
- [`reference.md` sections and the stack-pack contract](../reference/reference-architecture.md) — the authoritative section list and contract.
- [Create and use your `reference.md`](../tutorials/create-your-reference-architecture.md) — the guided walkthrough.
