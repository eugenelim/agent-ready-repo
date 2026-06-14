# How to run the research pipelines

The `research` pack ships seven skills. Three multi-skill pipelines compose them into the patterns adopters actually reach for: the **survey** pipeline for broad questions, the **decision** pipeline for contested choices, and the **archaeology** pipeline for "why did we do it this way" questions.

This guide is task-shaped. It assumes you already know what the pack does — if you don't, start with [your first research session](../tutorials/research-first-session.md). For the dry catalogue of every skill, see the [reference](../reference/research-pack.md).

```text
  survey       broad question, cited synthesis
    /build-outline ──► /source-map ──► /research
    outline.md         sources.md      research.md   (+ counterpoints.md with "go deep")

  decision     contested choice, weigh the positions
    /identify-perspectives ──► /source-map ──► /compare-hypotheses ──► /devils-advocate
    perspectives.md            sources.md       hypotheses.md           counterpoints.md

  archaeology  "why did we do it this way?"   (self-contained — no /source-map)
    /decision-archaeology
    archaeology.md
```

## Recipe 1 — the survey pipeline

**Use this when:** the question is broad and you need a structured synthesis with cited sources. Example: *"what does the field look like for X?"*

**Invocation sequence:**

```
/build-outline → /source-map → /research (standard or deep)
```

**Expected artifacts:**

1. `outline.md` — sub-questions a thorough answer must address.
2. `sources.md` — candidate sources grouped by primacy (`primary` / `secondary` / `tertiary`).
3. `research.md` — synthesised findings with GRADE-style confidence ratings. Add `go deep` to also produce `counterpoints.md`.

**Degraded-mode example:** skipping `/build-outline` and going straight to `/source-map` + `/research` works for narrower questions — the outline-stage decomposition is what makes the sources actually hit the sub-questions. Skip `/source-map` and `/research` falls back to its own retriever enumeration, which is fine for casual prompts but produces a thinner source list.

## Recipe 2 — the decision pipeline

**Use this when:** the question is contested and you need to compare competing positions with evidence. Example: *"should we adopt X approach, or Y, or Z?"*

**Invocation sequence:**

```
/identify-perspectives → /source-map → /compare-hypotheses → /devils-advocate
```

**Expected artifacts:**

1. `perspectives.md` — named camps with core claims and representative voices.
2. `sources.md` — candidates grouped by primacy *and* by camp (camp- grouping is the decision-pipeline-specific shape).
3. `hypotheses.md` — ACH-style matrix (hypotheses × evidence-for / against), with a ranking.
4. `counterpoints.md` — `/devils-advocate` against `hypotheses.md`; a per-finding verdict (rating downgrade, or do-not-resolve for an irreducible tension).

**Degraded-mode example:** if you skip `/source-map`, then `/compare-hypotheses` falls back to enumerating hypotheses with the sources it can find inline — it still produces `hypotheses.md`, but the matrix is thinner and `[high]` ratings will be rare because the triangulation discipline can't be satisfied. The downstream `/devils-advocate` pass then proposes more downgrades. The pipeline *degrades* gracefully — it doesn't break.

## Recipe 3 — the archaeology pipeline

**Use this when:** the question is "why did we do it this way?" — the artifact trail exists and you need to reconstruct rationale from it.

**Invocation sequence:**

```
/decision-archaeology
```

Just the one skill. `/decision-archaeology` is **self-contained** — it does not invoke `/source-map` or any other research-pack skill, because the source surface for archaeology is time-ordered internal artifacts, and authority is established by an artifact's place in the history rather than by external curation.

**Expected artifacts:**

1. `archaeology.md` — terminal artifact, chronology, rationale chain, alternatives considered.

**Degraded-mode example:** if the artifact trail is sparse — the decision was made in a chat archive that no longer exists, the doc was never written — `archaeology.md` will surface *alternatives-considered* as `[inference]` rather than cited material. The skill is honest about its evidence gaps; the `[inference]` tag is the signal that the rationale isn't established, just plausible.

## Picking between pipelines

| Question shape | Pipeline |
|---|---|
| "What does the field look like?" | survey |
| "What does X mean?" (factual, narrow) | `/research` quick mode alone |
| "Should we choose A, B, or C?" | decision |
| "Why did we choose this approach?" | archaeology |
| "What's wrong with this finding?" | `/devils-advocate` standalone |

When in doubt, start with `/research` in quick mode — it's the cheapest path and the answer might be enough.

## Composing further

The pipelines aren't mutually exclusive. After the decision pipeline produces `hypotheses.md`, you might run `/decision-archaeology` against the leading hypothesis to reconstruct how the team last considered it. After `/research` standard produces `research.md`, you might run `/devils-advocate` standalone against a single finding that surprised you.

The pack is set up so the artifacts compose: each downstream skill documents the upstream artifacts it expects, and what it does when they're absent.
