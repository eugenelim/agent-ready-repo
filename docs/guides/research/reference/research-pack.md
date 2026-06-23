# Research pack — reference

The dry catalogue of every primitive in the `research` pack. For the walkthrough, see [your first research session](../tutorials/research-first-session.md); for the why, see [the research methodology explanation](../explanation/research-methodology.md).

## Skills

Seven skills ship in the pack. The `name` and `description` below are reproduced verbatim from each skill's SKILL.md frontmatter (single- sourced — if the SKILL.md description changes, this reference is regenerated to match).

### identify-perspectives

**name:** `identify-perspectives`.

**description:** Enumerate the named camps on a contested topic before research begins. Builds the perspective scaffold that `/source-map` and `/compare-hypotheses` consume downstream in the decision pipeline. Grounded in Wikipedia NPOV (neutral point of view — fairly represent significant views) and ACH (competing hypotheses — surface all explanations before evaluating). Produces `<topic-slug>-perspectives.md` listing each camp's name, its core claim, and representative voices, plus a tension map recording which disagreements are irreducible (both sides right under different conditions) and what a forced resolution would destroy. Depth cues — `quickly`, `top three`, `briefly` for the dominant few; `comprehensively`, `exhaustively`, `in depth`, `extensive` for fringe and dissenting positions too.

### build-outline

**name:** `build-outline`.

**description:** Decompose a research question into the sub-questions a thorough answer must address. Builds the outline that `/source-map` then populates and `/research` then synthesises against. Grounded in STORM's outline stage (multi-perspective topic decomposition) and PRISMA's PICO framework (Population, Intervention, Comparison, Outcome — the systematic-review decomposition). Produces `<topic-slug>-outline.md` listing each sub-question with a brief rationale. Depth cues — `quickly`, `top three`, `briefly`, `summary only` for the must-answer few; `comprehensively`, `exhaustively`, `in depth`, `extensive` to chase second-order sub-questions.

### source-map

**name:** `source-map`.

**description:** Curate the authoritative sources for a topic before research begins. Surveys adjacent material to discover voices rather than asking the LLM directly who's authoritative — STORM's finding is that direct question-asking does not work well for source discovery. Produces `<topic-slug>-sources.md` grouping candidates by primacy (`primary` / `secondary` / `tertiary`). When invoked downstream of `/identify-perspectives`, groups sources by camp; in standalone invocations, skips the camp-grouping step. Depth cues — `quickly`, `top three`, `briefly`, `summary only` for narrow surveys; `comprehensively`, `exhaustively`, `in depth`, `extensive` for thorough ones.

### research

**name:** `research`.

**description:** Evidence-grounded research with selectable depth and discipline. Use for any look-up, find-out, fact-check, or comprehensive investigation, including prior art and best practice surveys. Carries a mode parameter (quick / standard / applied / deep) with `quick` as default — casual phrasings (`look up`, `find out`, `quick check`) stay quick; academic phrasings (`research with citations`, `evidence-grounded`, `go deep`, `comprehensively`) bias standard or deep; practitioner phrasings (`applied patterns for`, `best practice for`, `prior art on`, `grey literature`) bias applied. Quick mode is inline, ≤5 fetches, no artifact. Standard mode produces `<topic-slug>-survey.md` with GRADE-style confidence per finding from peer-reviewed and primary sources. Applied mode produces `<topic-slug>-survey.md` calibrated for practitioner grey literature with a discipline-aware confidence overlay. Deep mode additionally auto-runs `/devils-advocate`, producing `<topic-slug>-counterpoints.md`.

### devils-advocate

**name:** `devils-advocate`.

**description:** Adversarially review a research artifact (`<topic-slug>-survey.md`) or a user-supplied claim. Searches for counter-evidence, names the strongest objections, and routes each to a verdict — either a confidence-rating downgrade or a do-not-resolve verdict for an irreducible tension where both sides are well-evidenced under different conditions. Grounded in ACH (evidence-against column — the discipline that catches premature closure) and GIJN investigative-journalism practice ("what does the other side say"). Auto-invoked by `/research` deep mode against `<topic-slug>-survey.md`; runs standalone against any user-supplied claim. Produces `<topic-slug>-counterpoints.md` linking back to the source artifact. Depth cues — `quickly`, `top three`, `briefly`, `summary only` for the strongest objections; `comprehensively`, `exhaustively`, `in depth`, `extensive` for the full set.

