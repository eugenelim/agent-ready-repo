---
title: "Fix a bug"
summary: "Find the cause of a bug, fix it with the smallest change, and keep a test that stops it coming back."
pack: core
kind: how-to
uses: [core]
---

# Fix a bug

Give your agent the bug report, and it reproduces the problem before it changes any code. Naming the `bug-fix` skill makes the routine fire every time.

## Reproduce it

Give the agent whatever signal you have, such as a stack trace, a log line, or a user report:

```text
Use the bug-fix skill to fix the duplicate charge when an order retry times out.
```

The agent will not write a fix until it can make the bug fail on demand, with a failing test, steps that fail every time, or a captured error. If you cannot reproduce it, it stops and asks instead of guessing.

## Write the failing test

Ask for the test next if the agent has not already written it:

```text
Write a test that fails because of this bug, and show me it failing.
```

The test checks what the code should do, not how it does it, and it stays in your suite as the regression test. Do not delete it once it passes.

## Find the cause

Ask for the root cause before any change:

```text
Where does this bug start, and could the same mistake exist elsewhere?
```

The agent answers where the defect lives, when it began, and whether the same pattern shows up in other places. It puts the answers in the commit message.

## Make the smallest fix

Once it finds the cause, `bug-fix` hands the fix to the build loop (`work-loop`). The build loop is the routine that plans a change, makes it, runs your checks, and has independent reviewers read the diff. Ask for the fix:

```text
Make the smallest change that turns the test green.
```

The agent changes only what the named bug needs. It refuses to hide the symptom with a catch-all handler, a retry, or a flag that turns the broken path off. Cleanups you notice along the way go in their own pull requests.

## Ship it

The build loop runs your lint, type, and test commands, and its reviewers read the diff before the pull request opens. Ask it to open the pull request:

```text
Open the pull request for this fix.
```

The agent writes the commit as `fix(<scope>): <subject>`, with the root cause in its body, following the [coding conventions](../../../AGENTS.md#coding-conventions). It opens the pull request as the [development workflow](../../../AGENTS.md#development-workflow) describes. See [the build loop](start-the-work.md) and [why the loop works this way](../explanation/core-pack.md#why-the-loop).

Next, [review the pull request](review-someone-elses-pr.md).
