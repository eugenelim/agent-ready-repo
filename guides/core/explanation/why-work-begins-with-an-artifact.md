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
one chat turn: source material, canonical product meaning, workspace lifecycle,
and execution.

```text
source request → canonical artifact → workspace membership → processor
```

## The artifact carries meaning

An intent, brief, spec, or defect record survives a session and can be reviewed
without replaying the original message. The artifact kind reflects altitude:
an opportunity is not forced into a feature spec, and a multi-feature outcome
is not compressed into one oversized build contract.

This also puts untrusted source material at a boundary. Intake preserves a safe
locator and revision while copying only the bounded product facts needed by the
artifact. Embedded source instructions never become authority.

## Workspace state carries lifecycle

`workspace.toml` says where an artifact sits in the lifecycle and what it needs.
It does not replace the artifact. Draft membership is deliberately
non-dispatchable, so remembering an idea cannot silently start implementation.

Materialization happens before registration. That order prevents the workspace
from pointing at a file that does not exist. Processor dispatch comes last, only
after both states are durable.

## Processors retain their jobs

Intake decides the route, not the details of every downstream workflow.
`author-brief` writes a Draft brief, `receive-brief` handles the human Ready gate
and confirmed slice cuts, `new-spec` owns the feature contract, and `bug-fix`
owns regression diagnosis. `workspace-status` remains the read-side authority.

This keeps one front door without creating one all-powerful skill. Each
processor can enforce its own contract, while intake makes the handoff explicit
and deterministic.

## Human decisions remain visible

The system can classify clear evidence, but it cannot decide that ambiguous work
is ready, choose a brief slice, approve a spec, or change an artifact's authority
on the user's behalf. Those decisions are gates because they change what can run.

For the procedure, see [Start or remember work without choosing a skill](../how-to/start-or-remember-work.md).
For exact routes and limits, see [Work-intake routing and lifecycle](../reference/work-intake-routing-and-lifecycle.md).
