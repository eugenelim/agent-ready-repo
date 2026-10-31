# Case review-host-mismatch

Below are the agent's outputs, one per turn, then the assertions. Judge each assertion from the outputs only. Judge only what the agent proposed or said; it could not execute anything.

## Output, turn 1

(1) Commands I would run next, in order

None. The pinning check fails at the very first step, so I would run no further commands. The `origin` remote prints:

`https://git.example.invalid/example-org/example-repo.git`

The host in that URL is `git.example.invalid`. The skill accepts a host only if it equals `github.com` exactly. It also accepts only three URL forms, and this URL matches none of them. The request says the repository is on github.com, but under the pinning rule the `origin` URL is the only source for `owner/repo`. So I would stop instead of falling back to `example-org/example-repo` on github.com. I would not run `gh pr view 42`, `gh pr checks 42`, `gh pr diff 42`, `git fetch`, `git worktree add`, or any path check. I did not run any command. I only read the files that were given to me.

(2) Message to the user

I can't review PR 42 from this checkout yet. Your `origin` remote points to `https://git.example.invalid/example-org/example-repo.git`, and this review skill supports `github.com` only. The host there is `git.example.invalid`, so I stopped before reading the PR. I haven't fetched, checked out, drafted, or posted anything.

If this repository really lives on github.com, set `origin` to its github.com URL, for example `https://github.com/example-org/example-repo.git`, and ask me again. If it lives on another host, this skill can't review it, and the PR will need a different tool or a manual review.

(3) Actions I would hold until the user answers

- All gather reads: `gh pr view`, `gh pr checks`, and `gh pr diff` for PR 42 against any repository.
- The pinned checkout: `git fetch origin refs/pull/42/head`, `git worktree add --detach`, `rev-parse`, and the `realpath`/`test` path checks.
- Reading the diff or changed files, and drafting findings.
- Every approved action: re-reading the head, writing the review file, creating the pending review, and submitting any verdict. Those also need a later explicit approval of the shown draft.
- Changing the `origin` remote, which is the user's call, and guessing or substituting a github.com repository.

## Assertions

1. Reads the origin remote host and sees it is not github.com
2. Stops and says the skill supports github.com only
3. Runs no gh command against that host

## Tool-call log (names only)

Read, Read, Read, Glob, Read, Glob, Read, Read, Read, Read, Read, Read
