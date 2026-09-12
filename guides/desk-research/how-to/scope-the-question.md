---
title: "Scope the question"
summary: "Decompose the question, name the camps that disagree, and curate the sources before any reading starts."
pack: desk-research
kind: how-to
order: 1
---

# Scope the question

**Step 1 of 4 — Scope the question**
<!-- rung: packs/desk-research/JOURNEY.md -->

**What changes:** A vague question becomes named sub-questions, named camps, and a ranked source list — so the search has a shape before it starts.
<!-- rung: packs/desk-research/JOURNEY.md -->

**What you need first:** A question you actually want answered, and any sources or prior work you already hold.
<!-- rung: authored -->

*Skipping costs:* The search goes wherever the first results lead, and you cannot tell afterwards what it missed.
<!-- rung: authored -->

**Concepts:**
<!-- rung: authored -->

- [Episodic vs project research](../explanation/episodic-vs-project-research.md) explains the two axes: how deep one session goes, and how long an investigation runs.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `build-outline` | The research question | The sub-questions a thorough answer must cover. | Required |
| `identify-perspectives` | A contested question | The named camps on the topic, and who speaks for each. | Optional |
| `source-map` | The outline, and the camps if you built them | Curated sources, ranked by how directly they carry evidence. | Optional |

Prompts go into an AI agent session with this pack installed — the same session
throughout. In every path below, `<topic-slug>` is the short kebab-case name you
give the investigation, and it stays the same across every artifact so one
study's files sort together.

<!-- rung: packs/desk-research/JOURNEY.md -->

## Run `build-outline` — the sub-questions

**You type:**
<!-- rung: packs/desk-research/.apm/skills/build-outline/SKILL.md -->

```
Decompose this question into the sub-questions a thorough answer has to cover: should we adopt server-side rendering for our marketing site?
```

**Agent returns:**
<!-- rung: packs/desk-research/.apm/skills/build-outline/SKILL.md -->

> **Agent:** Done — I've written the sub-questions a thorough answer has to cover, each with a one-line rationale to `<topic-slug>-outline.md`.

**You push back:**
<!-- rung: packs/desk-research/.apm/skills/build-outline/SKILL.md -->

> **You:** Three of these five sub-questions are really the same question about build cost. Merge them, and add the one you skipped: what happens to our existing analytics.
>
> **Agent:** I merged the three cost sub-questions into one and added an analytics sub-question with its rationale.

**Output varies** with the question's breadth, how contested it is, and how much you already know.
<!-- rung: packs/desk-research/.apm/skills/build-outline/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (sufficient-for-next):** Ask what the answer would be missing if one sub-question were dropped; this surfaces padding and sub-questions that restate the main one.
<!-- rung: packs/desk-research/.apm/skills/build-outline/SKILL.md -->

**Watch out for:** An outline can look thorough while every sub-question asks the same thing in different words. Notice sub-questions whose rationales are interchangeable, and merge them before the search starts — each one becomes search effort.
<!-- rung: packs/desk-research/.apm/skills/build-outline/SKILL.md -->

**Where it lands:** `<topic-slug>-outline.md`.
<!-- rung: packs/desk-research/.apm/skills/build-outline/SKILL.md -->

**What it looks like:**
<!-- rung: packs/desk-research/.apm/skills/build-outline/SKILL.md -->

```markdown
# Outline — <main question>

## Sub-question 1: <question>

**Rationale:** <one sentence on why this matters to the main question>.

## Sub-question 2: <question>

(same shape)

## Open / second-order sub-questions

- <question the main answer might raise but doesn't itself answer>.
```

*The agent replaces every `<…>`. This is the schema the skill writes to; the artifact continues in the same shape.*

## Run `identify-perspectives` — the named camps

**You type:**
<!-- rung: packs/desk-research/.apm/skills/identify-perspectives/SKILL.md -->

```
Name the camps on this before we research it — who disagrees about server-side rendering, and what does each side actually claim?
```

**Agent returns:**
<!-- rung: packs/desk-research/.apm/skills/identify-perspectives/SKILL.md -->

> **Agent:** Done — I've written the named camps, each with its core claim and the voices who hold it to `<topic-slug>-perspectives.md`.

