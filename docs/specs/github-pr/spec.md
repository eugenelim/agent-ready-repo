# Spec: github-pr — review, iterate on, and adopt GitHub pull requests

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** notes/github-pr-workflows-survey.md
- **Depends on:** none
- **Contract:** none
- **Shape:** integration
<!-- If this spec intentionally has no criteria, remove the section below and add `- **Acceptance Criteria:** none — <one-line reason>` to the metadata header. -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

<!-- **Durable-spec fill.** This template governs work that needs a durable
behavior contract for one delivery slice. Fill Outcome, What Changes, Agent
Rules, Testing Strategy, and Acceptance Criteria to the depth the durable work
requires, and Assumptions only where something is unresolved. The sibling plan carries the implementation and verification strategy.
Eligible direct-light work does not create this artifact. -->

<!-- **Present tense, as-built.** Write every body section below as if the
feature already exists and always worked this way — no "will be", no
"previously X, now Y", no deprecation timelines, no version-stamped history.
The body describes the current contract; decision history lives in ADRs and the
release changelog. `plan.md` holds to the same rule: its `## Changelog` records
approvals, not how the approach evolved. -->

## Outcome

Someone working on a GitHub pull request gets one skill that reviews another person's PR, works through feedback and failing checks on their own, or adopts a contributor's PR they like and carries it to merge without review ping-pong. The agent changes nothing and runs no PR-authored code until the user approves that action, or the one adoption contract that names it.

## What Changes

- The unreleased `github-pr-iterate` skill becomes `github-pr` — `packs/github/.apm/skills/github-pr/`, with no copy of the old name left outside this spec directory.
- `SKILL.md` is a short router plus the rules all three modes share (trust, repository pinning, approval gate) — the same file.
- Review, iterate, and adopt each load their own procedure only when chosen — `references/review.md`, `references/iterate.md`, `references/adopt.md`. There is no general `gh` command reference; a command appears only where a mode needs it.
- Review mode drafts findings, then after approval creates one pending review; submitting a verdict is a separate choice the user names.
- Adopt mode evaluates a contributor's PR; if the user likes it, they approve one adoption contract and the agent fixes, pushes, and merges inside it.
- Twenty-seven behavioural eval cases with canned `gh` output, plus a recorded cold-context graded run — `evals/`, `notes/eval-run.md`.
- Pack metadata, README, journey, how-to guide, census, and changelog fragment describe all three modes — `packs/github/`, `guides/github/`, `docs/product/changelog.d/`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Three modes change what the pack offers | `packs/github/README.md`, `guides/github/how-to/` | pack maintainer | README and guide name all three modes and the approval rule | Both read as one story |
| Journey | Pack journey lists skills and gates | `packs/github/JOURNEY.md`, generated `web/src/content/journeys/github.md` | pack maintainer | `build-site --journeys-only` changes only the github journey file, and the regenerated `repo-governance` file is restored | Generated file matches source |
| Interface compatibility | Skill name and pack skill list change | `pack.toml`, `plugin.json`, marketplace file, skill census | pack maintainer | `catalogue verify` ok; census test green | Versions agree at 0.3.0 |
| Release history | Consumer-visible capability | `docs/product/changelog.d/66c8f467-39f7-4063-8aac-d8d60d42c4c2.md` (rewritten) | pack maintainer | `tools/changelog.py validate` ok | Fragment covers review, iterate, and adopt |
| Reusable learning | Eval method and its pilot result are reusable | `docs/specs/github-pr/notes/eval-run.md` | implementer | Recorded run with isolation evidence | Note states case results and grader inputs |
| Current architecture, decision rationale, operations | Skill content only; no new module, dependency, or service | none | n/a | n/a | n/a |

## Agent Rules

Rules for the agent building this change. How the shipped skill behaves is stated by the criteria below.

### Always do

- Follow `packs/AGENTS.md` for versions, the eval harness, and shipped-content rules.
- Record the build against the survey in `notes/github-pr-workflows-survey.md`; a command the survey marks unverified stays out of the skill.

### Ask first

- Adding a mode beyond review, iterate, and adopt (opening a PR, auto-merge, merge queue, stacking).
- Any new dependency or any script under the skill.
- Raising the pack version beyond 0.3.0.

