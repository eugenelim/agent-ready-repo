---
title: "`code-intelligence` — guides"
summary: Query an indexed code graph to answer what calls this, what a change breaks, and how an unfamiliar system is organised — with the index's own limits carried into the answer.
pack: code-intelligence
kind: explanation
---

# `code-intelligence` — guides

Agents guess about code they have not read. This pack replaces the guess with a
query.

[Wicked Estate](https://github.com/mikeparcewski/wicked-estate) indexes a
repository into a graph of symbols and the relationships between them. This pack
teaches an agent to use that index well: which question maps to which command,
when to stop digging, and how to report what the index could not resolve rather
than rounding it up to a clean answer.

## The boundary

Three layers, and keeping them apart is the design.

| Layer | Answers |
| --- | --- |
| Wicked Estate | *What is true about this software estate?* |
| This pack | *How should an agent use that intelligence effectively?* |
| Your workflow packs | *What are we trying to accomplish with it?* |

A blast radius belongs here. A migration phase does not. When placement is
unclear, the test is: **does this describe the software estate, or a job being
performed on the software?**

The payoff is composability. A migration pack, a debugging pack and a security
pack can all consume this one without knowing about each other, and Wicked
Estate never learns any of them exist.

## What it is honest about

The pack ships a fourteen-point assessment of what the provider does and does
not expose, and the answer is not "everything". There is no path query — you can
establish that A reaches B, not the route. The command-line blast radius carries
no depth, so direct and transitive impact cannot be separated from it alone. Its
traversal stops at twelve hops and does not say so.

Those are recorded rather than papered over, because an agent that knows where
the map ends is more useful than one that does not.

## Two provider surfaces, two maturities

The command-line surface is **validated** — exercised against a real index, with
tests pinning the shapes it returns. The MCP surface is **contract-complete**:
mapped from upstream's published schemas and never executed here. The capability
reference marks which is which, so a claim read from a schema is not mistaken
for one that was observed.

## Guides

- [Investigate a codebase](how-to/investigate-a-codebase.md) — the five
  investigation patterns and when each applies.
- [Your first code-intelligence session](tutorials/first-session.md) — install,
  index, and answer a real question.
- [Command and capability reference](reference/capability-surface.md) — what the
  pack calls, what it returns, and what it cannot do.
