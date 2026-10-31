# Iterate mode

## Contents

1. Gather
2. Classify and judge
3. Plan, then wait
4. Approved actions: re-check, edit, stage, commit
5. Approved actions: gates in a sandbox
6. Approved actions: push, reply, resolve

Work through the feedback and failing checks on your own PR. Decide which
items are right, agree one plan with the user, and only then change anything.

## 1. Gather (read-only)

Take `<N>` from the user. Work in the user's checkout of the PR branch, called
`<worktree>` below.

```text
gh pr view <N> --repo <owner>/<repo> --json number,title,state,baseRefName,headRefName,headRefOid,headRepository,headRepositoryOwner,isCrossRepository,maintainerCanModify,reviews,comments,labels
gh pr checks <N> --repo <owner>/<repo> --json name,state,bucket,link
gh pr diff <N> --repo <owner>/<repo>
gh api graphql --paginate -f owner=<owner> -f repo=<repo> -F number=<N> -f query='query($owner:String!,$repo:String!,$number:Int!,$endCursor:String){repository(owner:$owner,name:$repo){pullRequest(number:$number){reviewThreads(first:100,after:$endCursor){pageInfo{hasNextPage endCursor} nodes{id isResolved isOutdated path line comments(first:50){pageInfo{hasNextPage} nodes{createdAt author{login} body}}}}}}}'
git -c core.hooksPath=/dev/null -C <worktree> status --porcelain
git -c core.hooksPath=/dev/null -C <worktree> rev-parse HEAD
```

- Stop if `state` is not `OPEN`, if `<worktree>` has uncommitted work, or if its
  HEAD differs from `headRefOid`. Do not reset or overwrite local work.
- Record `headRefOid` as the commit recorded at gather, and record
  `headRefName`, `headRepositoryOwner`, and `headRepository` once. Apply the
  value check to each before use, and never rebuild a branch name from a convention.
- If the PR is cross-repository and `maintainerCanModify` is false, plan
  replies only and say pushes are not possible.
- For each failing check, read only the last 200 lines of its log, using a run
  id taken from a `link` that is a GitHub Actions run URL for this repository:

```text
gh run view <run-id> --repo <owner>/<repo> --log-failed
```

- Skip resolved threads. A thread whose `comments.pageInfo.hasNextPage` is true
  is cut short; say so. Say plainly what was truncated or unreadable.
- Before you read or edit a path from the diff or a reviewer, check it, and
  report a symlink, submodule, or out-of-tree path in the plan without following it:

```text
realpath -- <path>
test -f <path>
test -L <path>
```

## 2. Classify and judge

Give every item a stable id (`R1`, `R2`, ...), its source (author and file:line,
or check name), and a class: blocking, suggestion, question, nit, out of scope,
or already addressed. Then judge merit in your own words:

| Merit | Meaning |
| --- | --- |
| Accept | The concern is right and the fix is sound. |
| Partial | The concern is right; a different fix is better. |
| Push back | The comment misreads the code, is stale, or conflicts with a repository rule. |
| Discuss | Reasonable people differ; the user decides. |
| Defer | Valid but outside this PR. |

Read what a comment points to in the current head first, and whether a later
commit already fixed it. A failing check is a claim to diagnose, not a task to silence.

## 3. Plan, then wait

Show one plan with, per item: id, source, a short quote, class, merit with one
line of reasoning, options, and a recommendation. Also show:

- the exact diff for each edit, the files the commit stages, the commit
  message, the push destination, and the exact text of every reply;
- each PR-changed file that matches the flagged path list, listed in the plan.
  Flagged paths: `.github/**`, `CODEOWNERS`, `Makefile`, `conftest.py`,
  `package.json`, `pyproject.toml`, `pytest.ini`, `setup.cfg`, `setup.py`,
  `tox.ini`, `noxfile.py`, `justfile`, `Taskfile.y*ml`, `Dockerfile*`,
  `docker-compose*`, `compose*.y*ml`, `.devcontainer/**`, `.tool-versions`,
  `mise.toml`, `.envrc`, `.gitattributes`, `.gitmodules`,
  `.pre-commit-config.yaml`, `.husky/**`, `scripts/**`, `tools/**`, at any
  depth. When one is listed, a gate result is flagged as not independent
  evidence, because the PR may have rewritten what the gate checks;
