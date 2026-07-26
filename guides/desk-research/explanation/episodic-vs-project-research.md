# Episodic vs project research — the two axes

The `desk-research` pack answers questions at two very different scales, and it's
easy to reach for the wrong one. This page is about *when a question deserves a
one-off answer and when it deserves a project* — and why the pack treats those
as two independent axes rather than points on a single scale.

## Two axes, not one scale

It's tempting to imagine research as a single dial from "quick" to "thorough."
The pack doesn't model it that way. There are **two axes**, orthogonal to each
other:

- **Depth** — *how hard you look at a question in one sitting.* This is the
  `/desk-research` dial: `quick` (inline answer, no file), `standard` (cited
  synthesis), `applied` (practitioner grey-literature), `deep` (standard plus an
  adversarial pass). Depth is **episodic**: you ask, it answers, you get an
  artifact, you're done.
- **Lifecycle** — *whether the work is one-shot or accumulates over time.* This
  is project mode: the phases `capture → digest → synthesize → feedback`, a
  corpus that grows across days or weeks. Lifecycle is **stateful**: the project
  remembers what you've gathered and what you've concluded so far.

The axes are independent because a deep one-off and a sustained project are
different *shapes* of work, not different *amounts*. A single `deep` run can be
exhaustive and still be episodic — it answers one question, once. A project can
be made of many shallow `standard` runs and still be a project — because it
accumulates. Depth is how hard you look; lifecycle is how long you keep looking.

## What makes something a project

Reach for project mode when the work has these properties:

- **It outlasts one sitting.** You'll come back to it tomorrow, or next week,
  with more sources.
- **The corpus matters, not just the answer.** You want to see what forty
  sources collectively say, organized — not just read a synthesis of them.
- **The structure is still forming.** You don't yet know the dimensions the
  answer turns on; you'll discover them as you read. (The digest's emergent
  columns exist precisely for this.)
- **The decision is worth a durable artifact.** The end product is a brief
  someone will act on — an RFC, an ADR, a strategy call — not a passing answer.

If none of those hold, you want a one-off. *"What's the current default for X?"*,
*"is this claim true?"*, *"what have people tried for this shape of problem?"* —
those are episodic. Running a project for them is overhead with no payoff: a
folder, a lifecycle, and a digest where a single `<topic-slug>-survey.md` would
have done.

## The digest is the real difference

The visible difference is the folder and the phases. The *substantive*
difference is the **digest middle layer** — the `synthesis-matrix.md` and
`memos.md` that sit between raw sources and a synthesis.

A one-off `/desk-research` goes straight from sources to a written answer; the
intermediate reasoning is transient. A project makes that middle layer durable
and structured: a concept matrix whose columns are built from the material
(grounded-theory coding, not a fixed template), and analytic memos where the
working hypothesis forms and gets revised as evidence lands. That durable
middle layer is what lets a project hold a forty-source investigation a one-off
run can't: you can *see* the corpus, query it, and watch its structure
stabilize.

When the matrix structure stops changing — new sources only confirm existing
columns rather than adding new ones — the corpus has reached *theoretical
saturation*. That's the signal `/desk-research-project-check` reads, by eye, to tell
you when more gathering has stopped paying off.

## Why prompt-only, with no engine

A project tracks state — a `phase`, a stop-signal, a verdict status. It would be
natural to expect a little engine behind that: a counter of sources, a
computed saturation score, an index. There is none, deliberately.

`phase` is a string in `overview.md` that the agent reads and writes. Saturation
is a qualitative judgment a human confirms, not a threshold a number crosses.
The lifecycle is a **habit, not infrastructure** — it lives in the skill bodies
as instructions, the same way every other skill in the pack does. A score would
be false precision (what would "0.72 saturated" mean?), and an engine would be a
runtime the pack is built specifically not to need. The discipline is the
checklist; the judgment stays with you.

## How the two axes meet

They compose. Inside a project's capture phase, you run *episodic* `/desk-research`
calls per source or sub-question — depth in service of lifecycle. And a project's
synthesis reuses the same episodic skills as phase operations: `/source-map`
populates `sources/`, `/compare-hypotheses` *is* the adjudication synthesis,
`/devils-advocate` hardens the verdict. Project mode doesn't replace the depth
axis; it orchestrates it over time.

The decision tree is short: **one sitting, one answer → one-off `/desk-research`.
Accumulating corpus, durable brief → a project.** When in doubt, start with a
one-off; you can always promote what you learn into a project later, but you
rarely need to.

## See also

- [Your first research project](../tutorials/your-first-research-project.md) —
  run the lifecycle once, end to end.
- [Run a research project and feed it into an RFC](../how-to/run-a-research-project-into-an-rfc.md)
  — the task recipe and the governance handoff.
- [Research methodology — the why behind the pack](research-methodology.md) —
  the seven disciplines under the episodic depth axis.
- [Desk Research pack reference](../reference/desk-research-pack.md) — the catalogue of
  both axes' skills.
