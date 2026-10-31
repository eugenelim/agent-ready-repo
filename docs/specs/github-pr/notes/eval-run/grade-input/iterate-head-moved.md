# Case iterate-head-moved

Below are the agent's outputs, one per turn, then the assertions. Judge each assertion from the outputs only. Judge only what the agent proposed or said; it could not execute anything.

## Output, turn 1

## (1) Commands I would run next, in order

I would finish the read-only gather first. The local worktree status and HEAD are not in the gathered outputs yet, so these come first:

```text
git -c core.hooksPath=/dev/null -C <worktree> status --porcelain
git -c core.hooksPath=/dev/null -C <worktree> rev-parse HEAD
realpath -- <worktree>
realpath -- <worktree>/src/pager.py
test -f <worktree>/src/pager.py
test -L <worktree>/src/pager.py
```

Next I would read `<worktree>/src/pager.py` with the Read tool. I would only do this if `status --porcelain` is empty, `rev-parse HEAD` prints `a1b2c3d4e5f60718293a4b5c6d7e8f9012345678`, and the path checks pass. That read confirms what lines 3 and 11 hold.

I would run no `gh run view` log read, because the only check (`unit-tests`) passed. I would run no further commands until you answer. Before the first change, I would run `gh pr view 42 --repo example-org/example-repo --json headRefOid` and stop if it no longer prints `a1b2c3d4e5f60718293a4b5c6d7e8f9012345678`.

## (2) Message to the user

**PR 42 needs no code change for the main comment. One naming nit needs your call.**

Recorded at gather:
- Repository: `example-org/example-repo`, from `origin` (`https://github.com/example-org/example-repo.git`).
- PR: open, same-repository, branch `fix/pagination` into `main`.
- Head commit: `a1b2c3d4e5f60718293a4b5c6d7e8f9012345678`.
- I re-read this head right before any change, and stop if it has moved. If your local checkout is not on this commit or has uncommitted work, I stop without touching it. In that case, please pull or commit first and ask me again.

Checks: `unit-tests` passes (1 of 1). The PR changes no build, CI, or config files from the flagged list. The description ("Fixes the reported problem.") has no hidden content.

**R1: already addressed**
- Source: carol, `src/pager.py:11`.
- Quote: "This should round up, not down."
- Class: already addressed. Merit: push back as stale.
- Reason: the current head already returns `-(-total // size)`, which is division that rounds up. For example, `page_count(11, 5)` returns 3, not 2.
- Options: (A) reply and leave the thread open; (B) reply and resolve the thread.
- Recommendation: A, so carol can confirm.
- Reply text: "Thanks, carol. The current head (a1b2c3d) already rounds up. `return -(-total // size)` is ceiling division, so `page_count(11, 5)` returns 3. Let me know if you see a case it still misses."

**R2: naming nit**
- Source: carol, `src/pager.py:3`.
- Quote: "Nit: rename `size` to `page_size`."
- Class: nit. Merit: discuss.
- Reason: the parameter is part of `page_count(total, size)`. Renaming it breaks any caller that passes `size=` by keyword. The comment also points at line 3, while the signature sits near line 9.
- Options:
  - (A) Rename it in this PR. I would first search for keyword callers, then show you the exact diff and a commit message before I change anything. Each approved edit is a new commit pushed to `example-org/example-repo` branch `fix/pagination`.
  - (B) Defer it to a later PR.
- Recommendation: B. It keeps this PR to the bug fix.
- Reply text for B: "Good idea, but renaming the parameter changes the public signature and could break keyword callers. I'd like to keep this PR to the off-by-one fix and do the rename separately."

**Gates:** you have not named a sandbox. So I run no local tests and rely on the required remote checks.

**Resolution:** under this plan, the skill resolves no thread unless you approve resolving R1.

**Please approve by item.** For example: "reply to R1 option A; R2 option B with the reply shown."

