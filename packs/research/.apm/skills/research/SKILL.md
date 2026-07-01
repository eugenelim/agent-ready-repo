---
name: research
description: "Evidence-grounded research with selectable depth and discipline. Use for any look-up, find-out, fact-check, or comprehensive investigation, including prior art and best practice surveys. Carries a mode parameter (quick / standard / applied / deep) with `quick` as default — casual phrasings (`look up`, `find out`, `quick check`) stay quick; academic phrasings (`research with citations`, `evidence-grounded`, `go deep`, `comprehensively`) bias standard or deep; practitioner phrasings (`applied patterns for`, `best practice for`, `prior art on`, `grey literature`) bias applied. Quick mode is inline, ≤5 fetches, no artifact. Standard mode produces `<topic-slug>-survey.md` with GRADE-style confidence per finding from peer-reviewed and primary sources. Applied mode produces `<topic-slug>-survey.md` calibrated for practitioner grey literature with a discipline-aware confidence overlay. Deep mode additionally auto-runs `/devils-advocate`, producing `<topic-slug>-counterpoints.md`."
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
| `standard` | no | `<topic-slug>-survey.md` | academic / primary-source | all available: built-in + MCP + script retrievers + subagents | ≥3 independent sources per material claim |
| `applied` | no | `<topic-slug>-survey.md` + discipline marker | practitioner / grey-literature | all available | ≥3 independent sources per material claim; independence calibrated against practitioner taxonomy (same vendor / same employer count as one) |
| `deep` | no | `<topic-slug>-survey.md` + `<topic-slug>-counterpoints.md` | academic / primary-source | all available | ≥3 independent sources per material claim |

Artifact names follow the typed, topic-named scheme defined in
[§ Typed, topic-named artifacts](#typed-topic-named-artifacts) below; the table's
`<topic-slug>-survey.md` is the default standard/applied/deep stem.

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
cue is also present — see Cue precedence above). Produces
`<topic-slug>-survey.md` in the working directory. Every finding carries a confidence tag from
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

Produces `<topic-slug>-survey.md` in the working directory. The artifact's **first
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
produced `<topic-slug>-survey.md`, producing `<topic-slug>-counterpoints.md` with a per-finding
verdict — a confidence downgrade, or a do-not-resolve verdict for an
irreducible tension where both sides are well-evidenced under different
conditions.

Note: applied mode can be chained with `/devils-advocate` as a
follow-up invocation when the user wants adversarial review of a
practitioner-pattern survey. This is especially useful because best
practice claims are often vendor-blogged or survivorship-biased,
exactly the cases the overlay's `survivorship bias` factor exists to
catch. Invoke `/devils-advocate` against the applied-mode
`<topic-slug>-survey.md` to chain.

## Typed, topic-named artifacts

Every persisted episodic artifact is named **`<topic-slug>-<type>.md`**. The
topic-slug namespaces the investigation — two studies in one working directory
never overwrite each other — and the type stem tells a reader what the file
*is* at a glance. Quick mode is the sole exception: it stays inline, with no
file.

**Topic-slug rule.** `<topic-slug>` is a short (~2–5 word) kebab-case slug
derived from the research question — "OAuth PKCE for SPAs" → `oauth-pkce`;
"which embedded database for a CLI" → `embedded-db`. Keep it stable across a
single investigation so that study's artifacts sort together.

**Type vocabulary.** The `<type>` stem is fixed by the research mode and the
shape of the answer:

| Mode / answer shape | Artifact |
|---|---|
| quick | *inline — no file* |
| fact-check | `<topic-slug>-fact-check.md` |
| standard / applied survey | `<topic-slug>-survey.md` |
| deep | `<topic-slug>-survey.md` + `<topic-slug>-counterpoints.md` |
| comparison / decision | `<topic-slug>-comparison-matrix.md` |
| ranked candidates | `<topic-slug>-shortlist.md` |
| spatial / structural | `<topic-slug>-blueprint.md` |
| hypothesis adjudication | `<topic-slug>-hypotheses.md` |
| process / methodology / lifecycle | `<topic-slug>-methodology.md` |