### compare-hypotheses

**name:** `compare-hypotheses`.

**description:** Compare competing hypotheses on a decision-shaped question using an ACH-style evidence matrix (hypotheses × evidence-for/against). Dispatches per-hypothesis parallel retrieval on Claude Code (one `evidence-retriever` subagent per hypothesis — the +81% parallelizable-task case from multi-agent research). In decision-pipeline invocations expects upstream `<topic-slug>-perspectives.md` and `<topic-slug>-sources.md`; standalone invocations enumerate hypotheses inline. Produces `<topic-slug>-hypotheses.md` with the matrix and a most-supported ranking. Depth cues — `quickly`, `top three`, `briefly`, `summary only` for the dominant hypotheses; `comprehensively`, `exhaustively`, `in depth`, `extensive` for fringe ones too.

### decision-archaeology

**name:** `decision-archaeology`.

**description:** Reconstruct the rationale for a past decision by walking time-ordered artifacts (commits, PRs, design docs, chat logs, internal memos). Self-contained — does not invoke `/source-map` or other research-pack skills, because the source surface is time-ordered and internal, and authority is established by an artifact's place in the history rather than by external curation. Produces `<topic-slug>-archaeology.md` with chronology, the rationale chain, the alternatives that were considered and rejected, and a revival check flagging rejected alternatives whose original rejection rationale no longer holds. Depth cues — `quickly`, `top three`, `briefly`, `summary only` for the main rationale chain; `comprehensively`, `exhaustively`, `in depth`, `extensive` for branch alternatives and dead ends.

## Retrieval subagents

