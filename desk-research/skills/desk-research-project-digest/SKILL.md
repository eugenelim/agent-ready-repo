---
name: desk-research-project-digest
description: "Build the digest middle layer of a research project — the constructed-column synthesis matrix and analytic memos the pack previously lacked. Triggers on project-lifecycle phrasing — \"digest the sources\", \"build the synthesis matrix\", \"cluster what I've gathered\" — inside an existing project folder. Reads sources/*.md, clusters each source's contribution into emergent columns (rows = sources, columns constructed from the material, never a fixed pillar set) in synthesis-matrix.md, and writes analytic memos.md where the working hypothesis is formed and revised. Prompt-only: no engine, no scoring, no fixed schema. Advances no phase on its own — the human moves capture → digest → synthesize."
---

# /desk-research-project-digest

The **middle layer** of a research project — the step between a pile of raw
sources and a synthesis. It turns `sources/` into a structured, queryable
digest: a **synthesis matrix** plus **analytic memos**. This is the capability
episodic `/research` never had a home for; a multi-week project needs a durable
place to see what the corpus is actually saying.

## Output rendering

Table — When presenting several items that share the same fields, render a Markdown table. Cap at ~5 columns; beyond that, switch to a per-item detail list. Right-align numeric columns.

## When to invoke

Inside an existing project folder (one scaffolded by
`/desk-research-project-start`), on phrasing like *"digest the sources"*, *"build the
synthesis matrix"*, *"cluster what I've gathered so far"*. The project should be
in (or moving into) the `digest` phase.

## Inputs and outputs

- **Reads:** `sources/*.md` — the raw layer (each file one source, with its
  optional `reliability` / `credibility` provenance axes).
- **Writes:** `synthesis-matrix.md` (the concept matrix) and `memos.md`
  (analytic memos). Bare-named inside the project folder.

## The synthesis matrix — emergent, constructed columns

`synthesis-matrix.md` is a **concept matrix** (Webster & Watson): **rows are
sources, columns are concepts**. The columns are **constructed from the
material** — grounded-theory open coding — **not chosen from a fixed pillar
set**. You read the sources, notice the dimensions they actually speak to, and
let those become the columns; as new sources introduce a new dimension, you
**add a column and revisit** earlier rows against it.

```markdown
# Synthesis matrix — <topic>

| Source | <emergent concept A> | <emergent concept B> | <emergent concept C> |
|---|---|---|---|
| src-01 | <what it says on A> | — | <what it says on C> |
| src-02 | <…> | <…> | <…> |
```

**Do not pre-set the columns.** There is no fixed-pillar schema (no
"performance / cost / security" template imposed before reading) — that is
exactly the failure mode the emergent rule refuses. The columns are whatever the
corpus is organised around, discovered by reading it. Revise the column set as
the corpus grows; a matrix whose structure has stopped changing is the
saturation signal `/desk-research-project-check` reads.

## Analytic memos — where the hypothesis forms

`memos.md` holds the **analytic memos**: short written reasoning about what the
matrix is showing — patterns across rows, tensions between sources, gaps. This
is where the project's **working hypothesis is formed and revised**: a project
that started with an empty `working_hypothesis` in `overview.md` forms one here
as evidence accumulates; a project that started with a prior revises it here as
the matrix contradicts or confirms it. There is no hard hypothesis gate — the
claim is held loosely and rewritten as the corpus warrants. Record each
revision with a dated memo so the reasoning trail is auditable.

## Provenance

Sources carry the optional Admiralty `reliability` / `credibility` axes from
`/desk-research-project-start`; use them to weight a source's contribution in the
matrix and memos. They **inform** the analysis — the claim-level rail stays
**GRADE confidence + ≥3-source triangulation** at synthesis time.

## Reused skills in this phase

- `/source-map` populates `sources/` (curates and grades candidate sources).
- `/build-outline` can seed the **initial** matrix columns from the question's
  sub-questions — a starting scaffold the emergent coding then overrides as the
  material dictates.
- `/identify-perspectives` supplies **perspective columns** for a contested
  topic (each camp a lens the matrix can carry).

## What this skill is not

- Not a fixed-schema scorecard — columns are emergent, never pre-set.
- Not an engine — nothing scores saturation or advances `phase`; this skill
  writes Markdown the agent reasons over.
- Not the synthesis — it structures the corpus; `/desk-research-project-synthesize`
  reads this digest and writes the verdict and the brief.

## Next

When the matrix and memos are populated, run `/desk-research-project-check` to read
the saturation signal, and `/desk-research-project-synthesize` to emit the typed
verdict and the governance brief. Phase advance is **human-driven** — this skill
never moves the project past `digest` on its own.
