---
name: research
description: "Evidence-grounded research with selectable depth and discipline. Use for any look-up, find-out, fact-check, or comprehensive investigation, including prior art and best practice surveys. Carries a mode parameter (quick / standard / applied / deep) with `quick` as default — casual phrasings (`look up`, `find out`, `quick check`) stay quick; academic phrasings (`research with citations`, `evidence-grounded`, `go deep`, `comprehensively`) bias standard or deep; practitioner phrasings (`applied patterns for`, `best practice for`, `prior art on`, `grey literature`) bias applied. Quick mode is inline, ≤5 fetches, no artifact. Standard mode produces `research.md` with GRADE-style confidence per finding from peer-reviewed and primary sources. Applied mode produces `research.md` calibrated for practitioner grey literature with a discipline-aware confidence overlay. Deep mode additionally auto-runs `/devils-advocate`, producing `counterpoints.md`."
---

# /research

The research lifecycle's anchor. Selects one of four modes based on the
prompt's depth and discipline signals, dispatches retrievers, synthesises
findings with citations and per-finding confidence ratings, and (in deep
mode) adversarially reviews its own output.

## When to invoke

Any prompt that asks the model to find out, look up, investigate,
fact-check, survey prior art, or synthesise external information. The
mode is selected from the prompt's wording, not asked of the user.

## Modes

Mode parameter: `mode: quick | standard | applied | deep`. Default: `quick`.

| Mode | Default? | Artifact? | Discipline | Retrievers | Triangulation |
|---|---|---|---|---|---|
| `quick` | yes | no — inline answer | n/a | built-in WebFetch + WebSearch only; ≤5 fetches | not required |
| `standard` | no | `research.md` | academic / primary-source | all available: built-in + MCP + script retrievers + subagents | ≥3 independent sources per material claim |
| `applied` | no | `research.md` + discipline marker | practitioner / grey-literature | all available | ≥3 independent sources per material claim; independence calibrated against practitioner taxonomy (same vendor / same employer count as one) |
| `deep` | no | `research.md` + `counterpoints.md` | academic / primary-source | all available | ≥3 independent sources per material claim |

### Cue precedence

When a prompt contains cues for more than one mode, **applied cues are
scored before standard / deep cues**. A prompt containing any applied
cue from the closed set below dispatches `applied`, even when standard
or deep cues co-occur. This closes the obvious collision case —
*"comprehensively survey the applied patterns for X"* contains both
`comprehensively` (a standard cue) and `applied patterns for` (an
applied cue); precedence puts it in applied mode. The closed cue
tuples below are single-sourced from the conformance tests under
`packages/agentbundle/tests/unit/test_research_retrievers_conformance.py`.

### Quick mode (default)

The casual lookup path. Fires on prompts like `look up X`, `find out
about Y`, `quick check on Z`. Hard rail: ≤5 fetch operations total
across WebFetch + WebSearch combined; no MCP, no script retrievers, no
subagents. If a quick-mode answer would require more than 5 fetches,
**abort or downgrade**: tell the user "this needs `standard` or
`applied` mode to answer well" and stop, rather than spending the cap
on partial work. Quick mode produces no artifact — the answer is
inline in chat.

### Standard mode

Fires on explicit academic-discipline signals: `research with citations`,
`evidence-grounded`, `comprehensively`, `go deep` (when no applied
cue is also present — see Cue precedence above). Produces `research.md`
in the working directory. Every finding carries a confidence tag from
the closed set `[high]` / `[moderate]` / `[low]` / `[uncertain]`.
Material claims (those tagged `[high]` or `[moderate]`) require ≥3
independent sources — triangulation per OSINT, GIJN, ACH, PRISMA,
STORM, GRADE convergence. Findings tagged `[low]` or `[uncertain]` name
the downgrade reason. Confidence schema is the base GRADE set in
`references/confidence-schema.md`.

### Applied mode

Fires on explicit practitioner-discipline signals from the closed set
`applied patterns for`, `best practice for`, `prior art on`,
`grey literature`. Designed for **prior art** and **best practice**
surveys across the failure-mode shapes too — **case studies** and
**anti-patterns** — covering the practitioner / grey-literature surface
where the academic GRADE schema's `no peer review` downgrade factor
would otherwise poison every finding to `[low]` by construction.

**The four discipline frames** applied mode serves:

- **prior art** — what's been done before in this area; who's done it;
  what worked or failed in production.
- **best practice** — what the community currently considers the right
  approach (acknowledging that "current" decays — see the recency rule
  below).
- **case studies** — specific worked examples, post-mortems, retros;
  named adopters and their outcomes.
- **anti-patterns** — what to avoid; known failure modes; the inverse
  of best practice. The `survivorship bias` overlay factor in
  `references/confidence-schema.md` is exactly the discipline that
  surfaces these (only the successes blog; the failures rarely do).

Produces `research.md` in the working directory. The artifact's **first
non-heading line is the canonical discipline marker, byte-for-byte
literal**:

```
> Discipline: applied (practitioner-pattern survey)
```

No bold, no em-dash variant, no synonym substitution. The marker is
an audit signal recording that applied mode fired; it is NOT the
rule-set selector (the `mode` parameter is — see
`references/confidence-schema.md` § Applied-mode overlay).

**Practitioner-independence rule.** Triangulation requires ≥3 sources
per material claim, but in the practitioner surface independence is
calibrated against the taxonomy: three sources from the same vendor
count as one; three sources in the same employer cohort count as one;
three retweets / re-blogs of the same original post count as one. The
rule refuses the "Hacker News cargo cult" failure mode where ten
secondary mentions of one primary post look like ten independent
data points.

**Recency rule.** A pattern from >5 years ago in a fast-moving domain
(LLM tooling, frontend frameworks, observability stacks) is suspect
under the `stale prior art` downgrade factor; cite the pattern, then
flag that it predates the current generation of tools. Slower-moving
domains (compiler theory, database fundamentals) carry no such
penalty.

Confidence schema is the base GRADE set **plus the Applied-mode
overlay** in `references/confidence-schema.md` — drops `no peer review`
for practitioner domains; adds `survivorship bias` and `stale prior
art` to the closed downgrade-factor set.

### Deep mode

Fires on `go deep`, `exhaustively`, `extensive research` (when no
applied cue is also present — see Cue precedence above). Same artifact
shape as standard, plus auto-invocation of `/devils-advocate` on the
produced `research.md`, producing `counterpoints.md` with proposed
rating downgrades.

Note: applied mode can be chained with `/devils-advocate` as a
follow-up invocation when the user wants adversarial review of a
practitioner-pattern survey. This is especially useful because best
practice claims are often vendor-blogged or survivorship-biased,
exactly the cases the overlay's `survivorship bias` factor exists to
catch. Invoke `/devils-advocate` against the applied-mode `research.md`
to chain.

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
