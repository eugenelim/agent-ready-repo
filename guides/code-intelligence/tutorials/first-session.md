---
title: Your first code-intelligence session
summary: Install the indexer, index a repository, and answer a real question about it — including how to read the completeness numbers the answer carries.
pack: code-intelligence
kind: tutorial
---

# Your first code-intelligence session

By the end you will have indexed a repository and asked it what breaks if you
change something — and you will know how much to trust the answer.

**Time:** about ten minutes, most of it the one-off install.

## 1. Install the indexer

The pack drives a command-line tool it does not bundle.

```bash
cargo install wicked-estate --version 0.16.7 --locked
```

This compiles from source and takes several minutes. It needs `cargo` already
on your `PATH`; the pack will not install a Rust toolchain for you.

## 2. Keep the index out of version control

Indexing writes a database into your working tree, and it is large — a few
hundred megabytes on a mid-size repository.

```bash
echo '.wicked-estate/' >> .gitignore
```

Do this before the next step, not after.

## 3. Index the repository

```bash
wicked-estate index .
```

On a 4,600-file repository this takes around fifteen seconds and reports what it
found:

```
indexed . (.wicked-estate/graph.db) → 65981 nodes, 104379 edges, 4634 files
```

## 4. Check the pack agrees

```bash
python scripts/estate_preflight.py --check
```

`status: ready` means the binary and the index are both in place. Exit 2 is a
missing binary, 3 a missing index, 4 a version below the floor the pack was
verified against.

## 5. Ask a real question

In your agent, in ordinary language:

> What breaks if I change `parse_config`?

The agent resolves the name, computes the blast radius, picks dependents worth
reading, and reads them. What comes back should look like:

> 23 resolved dependents, 4 unresolved references, no truncation. I read five
> of them; four call `parse_config` directly on the changing path.

## 6. Read the numbers, not just the list

That second sentence is the part worth learning.

- **`unresolved`** counts references the indexer could not bind. Non-zero means
  there may be dependents you were not shown — dynamic dispatch and reflection
  both produce these.
- **`truncated_dependents`** means you are looking at a prefix, not the whole
  list.
- **Depth** is capped at twelve hops on the command line and *is not reported*,
  so a far-away dependent can be missing with nothing to tell you.

A blast radius is a floor, not a total. An answer that gives you a number
without these is overclaiming.

## What to do next

Ask the same repository how it is organised, and watch the answer separate what
the graph showed from what the agent concluded from it:

> How is this codebase organised?

Then read [Investigate a codebase](../how-to/investigate-a-codebase.md) for the
other patterns.
