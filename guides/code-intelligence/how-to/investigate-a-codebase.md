---
title: Understand the code
summary: Get evidence-backed answers about what a codebase does, what depends on it, and what a change would break.
pack: code-intelligence
uses: [code-intelligence]
kind: how-to
---

# Understand the code

Index your repository first, then ask your agent a question about the code.

## Build the index

Install `code-intelligence` with `agentbundle install --pack code-intelligence`, then install `wicked-estate`, the tool the pack queries, and index the repository:

```bash
cargo install wicked-estate --version 0.30.0 --locked
echo '.wicked-estate/' >> .gitignore
wicked-estate index .
```

This writes `.wicked-estate/graph.db` and leaves your code untouched. [Your first session](../tutorials/first-session.md) covers the setup in more detail.

## Ask your question

Ask in plain words, and the skill picks the right pattern:

```text
What breaks if I change the signature of parse_config?
```

The agent answers from the index, lists direct and indirect callers separately, and reads the important ones in source to check. Other questions work the same way: "What is X and how does it work?", "Why does X do Y?", "How is this organised?", and "What do I need to read for X?".

## Check how complete it is

If you get a bare list, ask:

```text
How complete is that?
```

The agent reports unresolved references, whether results were cut off, and which revision the index describes. When the index is missing, the agent says it fell back to text search and does not present that as the full list of affected code.

The agent reports what is true in the code and makes no recommendation. The [capability reference](../reference/capability-surface.md) lists every query it can run.

Next, [shape a feature](../../product-engineering/how-to/shape-a-feature-intent.md) with what you learned.