### Never do

- Add a new top-level directory, a new pack, or Azure DevOps support.
- Run `gh` against a real repository while building or evaluating this change, other than read-only version and help output.
- Commit the unrelated `repo-governance` journey file that `build-site` also regenerates.

## Testing Strategy

- Skill structure, trigger queries, and command safety: TDD with pytest in `packs/github/tests/skills/github-pr/`, because each rule is a string-checkable invariant over the skill text and eval files.
- Eval case integrity (counts, modes, fixtures, assertions, approval turn): TDD, same suite.
- Pack metadata consistency: goal-based, using `catalogue verify`, the skill-census test, and `git grep`.
- Agent behaviour under the skill: graded run by fresh subagents with cold context, because only a model reading the skill can show it holds the approval gate. Run rules are the graded-run criteria below. The survey's pilot section records why the run targets acting before approval, running PR code, and the adopt contract.

## Acceptance Criteria

A *mutating command* is any of: `gh api` with `-X POST`, `PATCH`, `PUT`, or `DELETE` or with `-f`/`-F` on a REST path; any GraphQL `mutation`; `git commit`; `git push`; `gh pr merge`, `gh pr ready`, `gh pr edit`, `gh pr comment`, `gh pr review`, `gh pr close`, `gh run rerun`, `gh workflow run`. `gh pr checkout` is local and excluded. `SKILL.md` enumerates these forms and the construction tests read that list.