Two read-only retrieval subagents. Available on hosts that support subagent dispatch (Claude Code, Codex, Kiro, and the Copilot CLI + app — on Copilot they keep live web access via Copilot's `web` tool); on hosts without subagent support, skills run their retrieval inline.

### evidence-retriever

| Field | Value |
|---|---|
| Tools | `Read, Grep, Glob, WebFetch, WebSearch` |
| Model | `sonnet` |
| Used by | `/research` (standard / deep), `/compare-hypotheses`, `/devils-advocate` |

Given a scoped query, fetches web and local material; returns a synthesised summary with citations. Does not return raw HTML or untruncated source text — it is the context-preservation buffer.

### source-extractor

| Field | Value |
|---|---|
| Tools | `Read, Grep, Glob, WebFetch, WebSearch` |
| Model | `sonnet` |
| Used by | `/source-map`, `/decision-archaeology` |

Given a list of candidate sources, extracts substantive content per source; returns per-source syntheses with citations.

## `/research` mode parameter

`/research` is the only skill with a formal mode parameter (the other six use depth-via-prompt cues). The closed set, four modes:

| Mode | Default? | Artifact | Discipline | Retrievers | Triangulation |
|---|---|---|---|---|---|
| `quick` | yes | none (inline) | n/a | built-in WebFetch + WebSearch only; ≤5 fetches | not required |
| `standard` | no | `<topic-slug>-survey.md` | academic / primary-source | all available | ≥3 independent sources |
| `applied` | no | `<topic-slug>-survey.md` + discipline marker | practitioner / grey-literature | all available | ≥3 independent sources; practitioner-independence calibration (same vendor / same employer count as one) |
| `deep` | no | `<topic-slug>-survey.md` + `<topic-slug>-counterpoints.md` | academic / primary-source | all available | ≥3 independent sources |

### Cue vocabulary

The dispatcher selects modes from the prompt's wording. Cue precedence: **applied cues are scored before standard / deep cues** — a prompt containing any applied cue dispatches `applied`, even when standard or deep cues co-occur. Closed tuples (single-sourced from the conformance test):

| Mode | Cue tuple (any one biases toward this mode) |
|---|---|
| `quick` (default; all three required in description) | `look up`, `find out`, `quick check` |
| `standard` / `deep` | `research with citations`, `evidence-grounded`, `go deep`, `comprehensively` |
| `applied` | `applied patterns for`, `best practice for`, `prior art on`, `grey literature` |

### Applied-mode discipline marker

Applied-mode `<topic-slug>-survey.md` carries this canonical, byte-for-byte literal as its first non-heading line:

```
> Discipline: applied (practitioner-pattern survey)
```

No bold, no em-dash variant. The marker is an audit signal recording that applied mode fired; it is NOT the rule-set selector (the `mode` parameter is — see the confidence schema overlay below).

## Confidence schema

Every finding in a standard / deep `<topic-slug>-survey.md` ends with a tag from the closed set: `high`, `moderate`, `low`, `uncertain`. A finding that would otherwise rate `high` steps down one level per downgrade factor that applies — `high` → `moderate` for one factor, `moderate` → `low` for two, `low` → `uncertain` for three or more.

| Level | Meaning |
|---|---|
| `high` | Multiple independent primary sources converge; no substantive contradicting evidence. |
| `moderate` | Independent sources converge but at least one downgrade factor applies. |
| `low` | Single source, or non-independent sources, or substantive contradicting evidence. |
| `uncertain` | Evidence is thin, conflicted, or absent. |

Examples — `high` reads "the evidence is unambiguous"; `moderate` reads "well-supported but with named caveats"; `low` reads "plausible but treat with caution"; `uncertain` reads "we don't know, and the artifact says so".

### Downgrade factors

Named explicitly when applied — silent downgrade is a defect.

- `single source` — claim rests on one citation.
- `no peer review` — sources are not peer-reviewed and alternatives exist. **Standard / deep mode only — dropped under the applied-mode overlay.**
- `vendor-blogged` — sources are vendor blog or marketing material.
- `contested-in-field` — `/devils-advocate` surfaced substantive counter-evidence.
- `heterogeneity` — cited sources do not agree on specifics.
- `indirectness` — sources address an adjacent question, not the exact one.

### Applied-mode overlay

Applied mode swaps two amendments into the base schema:

- **Drops** `no peer review` from the closed downgrade-factor set. The practitioner / grey-literature domain has no peer-reviewed alternative by construction; applying the factor would poison every finding to `[low]`.
- **Adds** two new downgrade factors:
  - `survivorship bias` — only successes blog; failed adopters rarely write post-mortems; the cited literature systematically under-represents failure stories.
  - `stale prior art` — a pattern from >5 years ago in a fast-moving domain may have been superseded.

The mode parameter (`mode: applied`) is the rule-set selector. The discipline marker on the produced artifact is the audit signal that the overlay fired — it does NOT retroactively re-rate findings if added to a standard-mode artifact after the fact.

## Retriever interface

User-registered Python script retrievers under `scripts/<name>-retriever.py` return a dict with three required keys:

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

A retriever returning `"raw"` or `"synthesized"` with an empty `citations` array is a contract violation.

## Depth cue vocabulary

Each of the six skills other than `/research` documents a closed vocabulary of depth cues an adopter can include in a prompt to adjust behavior. The full vocabulary, used across the pack:

- `quickly` — narrow scope, fastest path.
- `top three` — return the dominant few only.
- `briefly` — abbreviated artifact.
- `summary only` — one-line per item.
- `comprehensively` — full enumeration.
- `exhaustively` — chase second-order material.
- `in depth` — extended analysis per item.
- `extensive` — include fringe / weaker material.

Cue tokens are advisory — the skill body documents which cues bias which behavior. The pattern is natural-language depth selection, not a formal mode parameter.

## Pipeline shapes

| Pipeline | Sequence | Final artifacts |
|---|---|---|
| Survey | `/build-outline` → `/source-map` → `/research` | `<topic-slug>-outline.md` + `<topic-slug>-sources.md` + `<topic-slug>-survey.md` (+ `<topic-slug>-counterpoints.md` in deep) |
| Decision | `/identify-perspectives` → `/source-map` → `/compare-hypotheses` → `/devils-advocate` | `<topic-slug>-perspectives.md` + `<topic-slug>-sources.md` + `<topic-slug>-hypotheses.md` + `<topic-slug>-counterpoints.md` |
| Archaeology | `/decision-archaeology` | `<topic-slug>-archaeology.md` |

## Pack metadata

| Field | Value |
|---|---|
| Pack name | `research` |
| Version | `0.1.0` |
| Adapter contract | `0.8` |
| Default scope | `user` |
| Allowed scopes | `user`, `repo` |
| Allowed adapters | `claude-code`, `kiro`, `codex` |
