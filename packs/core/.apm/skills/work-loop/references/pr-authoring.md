# Writing the pull request

Load at FINISH, before opening a pull request. The body's shape is the template
in this skill's `assets` folder; copy it to the destination your forge reads.
This file owns how to fill it.

A reviewer opens the body to find out what changed, why, and whether to trust
the evidence. Everything else costs them attention they were going to spend on
the diff.

## Writing rules

1. **Lead with the result.** The first sentence says what is true now.
2. **Ground every claim.** Name the path, command, count, measurement, version,
   or error text. A claim you cannot ground is an assumption — say so.
3. **Never describe intended work as done.** State partial work as partial. A
   body that claims changes the diff does not contain is the one failure that
   makes a description worse than no description.
4. **Prose carries reasoning; bullets carry independent items.** Causes and
   trade-offs need connected sentences. One idea per bullet, grammatically
   parallel; a bullet that only continues the previous one belongs in prose.
5. **A table earns its place** when three or more items share two or more
   fields a reader must compare. Two items, or one field, is a list.
6. **Collapse only the optional.** A details block holds logs, inventories, and
   large screenshot sets. Risk, rationale, and verification stay visible.
7. **Draft for completeness, then edit once.** The pass that follows removes
   repetition and generic framing while preserving every name, number, scope
   boundary, and stated uncertainty.

Length follows content. There is no target word count; delete a sentence that
does not change what a reviewer understands or does.

## Worked body — a refactor

```markdown
## What does this change?

Retry policy now resolves in one module instead of three. The API, queue, and
batch clients had drifted to different backoff defaults; they now share one.
No configuration keys change and no retry behavior is intended to change.

## Why?

Implements: <spec-path>

The queue client's backoff diverged from the other two, and the duplicate
helpers made that divergence invisible in review.

## Review focus

Does an explicit per-request timeout still win over the shared default? That
precedence is the only behavior this refactor could silently change.

## How do I verify it?

- <test command> tests/retry_policy — 84 passed in 3.1s
- <test command> tests/clients — 217 passed in 22.4s
- <lint command> — clean
- Compared resolved policies by hand for the default, explicit-timeout, and
  retries-disabled configurations; all three match the pre-change values.

## What did you not change that you considered?

Metrics emission is still duplicated across the three clients. Folding it in
would have doubled the diff and mixed two review questions, so it stays for
separate work. Retry algorithms, configuration names, and metric labels are
untouched.
```

## Worked body — a one-line fix

```markdown
## What does this change?

The timeout flag was read as seconds and passed to a client expecting
milliseconds, so every configured timeout fired a thousand times early.

## Why?

Closes: <issue-reference>

## How do I verify it?

<test command> tests/cli_timeout — 6 passed, including a new case that fails on
the previous commit.

## What did you not change that you considered?

The same unit confusion may exist in the batch runner's deadline flag. I did
not audit it here; recorded as a backlog item rather than widened into this fix.
```

Note what the second omits: no `Review focus`, no table, no bullets where two
sentences did the work. The shape scales down.
