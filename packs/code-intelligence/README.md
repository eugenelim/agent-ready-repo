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

## Getting started

You need the CLI and an index.

```bash
cargo install wicked-estate --version 0.16.7 --locked
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
python scripts/estate_preflight.py --check
```

Exit 0 is ready, 2 means the binary is missing, 3 means there is no index, and
4 means the binary is older than the 0.16 floor this pack was verified against.

## CLI, not MCP, by default

Wicked Estate ships both a CLI and an MCP server. This pack drives the CLI, for
two reasons.

The MCP server advertises **29 tool schemas**, and they stay resident in the
agent's context for the entire session whether or not a single one is called.
The CLI costs nothing until you run it.

The CLI is also the larger surface. It accepts 34 subcommand names, including
several with no MCP equivalent: requirement linkage (`by-requirement`,
`semantics`), snapshot identity (`fingerprint`, `changed-since`, `stats`), the
annotation evidence envelope (`annotations`, `stale-annotations`), and
`entrypoints`, `leaves`, `dead-code`, `correspond`, and `drift`.

Four capabilities go the other way and have **no CLI verb at all** — `Lineage`,
`RulesInventory`, `rules.recall`, and the memory and knowledge domains. For
those, register the server, preferably read-only:

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

- **There is no path query.** You can establish that A reaches B. You cannot ask
  for the route.
- **The CLI blast radius has a silent depth-12 horizon**, reported by neither
  completeness field.
- **Nothing ranks a supplied set of symbols on the CLI** — `rank` is a fixed
  global top-25, so "which of these 47 dependents matter most" has no CLI answer.
- **Per-edge confidence and provenance are not printed on the CLI read paths**,
  even though every edge carries them. MCP `BlastRadius` does surface them.

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

- `core` ≥ 2.0
- `wicked-estate` ≥ 0.16 in `PATH` (Tier-2 dependency: detected first, installed
  only on explicit consent, pinned, never with sudo)
- An index built with `wicked-estate index <path>`
- Optionally `wicked-estate-mcp` ≥ 0.16, for the four MCP-only capabilities

Read-only by default. The commands that mutate the graph — `index`, `annotate`,
`semantics`, `compact`, and friends — always ask first.
