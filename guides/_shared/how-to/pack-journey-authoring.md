---
title: "Write a pack journey"
summary: "Show readers how to move through your pack, stage by stage."
pack: _shared
kind: how-to
---

# Write a pack journey

Add a `JOURNEY.md` file to your pack, and it is published as the pack's journey page. Add one when the pack has at least two stages with distinct human decisions.

## Describe each stage

Create `packs/<pack>/JOURNEY.md`. Each stage is a `###` heading followed by labelled lines in this order:

```markdown
### 1. Draft the artifact

- **Agent does:** drafts the artifact from your input.
- **You decide:** whether the draft is ready to save.
- **Output:** a draft artifact or findings report.
- **State:** proposed-write
```

Every stage needs `Output` and `State`, and a stage that writes, publishes, deletes, or waits for a choice also needs `You decide`. The frontmatter, the settings block at the top, names the journey and lists the pack's skills; [Pack JOURNEY.md format](../reference/pack-journey-format.md) lists every field.

## Validate it

Check the metadata, skill names, and states:

```bash
python tools/lint-pack-journeys.py
```

## Publish it

Build the journey page:

```bash
python tools/build-site.py --journeys-only
```

The page appears at `/journeys/<journey_id>/`, and `JOURNEY.md` is never installed with the pack.

Next, [add credentials to a skill](../../credential-brokers/how-to/add-a-credentialed-skill.md) if the pack calls an authenticated service.
