# Your first research session

In about twenty minutes you'll install the `desk-research` pack at user scope, run `/desk-research` in all four modes against real questions, and see the artifact signature that distinguishes them. By the end you'll know which mode to reach for and what each one leaves behind on disk.

This is a tutorial — it leads. For the dry catalogue of every flag and field, see the [desk-research pack reference](../reference/desk-research-pack.md). For *why* the pack is shaped the way it is — seven convergent methodologies, mode-on-research, retrieval-only subagents — see [the research methodology explanation](../explanation/desk-research-methodology.md).

## Prerequisites

- `agentbundle` on `$PATH` (the [install-agentbundle-from-clone](../../_shared/how-to/install-agentbundle-from-clone.md) guide walks the one-time setup).
- A project directory you can `cd` into — any project. The pack is user-scope, so it works from any repo you open.

## Step 1 — install at user scope

```bash
agentbundle install research --scope user
```

The pack lands in `~/.claude/skills/` and `~/.claude/agents/`. Every project you open from now on can invoke `/desk-research`, `/source-map`, and the other five skills.

You should see seven skills under `~/.claude/skills/`:

```
~/.claude/skills/identify-perspectives/
~/.claude/skills/build-outline/
~/.claude/skills/source-map/
~/.claude/skills/desk-research/
~/.claude/skills/devils-advocate/
~/.claude/skills/compare-hypotheses/
~/.claude/skills/decision-archaeology/
```

and two retrieval subagents under `~/.claude/agents/`:

```
~/.claude/agents/evidence-retriever.md
~/.claude/agents/source-extractor.md
```

## Step 2 — quick mode (default)

Quick mode is the default. Casual phrasings stay quick — `look up`, `find out`, `quick check`. Try it.

In your Claude Code session, type:

```
look up what PRISMA stands for
```

You'll see something like:

```
PRISMA stands for Preferred Reporting Items for Systematic Reviews and
Meta-Analyses — the standard for reporting systematic reviews in clinical
research, codified in 2009 and updated in 2020.
```

Check your working directory — `ls`. There's **no artifact** — nothing matching `*-survey.md` or any other typed name. That's the quick-mode signature: an inline answer, no file.

Quick mode is capped at five fetches across `WebFetch` and `WebSearch`. If a question would need more, the skill aborts and tells you to escalate.

## Step 3 — standard mode

Standard mode produces a citable artifact. The trigger is an explicit signal — `with citations`, `evidence-grounded`, `comprehensively`.

Try:

```
research with citations: what are the established frameworks for
grading evidence quality in clinical guidelines
```

The session takes longer. The skill dispatches WebSearch, follows the most promising URLs with WebFetch, and on Claude Code may dispatch the `evidence-retriever` subagent to preserve context.

When done, you'll see `evidence-grading-survey.md` in your working directory — the topic slug (`evidence-grading`) plus the type stem (`survey`). That's the `<topic-slug>-<type>.md` naming rule (the same one the signatures table below shows as a placeholder) applied to this question. Open it:

```markdown
# Research — frameworks for grading evidence quality

## Findings

- GRADE (Grading of Recommendations Assessment, Development and
  Evaluation) is the dominant framework, adopted by the WHO, Cochrane,
  and most clinical practice guideline developers since 2004. [high]
- Oxford CEBM Levels of Evidence remains in use, particularly in
  surgical and diagnostic literature. [moderate]
  Downgrade: heterogeneity (specialty-specific usage varies).
- ...

## Sources

1. [GRADE Working Group — gradeworkinggroup.org] (primary)
2. [Oxford CEBM Levels of Evidence — cebm.ox.ac.uk] (primary)
3. ...
```

Every finding ends with a confidence tag from the closed set — `[high]` / `[moderate]` / `[low]` / `[uncertain]`. Downgrade factors are named explicitly. That's the standard-mode signature: an artifact with cited, rated findings.

## Step 4 — applied mode

Applied mode is for prior-art and best-practice surveys across practitioner grey literature (blogs, conference talks, vendor case studies, community threads) — the kind of research where standard mode's `no peer review` downgrade factor would otherwise mis-rate every finding to `[low]` because the domain has no peer-reviewed alternative by construction. The trigger is one of four phrase-shaped cues: `applied patterns for`, `best practice for`, `prior art on`, `grey literature`.

Try:

```
applied patterns for inventory optimisation in last-mile shipping
```

The skill takes a while — it dispatches WebSearch + WebFetch across practitioner sources (vendor case studies, logistics blogs, conference talks, supply-chain community threads). When done, open `last-mile-inventory-survey.md`. The **first non-heading line** is the canonical discipline marker, byte-for-byte:

```markdown
> Discipline: applied (practitioner-pattern survey)

# Applied patterns for inventory optimisation in last-mile shipping

## Findings

- Finding: hub-and-spoke micro-fulfilment cuts last-mile cost per
  parcel by 20-30% in dense urban areas with ≥10 daily orders per
  square kilometre. [moderate]
  Downgrade: survivorship bias (cited adopters are success stories;
  no failed-adopter post-mortems surfaced).
- ...
```

That's the applied-mode signature. Two structural differences from standard mode: the discipline marker on line 1, and the confidence schema swaps in `survivorship bias` and `stale prior art` as new downgrade factors (and drops `no peer review`, which doesn't apply when no peer review exists in the domain).

When in doubt about which mode to reach for — academic standard or practitioner applied — the heuristic is the source taxonomy you're expecting. Peer-reviewed papers and primary specs → standard. Practitioner blogs, conference talks, case studies → applied.

## Step 5 — deep mode

Deep mode is standard plus an adversarial review pass. The trigger is `go deep`, `exhaustively`, `extensive`.

Try:

```
go deep on this: do vector databases outperform traditional databases
for similarity search at scale
```

This run takes the longest. After `vector-db-search-survey.md` is written, the skill auto-invokes `/devils-advocate` against it. When done, you'll see **two** artifacts — both carrying the same topic slug:

```
vector-db-search-survey.md
vector-db-search-counterpoints.md
```

`vector-db-search-counterpoints.md` walks each finding in `vector-db-search-survey.md`, names the strongest counter-position, cites counter-evidence, and routes each to a verdict — either a confidence-rating downgrade, or a *do-not-resolve* verdict when both sides are well-evidenced under different conditions and more evidence would not collapse the disagreement to one answer. Open it:

```markdown
# Counterpoints — vector-db-search-survey.md

## Finding: vector databases outperform traditional databases for
similarity search at scale.

- **Counter-position:** PostgreSQL + pgvector is within 15% on the
  cited workload class; "at scale" is contested.
- **Counter-evidence:** [peer-reviewed benchmark paper], [SIGMOD
  discussion].
- **Verdict:** rating downgrade — `[high]` → `[moderate]`. Reason:
  `contested-in-field`.

## Finding: a monorepo is the right default for multi-team codebases.

- **Counter-position:** polyrepo wins for independently-deployed teams
  with strong service boundaries; both are well-evidenced.
- **Counter-evidence:** [large-scale monorepo case study], [polyrepo
  migration retrospective].
- **Verdict:** do-not-resolve. Monorepo holds when tooling and release
  cadence are shared; polyrepo holds when teams deploy independently.
  More evidence would not collapse this to one answer.
```

That's the deep-mode signature: two artifacts, the second arguing against the first.

## Step 6 — see the signatures

The four modes leave four distinct on-disk signatures:

| Mode | Artifact in working directory | Distinguishing signal |
|---|---|---|
| `quick` | none — inline answer in chat | absence of any of the seven enumerated artifacts |
| `standard` | `<topic-slug>-survey.md` | a `*-survey.md` present, no discipline marker on line 1 |
| `applied` | `<topic-slug>-survey.md` | a `*-survey.md` present, canonical discipline marker as first non-heading line |
| `deep` | `<topic-slug>-survey.md` + `<topic-slug>-counterpoints.md` | second artifact present |

That signature is the work-loop verification gate — each mode is *observably* itself by what is or isn't on disk and what's on line 1.

## Where to go next

- The [how-to guide on research pipelines](../how-to/desk-research-pipelines.md) shows the three multi-skill recipes (survey, decision, archaeology).
- Got a question that outlasts one sitting? [Your first research project](your-first-research-project.md) walks the project lifecycle, and [episodic vs project research](../explanation/episodic-vs-project-research.md) explains when to reach for it instead of a one-off run.
- The [reference](../reference/desk-research-pack.md) catalogues every skill, subagent, mode, and depth cue.
- The [explanation](../explanation/desk-research-methodology.md) covers the seven methodologies and the design choices that shaped the pack.

## Manual-QA timing note

This tutorial is designed to land in twenty minutes for an adopter who already has `agentbundle` installed (four modes at roughly five minutes each; extended from the original three-mode ≤15-minute target by the applied-mode amendment). Authors of the implementing PR should append a timing note (e.g., "ran end-to-end in 18m on a fresh shell against an installed CLI") to the PR description as verification that the ≤20-minute target was met.
