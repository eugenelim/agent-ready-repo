---
title: Understand the code
summary: Get evidence-backed answers about what a codebase does, what depends on it, and what a change would break.
pack: code-intelligence
uses: [code-intelligence]
kind: how-to
---

# Understand the code

Ask your agent a question about your code and it answers from an index of the repository's symbols and their relationships, then reads the source to check.

## Build the index

To index the repository with `wicked-estate`, the tool the pack queries, run:

```bash
wicked-estate index .
```

This writes `.wicked-estate/graph.db` and leaves your code untouched. [Your first session](../tutorials/first-session.md) covers installing the tool.

## Ask your question

Ask in plain words, and the skill picks the right pattern:

```text
What breaks if I change the signature of parse_config?
```

The agent lists direct and indirect callers separately and reads the important ones in source. Other questions work the same way: "What is X and how does it work?", "Why does X do Y?", "How is this organised?", and "What do I need to read for X?".

## Check how complete it is

If you get a bare list, ask:

```text
How complete is that?
```

The agent reports unresolved references, whether results were cut off, and which revision the index describes. When the index is missing, the agent says it fell back to text search and does not call that a blast radius.

The agent reports what is true in the code and makes no recommendation. The [capability reference](../reference/capability-surface.md) lists every query it can run.

Next, [shape a feature](../../product-engineering/how-to/shape-a-feature-intent.md) with what you learned.
