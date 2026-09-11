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
| `artifact_outline` | The headings to expect inside it, with the source of that outline declared |
| `next_step` | What to run next, named and linked |
| `concept_resolved` | Any concept the step depends on, named and linked to where it is explained |

### How a step is written

Each obligation is declared by a label opening its own line, so the lint parses
rather than guesses. Prose that merely *mentions* a label does not declare it.

| Obligation | Label | Scope |
| --- | --- | --- |
| `position` | `**Step N of M — <title>**` | step |
| `prerequisite_cost` | `**You need:**` plus `*Skipping costs:*` | step |
| `concept_resolved` | `**Concepts:**` with links | step |
| `next_step` | `**Next:**` with a link | step |
| `utterance` | `**You type:**` | per skill |
| `attributed_response` | `**Agent returns:**` then a blockquote | per skill |
| `variability` | `**Output varies**` | per skill |
| `decision` | `**You decide:**`, or `**No decision gate at this step.**` | per skill |
| `judgement_check` | `**Check (<kind>):**` | per skill |
| `failure_path` | `**If it fails:**` | per skill |
| `artifact_location` | `**You now hold:**` with a backticked path | per skill |
| `artifact_outline` | `**Expect these headings:**` | per skill |

A per-skill obligation is declared inside that skill's own `#### Run \`<skill>\``
block and nowhere else. A step naming ten skills with one shared utterance
satisfies nothing — a step-level value cannot be attributed to one of ten
skills, which is the difference between a skill being mentioned and a reader
being able to run it. Templated path segments are written `<slug>`, never as a
literal.

Worked examples of each label, and the exact parse, are in
`python3 tools/lint-guidebook-steps.py --help`.

Take each projected value from the highest rung of its ladder that exists — the
pack's `JOURNEY.md` stage, then the skill's `SKILL.md`, then authored — and
record which rung it came from. Authoring is permitted only where no higher rung
exists.

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
wording, `next_step`, and `artifact_outline`'s authored fallback, which nothing
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
