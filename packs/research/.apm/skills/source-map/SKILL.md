---
name: source-map
description: Curate the authoritative sources for a topic before research begins. Surveys adjacent material to discover voices rather than asking the LLM directly who's authoritative — STORM's finding is that direct question-asking does not work well for source discovery. Produces `<topic-slug>-sources.md` grouping candidates by primacy (`primary` / `secondary` / `tertiary`). When invoked downstream of `/identify-perspectives`, groups sources by camp; in standalone invocations, skips the camp-grouping step. Depth cues — `quickly`, `top three`, `briefly`, `summary only` for narrow surveys; `comprehensively`, `exhaustively`, `in depth`, `extensive` for thorough ones.
metadata:
  boundaries: [network_fetch]
---

# /source-map

Discovers and curates the sources a research artifact will eventually
cite. Runs upstream of `/research` standard / deep mode and upstream of
the decision pipeline; can also run standalone before any synthesis.

## When to invoke

- Before standard or deep research on an unfamiliar topic.
- After `/identify-perspectives` in the decision pipeline — sources are
  grouped per camp.
- Standalone, to scope which authorities a topic actually has.

## Methodology

The core discovery move is **survey-by-adjacency**, not direct
question-asking. STORM's finding: asking the LLM "who's authoritative
on X" produces a generic, training-data-shaped list. Instead, survey
adjacent material — papers that cite each other, blog posts that cross-
reference, communities that share vocabulary — and let the authorities
fall out of the pattern.

Treat any "who is authoritative on X" intuition the LLM produces as
suspect. Discovery is empirical, not asserted.

## Source taxonomy

Every candidate gets three tags:

1. **Authority type** — `practitioner` / `researcher` / `vendor` /
   `journalist` / `community` / `regulator`.
2. **Recency** — `current` (≤2 years) / `recent` (2–5 years) /
   `historical` (>5 years, still cited).
3. **Primacy** — `primary` (original source — the paper, the spec, the
   regulator's text), `secondary` (analyses and syntheses of primary
   material), `tertiary` (summaries-of-summaries, textbooks,
   encyclopedias).

The primacy tag is the most load-bearing — `/research` triangulation
requires ≥3 independent sources, and independence depends on primacy:
three tertiary sources citing the same primary source count as one.

## Procedure

1. **Survey adjacency** — issue WebSearch on the topic's key terms;
   skim the top-cited items; note who cites whom.
2. **Dispatch extraction** — on Claude Code, dispatch `source-extractor`
   subagent against the candidate list. Otherwise read each candidate
   inline.
3. **Classify** — tag each surviving source by authority + recency +
   primacy.
4. **Write `<topic-slug>-sources.md`** — group by primacy (primary first). In a
   decision-pipeline invocation, sub-group within primacy by camp (the
   upstream `<topic-slug>-perspectives.md` provides the camps). `<topic-slug>`
   is the kebab-case topic slug; the naming rule lives in the `/research` skill
   body (§ Typed, topic-named artifacts).
5. **Cite the rule** — `/research` will use `<topic-slug>-sources.md` to choose
   which sources to triangulate against.

## Upstream / standalone behavior

`/source-map` runs in two shapes:

- **Decision-pipeline invocation** — expects an upstream
  `<topic-slug>-perspectives.md`. Sources are grouped by primacy *and* by camp,
  so `/compare-hypotheses` downstream can pull camp-aligned sources per
  hypothesis.
- **Standalone invocation** — no upstream `<topic-slug>-perspectives.md` required.
  Sources grouped by primacy only; the camp-grouping step is skipped.

The skill is **not** invoked by `/decision-archaeology`, which is self-
contained. See that skill's body for why.

## `<topic-slug>-sources.md` output schema

```markdown
# Sources — <topic>

## Primary

- **<title>** ([url]) — <one-sentence summary>. Authority: <type>.
  Recency: <bucket>. [synthesis or citation note]

## Secondary

(same shape)

## Tertiary

(same shape)
```

In decision-pipeline mode, each primacy section is sub-grouped by camp
under `### Camp: <name>`.

## Citation discipline

Every entry in `<topic-slug>-sources.md` carries a citation (the URL or local path).
Notes about a source — its angle, its bias, its credibility — are
marked `[synthesis]` when they integrate across sources or `[inference]`
when they deduce from one.

## Depth cues

Adopters can include cue tokens in the prompt to adjust behavior:

- `quickly`, `top three`, `briefly`, `summary only` — narrow the survey;
  return the most-cited handful per primacy bucket only.
- `comprehensively`, `exhaustively`, `in depth`, `extensive` — widen
  the survey; chase secondary citations into their primary sources;
  include weaker authorities for completeness.
