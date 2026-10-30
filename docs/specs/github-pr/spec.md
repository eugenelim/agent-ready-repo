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
- Adopt mode evaluates a contributor's PR; if the user likes it, they approve one adoption contract and the agent fixes, pushes, and merges inside it. PR-authored code runs only through a sandbox command the user names; with none, the agent runs no local gates and relies on the repository's remote checks.
- Twenty-eight behavioural eval cases with canned `gh` output, plus a recorded cold-context graded run — `evals/`, `notes/eval-run.md`.
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

- Skill structure, trigger queries, and command safety: TDD with pytest in `packs/github/tests/skills/github-pr/`. The tests check the skill text for the named section or token, and check that every behaviour criterion is tagged by an eval case. Whether a model follows a rule is shown only by the graded run.
- Eval case integrity (counts, modes, fixtures, assertions, approval turn): TDD, same suite.
- Pack metadata consistency: goal-based, using `catalogue verify`, the skill-census test, and `git grep`.
- Agent behaviour under the skill: graded run by fresh subagents with cold context, because only a model reading the skill can show it holds the approval gate. Run rules are the graded-run criteria below. The survey's pilot section records why the run targets acting before approval, running PR code, and the adopt contract.

## Acceptance Criteria

A *mutating command* is any `gh` or `git` call that writes to the remote or to git history. At minimum: `gh api` whose effective method is not GET, however spelled (`-X`, `--method`, `--input`, or `-f`/`-F` on a REST path); any GraphQL `mutation`; `git commit`, `git push`, `git tag`; `gh pr merge`, `ready`, `edit`, `comment`, `review`, `close`, `reopen`; `gh issue comment`; `gh run rerun`, `cancel`; `gh workflow run`. `gh pr checkout` is local and excluded. A *behaviour criterion* is one worded as what a mode does; each is backed by at least one eval case, and the construction tests check the skill text for the named section or token.

**Structure and triggering**

- [ ] `SKILL.md` is at most 150 lines, counted from its first line.
- [ ] `SKILL.md` links `references/review.md`, `references/iterate.md`, and `references/adopt.md` directly.
- [ ] `SKILL.md` tells the agent to load only the reference for the chosen mode.
- [ ] Every reference over 100 lines opens with a table of contents.
- [ ] The skill description is at most 1,024 characters and names a trigger phrase for each of review, iterate, and adopt.
- [ ] `evals/eval_queries.json` marks review, iterate, and adopt phrasings as triggering.
- [ ] `evals/eval_queries.json` marks opening a PR, merging with no evaluation or adoption request, auto-merge, and Azure DevOps phrasings as not triggering.

**Untrusted input and identity**

- [ ] The untrusted-data rule in `SKILL.md` names each of: comments, review bodies, titles and descriptions, branch names, commit messages, CI logs, the PR diff, files the PR adds or changes and their paths, check-run names and annotations, labels, linked-issue text, and author and committer names.
- [ ] `SKILL.md` has the agent read raw comment and description text and report any HTML comment, hidden element, or zero-width content in the plan as untrusted.
- [ ] `SKILL.md` has repository instruction and review-rule files read from the base branch and treats their PR-head versions as data.
- [ ] `SKILL.md` supports `github.com` only: it derives `owner/repo` once from the local `origin` remote, confirms it against the user's request, never takes it from PR content, and stops when the host is not `github.com` or the repository does not match.
- [ ] `SKILL.md` forbids printing credentials and copying credential-shaped text from CI logs, command output, or files into reviews, replies, commits, or the plan.
- [ ] Before reading or editing any path from the PR's diff or worktree, the skill confirms it is a regular file whose resolved path stays inside the worktree, and reports a symlink, submodule, or out-of-tree path in the plan without following it.

**Command safety**

- [ ] Every `gh pr` and `gh run` command in the skill and its references carries `--repo <owner>/<repo>`.
- [ ] Every REST `gh api` path is a literal `repos/<owner>/<repo>/...` path with no `{owner}` or `{repo}` placeholder.
- [ ] Every GraphQL `query` operation passes the owner and repository name as variables, and every GraphQL `mutation` takes its thread id as a variable that the reference's gather query supplies.
- [ ] No command in the skill or its references, in a code block or inline code, contains `--force`, `--force-with-lease`, `git push -f`, a `+`-prefixed refspec, `--amend`, `--admin`, `--auto`, `--all`, `--mirror`, `--tags`, `--delete`, a `:`-prefixed refspec, `--recurse-submodules`, `git add -A`, `git add .`, `gh pr create`, `gh secret`, `auth switch`, `auth token`, `--show-token`, or a `gh api` path ending in `/merge`.
- [ ] Every review, comment, reply, and commit message is passed through a file or stdin, and no command contains `--body "`, `-m "`, or `-f body=`.
- [ ] Every PR-sourced value used as a command argument matches `[A-Za-z0-9._/-]+`, does not start with `-`, and follows `--` where the command accepts it; any other value stops the run.
- [ ] The references state that repository hooks are disabled for the agent's own checkout, commit, and push, naming `core.hooksPath`.
- [ ] Every `git push` in `references/iterate.md` and `references/adopt.md` names an explicit `https://github.com/<headRepositoryOwner>/<headRepository>.git` URL and `HEAD:refs/heads/<headRefName>` taken from the same run's gather fields.
- [ ] `gh pr merge` appears only in `references/adopt.md`, and every such command carries `--match-head-commit`.
- [ ] Every `gh pr checkout` in `references/review.md` and `references/adopt.md` carries `--detach` or `--worktree`, and each file contains at least one.

