---
name: desk-research-project-synthesize
description: "Synthesize a research project into its typed verdict and a self-contained governance brief. Triggers on project-lifecycle phrasing — \"synthesize the project\", \"write up the findings\", \"produce the brief\" — inside an existing project folder. Reads synthesis-matrix.md + memos.md and writes BOTH the project's own typed synthesis (<type>.md, named by the project's shape) AND a single-file <topic-slug>-brief.md that governance can lift whole into an RFC. Applies GRADE confidence + ≥3-source triangulation; warns when the matrix is empty (digest was skipped). The brief is answer-first, self-contained, cited and per-finding confidence-tagged, with a Known unknowns section. Prompt-only: advances no phase on its own."
---

# /desk-research-project-synthesize

The **synthesis** phase of a research project. It reads the digest and emits two
artifacts: the project's own **typed verdict** (for the project's own readers)
and a **single-file governance brief** that can travel out of the folder into an
RFC, ADR, or spec.

## When to invoke

Inside an existing project folder with a populated digest, on phrasing like
*"synthesize the project"*, *"write up the findings"*, *"produce the brief"*.
The project should be in (or moving into) the `synthesize` phase.

## Inputs

- **Reads:** `synthesis-matrix.md` (the constructed-column concept matrix) and
  `memos.md` (the analytic memos, where the working hypothesis was formed and
  revised). Both from `/desk-research-project-digest`.

**Empty-matrix guard.** If `synthesis-matrix.md` is empty or absent — the digest
phase was skipped — **surface a warning** and recommend running
`/desk-research-project-digest` first. Synthesising with no digest produces an
ungrounded verdict; do not silently proceed.

## Outputs — two files

### 1. The typed synthesis `<type>.md`

The project's own verdict, named by the project's **shape** (from
`overview.md`), using the `/research` type vocabulary (§ Typed, topic-named
artifacts): a `survey` shape writes `survey.md`, a `comparison`/`decision` shape
writes `comparison-matrix.md`, an `adjudication` shape writes `hypotheses.md`,
a `structural` shape writes `blueprint.md`, a `methodology` shape writes
`methodology.md` (authored from
`../research/references/methodology-shape-template.md` — here the shape-name
equals the type-stem, so `methodology → methodology.md` follows the ordinary
`<shape-name>.md` rule, not the `adjudication → hypotheses.md` exception).
**Bare-named inside the folder** (the folder namespaces the topic). Every material claim carries GRADE confidence and
is backed by **≥3-source triangulation** per the `/research` confidence schema;
the optional `reliability`/`credibility` provenance axes inform the rating.

### 2. The governance brief `<topic-slug>-brief.md`

The **one exception to the bare-name rule** — topic-named because it travels out
of the folder. It is the distillation a code repo commits (the *decision*, not
the corpus). It MUST be:

- **Answer-first (BLUF).** The recommendation / answer is the top line, before
  any supporting detail — bottom-line-up-front.
- **Self-contained.** **No cross-links to other project files** (`memos.md`,
  `synthesis-matrix.md`, `sources/`). The brief is safe to copy whole out of the
  folder; a reader needs nothing else. Inline what matters; cite external
  sources by URL.
- **Cited and per-finding confidence-tagged.** Every load-bearing claim carries
  a citation and a GRADE confidence tag, exactly as a `/research` survey would.
- **Carrying a `## Known unknowns` section** — the questions a complete answer
  still needs, split into known-unknowns (answerable in principle; name the
  evidence that would close them) and unknowables (no evidence settles them).
  This section **maps 1:1 onto an RFC's *Evidence & prior art*** so the brief
  drops straight into governance.

```markdown
# <topic> — brief

**Bottom line:** <the answer / recommendation, one or two sentences>.

## What the evidence shows
- <finding> [high] — <citation>
- <finding> [moderate] — <citation>; downgrade: <factor>

## Known unknowns
- **Known-unknown:** <open question>. Would be closed by: <evidence>.
- **Unknowable:** <question no evidence settles>. Why not: <reason>.
```

## Reused skills in this phase

- `/compare-hypotheses` **is** the `hypotheses.md` synthesis for an adjudication
  shape — invoke it rather than re-deriving the matrix.
- `/devils-advocate` runs at synthesis against the typed verdict, producing the
  per-finding counter-pass that hardens the brief's confidence tags before it
  ships.

## What this skill is not

- Not a corpus dump — the brief is a distillation, self-contained and
  answer-first, not a tour of `sources/`.
- Not an engine — it writes Markdown the agent reasons into; nothing computes a
  verdict or advances `phase`.

## Next

The typed verdict and the brief are the project's durable output. Promote
`<topic-slug>-brief.md` into governance (an RFC's `NNNN-notes/` companion, an
ADR, or a spec). Phase advance to `feedback` is **human-driven** — this skill
never advances `phase` on its own.