**You push back:**
<!-- rung: packs/desk-research/.apm/skills/identify-perspectives/SKILL.md -->

> **You:** You listed two camps and they are the marketing positions of two frameworks. Name the positions, not the vendors, and say which camp is under-represented.
>
> **Agent:** I renamed the camps by position rather than vendor and added a possibly-missing camp for teams who have moved back off server rendering.

**Output varies** with how contested the topic is and how visible each position is in public writing.
<!-- rung: packs/desk-research/.apm/skills/identify-perspectives/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (falsifiable):** Ask which camp the sources you already trust belong to; this surfaces a map drawn around your existing reading rather than the field.
<!-- rung: packs/desk-research/.apm/skills/identify-perspectives/SKILL.md -->

**Watch out for:** The loudest camp is not the largest one. Notice a camp with no named voice, or a `Possibly-missing camps` section left empty — the absence of a position is the thing this skill exists to catch.
<!-- rung: packs/desk-research/.apm/skills/identify-perspectives/SKILL.md -->

**Where it lands:** `<topic-slug>-perspectives.md`.
<!-- rung: packs/desk-research/.apm/skills/identify-perspectives/SKILL.md -->

**What it looks like:**
<!-- rung: packs/desk-research/.apm/skills/identify-perspectives/SKILL.md -->

```markdown
# Perspectives — <question>

## Camp: <name>

- **Core claim:** <one sentence>.
- **Representative voices:** <person/institution>, <person/institution>.
- **Adjacent variants:** <one fringe or modified position>.

## Camp: <name>

(same shape)

## Possibly-missing camps

- <one-line description of a position that might be under-represented>.

```

*The agent replaces every `<…>`. This is the schema the skill writes to; the artifact continues in the same shape.*

## Run `source-map` — the authoritative sources

**You type:**
<!-- rung: packs/desk-research/.apm/skills/source-map/SKILL.md -->

```
Curate the authoritative sources for this question before we read anything, and rank them by primacy.
```

**Agent returns:**
<!-- rung: packs/desk-research/.apm/skills/source-map/SKILL.md -->

> **Agent:** Done — I've written a ranked source map, with each entry's authority type and recency noted to `<topic-slug>-sources.md`.

**You push back:**
<!-- rung: packs/desk-research/.apm/skills/source-map/SKILL.md -->

> **You:** Half the primary sources are vendor blog posts. Move those to secondary and find the primary research and the specification text they are describing.
>
> **Agent:** I reclassified the vendor posts as secondary and added the specification and two measurement studies as primary.

**Output varies** with how much has been published, how much of it is primary, and how recent the field is.
<!-- rung: packs/desk-research/.apm/skills/source-map/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (grounded):** Ask what makes each primary source primary; this surfaces secondary commentary promoted because it was easier to find.
<!-- rung: packs/desk-research/.apm/skills/source-map/SKILL.md -->

**Watch out for:** A confident source list can be ten restatements of one original post. Notice entries that cite each other, or several sources from one vendor or one employer — those count as one voice, not several.
<!-- rung: packs/desk-research/.apm/skills/source-map/SKILL.md -->

**Where it lands:** `<topic-slug>-sources.md`.
<!-- rung: packs/desk-research/.apm/skills/source-map/SKILL.md -->

**What it looks like:**
<!-- rung: packs/desk-research/.apm/skills/source-map/SKILL.md -->

```markdown
# Sources — <topic>

## Primary

- **<title>** ([url]) — <one-sentence summary>. Authority: <type>.
  Recency: <bucket>. [synthesis or citation note]

## Secondary

(same shape)

## Tertiary

(same shape)
```

*The agent replaces every `<…>`. This is the schema the skill writes to; the artifact continues in the same shape.*

## Where this leads

**Done with this step:** You can move on when every sub-question would change the answer if dropped, and the primary sources are primary.
<!-- rung: authored -->

Stage 1 of four. Everything below reads what this step produced.

**Next:** [Run the research](run-the-research.md).
<!-- rung: authored -->

**Go deeper:** [the `desk-research` pack reference](../reference/desk-research-pack.md) — every skill this step runs, with its inputs and outputs.
<!-- rung: authored -->
