# Linear

Start repository work from Linear, then review later source changes and
confirm narrow coordination write-back without surrendering local authority.

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
For an existing tracker-origin artifact, refresh shows a field-level delta and
updates only approved local fields. A trace link, pull-request link,
display-status update, comment, or closure is a separate remote mutation with
its own fresh confirmation and pending local receipt.

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
| Refresh an existing artifact | A reviewed delta through `work-intake`; requirement refresh is unavailable while the artifact is executing |
| Write coordination back | One profile-declared action after one fresh exact confirmation; no automatic mutation retry |

→ [Choose intake or sync](../../guides/linear/how-to/linear-brief-intake-and-sync.md)
→ [Refresh tracked work safely](../../guides/_shared/how-to/use-work-intake.md)
