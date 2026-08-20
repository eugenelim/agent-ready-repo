---
title: Choose Linear intake or brief sync
summary: Choose first-time intake or controlled brief synchronization and receive the corresponding validated route or update preview.
pack: linear
kind: how-to
---

# Choose Linear intake or brief sync

Use intake when Linear work should enter the repository for the first time. Use
refresh when an existing tracker-origin artifact needs an approval-gated
catch-up from Linear. `linear-brief-sync` preserves the older brief-specific
request language but delegates to that same refresh authority.

For intake, say:

```text
Intake Linear issue LIN-123 as repository work. Start read-only.
```

The immediate result is a validated content-based route. Linear remains
unchanged.

## Start new work with intake

`linear-brief-intake` reads an Issue, Project, Cycle, view, or explicit
selection through the sibling `linear` acquisition skill. It preserves stable
IDs and `updatedAt`, minimizes content, then hands `normalized-intake.v1` to
`work-intake`.

The Linear object type does not pick the artifact. One independently shippable
Issue may route to a spec. A Project that describes one coherent multi-spec
outcome may route to a Draft brief. An unrelated Cycle or view becomes separate
units, a view-only result, or one clarifying question.

**Read/write boundary:** intake never writes to Linear and never creates a
repository artifact directly. `work-intake` owns repository materialization
after validation and required human decisions.

## Catch up an existing artifact with refresh

When a registered artifact already exists and source fields have changed, ask:

```text
Sync Linear issue LIN-123 into docs/product/briefs/example-feature.md.
Show the delta and wait for approval.
```

The configured Linear processor validates and pins `api.linear.app` before
credentials, re-fetches the source, and shows a field-level diff. Local
requirement changes need the authority decision defined by the artifact and
repository policy. Refresh refuses while a spec is Implementing or a brief is
Executing.

Optional coordination write-back is separate from the local decision. Trace
links, pull-request links, display status, comments, and closure each require a
fresh confirmation bound to the exact target and payload. The processor records
a pending receipt before one GraphQL mutation and never retries that mutation
automatically.

## Decision table

| Situation | Use |
| --- | --- |
| No canonical artifact exists | intake |
| An Issue may be one shippable feature | intake; let content select the spec route |
| A Project or Issue with children may be one outcome | intake; let coherence select the route |
| A collection contains unrelated work | intake; expect separate units or view-only |
| An existing tracker-origin artifact changed | refresh, with field-level approval |
| The brief is executing | neither sync nor refresh; wait for the execution boundary |

## Intake limits

The default intake profile allows at most 5 pages, 250 items, 2 MiB, 30 seconds
per request, and one retry with a 1-second backoff. It accepts only the fixed
HTTPS API host. Destination validation happens before credential resolution;
non-public or unstable DNS answers fail closed. Partial results are marked
incomplete or refused, never hidden.

Tracker text cannot change the endpoint, tools, command arguments, routing, or
authority. Invalid strict JSON, missing provenance, an unknown profile, unsafe
redaction, or a confidentiality mismatch stops before repository writes.

## Next request

After intake, review the selected route and answer any named gap. After refresh,
review the proposed sections and approve only those you want changed.

See [tracker vocabulary](../../_shared/reference/tracker-vocabulary.md) for the
shared terms and [Refresh tracked work safely](../../_shared/how-to/use-work-intake.md)
for the common lifecycle and confirmation procedure.
