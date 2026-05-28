# Research pack — reference

The dry catalogue of every primitive in the `research` pack. For the
walkthrough, see [your first research session](../tutorials/research-first-session.md);
for the why, see [the research methodology explanation](../explanation/research-methodology.md).

## Skills

Seven skills ship in the pack. The `name` and `description` below are
reproduced verbatim from each skill's SKILL.md frontmatter (single-
sourced — if the SKILL.md description changes, this reference is
regenerated to match).

### identify-perspectives

**name:** `identify-perspectives`.

**description:** Enumerate the named camps on a contested topic
before research begins. Builds the perspective scaffold that
`/source-map` and `/compare-hypotheses` consume downstream in the
decision pipeline. Grounded in Wikipedia NPOV (neutral point of view
— fairly represent significant views) and ACH (competing hypotheses —
surface all explanations before evaluating). Produces
`perspectives.md` listing each camp's name, its core claim, and
representative voices. Depth cues — `quickly`, `top three`, `briefly`
for the dominant few; `comprehensively`, `exhaustively`, `in depth`,
`extensive` for fringe and dissenting positions too.

### build-outline

**name:** `build-outline`.

**description:** Decompose a research question into the sub-questions
a thorough answer must address. Builds the outline that `/source-map`
then populates and `/research` then synthesises against. Grounded in
STORM's outline stage (multi-perspective topic decomposition) and
PRISMA's PICO framework (Population, Intervention, Comparison,
Outcome — the systematic-review decomposition). Produces `outline.md`
listing each sub-question with a brief rationale. Depth cues —
`quickly`, `top three`, `briefly`, `summary only` for the must-answer
few; `comprehensively`, `exhaustively`, `in depth`, `extensive` to
chase second-order sub-questions.

### source-map

**name:** `source-map`.

**description:** Curate the authoritative sources for a topic before
research begins. Surveys adjacent material to discover voices rather
than asking the LLM directly who's authoritative — STORM's finding is
that direct question-asking does not work well for source discovery.
Produces `sources.md` grouping candidates by primacy (`primary` /
`secondary` / `tertiary`). When invoked downstream of
`/identify-perspectives`, groups sources by camp; in standalone
invocations, skips the camp-grouping step. Depth cues — `quickly`,
`top three`, `briefly`, `summary only` for narrow surveys;
`comprehensively`, `exhaustively`, `in depth`, `extensive` for
thorough ones.

### research

**name:** `research`.

**description:** Evidence-grounded research with selectable depth.
Use for any look-up, find-out, fact-check, or comprehensive
investigation. Carries `mode: quick | standard | deep` with `quick`
as default — casual phrasings (`look up`, `find out`, `quick check`,
`quickly`) stay quick; explicit phrasings (`research with citations`,
`evidence-grounded`, `go deep`, `comprehensively`) escalate. Quick
mode is inline, ≤5 fetches, no artifact. Standard mode produces
`research.md` with GRADE-style confidence per finding and ≥3
independent sources per material claim. Deep mode additionally
auto-runs `/devils-advocate`, producing `counterpoints.md` with
proposed rating downgrades.

### devils-advocate

**name:** `devils-advocate`.

**description:** Adversarially review a research artifact
(`research.md`) or a user-supplied claim. Searches for counter-
evidence, names the strongest objections, and proposes confidence-
rating downgrades. Grounded in ACH (evidence-against column — the
discipline that catches premature closure) and GIJN investigative-
journalism practice ("what does the other side say"). Auto-invoked by
`/research` deep mode against `research.md`; runs standalone against
any user-supplied claim. Produces `counterpoints.md` linking back to
the source artifact. Depth cues — `quickly`, `top three`, `briefly`,
`summary only` for the strongest objections; `comprehensively`,
`exhaustively`, `in depth`, `extensive` for the full set.

### compare-hypotheses

**name:** `compare-hypotheses`.

**description:** Compare competing hypotheses on a decision-shaped
question using an ACH-style evidence matrix (hypotheses ×
evidence-for/against). Dispatches per-hypothesis parallel retrieval
on Claude Code (one `evidence-retriever` subagent per hypothesis —
the +81% parallelizable-task case from multi-agent research). In
decision-pipeline invocations expects upstream `perspectives.md` and
`sources.md`; standalone invocations enumerate hypotheses inline.
Produces `hypotheses.md` with the matrix and a most-supported
ranking. Depth cues — `quickly`, `top three`, `briefly`,
`summary only` for the dominant hypotheses; `comprehensively`,
`exhaustively`, `in depth`, `extensive` for fringe ones too.

### decision-archaeology

**name:** `decision-archaeology`.

**description:** Reconstruct the rationale for a past decision by
walking time-ordered artifacts (commits, PRs, design docs, chat logs,
internal memos). Self-contained — does not invoke `/source-map` or
other research-pack skills, because the source surface is time-
ordered and internal, and authority is established by an artifact's
place in the history rather than by external curation. Produces
`archaeology.md` with chronology, the rationale chain, and the
alternatives that were considered and rejected. Depth cues —
`quickly`, `top three`, `briefly`, `summary only` for the main
rationale chain; `comprehensively`, `exhaustively`, `in depth`,
`extensive` for branch alternatives and dead ends.