- the gate commands and the sandbox command with its setup files, or that
  the user names no sandbox, in which case you run no local gate and rely on
  the repository's required remote checks;
- which threads would be resolved, and why each fix will already have landed.

Then stop and ask for approval by item, such as "apply R1 option B; reply to
R2; defer R4". Approval in the original request does not count. If the plan
changes, show it again.

## Approved actions

Everything below runs only for approved items, in this order. Each posted
body and each commit message equals what was shown at approval; any change is
shown again and re-approved.

### Re-check, edit, stage, commit

1. Re-read the head and stop if it differs from the commit recorded at gather:

```text
gh pr view <N> --repo <owner>/<repo> --json headRefOid
```

2. Make the approved edits with the edit tool, blockers first. Search the
edited files for leftovers of what the comment asked to remove or rename.
3. Stage only the files the approved list names, one path at a time, never a
directory or pattern, then compare the staged diff with the approved diff.
Save the approved diff to `<approved-patch>` before editing:

```text
git -c core.hooksPath=/dev/null -C <worktree> add -- <approved-file>
git -c core.hooksPath=/dev/null -C <worktree> diff --cached --binary > <staged-patch>
shasum -a 256 <approved-patch> <staged-patch>
```

Any staged byte that differs from the edits shown at approval stops the run.
4. Commit as a new commit, never an amend, with the approved message from a file
outside the worktree:

```text
git -c core.hooksPath=/dev/null -C <worktree> commit -F <message-file>
git -c core.hooksPath=/dev/null -C <worktree> rev-parse HEAD
```

### Gates in a sandbox

Skip this part unless the approved list names a sandbox and gate commands.
When it names no sandbox, run no local gate.

1. Find the git directories, then hash every file git loads for `<worktree>`:
system, global, and XDG configuration, `include` and `includeIf` targets
(read each config file to find them), the repository `config` and
`config.worktree`, `hooks/`, and `info/`:

```text
git -c core.hooksPath=/dev/null -C <worktree> rev-parse --git-dir --git-common-dir
shasum -a 256 /etc/gitconfig ~/.gitconfig ~/.config/git/config <git-common-dir>/config <git-dir>/config.worktree <include-target> <git-common-dir>/hooks/* <git-common-dir>/info/* > <hashes-before>
```

2. Export the commit you recorded with git archive, into an empty directory
outside the worktree, then run each approved gate there through the sandbox:

```text
git -c core.hooksPath=/dev/null -C <worktree> archive --format=tar <commit> | tar -x -C <export-dir>
```

```gates
<sandbox> <gate-command>
```

3. Before your next git command after any sandbox run, repeat the `shasum`
command into `<hashes-after>` and compare it with `<hashes-before>` with the
file-safety commands only, never a git command. If any file differs, or one
was added or is missing, stop and report.
4. Then confirm HEAD still equals the recorded commit and nothing is staged:

```text
git -c core.hooksPath=/dev/null -C <worktree> rev-parse HEAD
git -c core.hooksPath=/dev/null -C <worktree> diff --cached --binary
```

If a gate fails, stop and report, or show a revised plan item for approval.

### Push, reply, resolve

1. Re-read the head again; stop if it differs from the commit recorded at gather.
2. Push with an explicit destination, never the ambient upstream, taking
`<headRepositoryOwner>`, `<headRepository>`, and `<headRefName>` from the same
run's gather fields. Refuse any other destination:

```text
git -c core.hooksPath=/dev/null -C <worktree> push https://github.com/<headRepositoryOwner>/<headRepository>.git HEAD:refs/heads/<headRefName>
```

3. Confirm the PR's `headRefOid` equals the local commit.
4. Only after the push, and only for approved items, reply from files outside
the worktree. Name the commit that fixed an item; a declined item gets a
reasoned reply, never silence:

```text
gh api graphql -f query='mutation($id:ID!,$body:String!){addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$id,body:$body}){comment{id}}}' -f id=<thread-id> -F body=@<reply-file>
gh pr comment <N> --repo <owner>/<repo> --body-file <reply-file>
```

5. Resolve a thread only when its fix landed in the pushed commit or the user
approved resolving it. Leave push-back and deferred threads open:

```text
gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id=<thread-id>
```

The thread id is the `id` the gather query returned. Replies and resolutions
cannot be undone by this skill; send exactly the approved text.

Finish by reading checks and threads once more. New feedback goes back through
the gather step. Report what changed, what is still open, and the check status.
