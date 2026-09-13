---
title: "Run the research"
summary: "Run the evidence pass at a depth you chose deliberately, and read the confidence tags before the prose."
pack: desk-research
kind: how-to
order: 2
---

# Run the research

**Step 2 of 4 — Run the research**
<!-- rung: packs/desk-research/JOURNEY.md -->

**What changes:** The scoped question becomes a synthesis where every finding carries a confidence rating and the gaps are named rather than hidden.
<!-- rung: packs/desk-research/JOURNEY.md -->

**What you need first:** The question, the depth mode you want, and the outline if you built one.
<!-- rung: authored -->

*Skipping costs:* You get an answer with no way to tell which parts are well-evidenced and which are one blog post.
<!-- rung: authored -->

**Concepts:**
<!-- rung: authored -->

- [Episodic vs project research](../explanation/episodic-vs-project-research.md) explains the two axes: how deep one session goes, and how long an investigation runs.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `desk-research` | The question, and the outline if you built one | A synthesis with a confidence rating on every finding, and a named gap list. | Required |

Prompts go into an AI agent session with this pack installed — the same session
throughout. In every path below, `<topic-slug>` is the short kebab-case name you
give the investigation, and it stays the same across every artifact so one
study's files sort together.

<!-- rung: packs/desk-research/JOURNEY.md -->

## Run `desk-research` — the evidence-graded answer

**You type:**
<!-- rung: packs/desk-research/.apm/skills/desk-research/SKILL.md -->

```
Research this at applied depth: what do teams actually report after moving a marketing site to server-side rendering? Cite primary sources.
```

**Agent returns:**
<!-- rung: packs/desk-research/.apm/skills/desk-research/SKILL.md -->

> **Agent:** Done — I've written a synthesis with a confidence tag on every finding and an explicit list of what the evidence could not answer to `<topic-slug>-survey.md`.

**You push back:**
<!-- rung: packs/desk-research/.apm/skills/desk-research/SKILL.md -->

> **You:** Two findings are tagged high confidence on one source each. Either find two more independent sources or downgrade them, and say which you did.
>
> **Agent:** I downgraded both to moderate and named the downgrade reason, because the additional sources I found were restatements of the same original.

**Output varies** with the depth mode you choose, what has been published, and how much of it is primary.
<!-- rung: packs/desk-research/.apm/skills/desk-research/SKILL.md -->

**You decide:** Set the scope and the depth mode before this runs — the pack's `set-research-scope-and-depth` gate. Depth decides how much it will read, and it cannot be renegotiated halfway.
<!-- rung: packs/desk-research/JOURNEY.md -->

**Check (grounded):** Pick the finding you most want to be true and ask what would have to be false for it to fail; this surfaces a conclusion the search was shaped to reach.
<!-- rung: packs/desk-research/.apm/skills/desk-research/SKILL.md -->

**Watch out for:** Every finding reads with the same authority whether it rests on three independent studies or one blog post. Read the confidence tags before the prose, and treat an untagged claim as untagged, not as certain.
<!-- rung: packs/desk-research/.apm/skills/desk-research/SKILL.md -->

**Where it lands:** `<topic-slug>-survey.md`.
<!-- rung: packs/desk-research/.apm/skills/desk-research/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
# <topic-slug> — survey

> Discipline: applied (practitioner-pattern survey)

## Finding 1: <claim> [high]

<the evidence, with citations>

## Known unknowns and unknowables

- **Known-unknown:** <what evidence would close it>.
- **Unknowable:** <why no evidence could>.
```

*Section shape only. The depth mode decides the artifact's name and its sections, so this skill ships no single template — confirm the shape against what you get back.*

## Where this leads

**Done with this step:** You can move on when every finding carries a confidence tag and the gap section is not empty.
<!-- rung: authored -->

Stage 2 of four, and the pack's first human gate — depth is set here and cannot be renegotiated halfway.

**Next:** [Challenge the result](challenge-the-result.md).
<!-- rung: authored -->

**Go deeper:** [the `desk-research` pack reference](../reference/desk-research-pack.md) — every skill this step runs, with its inputs and outputs.
<!-- rung: authored -->
