---
title: "Run it as a project"
summary: "Carry a question that outlasts one session: accumulate a corpus, digest it, and stop when it stops moving."
pack: desk-research
kind: how-to
order: 4
---

# Run it as a project

**Step 4 of 4 — Run it as a project**
<!-- rung: packs/desk-research/JOURNEY.md -->

**What changes:** A question too large for one session becomes a standing project with a falsifiable hypothesis, a corpus, and an explicit stop signal.
<!-- rung: packs/desk-research/JOURNEY.md -->

**What you need first:** A question worth weeks rather than one session, and somewhere to keep the project folder.
<!-- rung: authored -->

*Skipping costs:* The corpus grows forever, because nothing states what would settle the question.
<!-- rung: authored -->

**Concepts:**
<!-- rung: authored -->

- [Episodic vs project research](../explanation/episodic-vs-project-research.md) explains the two axes: how deep one session goes, and how long an investigation runs.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `desk-research-project-start` | A question worth weeks, not one session | The project folder, its overview, and the working hypothesis. | Required |
| `desk-research-project-digest` | A collected corpus | A synthesis matrix and the analytic memos behind it. | Required |
| `desk-research-project-check` | A synthesis matrix | A read on whether new sources are still changing the structure. | Required |
| `desk-research-project-synthesize` | A saturated corpus | The typed verdict and a brief someone else can act on. | Required |
| `desk-research-project-status` | Nothing — it reads what exists | The phase, the hypothesis, and what to do next. | Optional |

Prompts go into an AI agent session with this pack installed — the same session
throughout. In every path below, `<topic-slug>` is the short kebab-case name you
give the investigation, and it stays the same across every artifact so one
study's files sort together.

<!-- rung: packs/desk-research/JOURNEY.md -->

## Run `desk-research-project-start` — open the project

**You type:**
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-start/SKILL.md -->

```
Start a research project on how teams operate design systems at scale. This runs over several weeks.
```

**Agent returns:**
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-start/SKILL.md -->

> **Agent:** Done — I've written a project folder with an overview, a stated working hypothesis, and the phase it is starting in to `<project-folder>/overview.md`.

**You push back:**
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-start/SKILL.md -->

> **You:** The working hypothesis is a topic, not a hypothesis. State something the evidence could contradict.
>
> **Agent:** I rewrote it as a falsifiable claim and recorded the original topic as the project's scope line instead.

**Output varies** with the question, the time you have, and whether a prior corpus exists.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-start/SKILL.md -->

**You decide:** Set the scope and the depth before this runs — the pack's `set-research-scope-and-depth` gate. A project is a standing commitment, not a session.
<!-- rung: packs/desk-research/JOURNEY.md -->

**Check (falsifiable):** Ask what finding would make you abandon the working hypothesis; this surfaces a hypothesis that no evidence could contradict.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-start/SKILL.md -->

**Watch out for:** A project started without a falsifiable hypothesis accumulates sources forever, because nothing can ever settle it. Notice a hypothesis phrased as a topic — "how teams do X" is a subject, not a claim.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-start/SKILL.md -->

**Where it lands:** `<project-folder>/overview.md`.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-start/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
# <project name>

**Phase:** collect
**Working hypothesis:** <a claim the evidence could contradict>
**Scope:** <what is in, what is out>

## Corpus

## Stop-signal verdict
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Run `desk-research-project-digest` — the synthesis matrix

**You type:**
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-digest/SKILL.md -->

```
Digest the sources we have collected into the synthesis matrix.
```

**Agent returns:**
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-digest/SKILL.md -->

> **Agent:** Done — I've written a synthesis matrix with constructed columns, plus the analytic memos behind each column to `<project-folder>/synthesis-matrix.md`.

**You push back:**
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-digest/SKILL.md -->

> **You:** These columns are just the source categories. Construct columns from what the sources disagree about, not from where they came from.
>
> **Agent:** I rebuilt the columns around three axes of disagreement and moved the provenance into the memo notes.

**Output varies** with how many sources you have and how much they disagree.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-digest/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (observable):** Ask which column any one source scores differently on than its neighbours; this surfaces columns that every source answers the same way and therefore separate nothing.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-digest/SKILL.md -->

**Watch out for:** A matrix whose columns are source types is an inventory, not a synthesis. Notice columns named after venues or formats rather than claims.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-digest/SKILL.md -->

**Where it lands:** `<project-folder>/synthesis-matrix.md`.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-digest/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
# Synthesis matrix — <project name>

| Source | <constructed column> | <constructed column> |
| --- | --- | --- |

## Memo: <constructed column>

<why this column exists and what it separates>
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Run `desk-research-project-check` — has it stopped moving?

**You type:**
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-check/SKILL.md -->