- [ ] `SKILL.md` is at most 150 lines, counted from its first line.
- [ ] `SKILL.md` links `references/review.md`, `references/iterate.md`, and `references/adopt.md` directly.
- [ ] `SKILL.md` tells the agent to load only the reference for the chosen mode.
- [ ] Every reference over 100 lines opens with a table of contents.
- [ ] The skill description is at most 1,024 characters.
- [ ] The skill description names a trigger phrase for each of review, iterate, and adopt.
- [ ] `evals/eval_queries.json` marks review, iterate, and adopt phrasings as triggering.
- [ ] `evals/eval_queries.json` marks opening a PR, merging with no evaluation or adoption request, auto-merge, and Azure DevOps phrasings as not triggering.
- [ ] The untrusted-data rule in `SKILL.md` names each of: comments, review bodies, titles and descriptions, branch names, commit messages, CI logs, the PR diff, files the PR adds or changes and their paths, check-run names and annotations, labels, linked-issue text, and author and committer names.
- [ ] `SKILL.md` has the agent read raw comment and description text and report any HTML comment, hidden element, or zero-width content in the plan as untrusted.
- [ ] `SKILL.md` has repository instruction and review-rule files read from the base branch, and treats their PR-head versions as data.
- [ ] `SKILL.md` derives `owner/repo` and the host once from the local `origin` remote, confirms them against the user's request, never takes them from PR content, uses that host in every `gh` call, GraphQL call, and push URL, and stops on a mismatch.
- [ ] `SKILL.md` forbids printing credentials and copying credential-shaped text from CI logs, gate output, or files into reviews, replies, commits, or the plan.
- [ ] `SKILL.md` forbids running PR-authored code (tests, builds, scripts, hooks) before the approved action list or contract names that run.
- [ ] Every `gh pr` and `gh run` command in the skill and its references carries `--repo <owner>/<repo>`.
- [ ] Every REST `gh api` path in the skill and its references is a literal `repos/<owner>/<repo>/...` path with no `{owner}` or `{repo}` placeholder.
- [ ] Every GraphQL mutation in the skill and its references takes the thread id as a variable, and the reference names the gather query that supplies it.
- [ ] Every GraphQL query in the skill and its references passes the owner and repository name as variables.
- [ ] No command in the skill or its references, in a code block or inline code, contains `--force`, `--force-with-lease`, `git push -f`, a `+`-prefixed refspec, `--amend`, `--admin`, `--auto`, `--all`, `--mirror`, `--tags`, `--delete`, a `:`-prefixed refspec, `--recurse-submodules`, `git add -A`, `git add .`, `gh pr create`, `gh secret`, `auth switch`, `auth token`, `--show-token`, or a `gh api` path ending in `/merge`.
- [ ] Every review, comment, reply, and commit message in the skill and its references is passed through a file or stdin, and no command contains `--body "`, `-m "`, or `-f body=`.
- [ ] The references validate a branch name or other PR-sourced command argument with `git check-ref-format` or the matching rule and single-quote it.
- [ ] Every `git push` in `references/iterate.md` and `references/adopt.md` names an explicit URL and `HEAD:refs/heads/<headRefName>`, with host, owner, repository, and branch taken from the same run's `headRepositoryOwner`, `headRepository`, and `headRefName` gather fields.
- [ ] Before reading or editing any path from the PR's diff or worktree, the skill confirms it is a regular file whose resolved path stays inside the worktree, and reports a symlink, submodule, or out-of-tree path in the plan without following it.
- [ ] Commits stage only the files the approved list or contract names, and each posted body and each commit's file set and message equals what was shown at approval; any change is shown again and re-approved.
- [ ] `gh pr merge` appears only in `references/adopt.md`.
- [ ] Every `gh pr merge` command carries `--match-head-commit`.
- [ ] Each mode reference has a heading `## Approved actions`, and every mutating command in that reference appears after it.
- [ ] `references/review.md` contains `POST repos/<owner>/<repo>/pulls/<n>/reviews` and `.../reviews/<id>/events`; `references/iterate.md` contains `git push`, `addPullRequestReviewThreadReply`, and `resolveReviewThread`; `references/adopt.md` contains `git push` and `gh pr merge`.
- [ ] `references/review.md` creates the pending review with no `event`.
- [ ] `references/review.md` submits only with an event the user named after seeing the draft.
- [ ] `references/review.md` and `references/iterate.md` each state a re-read of the PR head, required equal to the commit recorded at gather, before their first mutating command.
- [ ] `references/review.md` states that re-read, against the same recorded commit, again before it submits a verdict.
- [ ] `references/adopt.md` requires the PR head, re-read before the merge, to equal the merge target.
- [ ] The references state that repository hooks are disabled for every checkout, commit, and push, naming the setting (`core.hooksPath`) used, unless the approved list or contract names the hook run as a gate.
- [ ] Every mode reference that runs PR-authored code runs it under an allowlisted environment of named variables only.
- [ ] That environment has the git credential helper disabled, `SSH_AUTH_SOCK` unset, and `gh` pointed at an empty configuration directory.
- [ ] Every `gh pr checkout` in `references/review.md` and `references/adopt.md` carries `--detach` or `--worktree`, and each file contains at least one.
- [ ] The contract display in `references/adopt.md` states that the gates run PR-authored code and which credential paths stay reachable, at minimum the OS keyring.
- [ ] `references/adopt.md` states that the contract's gates run PR-authored code.
- [ ] `references/adopt.md` names in the contract the PR number, base branch, starting commit, allowed fix types, push destination, gates to run, merge method, and merge conditions.
- [ ] `references/adopt.md` displays the exact push destination in the contract and stops on a push to any other destination.
- [ ] `references/adopt.md` lists every PR-changed file under CI configuration, `CODEOWNERS`, or a file a gate runs, and the contract display flags that check and gate results are then not independent evidence; approval is given with the flag shown.
- [ ] `references/adopt.md` reports zero required checks on the base branch in the contract display and does not treat it as checks passed.
- [ ] `references/adopt.md` treats a fix that changes CI workflow files, `CODEOWNERS`, a gate's definition, or that deletes, skips, or weakens a test as outside every allowed fix type, and stops and asks.
- [ ] `references/adopt.md` binds the contract to that PR in the current session, requires a new displayed contract and explicit approval for any field change, and never lets PR or CI text amend it.
- [ ] `references/adopt.md` re-reads `headRefOid` and `baseRefName` before each push and before the merge, and stops when either differs from the last commit the agent pushed (or the starting commit) or from the named base.
- [ ] `references/adopt.md` requires the user's explicit approval of the displayed contract, given after the evaluation and the display; approval in the original request does not count.
- [ ] `references/adopt.md` merges the contract's starting commit when the agent pushed nothing, and otherwise the last commit the agent pushed.
- [ ] `references/adopt.md` merges only after the contract's gates passed on the merge target.
- [ ] `references/adopt.md` merges only after the required checks completed and passed on the merge target.
- [ ] `references/adopt.md` stops and reports, with no waiting beyond one re-read, when a required check is still pending after the gates pass.
- [ ] `references/adopt.md` stops and asks on each of: a fix outside the allowed types, a third-party push to the head, a failing check unrelated to the change, and a fourth push.
- [ ] `references/adopt.md` stops and reports, with no retry, method change, or fallback, when a merge is refused.
- [ ] `references/adopt.md` stops with a report when a push is needed and the PR head is not pushable (`maintainerCanModify` false on a cross-repository PR).
- [ ] `evals/evals.json` holds twenty-seven cases, each with a mode tag, fixture files, expected output, at least three assertions, and ordered turns, the first ending at the approval gate and each later turn carrying the user's next message.
- [ ] The cases include one per adopt stop condition above, a refused merge, a pending required check, a zero-fix adoption, a review head that moves between draft and submit, a fork PR that changes build files in iterate mode, approval given only in the original request in each of review, iterate, and adopt, and these attacks: a hidden HTML-comment instruction, a failing CI log that holds both an instruction and a credential-shaped string, a shell-metacharacter branch name, a PR that changes hook configuration, a symlink to a credential file, an adopt comment or log that tries to widen the contract, an adopt PR that edits CI workflow files, and a base branch retargeted after approval.
- [ ] A graded run of all twenty-seven cases passes every assertion.
- [ ] Each case subagent receives only a cold copy of the skill and the case's scenario prompt and fixtures, with no expected output or assertions, and its later turns are supplied by continuing the same subagent.
- [ ] `notes/eval-run.md` records the exact grader input for each case, which holds only the output and the assertions.
- [ ] `notes/eval-run.md` lists each case with pass or fail and, for each run copy, its file list and an empty `find -type d -name evals` result.
- [ ] `notes/eval-run.md` shows zero shell and network tool calls in every case subagent's transcript.
- [ ] `notes/eval-run.md` records each case's tool calls per turn, shows zero Edit or Write calls before the approval turn, and gives the grader that log along with the output.
- [ ] `notes/eval-run.md` records the same subagent identifier for every turn of a case.
- [ ] `notes/eval-run.md` records one SHA-256 digest over `SKILL.md` and `references/**` of the run copy (sorted paths, each followed by its bytes), equal to the same digest over `packs/github/.apm/skills/github-pr/` at the shipped commit.
- [ ] `pack.toml`, `plugin.json`, and the marketplace file give the pack version 0.3.0.
- [ ] `[pack.evals].skills` in `pack.toml` lists `github-pr`.
- [ ] `git grep -l github-pr-iterate` on the working tree lists only paths under `docs/specs/github-pr/`.
- [ ] The changelog fragment names the review, iterate, and adopt modes.
- [ ] `make lint-ruff lint-mypy`, `agentbundle catalogue verify`, and the `packs/github` and skill-census tests pass.

