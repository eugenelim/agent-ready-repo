---
title: "Close it out"
summary: "Record what shipped, what did not, and why — the reasoning is the part worth keeping."
pack: core
kind: how-to
order: 4
---

# Close it out

**Step 4 of 4 — Close it out**
<!-- rung: packs/core/JOURNEY.md -->

**What changes:** A merged change becomes a lifecycle record, an updated workspace, and whatever was learned.
<!-- rung: packs/core/JOURNEY.md -->

**What you need first:** A merged, reviewed change.
<!-- rung: authored -->

*Skipping costs:* The work disappears from the queue with its decisions unrecorded, and the next person rediscovers them.
<!-- rung: authored -->

**Concepts:**
<!-- rung: authored -->

- [The two-room model](../explanation/two-room-model.md) explains why shaping and building are separate rooms.
- [Why work begins with an artifact](../explanation/why-work-begins-with-an-artifact.md) explains why the loop refuses to start from a chat message.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `close-work` | A merged change | The lifecycle record, and the workspace updated. | Required |
| `project-knowledge` | Something learned worth keeping | A durable note on a topic the repository keeps. | Optional |

Prompts go into an AI agent session with this pack installed — the same session
throughout. `<slug>` is the short kebab-case name for this piece of work; it
names the spec directory and stays the same until the work closes.

<!-- rung: packs/core/JOURNEY.md -->

## Run `close-work` — close it properly

**You type:**
<!-- rung: packs/core/.apm/skills/close-work/SKILL.md -->

```
Close this work out.
```

**Agent returns:**
<!-- rung: packs/core/.apm/skills/close-work/SKILL.md -->

> **Agent:** Done — I've written a lifecycle record and the workspace membership updated to match to `docs/lifecycle/<slug>.md`.

**You push back:**
<!-- rung: packs/core/.apm/skills/close-work/SKILL.md -->

> **You:** You closed it without recording why two acceptance criteria were dropped. That reasoning is the only thing worth keeping.
>
> **Agent:** I recorded the reason for each dropped criterion in the disposition rather than leaving them unexplained.

**Output varies** with how much of the spec shipped as written and how many findings were dispositioned.
<!-- rung: packs/core/.apm/skills/close-work/SKILL.md -->

**You decide:** Merge the reviewed change — the pack's `merge-reviewed-change` gate, after mechanical gates pass and review is clean.
<!-- rung: packs/core/JOURNEY.md -->

**Check (grounded):** Ask what was dropped or changed from the original spec and why; this surfaces a closure that records completion but not the decisions.
<!-- rung: packs/core/.apm/skills/close-work/SKILL.md -->

**Watch out for:** Closing is where the reasoning is most likely to be lost, because the work feels finished. Notice a record that lists what shipped without saying what did not.
<!-- rung: packs/core/.apm/skills/close-work/SKILL.md -->

**Where it lands:** `docs/lifecycle/<slug>.md`.
<!-- rung: packs/core/.apm/skills/close-work/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
# Lifecycle: <slug>

- **Outcome:** <shipped | withdrawn | superseded>
- **Closed:** <YYYY-MM-DD>

## What shipped

## What did not, and why

- <criterion> — <the reason it was dropped>

## What we would keep
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Run `project-knowledge` — keep what was learned

**You type:**
<!-- rung: packs/core/.apm/skills/project-knowledge/SKILL.md -->

```
Capture what we learned about the CI flake so the next person does not rediscover it.
```

**Agent returns:**
<!-- rung: packs/core/.apm/skills/project-knowledge/SKILL.md -->

> **Agent:** Done — I've written a durable note on the topic, distilled rather than transcribed. Nothing was written to disk.

**You push back:**
<!-- rung: packs/core/.apm/skills/project-knowledge/SKILL.md -->

> **You:** This is a transcript of what we did. Keep the finding and the reason it was surprising; drop the narrative.
>
> **Agent:** I cut it to the finding and why it was non-obvious, and dropped the chronology.

**Output varies** with how much was learned and whether the topic already has a note.
<!-- rung: packs/core/.apm/skills/project-knowledge/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (sufficient-for-next):** Ask what someone would do differently having read it; this surfaces a note that records events rather than knowledge.
<!-- rung: packs/core/.apm/skills/project-knowledge/SKILL.md -->

**Watch out for:** A knowledge note drifts into a diary, which nobody reads twice. Notice chronology — if the order of events matters more than the finding, it is the wrong artifact.
<!-- rung: packs/core/.apm/skills/project-knowledge/SKILL.md -->

**Writes no artifact.** It reports in the agent session and does not change files.
<!-- rung: packs/core/.apm/skills/project-knowledge/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
# <topic>

## What we learned

<the finding, stated so someone can act on it>

## Why it was non-obvious

<what a reasonable person would have assumed instead>
```

*Section shape only. This skill appends to a repository knowledge topic — confirm the shape against what you get back.*

## Where this leads

**Done with this step:** You are done when the record says what did not ship and why, not only what did.
<!-- rung: authored -->

Stage 4 of four, and the pack's second gate. After this the workspace is clean and the next request starts at step 1.

**Next:** [Start the work](start-the-work.md) — the workspace is clean and the next request comes back through the front door. If the work exposed a new outcome rather than finishing one, it goes to [Frame the intent](../../product-engineering/how-to/frame-the-intent.md) instead.
<!-- rung: authored -->

**Go deeper:** [the `core` pack reference](../explanation/core-pack.md) — how the loop, the gates and the reviewers fit together.
<!-- rung: authored -->
