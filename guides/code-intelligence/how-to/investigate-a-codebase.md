---
title: Investigate a codebase
summary: Pick the right investigation pattern for the question — understand an entity, analyze change impact, investigate behavior, analyze architecture, or assemble task context — and know when to stop.
pack: code-intelligence
kind: how-to
---

# Investigate a codebase

**Use this when:** you have a question about what is true in a codebase and want
the agent to gather evidence deliberately rather than wander the graph.

**Before you start:** the repository must be indexed. See
[Your first session](../tutorials/first-session.md).

## Choose the pattern from the question

You do not need to name the pattern — the skill selects it — but knowing which
one is running tells you what to expect back.

| You ask | Pattern | It ends when |
| --- | --- | --- |
| "What is X and how does it work?" | Understand an entity | The agent can state X's job, inputs, and callers |
| "What breaks if I change X?" | Analyze change impact | Direct and transitive impact are separated and the important paths read |
| "Why does X do Y?" | Investigate behavior | Evidence explains it, or the unexplained link is named |
| "How is this organised?" | Analyze architecture | Structure is described and interpretation labelled as such |
| "What do I need to read for X?" | Assemble task context | The bundle is bounded and every item has a reason |

## The habit underneath all five

1. **Resolve before reading.** Names are not unique. Two matches is a finding,
   not an inconvenience — expect to be asked which you meant.
2. **Read source before concluding.** A graph edge says a call exists; only the
   source says what it does.
3. **Expand one hop at a time.** Pulling a large subgraph and reasoning over
   unread code produces confident wrong answers.
4. **Stop when the question is answered**, not when the graph is exhausted.

## Ask for the limits when they matter

The index reports its own incompleteness and a good answer passes that on. If
you get a bare list, ask:

> How complete is that?

Four things should come back: unresolved references, whether output was
truncated, whether the depth horizon was reached (`depth_horizon_reached`), and
which revision the index describes. When `depth_horizon_reached` is true, use
`blast-radius <name> --depth N` (max 24) to look further.

## When architecture is the question

Watch for the answer separating two things:

> **Observed:** cluster 3 holds 41 symbols across `billing/` and `invoicing/`.
>
> **Interpretation:** those two directories are probably one domain split by
> folder rather than responsibility.

The first is what the graph reported. The second may be wrong. An answer that
merges them is doing something you cannot check.

## When the index is absent

The skill falls back to ordinary repository search and must say so. What it
must never do is present that fallback as a blast radius, lineage, or
provenance — those are properties of an index, and text search does not have
them. If you see those words without an index, something has gone wrong.

## A worked example

The pack ships a composition example that walks one question — before changing
the signature of `parse_config`, which call sites must change, and which could
not be established? — through two paths.

The **provider-fit path** shows the preflight check, a freshness check, the
direct-dependents query, source verification of the load-bearing call sites, and
the stopping point.

The **fallback path** shows what to do when the binary is absent, the index has
not been built, the binary is older than the supported floor, or the index is
stale for the file being changed. It labels text search and source reading as a
different evidence class from an indexed call graph and names what they cannot
establish.

The example is illustrative, not a contract. Other providers may expose fewer,
different, or new capabilities and need not emulate Wicked Estate. The current
investigation patterns may change.

## What this will not give you

- **A deletion list.** `dead-code` returns symbols with no edges, which on one
  real repository was 65% of all nodes — reflection and framework registration
  look identical to genuinely dead code.
- **Ranked dependents on the CLI.** `rank` is a global top-25 with no seed and
  no input set, so the CLI cannot tell you which of your 47 dependents matter most.
- **A recommendation.** The pack reports what is true. What to do about it
  belongs to whichever workflow asked.
