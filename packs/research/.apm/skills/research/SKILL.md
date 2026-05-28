---
name: research
description: "Evidence-grounded research with selectable depth. Use for any look-up, find-out, fact-check, or comprehensive investigation. Carries a mode parameter (quick / standard / deep) with `quick` as default — casual phrasings (`look up`, `find out`, `quick check`, `quickly`) stay quick; explicit phrasings (`research with citations`, `evidence-grounded`, `go deep`, `comprehensively`) escalate. Quick mode is inline, ≤5 fetches, no artifact. Standard mode produces `research.md` with GRADE-style confidence per finding and ≥3 independent sources per material claim. Deep mode additionally auto-runs `/devils-advocate`, producing `counterpoints.md` with proposed rating downgrades."
---

# /research

The research lifecycle's anchor. Selects one of three modes based on the
prompt's depth signal, dispatches retrievers, synthesises findings with
citations and per-finding confidence ratings, and (in deep mode)
adversarially reviews its own output.

## When to invoke

Any prompt that asks the model to find out, look up, investigate,
fact-check, or synthesise external information. The mode is selected
from the prompt's wording, not asked of the user.

## Modes

Mode parameter: `mode: quick | standard | deep`. Default: `quick`.

| Mode | Default? | Artifact? | Retrievers | Triangulation |
|---|---|---|---|---|
| `quick` | yes | no — inline answer | built-in WebFetch + WebSearch only; ≤5 fetches | not required |
| `standard` | no | `research.md` | all available: built-in + MCP + script retrievers + subagents | ≥3 independent sources per material claim |
| `deep` | no | `research.md` + `counterpoints.md` | all available | ≥3 independent sources per material claim |

### Quick mode (default)

The casual lookup path. Fires on prompts like `look up X`, `find out
about Y`, `quick check on Z`. Hard rail: ≤5 fetch operations total
across WebFetch + WebSearch combined; no MCP, no script retrievers, no
subagents. If a quick-mode answer would require more than 5 fetches,
**abort or downgrade**: tell the user "this needs `standard` mode to
answer well" and stop, rather than spending the cap on partial work.
Quick mode produces no artifact — the answer is inline in chat.

### Standard mode

Fires on explicit signals: `research with citations`, `evidence-grounded`,
`comprehensively`, `in depth`, `with sources`. Produces `research.md` in
the working directory. Every finding carries a confidence tag from the
closed set `[high]` / `[moderate]` / `[low]` / `[uncertain]`. Material
claims (those tagged `[high]` or `[moderate]`) require ≥3 independent
sources — triangulation per OSINT, GIJN, ACH, PRISMA, STORM, GRADE
convergence. Findings tagged `[low]` or `[uncertain]` name the downgrade
reason.

### Deep mode

Fires on `go deep`, `exhaustively`, `extensive research`. Same artifact
shape as standard, plus auto-invocation of `/devils-advocate` on the
produced `research.md`, producing `counterpoints.md` with proposed
rating downgrades.

## Pipeline

1. **Plan** — restate the question; enumerate sub-questions if the
   question is broad.
2. **Enumerate retrievers** — in standard/deep mode only, list the
   retrievers available in this session (see Retrievers below).
3. **Dispatch** — issue queries across retrievers; on Claude Code,
   `evidence-retriever` and `source-extractor` subagents preserve main-
   session context for the synthesis step.
4. **Synthesise** — write findings to `research.md` (standard/deep) or
   inline (quick). Cite every factual claim or mark it `[synthesis]` /
   `[inference]` per Wikipedia V/RS and GRADE convergence.
5. **Rate** — apply the confidence schema in
   `references/confidence-schema.md` to every finding.
6. **Moderator pass** — before declaring done, scan retrieved-but-
   uncited material and consider one more query from the highest-signal
   unused snippet (Co-STORM contribution). Skip in quick mode.
7. **Adversarial review (deep mode only)** — auto-invoke
   `/devils-advocate` on `research.md`; emit `counterpoints.md`.

## Retrievers

Standard and deep mode enumerate retrievers from three surfaces before
dispatching queries. Built-in retrievers are always available; MCP and
script retrievers depend on the session.

1. **Built-in** — `WebFetch` and `WebSearch`. Always available on Claude
   Code. Used for general-purpose lookups; cap of 5 in quick mode.
2. **MCP tools** — any retrieval-shaped MCP tools registered in the
   session (search engines, vector stores, internal knowledge bases).
   Use the MCP path for shared/team/multi-process access and any
   authenticated service that already has an MCP server.
3. **User-registered Python script retrievers** — files at
   `scripts/<name>-retriever.py` invoked from the main session via
   `Bash`. Subagents do not execute scripts — their tool surface
   excludes `Bash`. Use scripts for personal, lightweight, or
   already-credentialed-CLI wrappers; the env-broker shape composes
   with the credentialed-skill contract (see `metadata.auth` in
   `references/retriever-interface.md`). Two examples ship in this
   skill:
   - `scripts/arxiv-retriever.py` — unauthenticated arXiv API wrapper.
   - `scripts/perplexity-retriever.py` — env-broker Perplexity wrapper
     reading `PERPLEXITY_API_KEY`.

### Interface contract (script retrievers)

Every retriever returns a dict with three top-level keys. The schema is
codified — not prose — so a retriever response can be validated
structurally:

```json
{
  "content": "string — synthesised text or extracted passage",
  "citations": [
    {"url": "string", "title": "string", "primacy": "primary|secondary|tertiary"}
  ],
  "shape": "raw"
}
```

Valid `"shape"` values are `"raw"` (returns extracted material verbatim;
caller synthesises), `"synthesized"` (returns a model-synthesised
summary; caller cites and rates), and `"meta"` (returns retrieval
metadata only — counts, availability, capabilities — and is the only
shape permitted to return an empty `citations` array).

See `references/retriever-interface.md` for the full convention,
including how to add a new script retriever.

## Citations and confidence

Every factual claim in `research.md` carries a citation, or is marked
`[synthesis]` (a synthesis across cited material) or `[inference]` (a
defensible deduction that no single source states). Confidence per
finding follows the four-level schema in
`references/confidence-schema.md`; downgrade factors are named explicitly.

## Moderator pass (standard / deep)

Before declaring the artifact done, scan retrieved-but-uncited
material. If the highest-signal unused snippet would change a rating
or fill a gap, issue one more targeted query. This is the Co-STORM
contribution — it catches the trail you almost left on the table.

## What this skill is not

- Not a generic web-search loop. Quick mode caps fetches at 5
  precisely to refuse rabbit-holes.
- Not the rationale-reconstruction skill — that's `/decision-archaeology`,
  which is self-contained and does not invoke this skill.
- Not a perspective-enumeration skill — that's `/identify-perspectives`,
  invoked upstream in the decision pipeline.

## Methodology

The seven convergent disciplines — STORM, PRISMA, ACH, Wikipedia
V/RS/NPOV, OSINT, GIJN, GRADE — are summarised in
`references/methodologies.md`. The skill body codifies the convergent
contributions (citation-forcing, triangulation, perspective discovery,
counter-evidence, confidence rating); the reference catalogues each
discipline's distinct contribution.
