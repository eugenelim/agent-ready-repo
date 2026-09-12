# AGENTS.md — `guides/`

Applies to `guides/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

## Audience and publication

`guides/` is adopter-facing; `docs/guides/` is maintainer material. This tree is
published by `tools/build-site.py`: writing a valid file is all publication and
navigation require. Use the `author-product-docs` skill for authoring work.

## Content traps

[`contracts/guide.schema.json`](../contracts/guide.schema.json) owns frontmatter;
`additionalProperties: false` means new fields belong there first. Keep `title`
and the leading body H1 identical: `_shared` guides ship without rendered
frontmatter, so no H1 leaves adopters without a page heading.

When deleting or renaming a page, delete its `guide-nav-baseline.toml` entry in
the same change. The nav-ineligible set is pinned by its inventory test.

- Prefer in-tree link targets: links out of `guides/` render as GitHub blob URLs
  and send readers off-site.

## The guidebook step contract

**Every guidebook step must carry every obligation below.** A guidebook
step is a guide page carrying `order:` frontmatter inside a pack's guidebook;
`tools/lint-guidebook-steps.py` enforces this list and reads its identifiers,
judgement kinds and prohibited vocabulary from this section.

| Id | The step carries |
| --- | --- |
| `position` | Where you are in the sequence, with this step marked, in the page body |
| `prerequisite_cost` | What you must already hold, and what skipping it costs |
| `utterance` | What you type — a literal request |
| `attributed_response` | What comes back, attributed as the agent's turn and separate from your input |
| `variability` | That output varies — stated at this step, not once up front |
| `decision` | Where you decide, or that this step has no decision gate |
| `judgement_check` | How to tell it worked — a declared judgement kind, never a structural check the lint performs |
| `failure_path` | What to do when it does not: fix locally, re-prompt with the failing case, discard, step back, or escalate |
| `artifact_location` | The deliverable named, with its path; templated segments marked as templated |
| `artifact_preview` | An excerpt of the artifact itself, taken verbatim from the source that defines its shape |
| `next_step` | What to run next, named and linked |
| `concept_resolved` | Any concept the step depends on, named and linked to where it is explained |
| `what_changes` | What this step makes different, and what it costs to skip it |
| `correction` | One turn where the reader pushes back and the agent adjusts |
| `go_deeper` | One closing pointer at the authoritative source this step projects from |
| `step_map` | A table naming every skill this step runs, what each produces, and whether it is needed |

### How a step is written

Each obligation is declared by a label opening its own line, so the lint parses
rather than guesses. Prose that merely *mentions* a label does not declare it.

| Obligation | Label | Scope |
| --- | --- | --- |
| `position` | `**Step N of M — <title>**` | step |
| `what_changes` | `**What changes:**` | step |
| `prerequisite_cost` | `**What you need first:**` plus `*Skipping costs:*` | step |
| `concept_resolved` | `**Concepts:**` with links | step |
| `step_map` | `## What you will run` then a table | step |
| `next_step` | `**Next:**` with a link | step |
| `go_deeper` | `**Go deeper:**` with a resolving link | step |
| `utterance` | `**You type:**` then a fenced block | per skill |
| `attributed_response` | `**Agent returns:**` then a blockquote | per skill |
| `correction` | `**You push back:**` then a blockquote | per skill |
| `variability` | `**Output varies**` | per skill |
| `decision` | `**You decide:**`, or `**No decision gate at this step.**` | per skill |
| `judgement_check` | `**Check (<kind>):**` | per skill |
| `failure_path` | `**Watch out for:**` | per skill |
| `artifact_location` | `**Where it lands:**` with a backticked path, or `**Writes no artifact.**` | per skill |
| `artifact_preview` | `**What it looks like:**` then a fenced excerpt, or `**Writes no artifact.**` | per skill |

A per-skill obligation is declared inside that skill's own `## Run \`<skill>\``
block and nowhere else. A step naming ten skills with one shared utterance
satisfies nothing — a step-level value cannot be attributed to one of ten
skills, which is the difference between a skill being mentioned and a reader
being able to run it. Templated path segments are written `<slug>`, never as a
literal.

### The page skeleton, and why the heading levels are what they are

Every step page carries exactly these `##` headings, in this order:

1. `## What you will run`
2. `## Run \`<skill>\`` — one per skill, in run order
3. `## Where this leads`

Nothing else may be an `##`. The step's own framing — position, what changes,
what you need first, concepts — sits above the first heading, because a reader
arriving from search needs it before any navigation.

**The level is load-bearing, not cosmetic.** The docs site renders an in-page
table of contents from `h2`–`h3` only. These blocks were once `####`, so a step
running eight skills published a table of contents with one entry and a reader
on a long page had no way to jump to the skill they wanted. Eye-tracking work on
scanning also finds that a reader skimming a page reads the `h2` and `h3`
headings and little else — which is why the heading names a skill and what it
produces, rather than being a bare label.

`step_map` is the step's one overview, and it exists to answer a question the
per-skill blocks structurally cannot: **which of these do I actually have to
run?** A step presenting four skills in the same imperative `Run` form, with the
optional ones distinguished only by a sentence of prose, reads as four
obligations. The table's third column says so per skill, and the lint checks the
table against the headings in both directions — a skill with no row, or a row
with no block, is a finding.

`utterance` is a **fenced block**, not inline code. The site attaches a copy
button to fenced blocks and to nothing else, so an inline utterance made the one
value on the page a reader must transfer verbatim the one value they had to
retype. Keep the fence unlabelled: it is a sentence typed into a chat session,
not source in any language.