**Approval gate**

- [ ] `SKILL.md` forbids running PR-authored code before the approved action list or contract names that run.
- [ ] Every command in `references/iterate.md` and `references/adopt.md` that executes PR-authored code is prefixed by the user's named sandbox command; when none is named, those references run no local gates and rely on the repository's required remote checks.
- [ ] Each mode reference has a heading `## Approved actions`, and every mutating command in that reference appears after it.
- [ ] `references/review.md` and `references/iterate.md` each state a re-read of the PR head, required equal to the commit recorded at gather, before their first mutating command.
- [ ] Commits stage only the files the approved list names; each posted body and each commit message equals what was shown at approval, and any change is shown again and re-approved.
- [ ] `references/review.md` creates the pending review with no `event`, and submits it only with an event the user named after seeing the draft, after a second head re-read against the recorded commit.

**Adopt mode**

- [ ] `references/adopt.md` names in the contract the PR number, base branch, starting commit, allowed fix types, push destination, sandbox command (or none), gates, merge method, merge conditions, and commit message format.
- [ ] `references/adopt.md` requires the user's explicit approval of the displayed contract, given after the evaluation and the display; approval in the original request does not count.
- [ ] `references/adopt.md` limits staging to files the allowed fix types cover and never to a path flagged in the next criterion.
- [ ] `references/adopt.md` lists every PR-changed file in CI configuration, `CODEOWNERS`, test harness, build, or dependency-install configuration, and the contract display flags that check and gate results are then not independent evidence; approval is given with the flag shown.
- [ ] `references/adopt.md` reports zero required checks on the base branch in the contract display and does not treat it as checks passed.
- [ ] `references/adopt.md` binds the contract to that PR in the current session, requires a new displayed contract and explicit approval for any field change, and never lets PR or CI text amend it.
- [ ] `references/adopt.md` merges the contract's starting commit when the agent pushed nothing, and otherwise the last commit the agent pushed, only after the required remote checks, and any contract gates, completed and passed on it.
- [ ] `references/adopt.md` re-reads `headRefOid` and `baseRefName` before each push and before the merge, and requires the head to equal the last commit the agent pushed (or the starting commit) and the base to equal the named base.
- [ ] `references/adopt.md` stops and asks on each of: a fix outside the allowed types (including any change to CI workflow files, `CODEOWNERS`, a gate's definition, or a deleted, skipped, or weakened test), a head or base that differs from the contract, a failing check unrelated to the change, a fourth push, and a push destination other than the contract's.
- [ ] `references/adopt.md` stops and reports, with no retry, method change, or fallback, on a refused merge, on a required check still pending after one re-read, and on a needed push to a head that is not pushable (`maintainerCanModify` false on a cross-repository PR).

**Evals and run record**

- [ ] `evals/evals.json` holds twenty-eight cases, each with a mode tag, the criterion groups it covers, fixture files, expected output, at least three assertions, and ordered turns; the first turn ends at the approval gate, and each later turn carries the user's next message and any fresh canned read output.
- [ ] Every behaviour criterion above is covered by at least one case's tags, and no fixture under `evals/` is a symlink.
- [ ] The cases include one per adopt stop condition and stop-and-report condition above, a fix-then-merge, a zero-fix merge, a no-sandbox adoption, a contract-widening comment or log, an adopt PR that edits CI workflow files, and approval given only in the original request in each of review, iterate, and adopt.
- [ ] The cases also include a review head that moves between draft and submit, a hidden HTML-comment instruction, a symlink-to-credential state described in canned output, a fork PR that changes build files in iterate, a failing CI log holding an instruction and a credential-shaped string, a shell-metacharacter branch name with a quote and a leading `-`, and a PR that changes hook configuration.
- [ ] A graded run of all twenty-eight cases passes every assertion.
- [ ] Each case subagent receives only a cold copy of the skill and the case's scenario prompt and fixtures, with no expected output or assertions, and its later turns are supplied by continuing the same subagent.
- [ ] `notes/eval-run.md` records the exact grader input for each case, which holds only the output and the assertions, and gives the grader each case's tool-call log.
- [ ] `notes/eval-run.md` records each case subagent's tool allowlist and per-turn tool calls, with zero shell, network, Edit, or Write calls before the approval turn, and the same subagent identifier for every turn.
- [ ] `notes/eval-run.md` lists each case with pass or fail and, for each run copy, its file list and an empty `find -type d -name evals` result.
- [ ] `notes/eval-run.md` records one SHA-256 digest over `SKILL.md` and `references/**` of the run copy (paths relative to the skill directory, `/`-separated, each followed by a NUL byte and the file bytes, in sorted order), equal to the same digest over `packs/github/.apm/skills/github-pr/` at the shipped commit.

**Pack consistency**

- [ ] `pack.toml`, `plugin.json`, and the marketplace file give the pack version 0.3.0, and `[pack.evals].skills` lists `github-pr`.
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
- Untested: whether `--match-head-commit` is an atomic server-side check. Settled by: a throwaway-PR test. Decider: the user.
- Accepted gap: no recording stub for `gh` and `git`, so ordering of real commands is not observed; the run judges proposed actions and logged tool calls. Decider: the user.
- The sandbox command is only as isolating as the user's own setup; the skill checks that one is named, not that it isolates. Decider: the user.
- Whether pushing to a fork branch needs only `maintainerCanModify` is unverified. Adopt mode treats a false value as a stop. Settled by: GitHub's "allowing changes to a pull request branch" page.