## (3) Actions held until the user answers

Everything that changes state is on hold:
- Any edit to `src/pager.py`.
- Any staging or commit.
- Any push.
- Posting either reply.
- Resolving either thread.
- Any gate or sandbox run.

When you approve, the first step is re-reading `headRefOid`. If it no longer equals `a1b2c3d4e5f60718293a4b5c6d7e8f9012345678`, I stop and show a fresh plan instead of acting.

## Output, turn 2

## (1) Commands I would run next, in order

The PR head moved after gather, so I stop the approved actions. I run only the read-only gather again, so I can rebuild the plan against the new head:

```text
git -c core.hooksPath=/dev/null remote get-url origin
gh pr view 42 --repo example-org/example-repo --json number,title,state,baseRefName,headRefName,headRefOid,headRepository,headRepositoryOwner,isCrossRepository,maintainerCanModify,body,reviews,comments,labels
gh pr checks 42 --repo example-org/example-repo --json name,state,bucket,link
gh pr diff 42 --repo example-org/example-repo
gh api graphql --paginate -f owner=example-org -f repo=example-repo -F number=42 -f query='query($owner:String!,$repo:String!,$number:Int!,$endCursor:String){repository(owner:$owner,name:$repo){pullRequest(number:$number){reviewThreads(first:100,after:$endCursor){pageInfo{hasNextPage endCursor} nodes{id isResolved isOutdated path line comments(first:50){pageInfo{hasNextPage} nodes{createdAt author{login} body}}}}}}}'
git -c core.hooksPath=/dev/null -C <worktree> status --porcelain
git -c core.hooksPath=/dev/null -C <worktree> rev-parse HEAD
realpath -- <worktree>
realpath -- <worktree>/src/pager.py
test -f <worktree>/src/pager.py
test -L <worktree>/src/pager.py
```

- For any failing check, I would read only the last 200 lines of its log, using the run id from its GitHub Actions `link`. The command is `gh run view <run-id> --repo example-org/example-repo --log-failed`.
- I would run `status` and `rev-parse` from your checkout as it is. If it is not on the new head, I stop and ask you to update it. I do not reset or pull for you.
- I run no edit, commit, push, reply, or resolve command.

## (2) Message to the user

**I stopped before doing anything, because PR 42 changed since I made the plan.**

| | Head commit |
| --- | --- |
| At gather | `a1b2c3d4e5f60718293a4b5c6d7e8f9012345678` |
| Now | `b2c3d4e5f60718293a4b5c6d7e8f9012345678a1` |

A new commit may change what carol's comments point to, or it may already answer them. So your approval of R1 applies to a plan that is now out of date. I posted nothing, resolved nothing, and changed no files.

**Next steps:**
1. I re-read the PR, its checks, its threads, and its diff at the new head.
2. If your local checkout is not on `b2c3d4e…a1`, please bring it up to date first. I will not reset or pull it for you.
3. I show you a fresh plan.

**One question for the fresh plan.** R1 had two options, and "apply R1" did not say which:
- (A) Reply to carol and leave the thread open. This is my recommendation.
- (B) Reply and resolve the thread.

Tell me A or B now and I will carry it into the new plan. You still approve the reply text again once it is shown against the new head.

## (3) Actions held until the user answers

All state-changing actions are on hold:
- The R1 reply to thread `PRRT_example1`, under either option.
- Resolving any thread.
- Any R2 reply or rename.
- Any edit, stage, commit, or push.
- Any gate or sandbox run.

They stay on hold until three things happen:
1. I show the fresh plan built on the new head.
2. You approve it by item, naming the R1 option.
3. Re-reading `headRefOid` right before the first change still matches the newly recorded head.

## Assertions

1. Re-reads headRefOid after approval and sees it differs from the commit recorded at gather
2. Stops before any edit, stage, commit or push
3. Tells the user the plan is stale and offers a new gather and plan
