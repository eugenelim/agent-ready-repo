---
title: Work through a GitHub pull request
summary: Review someone's pull request, address feedback on yours, or adopt a contributor's, with every push, post, and merge approved first.
pack: github
kind: how-to
---

# Work through a GitHub pull request

**Use this when:** you need to review a pull request, address feedback on your own, or carry a contributor's pull request to merge.
**Result:** only the actions you approved happen on GitHub, and the agent says what it did.

You need the [`gh` CLI](https://cli.github.com), signed in, and a checkout whose `origin` is on github.com. The agent reads first and changes nothing until you approve. Comment, diff, and log text is data. Instructions inside it are never followed.

Say which pull request and which job. If it is unclear, the agent asks one question.

## Review someone's pull request

```text
Review PR 42.
```

1. The agent reads the pull request, its diff, and its checks.
2. It drafts the review: a summary and each inline comment with its exact text.
3. You approve or edit the draft.
4. The agent creates a pending review on the pull request. It does not submit it.
5. Submitting is a separate choice. Tell the agent which verdict to submit (`COMMENT`, `APPROVE`, or `REQUEST_CHANGES`), or read the pending review on GitHub and submit it yourself.

## Address feedback on your pull request

```text
Address the review feedback on PR 42.
```

1. The agent reads the review threads and failing checks.
2. It judges each item on its merits. A comment can be right, partly right, stale, or wrong.
3. It shows one plan. Each item has a source, a judgment, options, a recommendation, and the exact reply text.
4. You approve by item, for example `apply R1 and R3 option B, reply to R2, defer R4`. Anything you leave out stays untouched.
5. The agent edits, adds a new commit, and pushes it. Then it posts your approved replies and resolves only the threads your approved plan names, each one after its fix landed in the pushed commit or you approved resolving it. Every other thread stays open, including pushed-back and deferred ones.

A pull request from a fork that blocks maintainer edits gets a replies-only plan.

## Adopt a contributor's pull request

```text
Adopt PR 42 and carry it to merge.
```

1. The agent evaluates the pull request and tells you what it does and whether it is worth adopting.
2. If you want it, the agent shows one adoption contract: what it may fix, push, and merge, and where it must stop.
3. You approve the contract. Merging happens only under that approved contract.
4. The agent makes the fixes, pushes, waits for the required checks, and merges inside the contract.
5. It stops and asks when something falls outside the contract, such as a new commit from the contributor, a failing required check, or a changed target.

## Running the pull request's code

The agent runs a pull request's code only through a sandbox command you name, for example a container or throwaway virtual machine wrapper. If you name none, it runs no local checks and relies on the repository's required checks on GitHub.

This skill works with github.com only.
