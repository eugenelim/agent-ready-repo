---
name: compare-hypotheses
description: Compare competing hypotheses on a decision-shaped question using an ACH-style evidence matrix (hypotheses × evidence-for/against). Dispatches per-hypothesis parallel retrieval on Claude Code (one `evidence-retriever` subagent per hypothesis — the +81% parallelizable-task case from multi-agent research). In decision-pipeline invocations expects upstream `<topic-slug>-perspectives.md` and `<topic-slug>-sources.md`; standalone invocations enumerate hypotheses inline. Produces `<topic-slug>-hypotheses.md` with the matrix and a most-supported ranking. Depth cues — `quickly`, `top three`, `briefly`, `summary only` for the dominant hypotheses; `comprehensively`, `exhaustively`, `in depth`, `extensive` for fringe ones too.
---

# /compare-hypotheses

The decision-support skill. Takes the camps and sources from upstream
and produces a matrix that says which hypothesis the evidence
actually favors.

## When to invoke

- **Decision pipeline** — after `/identify-perspectives` and
  `/source-map`. Expects both upstream artifacts. This is the primary
  invocation shape.
- **Standalone** — when the user names the hypotheses to compare
  directly. The skill enumerates them inline (no upstream).
- **Not** for descriptive factual questions — those go to `/desk-research`.

## Invocation shapes

- **Pipeline invocation** — expects upstream `<topic-slug>-perspectives.md`
  (camps) and `<topic-slug>-sources.md` (sources tagged by primacy, optionally
  grouped by camp). The hypotheses come from the camps; the evidence comes from
  the sources.
- **Standalone invocation** — the user supplies the hypotheses
  directly; the skill enumerates them inline. Sources come from
  retriever dispatch within this skill rather than from an upstream
  artifact.

## Methodology

**ACH (Analysis of Competing Hypotheses)** matrix:

|                 | H1   | H2   | H3   |
|-----------------|------|------|------|
| Evidence E1     | ++   | --   | 0    |
| Evidence E2     | +    | +    | --   |
| Evidence E3     | --   | ++   | 0    |

Cells: `++` strongly supports, `+` weakly supports, `0` neutral, `-`
weakly contradicts, `--` strongly contradicts. The discipline catches
the analyst who weighs evidence asymmetrically across hypotheses.

## Parallel retrieval

On Claude Code, hypotheses-by-evidence is a +81% parallelizable-task
case: each hypothesis can be evaluated independently against the same
source pool. Dispatch N parallel `evidence-retriever` subagents — one
per hypothesis — and synthesise the returned per-hypothesis evidence
into the matrix.

On hosts without subagent support, fall back to sequential evaluation.

## Procedure

1. **Load upstream** (pipeline mode) or enumerate hypotheses (standalone
   mode).
2. **Dispatch retrievers** — one `evidence-retriever` per hypothesis,
   in parallel, scoped to the same source pool.
3. **Build the matrix** — rows are evidence items, columns are
   hypotheses; cell values per ACH notation above.
4. **Rate per-hypothesis confidence** — apply
   `references/confidence-schema.md` to each hypothesis's overall
   evidence position. Note where evidence is thin or single-sourced.
5. **Rank** — most-supported first. Name the dominant supporting
   evidence and the strongest contradicting evidence per hypothesis.
6. **Write `<topic-slug>-hypotheses.md`** — `<topic-slug>` is the kebab-case
   topic slug; the naming rule lives in the `/desk-research` skill body (§ Typed,
   topic-named artifacts).

## `<topic-slug>-hypotheses.md` output schema

```markdown
# Hypotheses — <decision question>

## Hypothesis H1: <name>

- **Claim:** <one sentence>.
- **Confidence:** `[moderate]`.
- **Strongest supporting:** <evidence item with citation>.
- **Strongest contradicting:** <evidence item with citation>.

## Hypothesis H2: <name>

(same shape)

## Matrix

|                 | H1  | H2  | H3  |
|-----------------|-----|-----|-----|
| <evidence E1>   | ++  | --  | 0   |
| <evidence E2>   | +   | +   | --  |

## Ranking

1. **H2** — strongest cited support, two `++` cells against H1's one.
2. **H1** — ...
3. **H3** — ...
```

## Citation discipline

Every cell value in the matrix traces to a cited evidence item. The
ranking rationale cites the matrix; cells cite the source.

## Depth cues

- `quickly`, `top three`, `briefly`, `summary only` — return the
  ranking with the dominant supporting / contradicting per hypothesis;
  omit the full matrix.
- `comprehensively`, `exhaustively`, `in depth`, `extensive` — full
  matrix; include fringe hypotheses; chase contradicting evidence
  harder.