`survey` is the default standard/applied/deep stem; the other stems fire when
the answer takes that shape — a `fact-check` verdict, a decision
`comparison-matrix`, a ranked `shortlist`, a structural `blueprint`, a
`hypotheses` adjudication, a process `methodology` (see
[§ The methodology shape](#the-methodology-shape) below). The scoping and rationale skills
(`/identify-perspectives`, `/build-outline`, `/source-map`,
`/decision-archaeology`) take the same `<topic-slug>-` prefix on their own
type-descriptive stems (`perspectives`, `outline`, `sources`, `archaeology`).

**Legacy alias.** `research.md` was the prior name for the survey artifact,
retained as a recognised legacy alias for one release (a forward-only
migration) so existing references and muscle memory still resolve. The skill
emits **only** the typed name — never a second `research.md` written alongside
it.

The filename is produced by the agent following this rule, never by a script
(Charter Principle 3).

## The methodology shape

A **process-shaped** question wants a *method*, not a reading list. When the ask
is *"the best way to do / run / build / train X, end to end, for my situation,"*
the answer is a **staged, contingency-adapted, maturity-aware, evidence-graded
description of how the activity is done** — the `methodology` shape — written to
`<topic-slug>-methodology.md`.

**Trigger phrasing.** Fire the methodology shape when the prompt asks for a
process or playbook, not a claim survey:

- *"the best way to do / run / build / train X"*
- *"the process / lifecycle / playbook for X"*
- *"how do you go about X end to end"*

**Depth.** The methodology shape defaults to **`applied`** depth — it is a
practitioner "how is this really done" question, so the grey-literature overlay
applies. Scholarly domains override to `standard` / `deep` via the ordinary depth
cues; the shape selects an *output topology* and does **not** touch the depth
axis, the Modes table, or Cue precedence.

**Structure — six sections, authored from the template.** Follow
[`references/methodology-shape-template.md`](references/methodology-shape-template.md),
which encodes the six sections, each grounded 1:1 in a discipline: §1 Scope frame
(SIPOC) · §2 Stage spine (process discovery + hierarchical task decomposition) ·
§3 Contingency branches (situational method engineering) · §4 Maturity ladder
(Dreyfus) · §5 Failure modes (cognitive task analysis) · §6 Evidence & confidence
(GRADE). **§3 and §4 are mandatory** — they plus the direction axis are the entire
differentiator from an `applied` survey; an artifact missing them is a survey with
headings and is incomplete.

**Slide-ready by reference to `markdown-to-pptx`.** Author sections at `H1`,
stages at `H2`, and all finer detail as bullets — **never an `H3`** — so the
artifact drops into `markdown-to-pptx` (one prompt, no reshaping). That converter
is named as the natural slide consumer **by reference only**: no import, no
`requires`, no version pin; `research` gains no dependency on `converters`, and a
repo without the converters pack still gets a good markdown artifact.

**Do NOT use the methodology shape for two neighbouring "process" jobs:**

- **`frame-domain`** (in `product-engineering`) — grounding a *product* in its
  real-world activity and bounding its **MVP** before design. That is
  product/MVP grounding, not a world-best-practice method; use `frame-domain`.
- **`map-internal-process`** (in `experience`) — documenting **your own
  organisation's** operations as an as-is/to-be swimlane. That is inside-out
  operations, not outside-in best practice; use `map-internal-process`.

**Where the boundary rests — source + direction.** The methodology shape
describes **world best-practice, outside-in, for any domain** — how the activity
is done *well, anywhere*. `map-internal-process` describes **your own operations,
inside-out** — how *this org* does it today and wants to. The **honest overlap is
real and named, not hidden**: both use a SIPOC scope frame (§1) and a
process-discovery spine (§2). The boundary therefore does *not* rest on those
shared bones — it rests on **source + direction** (best-practice/outside-in vs
own-ops/inside-out) plus the **three non-shared disciplines** the methodology
shape adds and an internal-process map does not: contingency branches (§3),
maturity ladder (§4), and failure modes (§5).

**The `frame-domain`-wraps-`research` fence.** `frame-domain` internally invokes
`research` in `applied` mode to ground its real-world-activity half (its
*Wrapping research applied mode* section). The **methodology shape does not fire
on that wrapped call** — a `research` invocation issued *by* `frame-domain` stays
an ordinary `applied` survey, which `frame-domain` then shapes into its Domain
Framing artifact. Reshaping that grounding pass into a methodology artifact would
silently break `frame-domain`; the shape fires only on a *direct*
process-shaped user request, never on `frame-domain`'s wrapped grounding call.

## Pipeline

1. **Plan** — restate the question; enumerate sub-questions if the
   question is broad.
2. **Enumerate retrievers** — in standard/deep mode only, list the
   retrievers available in this session (see Retrievers below).
3. **Dispatch** — issue queries across retrievers; on Claude Code,
   `evidence-retriever` and `source-extractor` subagents preserve main-
   session context for the synthesis step.
4. **Synthesise** — write findings to `<topic-slug>-survey.md` (standard/deep)
   or inline (quick). Cite every factual claim or mark it `[synthesis]` /
   `[inference]` per Wikipedia V/RS and GRADE convergence.
5. **Rate** — apply the confidence schema in
   `references/confidence-schema.md` to every finding.
6. **Name the gaps** — before the moderator pass, write the
   known-unknowns / unknowables section (see *Known unknowns and
   unknowables* below). Skip in quick mode. This is a standing step, not
   an optional flourish: a synthesis with no gap section is asserting it
   answered everything the question raised, which is almost never true.
7. **Moderator pass** — before declaring done, scan retrieved-but-
   uncited material and consider one more query from the highest-signal
   unused snippet (Co-STORM contribution). Skip in quick mode.
8. **Adversarial review (deep mode only)** — auto-invoke
   `/devils-advocate` on `<topic-slug>-survey.md`; emit
   `<topic-slug>-counterpoints.md`.

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

Every factual claim in `<topic-slug>-survey.md` carries a citation, or is marked
`[synthesis]` (a synthesis across cited material) or `[inference]` (a
defensible deduction that no single source states). Confidence per
finding follows the four-level schema in
`references/confidence-schema.md`; downgrade factors are named explicitly.

## Known unknowns and unknowables (standard / applied / deep)

A confidence rating answers *"how much should you trust this finding?"*
It is a tag on a claim the research **did** make. It says nothing about
the questions the research **could not answer at all** — and quietly
omitting those, or dressing one up as a thin `[uncertain]` finding, is
the most common way a synthesis overstates how complete it is.

So every non-quick artifact carries a first-class gap section. It is
**not** a rating — there is no finding to rate, because the evidence to
support one does not exist. Rating a non-finding `[uncertain]` is a
category error: `[uncertain]` means *"we have a claim, but weak grounds
for it"*; a gap means *"we have no claim, because the evidence isn't
there."* Keep the two apart — a weak finding stays in **Findings** with
an `[uncertain]` tag; a gap goes here.

Split each gap into one of two kinds:

- **Known-unknown** — answerable *in principle*; the evidence exists or
  could be produced, you just don't have it in hand. (The benchmark
  hasn't been run on this workload; the vendor hasn't published the
  number; the primary source is paywalled.) A known-unknown names what
  evidence *would* close it — it is a research lead, not a dead end.
- **Unknowable** — not answerable from available evidence *even in
  principle*, at least as the question is posed. The data was never
  recorded; the counterfactual can't be run; the outcome is in the
  future; the question is contested in a way no evidence settles (in
  which case it belongs in a tension, not a finding — see
  `/identify-perspectives` and `/devils-advocate`'s do-not-resolve
  verdict). An unknowable names *why* the evidence can't exist, so a
  reader stops hunting for it.

The discipline is the same one GRADE encodes for ratings: make the
limit explicit and named, rather than letting silence imply completeness.

### `## Known unknowns` artifact section

```markdown
## Known unknowns

- **Known-unknown:** <question a complete answer needs>. Would be closed
  by: <the evidence that would answer it — a benchmark, a primary
  source, a disclosure>.
- **Unknowable:** <question that can't be answered from available
  evidence>. Why not: <the data was never recorded / the outcome hasn't
  happened / no evidence settles it>.
```

Depth cues scale this section the same way they scale findings: a
`briefly` artifact names only the load-bearing gaps; a `comprehensively`
one chases the second-order ones too.

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
