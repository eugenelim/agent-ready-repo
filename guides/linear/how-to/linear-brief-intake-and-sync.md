---
title: Choose Linear intake or brief sync
summary: Choose first-time intake or controlled brief synchronization and receive the corresponding validated route or update preview.
pack: linear
kind: how-to
---

# Choose Linear intake or brief sync

Use intake when Linear work should enter the repository for the first time. Use
sync only when an existing brief needs an approval-gated catch-up from Linear.

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

## Catch up an existing brief with sync

Use `linear-brief-sync` only when a brief already exists and source fields have
changed:

```text
Sync Linear issue LIN-123 into docs/product/briefs/example-feature.md.
Show the delta and wait for approval.
```

Sync re-fetches the Issue, compares only Linear-sourced sections, and shows a
before/after diff. It writes only approved sections and refuses while the brief
is executing. Sync is a separate workflow; its write behavior does not broaden
the read-only intake boundary.

## Decision table

| Situation | Use |
| --- | --- |
| No canonical artifact exists | intake |
| An Issue may be one shippable feature | intake; let content select the spec route |
| A Project or Issue with children may be one outcome | intake; let coherence select the route |
| A collection contains unrelated work | intake; expect separate units or view-only |
| An existing brief's imported source sections changed | sync, with diff approval |
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

After intake, review the selected route and answer any named gap. After sync,
review the proposed sections and approve only those you want changed.

See [tracker vocabulary](../../_shared/reference/tracker-vocabulary.md) for the
shared terms.
