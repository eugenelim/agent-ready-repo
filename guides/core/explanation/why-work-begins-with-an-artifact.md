---
title: Why work begins with an artifact
summary: How intake separates source material, durable product meaning, lifecycle state, and execution.
pack: core
kind: explanation
order: 11
journey: core
---

# Why work begins with an artifact

A request is evidence that work may exist. It is not yet the durable definition
of that work. `work-intake` separates four concerns that otherwise collapse into
one chat turn: source material, canonical product meaning, lifecycle,
and execution.

```text
source request → canonical artifact → processor
```

## The artifact carries meaning

An intent, brief, spec, or defect record survives a session and can be reviewed
without replaying the original message. The artifact kind reflects altitude:
an opportunity is not forced into a feature spec, and a multi-feature outcome
is not compressed into one oversized build contract.

This also puts untrusted source material at a boundary. Intake preserves a safe
locator and revision while copying only the bounded product facts needed by the
artifact. Embedded source instructions never become authority.

## The artifact's headers carry lifecycle

The artifact's own `Status:` line says where it sits in the lifecycle, and its
`Depends on:` line says what it waits for. A Draft is deliberately
non-dispatchable, so remembering an idea cannot silently start implementation.

Materialization happens first. Processor dispatch comes last, only
after the artifact is durable.

## Processors retain their jobs

Intake decides the route, not the details of every downstream workflow.
`author-delivery-brief create` writes a Draft brief, `continue` handles the human Ready gate
and confirmed slice cuts, `new-spec` owns the feature contract, and `bug-fix`
owns regression diagnosis. `work-loop`'s `dispatch.py` remains the read-side authority for what is ready.

This keeps one front door without creating one all-powerful skill. Each
processor can enforce its own contract, while intake makes the handoff explicit
and deterministic.

## Human decisions remain visible

The system can classify clear evidence, but it cannot decide that ambiguous work
is ready, choose a brief slice, approve a spec, or change an artifact's authority
on the user's behalf. Those decisions are gates because they change what can run.

For the procedure, see [Start a software change](../how-to/start-or-remember-work.md).
For exact routes and limits, see [Work-intake routing and lifecycle](../reference/work-intake-routing-and-lifecycle.md).
