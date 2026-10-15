---
title: "Review a pull request"
summary: "Get an independent, severity-ranked review of a branch or pull request someone else wrote."
pack: core
kind: how-to
uses: [core]
---

# Review a pull request

Name a branch or pull request someone else wrote, and your agent returns findings you can hand back to the author.

## Ask for the review

Name the branch:

```text
Use the work-loop to review branch feature/payment-refund.
```

The agent reads the diff and runs `adversarial-reviewer`, adding `security-reviewer` and `quality-engineer` when the change warrants them.

## Review a hosted change

If your agent has `gh`, `glab`, or an MCP server for your host, name the pull request instead:

```text
Use the work-loop to review GitHub PR #123.
```

A local branch always works. For a GitLab merge request, say "review this GitLab MR".

## Check against a spec

A branch in progress usually has no spec, so the reviewer judges the diff on its own. If the branch carries a spec, a short document that says what done means, name it:

```text
Review this branch against docs/specs/payment-refund/spec.md.
```

The reviewer then checks the diff against that spec.

## Read the findings

The agent returns findings tagged Blockers, Concerns, and Nits. This is a one-off review, so it writes no loop state and starts no build; hand the findings to the author to repair. The `shaping-reviewer` checks draft intents, briefs, and specs before building starts, so it does not review these diffs the way the adversarial, security, and quality reviewers do.

Next, [fix a bug](bug-fix.md) the review found, or [release the change](../../release-engineering/how-to/run-a-release.md).
