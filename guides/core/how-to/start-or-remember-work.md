---
title: Start a software change
summary: Give Core a known change and let it choose the shortest safe route into delivery.
pack: core
kind: how-to
order: 9
journey: core
---

# Start a software change

Use this when you know the change you want to make in a repository. Core turns
that request into the right delivery route, without making you choose a skill or
artifact first.

Start with the outcome:

```text
Start work on adding export retention controls for workspace owners.
```

## What Core does

1. Reads your request and the repository's current work state.
2. Chooses the shortest safe route: direct build, spec, delivery brief, or
   defect diagnosis.
3. Starts the next workflow only after any required artifact is safely written.

For a bounded, low-risk change, Core can enter the build loop directly. That
immediate route creates no intake artifact.

For durable work, Core writes the artifact:

- one independently shippable change becomes a spec and plan;
- work that spans several changes or repositories becomes a delivery brief.

Cited regression evidence is written as its own file under
`docs/product/captured/`, and diagnosis starts before
implementation.

You decide only at real gates: clarify an ambiguous route, approve a brief,
approve a spec or plan, or make the final merge decision.

## Shape first when the product question is open

If the user, problem, outcome, or solution direction is still open, start in
[Product Engineering](../../product-engineering/how-to/shape-a-feature-intent.md)
before Core.

That path frames the intent, explores options when the direction is open,
de-risks the chosen bet, and decomposes it into a buildable slice. A human then
commits the shaped result to build.

For the Core handoff, say:

```text
Start this confirmed delivery handoff through Core intake.
```

Core preserves the confirmed outcome, boundaries, non-goals, dependencies, and
delivery questions. It still uses the normal spec or delivery-brief route, and
it does not skip approval gates. See
[Hand an intent to build](../../product-engineering/how-to/hand-an-intent-to-build.md)
for the full handoff.

## Result and next move

A typical durable result looks like this:

```text
route        durable spec
created      docs/specs/export-retention/spec.md
waiting for  your spec and plan approval
next         approve the spec and plan before implementation
```

This step is done when Core has either started the build loop or shown the
created artifact and the next approval it needs.

Next, follow the reported action. If a later session resumes the work, ask:

```text
What is ready to work on?
```

The agent runs `work-loop`'s `dispatch.py`, which shows what is ready, blocked or active.

## Remember work for later

To park something that is not an intent, such as a defect or a research question, say:

```text
Remember this for later: the nightly export drops rows with an empty name.
```

Core writes the item as its own file under `docs/product/captured/`. To close it later, set the file's `Status:` to `Closed` and add `Resolution:` (`fixed`, `declined`, or `superseded`). A downstream item that lists the file in its `Depends on:` header is unblocked once the file is `Closed` with `Resolution: fixed`. To list your captured items, ask the agent to run `dispatch.py --captured`.

If your repository registered captured items in `workspace.toml` in an older release, run the repair in [Upgrade from a workspace.toml registry](upgrade-from-a-workspace-registry.md).

## State and skill reference

The routing skill is `work-intake` when you need to invoke or debug it. See
[Work-intake routing and lifecycle](../reference/work-intake-routing-and-lifecycle.md)
for every route and [Why work begins with an artifact](../explanation/why-work-begins-with-an-artifact.md)
for the model behind durable work.
