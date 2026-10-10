# Wicked Estate code intelligence

Agents guess about code they have not read. This pack replaces the guess with a
query.

[Wicked Estate](https://github.com/mikeparcewski/wicked-estate) indexes a
repository into a queryable graph of symbols and the relationships between
them. This pack teaches a coding agent how to use that index well — which
question maps to which command, when to stop digging, and how to report what
the index could not resolve instead of quietly rounding it up to a clean answer.

## The boundary

Three layers, and keeping them apart is the whole design.

| Layer | Answers |
| --- | --- |
| Wicked Estate | *What is true about this software estate?* |
| This pack | *How should an agent use that intelligence effectively?* |
| Your workflow skills | *What are we trying to accomplish with it?* |

So a blast radius lives here. A migration phase does not. The test, when you are
unsure where something belongs:

> Does this describe the **software estate**, or a **job being performed on** the
> software?

Entities, relationships, source, dependency structure, lineage, blast radius,
rules, hotspots, communities, provenance, and confidence describe the estate.

Migration phase, cutover readiness, bug triage status, release approval, review
gates, modernization wave, and plan state describe a job. They belong to the
pack that owns that job.

The payoff is composability. A migration pack, a debugging pack, and a security
pack can all consume `code-intelligence` without knowing about each other, and
Wicked Estate never learns that any of them exist.

## What you get

- **`code-intelligence`** — the skill. Five reusable investigation patterns
  (understand an entity, analyze change impact, investigate behavior, analyze
  architecture, assemble task context), a capability map from tool-neutral
  intent to the exact command, and the evidence discipline that keeps a
  heuristic edge from being reported as a fact.
- **`code-investigator`** — a forked-context subagent for evidence-driven
  investigation. Returns findings labelled observed, verified, or unestablished.
- **`impact-analyst`** — a forked-context subagent for structured change-impact
  analysis. Leads with its own completeness limits.

## Composition example

Before changing the signature of `parse_config`, which call sites must change, and which could not be established?
[`.apm/skills/code-intelligence/references/composition-example.md`](.apm/skills/code-intelligence/references/composition-example.md)
walks that question through two paths: the provider-fit path using an indexed
call graph, and the fallback path using repository-native search — the agent's
own text search and file-reading tools — when the provider is absent or the
index is stale. It closes with a section that
separates the baseline rules that hold with any provider from the details
specific to Wicked Estate.

The example is illustrative, not a contract. Other providers may expose fewer,
different, or new capabilities and need not emulate Wicked Estate. The current
investigation patterns may change as the pack evolves.

## Getting started

You need the CLI and an index.

```bash
cargo install wicked-estate --version 0.21.0 --locked
echo '.wicked-estate/' >> .gitignore   # the index is large and local
wicked-estate index .
```

Then ask an ordinary question:

> What breaks if I change the request handler?

The skill resolves the symbol, computes the blast radius, ranks the dependents,
reads the ones that matter, and tells you how many call sites the indexer could
not bind.

To check your setup at any point:

```bash
python '<skill-dir>/scripts/estate_preflight.py' --check
```

`<skill-dir>` is the installed `code-intelligence` skill folder, for example
`.claude/skills/code-intelligence` at repo scope or
`~/.claude/skills/code-intelligence` at user scope.

Exit 0 is ready, 2 means the binary is missing, 3 means there is no index, and
4 means the binary is older than the 0.21 floor this pack was verified against.

## CLI, not MCP, by default

Wicked Estate ships both a CLI and an MCP server. This pack drives the CLI, for
two reasons.

The MCP server advertises **30 tool schemas**, and they stay resident in the
agent's context for the entire session whether or not a single one is called.
The CLI costs nothing until you run it.

The CLI is also the larger surface. It accepts 40 names, including several with
no MCP equivalent: requirement linkage (`by-requirement`, `semantics`), snapshot
identity (`fingerprint`, `changed-since`, `stats`), the annotation evidence
envelope (`annotations`, `stale-annotations`), and `entrypoints`, `leaves`,
`dead-code`, `correspond`, and `drift`.

The memory, knowledge, and proposal domains have **no CLI verb** and are
reachable only over MCP. The richer MCP response shapes — per-dependent `depth`
and `summary.top_by_pagerank` on `BlastRadius`, `Communities` summaries,
`ContextBundle` — are also MCP-only. For those, register the server, preferably
read-only:

```bash
claude mcp add wicked-estate -s project -- \
  wicked-estate-mcp --readonly --db "$PWD/.wicked-estate/graph.db"
```

The capability map marks every row with which surface serves it, so the skill
never implies coverage that is not there.

## Honest about limits

The pack ships a gap analysis rather than a feature list. Fourteen points of a
general code-intelligence contract are assessed against what Wicked Estate
actually exposes today, each classified as available directly, available by
composition, partially available, not available today, or unclear.

Some of what that found:

- **Ranking a dependent set is a composition.** `rank --seeds` biases a
  graph-wide ranking; keep only the rows in your set. The row list is capped at
  25K characters, so report members absent from the output as unranked.
- **Per-edge confidence and provenance are not in blast-radius rows**, although
  every edge carries them. The `confidence` object in `blast-radius --json` covers
  the full traversal, not individual rows. Use `wicked-estate path A B --json`
  when you need per-hop confidence and provenance on a specific route.
- **The memory, knowledge, and proposal domains are MCP-only.** Forward transitive
  reachability (`lineage`), rules inventory, and rules recall have CLI verbs;
  the memory, knowledge, and proposal domains do not.

None of these are requests to change Wicked Estate, and nothing in this pack
depends on them changing. They are the map of where an agent must stop and say
so.

## Degrading without the index

If the binary or graph is absent, the skill may fall back to ordinary
repository search — and must label it as such. Blast radius, lineage,
provenance, confidence, and completeness counts are properties of an index.
Without one you do not have them, and a list of candidate callers assembled
from `grep` is not a blast radius.

## Requires

- `wicked-estate` ≥ 0.21 in `PATH` (Tier-2 dependency: detected first, installed
  only on explicit consent, pinned, never with sudo)
- An index built with `wicked-estate index <path>`
- Optionally `wicked-estate-mcp` ≥ 0.21, for the memory, knowledge, and proposal
  domains and richer MCP response shapes

The pack installs at repo or user scope and needs no other pack.

## Works with

The `core` pack is optional. When it is installed, its exploration skill can use
this pack as a provider of code-graph evidence.

Read-only by default. The commands that mutate the graph — `index`, `annotate`,
`semantics`, `compact`, and friends — always ask first.