`## What you will run` also states **where** these are typed and what the
templated path segments mean, once, in a line under the table. A reader arriving
from search lands mid-guidebook and never sees the entry page, so a step that
shows `<output_dir>/journeys/<slug>.md` without ever resolving either segment
has named a location the reader cannot find. Say it on every step; the
repetition is the point.

Worked examples of each label, and the exact parse, are in
`python3 tools/lint-guidebook-steps.py --help`.

Take each projected value from the highest rung of its ladder that exists — the
pack's `JOURNEY.md` stage, then the skill's `SKILL.md`, then authored — and
record which rung it came from **in an HTML comment**, `<!-- rung: … -->`,
anywhere inside that obligation's block.

**Where the rung is a file, write its repository-relative path.** For
`artifact_preview` this is load-bearing: the lint compares the excerpt against
that file, so a rung naming a source without its path — "the skill's asset
template" — makes the comparison silently do nothing. Write
`<!-- rung: packs/<pack>/.apm/skills/<skill>/assets/<file>.md -->`, or
`<!-- rung: authored -->` when there is nothing to compare against. Authoring is permitted only where no higher rung
exists.

The comment form is not decoration. Provenance is bookkeeping for a maintainer
and a lint; a reader asked what "Rung" meant when it was published as visible
prose. A comment keeps it checkable and keeps it off the page.

`correction` exists because a step showing only a clean response teaches a
reader to accept the first draft. Show the reader rejecting something and the
agent adjusting — confident output is a halo effect, and a guide that never
models disagreement is a demo.

`what_changes` states what the step makes different. A step with no stated
purpose reads as ceremony. Keep it factual: this surface's content brief
forbids a persuasive before-and-after framing.

`go_deeper` closes with a link a reader can follow, and it must cover the whole
step. A step running eight skills that pointed at one skill's `SKILL.md` was
wrong twice over: the skill was chosen arbitrarily, and a `SKILL.md` is an
instruction file written for an agent, not reference written for an adopter.
Point at the pack's own reader-facing reference, which covers every skill the
step runs. Where a step runs exactly one skill, that skill's entry in the same
reference is the right depth.

`artifact_preview` shows the reader the thing, not a description of it. A list
of headings tells someone what sections exist; it does not tell them what the
artifact *is* — whether a stage is a paragraph or a table, whether the frontmatter
matters, how much they will be reading. A reader who has never seen the output
cannot judge whether what they got back is right, which is the whole job the
judgement check asks of them.

The excerpt is **a contiguous run of lines copied verbatim from the declared
rung source** — the lint looks for it there and a divergence is a finding. It is
not required to be the source's opening, because a template does not always
*be* the artifact: the screen brief opens with a page of rationale and carries
the artifact in a nested block partway down. Excerpting rather than
authoring is deliberate: an invented example that drifts from what the skill
actually writes teaches the reader the wrong shape and nothing fails. Show
enough to convey the form — through the first repeating unit is usually right —
and caption it with what the reader should notice. Where a skill declares no
template there is nothing to excerpt from, the preview is authored, and nothing
verifies it; that is a known and recorded limit, not a licence to invent freely.

Three further rules a lint enforces, each because a reader hit it:

- **`**Next:**` carries a resolving link**, not a prose promise. "Continue with
  the build workflow" names nothing a reader can click.
- **Every runnable a step names must be a published skill of that pack.** A
  subagent or a reviewer role is not something a reader can type, so it is
  described, never presented as a run.
- **A templated path segment uses `<segment>` and no other form.** A reader
  could not tell whether `[/screen]` was literal, an argument, or a
  placeholder.

**Link to an explanation; never absorb it.** Inlining explanation into a step is
content drift. Author a bounded explanation — a sentence or two plus a link out —
only where nothing exists to link to.

### Judgement kinds — closed set

The `judgement_check` obligation declares exactly one kind, from this list and
no other:

- `falsifiable`
- `testable`
- `observable`
- `sufficient-for-next`
- `grounded`

None names a structural obligation, and that is the point: a judgement list
that contains machine-checkable items degrades its own judgement items, because
a reader who knows a tool is watching reads less carefully.

### Prohibited vocabulary

No guidebook step may contain any of these terms. One per line, because a
backticked term wrapped across a newline stops being one token and is silently
dropped by every parser that reads this section — which is how two of these
went unenforced until a test noticed:

- `first value`
- `time to value`
- `faster adoption`
- `adopt faster`
- `completion rate`
- `task success`
- `productive sooner`
- `reach value sooner`

A step must not claim the reader adopts faster or succeeds more often — no
evidence supports it, and the install-to-first-value probe is unrun.

No step may state that each discipline **hands a named artifact to the next**,
or select a route on **how clear the problem is**. Both are retired claims: the
packs' own shipped contracts do not support the first, and the second made two
paths claim the same case.

These lists are lexical and the lint is lexical. A novel paraphrase passes it
and is caught by the cold read, not here.

### Why these obligations

[`docs/product/research/workflow-guidebooks-survey.md`](../docs/product/research/workflow-guidebooks-survey.md)
owns the evidence, the per-obligation confidence, and the known limitations —
this section does not restate them. Four obligations are **house choices** the
survey does not evidence and labels as such: `position`, `variability`'s
wording, `next_step`, and `artifact_preview`'s authored fallback, which nothing
independently verifies where a skill declares no shape.

## Essential commands

```bash
python3 tools/validate_guides.py
python3 tools/check-guide-index.py
python3 tools/lint-guide-titles.py
python3 tools/lint-guidebook-steps.py guides/<pack>
python3 tools/build-site.py
```

## Deeper pointers

`site.toml` and `tools/build-site.py` own navigation and projection details. For
rendered checks, follow [`docs-site/AGENTS.md` § Build](../docs-site/AGENTS.md#build).
