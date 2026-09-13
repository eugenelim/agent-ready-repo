# The pack walk

One record per pack, written by walking its guidebook page by page and skill by
skill as a first-time reader — not by reading the source that produced it.

## Why this exists as a record and not a checklist run

Three of the ordering and navigation defects in the first pack were invisible to
every lint we had, because each surface was internally consistent and wrong only
against something in another file. A walk is the only instrument that crosses
those boundaries, and a walk that leaves no record cannot be re-run against a
later version to see what moved.

## The seven dimensions

Walk every skill of every step against each. One row per skill.

| # | Dimension | The question a first-time reader is actually asking |
| --: | --- | --- |
| 1 | Starting point | What must already exist before I run this, and who made it? |
| 2 | Human vs agent | What is mine to decide and what is the agent's to produce? |
| 3 | Chat display | What does this exchange actually look like in a session? |
| 4 | Artifact to review | What am I about to be handed, and where does it land? |
| 5 | Result | How do I know it worked, and when may I move on? |
| 6 | Handover | What runs next, what does it need from this, and in what order? |
| 7 | Orientation | Where am I in this pack, and what happens after the pack ends? |

## Every finding names an owner

A walk finding is not automatically a guide defect. Route it, because fixing the
projection when the source is wrong makes the two disagree permanently:

| Owner | The finding is about | Fix in |
| --- | --- | --- |
| `guide` | How the walk is explained — wording, missing preview, absent orientation | `guides/<pack>/` |
| `skill` | What the skill declares — no output template, a contradicted precondition | `packs/<pack>/.apm/skills/<skill>/SKILL.md` |
| `journey` | What the pack declares about its own sequence and gates | `packs/<pack>/JOURNEY.md` |
| `contract` | Something no pack can currently express | the schema that owns the field |

**The guide and the skills drive each other.** The guide is a projection, so it
cannot be more correct than its source — but authoring it is the first time
anyone reads the pack in run order, which is why it finds source defects the
source's own tests cannot. When the walk and the source disagree, the source
wins and the finding is routed to it; when the source is silent, that silence is
itself the finding.

## Procedure

1. Walk the rendered pages, not the Markdown. A reader gets the rendered page.
2. One row per skill per dimension. Record what is there, not what should be.
3. Route every finding to an owner before fixing anything.
4. Fix, rebuild, and **rewalk** — the rewalk is what catches a fix that moved the
   defect rather than removing it.
5. Record the rewalk result in the same file, so the record shows both states.