## Retrieval subagents

Two read-only retrieval subagents. Available only on hosts that
support subagent dispatch (Claude Code); on hosts without subagent
support, skills run their retrieval inline.

### evidence-retriever

| Field | Value |
|---|---|
| Tools | `Read, Grep, Glob, WebFetch, WebSearch` |
| Model | `sonnet` |
| Used by | `/research` (standard / deep), `/compare-hypotheses`, `/devils-advocate` |

Given a scoped query, fetches web and local material; returns a
synthesised summary with citations. Does not return raw HTML or
untruncated source text — it is the context-preservation buffer.

### source-extractor

| Field | Value |
|---|---|
| Tools | `Read, Grep, Glob, WebFetch, WebSearch` |
| Model | `sonnet` |
| Used by | `/source-map`, `/decision-archaeology` |

Given a list of candidate sources, extracts substantive content per
source; returns per-source syntheses with citations.

## `/research` mode parameter

`/research` is the only skill with a formal mode parameter (the
other six use depth-via-prompt cues). The closed set:

| Mode | Default? | Artifact | Retrievers | Triangulation |
|---|---|---|---|---|
| `quick` | yes | none (inline) | built-in WebFetch + WebSearch only; ≤5 fetches | not required |
| `standard` | no | `research.md` | all available | ≥3 independent sources |
| `deep` | no | `research.md` + `counterpoints.md` | all available | ≥3 independent sources |

## Confidence schema

Every finding in a standard / deep `research.md` ends with a tag from
the closed set: `high`, `moderate`, `low`, `uncertain`. A finding
that would otherwise rate `high` steps down one level per downgrade
factor that applies — `high` → `moderate` for one factor, `moderate`
→ `low` for two, `low` → `uncertain` for three or more.

| Level | Meaning |
|---|---|
| `high` | Multiple independent primary sources converge; no substantive contradicting evidence. |
| `moderate` | Independent sources converge but at least one downgrade factor applies. |
| `low` | Single source, or non-independent sources, or substantive contradicting evidence. |
| `uncertain` | Evidence is thin, conflicted, or absent. |

Examples — `high` reads "the evidence is unambiguous"; `moderate`
reads "well-supported but with named caveats"; `low` reads "plausible
but treat with caution"; `uncertain` reads "we don't know, and the
artifact says so".

### Downgrade factors

Named explicitly when applied — silent downgrade is a defect.

- `single source` — claim rests on one citation.
- `no peer review` — sources are not peer-reviewed and alternatives exist.
- `vendor-blogged` — sources are vendor blog or marketing material.
- `contested-in-field` — `/devils-advocate` surfaced substantive counter-evidence.
- `heterogeneity` — cited sources do not agree on specifics.
- `indirectness` — sources address an adjacent question, not the exact one.

## Retriever interface

User-registered Python script retrievers under
`scripts/<name>-retriever.py` return a dict with three required keys:

| Key | Type | Meaning |
|---|---|---|
| `"content"` | string | The substantive material. |
| `"citations"` | list of `{url, title, primacy}` | Citation list. |
| `"shape"` | string from closed set | Retrieval shape — see below. |

### Shape values

| Value | Meaning | `citations` |
|---|---|---|
| `"raw"` | Returns extracted material verbatim; caller synthesises. | Required, non-empty. |
| `"synthesized"` | Returns a model-synthesised summary; caller cites and rates. | Required, non-empty. |
| `"meta"` | Returns retrieval metadata only (counts, capabilities). | Empty array permitted. |

A retriever returning `"raw"` or `"synthesized"` with an empty
`citations` array is a contract violation.

## Depth cue vocabulary

Each of the six skills other than `/research` documents a closed
vocabulary of depth cues an adopter can include in a prompt to
adjust behavior. The full vocabulary, used across the pack:

- `quickly` — narrow scope, fastest path.
- `top three` — return the dominant few only.
- `briefly` — abbreviated artifact.
- `summary only` — one-line per item.
- `comprehensively` — full enumeration.
- `exhaustively` — chase second-order material.
- `in depth` — extended analysis per item.
- `extensive` — include fringe / weaker material.

Cue tokens are advisory — the skill body documents which cues bias
which behavior. The pattern is natural-language depth selection, not
a formal mode parameter.

## Pipeline shapes

| Pipeline | Sequence | Final artifacts |
|---|---|---|
| Survey | `/build-outline` → `/source-map` → `/research` | `outline.md` + `sources.md` + `research.md` (+ `counterpoints.md` in deep) |
| Decision | `/identify-perspectives` → `/source-map` → `/compare-hypotheses` → `/devils-advocate` | `perspectives.md` + `sources.md` + `hypotheses.md` + `counterpoints.md` |
| Archaeology | `/decision-archaeology` | `archaeology.md` |

## Pack metadata

| Field | Value |
|---|---|
| Pack name | `research` |
| Version | `0.1.0` |
| Adapter contract | `0.8` |
| Default scope | `user` |
| Allowed scopes | `user`, `repo` |
| Allowed adapters | `claude-code`, `kiro`, `codex` |