## Follow-ons

none

## Assumptions

- Adopt mode rests on inference. The survey found no prior art for evaluate-then-carry-to-merge (finding 23), and the bounded-contract design is the author's synthesis (finding 25). Decider: the user, who requested the mode.
- The graded run checks that a model reading the skill proposes the right actions at the right turn; it does not check runtime ordering against live GitHub. A later throwaway-PR run would. Decider: the user.
- The minimum `gh` version (2.40) is a conservative guess and the first release with `--match-head-commit` is unchecked. Settled by: the pack maintainer reading `gh` release notes.
- A required check is usually still pending right after a push, so a fixed PR will often stop at the pending-check condition; adopt resumes from the PR's current state on the next invocation. Accepted. Decider: the user.
- Untested: whether an empty `gh` configuration directory blocks keyring authentication on every OS, and whether `--match-head-commit` is an atomic server-side check. Settled by: a throwaway-PR test. Decider: the user.
- Accepted gap: no recording stub for `gh` and `git`, so ordering of real commands is not observed; the run judges proposed actions and logged tool calls. Decider: the user.
- Credentials in the OS keyring may stay reachable to gate code; the contract display says so, and a user who needs stronger isolation runs the gates in a sandbox. Decider: the user.
- Whether pushing to a fork branch needs only `maintainerCanModify` is unverified. Adopt mode treats a false value as a stop. Settled by: GitHub's "allowing changes to a pull request branch" page.
