---
title: "Check decision health"
summary: "Find accepted ADRs whose revisit date has passed, superseded decisions still cited, and confirmation checks that are missing, without writing or running anything."
pack: repo-governance
kind: how-to
uses: [repo-governance]
---

# Check decision health

Ask your agent which decisions need a fresh look, and it answers in one short block. It reads your ADRs and RFCs, runs none of the checks they name, and writes nothing.

## Ask for a health check

Use this when you want to know whether your recorded decisions are still current:

```text
Use navigate-decisions in health mode: which of our decisions are due for review or out of date?
```

## Read the result

The agent runs the skill's health command, then replies with this block:

```text
HEALTH:
- Checked: <count> accepted ADRs on <today>
- Due triggers: <ADR, date and excerpt per item, or "none">
- Versions to compare: <ADR and versions per item, or "none">
- Superseded still cited: <superseded ADR, citing records per item, or "none">
- Missing signal paths: <ADR and path per item, or "none">
- Invalid signal paths: <ADR and path per item, or "none">
- No Confirmation: <count> of <count>
- Needs a person to judge: <count>, listed below the block
```

- **Due triggers** are accepted ADRs whose `Revisit if:` line names a date that has passed.
- **Versions to compare** name a version, such as `1.0` or `v2`. The agent cannot tell offline whether that version has shipped, so you compare it.
- **Superseded still cited** lists accepted records whose header still points to a superseded ADR without naming the ADR that replaced it.
- **Missing signal paths** are files or folders that an ADR's `Confirmation` signal names and the repository does not have.
- **Invalid signal paths** are paths the agent refused to look at, for example because they leave the repository, pass through a link, or are too long. That is not the same as missing.
- **No Confirmation** counts accepted ADRs with no `Confirmation` section.
- **Needs a person to judge** lists the remaining `Revisit if:` lines. They name no date or version, so only a reader can say whether they have come true.

Text from your records is shown with control and hidden direction characters removed.

## Act on it

When a decision has come due or no longer holds, [record a new decision](new-adr.md) that supersedes it. When the direction itself is open again, [propose it with an RFC](new-rfc.md).
