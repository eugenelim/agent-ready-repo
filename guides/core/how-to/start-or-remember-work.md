---
title: Start or remember work without choosing a skill
summary: Route a request into the right artifact and workspace lifecycle state with the Core pack.
pack: core
kind: how-to
order: 9
journey: core
---

# Start or remember work without choosing a skill

Use one request to get a durable artifact and a visible workspace entry. You do
not need to decide whether the work belongs in an intent, brief, spec, or defect
record first.

```text
Start work on adding export retention controls for workspace owners.
```

The agent uses `work-intake` to classify the request from its content, writes
the canonical artifact, registers it in `workspace.toml`, and reports the route.
It dispatches a processor only after both writes succeed.

## Start work now

Describe the outcome, constraints, and evidence you already have. The common
routes are:

- One independently shippable change becomes a spec and continues through
  `new-spec` for your approval.
- A coherent outcome that needs several specs becomes a Draft brief.
- A cited regression becomes defect context for `bug-fix`.
- A bounded opportunity that is not ready to ship becomes a Draft intent.

If two routes are plausible, the agent asks for the smallest missing choice or
records the gap. It does not infer that incomplete work is ready.

## Remember work for later

Say that you want to remember the work and stop:

```text
Remember that workspace owners need export retention controls. Do not start implementation.
```

The agent creates a Draft artifact, registers non-dispatchable membership, and
stops. A future `workspace-status` call can surface it, but `work-loop` cannot
execute it until the required artifact and approvals exist.

## Check status or request refresh

For a read-only view, say:

```text
workspace-status
```

`work-intake` passes this directly to `workspace-status`; it does not reclassify
or edit the result. Requirements refresh is intentionally unavailable in this
release. A refresh request resolves the current artifact and processor, reports
that limit, and changes no artifact or workspace state.

## Read and write boundary

The route reads your normalized request, existing target paths, and
`workspace.toml`. It may create one canonical artifact and register one
schema-valid entry. Source text is treated as untrusted data, and target paths
must remain inside the repository and configured artifact directory.

The agent asks before overwriting an artifact, changing its location or
authority, or accepting input whose confidentiality does not fit the target.

## Next step

Run `workspace-status` to confirm lifecycle state. When it shows an approved
spec with a sibling plan as ready, say `work-loop` to implement it.

See [Work-intake routing and lifecycle](../reference/work-intake-routing-and-lifecycle.md)
for the complete route table and [Why work begins with an artifact](../explanation/why-work-begins-with-an-artifact.md)
for the model behind it.