```
Check the stop signal — are new sources still changing the matrix, or have we saturated?
```

**Agent returns:**
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-check/SKILL.md -->

> **Agent:** Done — I've written a saturation read on the corpus and a recommendation on whether to keep collecting. Nothing was written to disk.

**You push back:**
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-check/SKILL.md -->

> **You:** You called it saturated after three sources in one camp. Check whether the camps we identified are all represented before recommending we stop.
>
> **Agent:** I checked coverage by camp, found one unrepresented, and changed the recommendation to keep collecting in that camp only.

**Output varies** with corpus size, how evenly the camps are covered, and how fast the field moves.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-check/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (observable):** Ask which of the last three sources changed a column; this surfaces saturation declared from fatigue rather than from evidence.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-check/SKILL.md -->

**Watch out for:** Saturation and boredom look identical from inside the project. Notice a verdict that cites no recent source, and treat a stop recommendation with no coverage breakdown as unfinished.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-check/SKILL.md -->

**Writes no artifact.** It reports in the agent session and does not change files.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-check/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
Stop-signal check — <project name>

Recent sources: <n>
Columns changed by them: <n>
Coverage by camp: <camp>: <n>, <camp>: <n>

Verdict: <saturated | keep collecting>
Recommendation: <what to do next>
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Run `desk-research-project-synthesize` — the governance brief

**You type:**
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-synthesize/SKILL.md -->

```
Synthesize the project into its verdict and write the governance brief.
```

**Agent returns:**
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-synthesize/SKILL.md -->

> **Agent:** Done — I've written a typed verdict and a self-contained brief, with the gaps named rather than smoothed over to `<project-folder>/brief.md`.

**You push back:**
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-synthesize/SKILL.md -->

> **You:** The brief assumes the reader has the matrix open. Make it stand alone — state the verdict and the evidence in it.
>
> **Agent:** I made the brief self-contained, moved the matrix to an appendix reference, and kept the gap list in the body.

**Output varies** with the question's shape, which decides the verdict type the brief carries.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-synthesize/SKILL.md -->

**You decide:** Review the synthesis before it is used — the pack's `review-research-synthesis` gate. This is the artifact other people will act on.
<!-- rung: packs/desk-research/JOURNEY.md -->

**Check (sufficient-for-next):** Hand the brief to someone who has not read the corpus and ask what they would do; this surfaces a brief that only works for its author.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-synthesize/SKILL.md -->

**Watch out for:** Weeks of work create pressure to state a conclusion. Notice a verdict stated more confidently than the matrix supports, and check the gap list is still in the brief rather than trimmed for length.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-synthesize/SKILL.md -->

**Where it lands:** `<project-folder>/brief.md`.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-synthesize/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
# <project name> — brief

**Verdict:** <typed verdict>

## What the evidence supports

## What it does not

## Gaps

- **Known-unknown:** <what evidence would close it>.
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Run `desk-research-project-status` — where the project is

**You type:**
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-status/SKILL.md -->

```
Where are we on the design-systems research?
```

**Agent returns:**
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-status/SKILL.md -->

> **Agent:** Done — I've written the current phase, the working hypothesis, the last stop-signal verdict, and the next action. Nothing was written to disk.

**You push back:**
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-status/SKILL.md -->

> **You:** You reported the phase from the folder name. Read the overview and report what the stop-signal check actually said.
>
> **Agent:** I read the overview and reported the recorded verdict, which was keep collecting, not the phase I inferred.

**Output varies** with what the project folder contains and how recently it was updated.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-status/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (observable):** Compare the reported phase with the last dated entry in the overview; this surfaces a status read from structure rather than from content.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-status/SKILL.md -->

**Watch out for:** A status report is only as fresh as the overview it reads. Notice a confident phase with no recent entry behind it — the project may have stalled rather than progressed.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-status/SKILL.md -->

**Writes no artifact.** It reports in the agent session and does not change files.
<!-- rung: packs/desk-research/.apm/skills/desk-research-project-status/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
Research project — <project name>

Phase: <phase>
Working hypothesis: <claim>
Last stop-signal verdict: <verdict>

What to do next: <skill>
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Where this leads

**Done with this step:** You are done when the stop signal says the corpus has stopped changing the structure and the brief stands alone.
<!-- rung: authored -->

Stage 4 of four, and the pack's second human gate. The brief is what other packs read.

**Next:** [the guides hub](../../README.md#p3--build-it--2-hours) — evidence feeds a decision, and a decision feeds the build loop.
<!-- rung: authored -->

**Go deeper:** [the `desk-research` pack reference](../reference/desk-research-pack.md) — every skill this step runs, with its inputs and outputs.
<!-- rung: authored -->
