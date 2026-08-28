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
- A bounded outcome that should be preserved before a solution artifact is
  chosen goes to `intake-intent` and becomes a Draft repository intent.

If two routes are plausible, the agent asks for the smallest missing choice or
records the gap. It does not infer that incomplete work is ready.

### Start from confirmed upstream shaping

When an installed shaping workflow offers a validated handoff, ask:

```text
Start this confirmed delivery handoff through Core intake.
```

One independently shippable feature enters as a delivery contract for
`new-spec`. Multi-spec or cross-repository work enters as a delivery brief for
`author-delivery-brief continue` or `create`. The handoff supplies bounded context and
provenance; it does not approve an artifact or skip a gate.

If the destination is ambiguous, intake stops for your choice without writing.
If no handoff is present, Core follows the ordinary routes above. External
locators remain opaque unless another trusted workflow has already acquired and
supplied matching bounded content.

## Remember work for later

Say that you want to remember the work and stop:

```text
Remember that workspace owners need export retention controls. Do not start implementation.
```

The agent creates a Draft artifact, registers non-dispatchable membership, and
stops. A future `workspace-status` call can surface it, but `work-loop` cannot
execute it until the required artifact and approvals exist.

For intent-only capture, `intake-intent` records the outcome, boundary, owner,
unresolved questions, projection, and source. Product altitude, opportunity,
assumptions, scale, and JTBD context are optional. If an intent already exists,
the skill updates that repository path instead of creating a renamed copy.
Chat-only or personal/vault input also needs a confirmed repository destination
and explicit authority transfer; its minimized source locator remains
provenance, never executable work.

## Check status or request refresh

For a read-only view, say:

```text
workspace-status
```

`work-intake` passes this directly to `workspace-status`; it does not reclassify
or edit the result. For an existing registered tracker-origin artifact, request
`work-intake` refresh and review the field-level delta. Refresh changes local
requirements only after the lifecycle permits it and an authorized approver
records every decision. Any supported remote coordination write is separate
and requires its own fresh, exact confirmation. See
[Use work intake](../../_shared/how-to/use-work-intake.md) for the full flow and
tracker capability limits.

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
