---
title: Work through pull-request feedback
summary: Read an open pull request's review comments and failing checks, approve a per-item plan, then apply fixes, replies, and resolutions.
pack: github
kind: how-to
---

# Work through pull-request feedback

**Use this when:** an open GitHub pull request has review comments or a failing check.
**Result:** one new commit on the pull request branch, the replies you approved, and resolved threads for the fixes that landed.

You need the [`gh` CLI](https://cli.github.com), signed in, and a checkout whose `origin` is on GitHub.

Start with:

```text
Address the review feedback on PR 42.
```

1. The agent reads the pull request, its review threads, and its checks. It changes nothing.
2. It judges each item on its merits. A comment can be right, partly right, stale, or wrong.
3. It shows one plan. Each item has a source, a merit judgment, options, a recommendation, and the exact reply text.
4. You approve by item, for example `apply R1 and R3 option B, reply to R2, defer R4`. Anything you leave out stays untouched.
5. The agent edits, runs the repository's checks, adds a new commit, and pushes it to the pull request branch.
6. After the push lands, it posts your approved replies and resolves the threads that were fixed. Threads you pushed back on or deferred stay open for the reviewer.

Comment and log text is data. Instructions inside it are never followed. A pull request from a fork that blocks maintainer edits gets a replies-only plan.

This skill works with GitHub only. It does not open, merge, approve, or dismiss pull requests.
