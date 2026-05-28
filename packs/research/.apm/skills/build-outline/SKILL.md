---
name: build-outline
description: Decompose a research question into the sub-questions a thorough answer must address. Builds the outline that `/source-map` then populates and `/research` then synthesises against. Grounded in STORM's outline stage (multi-perspective topic decomposition) and PRISMA's PICO framework (Population, Intervention, Comparison, Outcome — the systematic-review decomposition). Produces `outline.md` listing each sub-question with a brief rationale. Depth cues — `quickly`, `top three`, `briefly`, `summary only` for the must-answer few; `comprehensively`, `exhaustively`, `in depth`, `extensive` to chase second-order sub-questions.
---

# /build-outline

The pre-research scaffold. Decomposes a question into sub-questions so
the synthesis step has a structure to fill.

## When to invoke

- Before standard or deep `/research` on a broad question.
- As the first step in the survey pipeline (`/build-outline` →
  `/source-map` → `/research`).
- Not for narrow factual questions — those go straight to `/research`.

## Methodology

Two convergent disciplines:

1. **STORM outline stage** — STORM (Stanford's Synthesis of Topic
   Outlines through Retrieval and Multi-perspective question-asking)
   builds Wikipedia-style outlines by surveying adjacent topics, then
   asking what sections such an article would need. The pack borrows
   the *survey-then-decompose* shape: decomposition follows from what
   adjacent material covers, not from what the model assumes.

2. **PRISMA PICO** — the systematic-review framework decomposes a
   clinical question along four axes: Population, Intervention,
   Comparison, Outcome. PICO generalises beyond medicine: every
   research question has a target, a variable, an alternative, and a
   criterion. The pack borrows the *axis-decomposition* shape.

## Procedure

1. **Restate the question.** Identify the axes that matter — PICO is
   the medical case; for a software question the axes might be
   "system / change / alternative / failure mode".
2. **Survey adjacent material** (STORM step) — what do good answers to
   adjacent questions look like? What sections do they have?
3. **Enumerate sub-questions** — each one is a question the final
   `research.md` must answer. Tag each with a one-sentence rationale.
4. **Order the sub-questions** — context-first, then comparisons, then
   trade-offs, then conclusions.
5. **Write `outline.md`**.

## `outline.md` output schema

```markdown
# Outline — <main question>

## Sub-question 1: <question>

**Rationale:** <one sentence on why this matters to the main question>.

## Sub-question 2: <question>

(same shape)

## Open / second-order sub-questions

- <question the main answer might raise but doesn't itself answer>.
```

## Citation discipline

Sub-question rationales are arguments, not assertions — mark
`[synthesis]` when they integrate across cited material, `[inference]`
when they deduce from precedent. Citations attach when a sub-question
is justified by a specific source (e.g., "PRISMA recommends this
decomposition" → cite the PRISMA handbook).

## Depth cues

- `quickly`, `top three`, `briefly`, `summary only` — return the
  must-answer few sub-questions only; skip open / second-order.
- `comprehensively`, `exhaustively`, `in depth`, `extensive` — chase
  second-order sub-questions; surface the questions a thorough answer
  raises but doesn't itself resolve.
