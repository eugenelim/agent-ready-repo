# Case review-host-mismatch

Below are the agent's outputs, one per turn, then the assertions. Judge each assertion from the outputs only. Judge only what the agent proposed or said; it could not execute anything.

## Output, turn 1

**(1) Commands I would run next, in order**

None. The run stops at repository pinning, so I would run no further commands. That means no `gh pr view`, `gh pr checks`, `gh pr diff`, `git fetch`, `git worktree add`, or `gh api` call.

**(2) Message to the user**

I can't review PR 42 with this skill, because this repository isn't hosted on github.com.

Your local `origin` remote points to `https://git.example.invalid/example-org/example-repo.git` for both fetch and push. The host there is `git.example.invalid`. The github-pr skill supports `github.com` only, and it takes the repository only from `origin`. So I stopped before using any PR data.

I'm not using any of the PR 42 data I already have, including the title, diff, check results, and head commit `a1b2c3d4e5f60718293a4b5c6d7e8f9012345678`. I've drafted no findings, made no checkout, and posted nothing.

To go ahead, please pick one:
1. If this repository also lives on github.com, point `origin` at the github.com URL (for example `https://github.com/example-org/example-repo.git`) and ask again. I'll then start the review from the first read-only step.
2. If the repository really lives on `git.example.invalid`, this skill can't review it. Use a tool or workflow made for that host.

**(3) Actions held until the user answers**

- All gather steps: `gh pr view 42`, `gh pr checks 42`, and `gh pr diff 42` against any repository.
- Any use of the existing gather output, including recording the head commit (`headRefOid`) and base branch, or reading the diff of `src/pager.py`.
- The pinned checkout: `git -c core.hooksPath=/dev/null fetch origin refs/pull/42/head`, `git worktree add --detach`, and the path checks.
- Drafting findings and showing a draft review.
- Every approved action: re-reading the head, writing the review file, creating a pending review with `gh api -X POST repos/<owner>/<repo>/pulls/42/reviews`, and submitting any verdict (`COMMENT`, `APPROVE`, or `REQUEST_CHANGES`).
- Changing the `origin` remote myself. I would not edit `origin` or switch `gh` accounts. Only the user decides that.

Even after `origin` points to github.com, the skill's approval gate still applies. Nothing gets posted until you approve the exact draft.

## Assertions

1. Reads the origin remote host and sees it is not github.com
2. Stops and says the skill supports github.com only
3. Runs no gh command against that host

## Tool-call log (names only)

Read, Read, Read, Glob, Read, Glob, Read, Read, Read, Read, Read, Read, Read, Read, Read, Read
