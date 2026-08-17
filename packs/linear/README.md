# Linear

Start repository work from a Linear Issue, Project, Cycle, or explicit
selection without making a tracker change.

Try:

```text
Intake Linear issue LIN-123 as repository work. Start read-only.
```

The pack reads a bounded set of Linear fields, preserves stable provenance,
and hands a validated `normalized-intake.v1` record to `work-intake`. Content
decides whether the result is an intent, brief, spec, defect, separate units,
or a view-only refusal. Linear object types, labels, and item counts are hints.

Tracker intake never writes to Linear. Repository materialization belongs to
`work-intake` and happens only after validation and any required human choice.
The separate `linear-brief-sync` workflow can update an existing brief after
showing a section-level diff and receiving approval.

## Install

```bash
agentbundle install --pack linear --scope user <catalogue>
```

Install the `credential-brokers` pack, then use `credential-setup` to store a
Linear Personal API Key. The key never belongs in a request or repository file.

## What you get

| Workflow | Result |
| --- | --- |
| Start from Linear work | Read-only acquisition, strict normalization, then content-based `work-intake` routing |
| Inspect Linear directly | Credentialed `check`, `get-issue`, and `get-project` reads |
| Catch up an existing brief | An approval-gated delta from `linear-brief-sync`; unavailable while the brief is executing |

→ [Choose intake or sync](../../guides/linear/how-to/linear-brief-intake-and-sync.md)
