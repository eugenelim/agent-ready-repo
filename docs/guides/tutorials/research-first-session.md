# Your first research session

In about fifteen minutes you'll install the `research` pack at user
scope, run `/research` in all three modes against a real question, and
see the artifact signature that distinguishes them. By the end you'll
know which mode to reach for and what each one leaves behind on disk.

This is a tutorial — it leads. For the dry catalogue of every flag and
field, see the [research pack reference](../reference/research-pack.md).
For *why* the pack is shaped the way it is — seven convergent
methodologies, mode-on-research, retrieval-only subagents — see [the
research methodology explanation](../explanation/research-methodology.md).

## Prerequisites

- `agentbundle` on `$PATH` (the [install-agentbundle-from-clone](../how-to/install-agentbundle-from-clone.md)
  guide walks the one-time setup).
- A project directory you can `cd` into — any project. The pack is
  user-scope, so it works from any repo you open.

## Step 1 — install at user scope

```bash
agentbundle install research --scope user
```

The pack lands in `~/.claude/skills/` and `~/.claude/agents/`. Every
project you open from now on can invoke `/research`, `/source-map`,
and the other five skills.

You should see seven skills under `~/.claude/skills/`:

```
~/.claude/skills/identify-perspectives/
~/.claude/skills/build-outline/
~/.claude/skills/source-map/
~/.claude/skills/research/
~/.claude/skills/devils-advocate/
~/.claude/skills/compare-hypotheses/
~/.claude/skills/decision-archaeology/
```

and two retrieval subagents under `~/.claude/agents/`:

```
~/.claude/agents/evidence-retriever.md
~/.claude/agents/source-extractor.md
```

## Step 2 — quick mode

Quick mode is the default. Casual phrasings stay quick — `look up`,
`find out`, `quick check`. Try it.

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

Check your working directory — `ls`. There's **no `research.md`**.
That's the quick-mode signature: an inline answer, no artifact.

Quick mode is capped at five fetches across `WebFetch` and `WebSearch`.
If a question would need more, the skill aborts and tells you to escalate.

## Step 3 — standard mode

Standard mode produces a citable artifact. The trigger is an explicit
signal — `with citations`, `evidence-grounded`, `comprehensively`.

Try:

```
research with citations: what are the established frameworks for
grading evidence quality in clinical guidelines
```

The session takes longer. The skill dispatches WebSearch, follows the
most promising URLs with WebFetch, and on Claude Code may dispatch the
`evidence-retriever` subagent to preserve context.

When done, you'll see `research.md` in your working directory. Open it:

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

Every finding ends with a confidence tag from the closed set —
`[high]` / `[moderate]` / `[low]` / `[uncertain]`. Downgrade factors
are named explicitly. That's the standard-mode signature: an artifact
with cited, rated findings.

## Step 4 — deep mode

Deep mode is standard plus an adversarial review pass. The trigger is
`go deep`, `exhaustively`, `extensive`.

Try:

```
go deep on this: do vector databases outperform traditional databases
for similarity search at scale
```

This run takes the longest. After `research.md` is written, the skill
auto-invokes `/devils-advocate` against it. When done, you'll see
**two** artifacts:

```
research.md
counterpoints.md
```

`counterpoints.md` walks each finding in `research.md`, names the
strongest counter-position, cites counter-evidence, and proposes
confidence-rating downgrades. Open it:

```markdown
# Counterpoints — research.md

## Finding: vector databases outperform traditional databases for
similarity search at scale.

- **Counter-position:** PostgreSQL + pgvector is within 15% on the
  cited workload class; "at scale" is contested.
- **Counter-evidence:** [peer-reviewed benchmark paper], [SIGMOD
  discussion].
- **Proposed rating change:** `[high]` → `[moderate]`. Reason:
  `contested-in-field`.
```

That's the deep-mode signature: two artifacts, the second arguing
against the first.

## Step 5 — see the signature

The three modes leave three distinct on-disk signatures:

| Mode | Artifact in working directory |
|---|---|
| `quick` | none — inline answer in chat |
| `standard` | `research.md` |
| `deep` | `research.md` + `counterpoints.md` |

That signature is the work-loop verification gate — quick mode is
*observably* quick because no file was written.

## Where to go next

- The [how-to guide on research pipelines](../how-to/research-pipelines.md)
  shows the three multi-skill recipes (survey, decision, archaeology).
- The [reference](../reference/research-pack.md) catalogues every skill,
  subagent, mode, and depth cue.
- The [explanation](../explanation/research-methodology.md) covers the
  seven methodologies and the design choices that shaped the pack.

## Manual-QA timing note

This tutorial is designed to land in fifteen minutes for an adopter
who already has `agentbundle` installed. Authors of the implementing
PR should append a timing note (e.g., "ran end-to-end in 13m on a
fresh shell against an installed CLI") to the PR description as
verification that the ≤15-minute target was met.
