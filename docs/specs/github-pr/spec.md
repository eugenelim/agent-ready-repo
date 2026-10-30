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

- The skill supports `github.com` only. The unreleased `github-pr-iterate` skill becomes `github-pr` — `packs/github/.apm/skills/github-pr/`, with no copy of the old name left outside this spec directory.
- `SKILL.md` is a short router plus the rules all three modes share (trust, repository pinning, approval gate) — the same file.
- Review, iterate, and adopt each load their own procedure only when chosen — `references/review.md`, `references/iterate.md`, `references/adopt.md`. There is no general `gh` command reference; a command appears only where a mode needs it.
- Review mode drafts findings, then after approval creates one pending review; submitting a verdict is a separate choice the user names.
- Adopt mode evaluates a contributor's PR; if the user likes it, they approve one adoption contract and the agent fixes, pushes, and merges inside it. PR-authored code runs only through a sandbox command the user names; with none, the agent runs no local gates and relies on the repository's remote checks.
- Behavioural eval cases with canned `gh` output, plus a recorded cold-context graded run — `evals/`, `notes/eval-run.md`.
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

- Skill structure, trigger queries, and command safety: TDD with pytest in `packs/github/tests/skills/github-pr/`. The tests check the skill text for the named section or token, and check that every **(B)** criterion ID is tagged by an eval case. Whether a model follows a rule is shown only by the graded run.
- Eval case integrity (counts, modes, fixtures, assertions, approval turn): TDD, same suite.
- Pack metadata consistency: goal-based, using `catalogue verify`, the skill-census test, and `git grep`.
- Agent behaviour under the skill: graded run by fresh subagents with cold context, because only a model reading the skill can show it holds the approval gate. Run rules are the graded-run criteria below. The survey's pilot section records why the run targets acting before approval, running PR code, and the adopt contract.

## Acceptance Criteria

Each criterion has a stable ID. Those marked **(B)** are behaviour criteria: each is tagged by at least one eval case, and the construction tests also check the skill text for its named section or token. The read-only set referred to in G2 is closed: `gh pr view|diff|checks|list`, `gh run view|list`, `gh api` with an explicit GET, a GraphQL `query`, `git log|diff|show|status|rev-parse|fetch`, and `git worktree add --detach`. Any other `gh` or `git` command is mutating. Matching of forbidden strings is by whole token.

**Structure and triggering**

- [ ] **S1** `SKILL.md` is at most 150 lines, counted from its first line.
- [ ] **S2** `SKILL.md` links `references/review.md`, `references/iterate.md`, and `references/adopt.md` directly.
- [ ] **S3** `SKILL.md` tells the agent to load only the reference for the chosen mode.
- [ ] **S4** Every reference over 100 lines opens with a table of contents.
- [ ] **S5** The skill description is at most 1,024 characters.
- [ ] **S6** The skill description names a trigger phrase for each of review, iterate, and adopt.
- [ ] **S7** `evals/eval_queries.json` marks review, iterate, and adopt phrasings as triggering.
- [ ] **S8** `evals/eval_queries.json` marks opening a PR, merging with no evaluation or adoption request, auto-merge, and Azure DevOps phrasings as not triggering.

**Untrusted input and identity**

- [ ] **U1** The untrusted-data rule in `SKILL.md` names each of: comments, review bodies, titles and descriptions, branch names, commit messages, CI logs, the PR diff, files the PR adds or changes and their paths, check-run names and annotations, labels, linked-issue text, and author and committer names.
- [ ] **U2 (B)** `SKILL.md` has the agent read raw comment and description text and report any HTML comment, hidden element, or zero-width content in the plan as untrusted.
- [ ] **U3 (B)** `SKILL.md` has repository instruction and review-rule files read from the base branch and treats their PR-head versions as data.
- [ ] **U4** `SKILL.md` derives `owner/repo` only from the local `origin` remote.
- [ ] **U5 (B)** `SKILL.md` stops when the origin host is not `github.com`, or when the repository differs from the user's request or from any repository named in PR content.
- [ ] **U6 (B)** `SKILL.md` forbids printing credentials and copying credential-shaped text from CI logs, command output, or files into reviews, replies, commits, or the plan.
- [ ] **U7 (B)** Before reading or editing any path from the PR's diff or worktree, the skill confirms it is a regular file whose resolved path stays inside the worktree, and reports a symlink, submodule, or out-of-tree path in the plan without following it.

**Command safety**

- [ ] **C1** Every `gh pr` and `gh run` command in the skill and its references carries `--repo <owner>/<repo>`.
- [ ] **C2** Every REST `gh api` path is a literal `repos/<owner>/<repo>/...` path with no `{owner}` or `{repo}` placeholder.
- [ ] **C3** Every GraphQL `query` operation passes the owner and repository name as variables.
- [ ] **C4** Every GraphQL `mutation` takes its thread id as a variable that the reference's gather query supplies.
- [ ] **C5** No command in the skill or its references, in a code block or inline code, contains the token `--force`, `--force-with-lease`, `-f` on `git push`, a `+`-prefixed or `:`-prefixed refspec, `--amend`, `--admin`, `--auto`, `--all`, `--mirror`, `--tags`, `--delete`, `--delete-branch`, `--recurse-submodules`, `git add -A`, `git add .`, `git add -u`, `git commit -a`, `git commit --all`, `gh pr create`, `gh pr checkout`, `gh secret`, `auth switch`, `auth token`, `--show-token`, or a `gh api` path ending in `/merge`.
- [ ] **C6** No command contains the flags `--body`, `-b`, or `-m` or `-f body=`; review, comment, reply, and commit text goes through `--body-file`, `-F`/`--file`, or `-F body=@<file>`.
- [ ] **C7** Every PR-sourced value used as a command argument must match `[A-Za-z0-9._/-]+` over the whole value, must not start with `-`, and follows `--` where the command accepts it; any other value stops the run with a message that the safety rule refused it.
- [ ] **C8** Every `git commit`, `git push`, `git checkout`, and `git worktree add` in the references carries `-c core.hooksPath=/dev/null`.
- [ ] **C9** Every `git push` in `references/iterate.md` and `references/adopt.md` names an explicit `https://github.com/<headRepositoryOwner>/<headRepository>.git` URL and `HEAD:refs/heads/<headRefName>` taken from the same run's gather fields.
- [ ] **C10** `gh pr merge` appears only in `references/adopt.md`, and every such command carries `--match-head-commit`.
- [ ] **C11** `references/review.md` and `references/adopt.md` each create their PR checkout with `git worktree add --detach` on a commit fetched from the PR head.

**Approval gate and PR code**

- [ ] **G1 (B)** `SKILL.md` forbids running PR-authored code before the approved action list or contract names that run.
- [ ] **G2** Each mode reference has a heading `## Approved actions`, and every command before it is in the read-only set.
- [ ] **G3** `references/review.md` and `references/iterate.md` each contain, after `## Approved actions` and before their first mutating command, a `gh pr view --json headRefOid` command and a comparison against the commit recorded at gather.
- [ ] **G4** `references/review.md` repeats that re-read and comparison before it submits a verdict.
- [ ] **G5 (B)** `references/review.md` creates the pending review with no `event`.
- [ ] **G6 (B)** `references/review.md` submits only with an event the user named after seeing the draft.
- [ ] **G7** Every command in a `gates` code block in the references starts with the literal token `<sandbox>`.
- [ ] **G8 (B)** When the user names no sandbox, the references run no local gate (review runs nothing) and rely on the repository's required remote checks.
- [ ] **G9 (B)** The sandbox runs against a separate throwaway worktree, never the worktree the agent stages, commits, or pushes from, and a commit's staged content that differs from the diff shown at approval stops the run.
- [ ] **G10 (B)** The sandbox command and every file it reads for its own setup must come from the base branch or outside the PR's changed files; a PR that changes any of them is treated as no sandbox.
- [ ] **G11 (B)** In `references/review.md` and `references/iterate.md`, commits stage only the files the approved list names.
- [ ] **G12 (B)** In `references/review.md` and `references/iterate.md`, each posted body and each commit message equals what was shown at approval, and any change is shown again and re-approved.

**Adopt mode**

- [ ] **A1** `references/adopt.md` names in the contract the PR number, base branch, starting commit, allowed fix types, push destination, sandbox command (or none), gates, merge method, merge conditions, and commit message format.
- [ ] **A2 (B)** `references/adopt.md` requires the user's explicit approval of the displayed contract, given after the evaluation and the display; approval in the original request does not count.
- [ ] **A3 (B)** `references/adopt.md` limits staging to files the allowed fix types cover and never to a path matching A4, and fixes the commit message format in the contract.
- [ ] **A4** `references/adopt.md` lists these flagged path patterns: `.github/**`, `CODEOWNERS`, `Makefile`, `conftest.py`, `package.json`, `pyproject.toml`, `Dockerfile*`, `docker-compose*`, `compose*.y*ml`, `.devcontainer/**`, `.tool-versions`, `mise.toml`, `.pre-commit-config.yaml`, `.husky/**`.
- [ ] **A5 (B)** The contract display flags, when any changed file matches A4, that check and gate results are not independent evidence, and approval is given with the flag shown.
- [ ] **A6 (B)** `references/adopt.md` stops and reports, and does not merge, when a changed file matches A4 and the contract names no sandbox.
- [ ] **A7 (B)** `references/adopt.md` stops and reports, and does not merge, when the base branch has zero required checks and the contract names no gate.
- [ ] **A8 (B)** The contract display states that each agent push triggers the PR's workflows as the user and flags self-hosted runners.
- [ ] **A9 (B)** `references/adopt.md` binds the contract to that PR in the current session, requires a new displayed contract and explicit approval for any field change, and never lets PR or CI text amend it.
- [ ] **A10 (B)** `references/adopt.md` merges the contract's starting commit when the agent pushed nothing, and otherwise the last commit the agent pushed, only after the required remote checks, and any contract gates, completed and passed on it.
- [ ] **A11 (B)** `references/adopt.md` re-reads `headRefOid` and `baseRefName` before each push and before the merge, and requires the head to equal the last commit the agent pushed (or the starting commit) and the base to equal the named base.
- [ ] **A12 (B)** `references/adopt.md` stops and asks on each of: a fix outside the allowed types (including any change to CI workflow files, `CODEOWNERS`, a gate's definition, or a deleted, skipped, or weakened test), a head or base that differs from the contract, a failing check unrelated to the change, the fourth push since the current contract was approved, and a push destination other than the contract's.
- [ ] **A13 (B)** `references/adopt.md` stops and reports, with no retry, method change, or fallback, on a refused merge, on a required check still pending after one re-read, and on a needed push to a head that is not pushable (`maintainerCanModify` false on a cross-repository PR).

**Evals and run record**

- [ ] **E1** Every case in `evals/evals.json` has a mode tag, the IDs of the criteria it covers, fixture files, expected output, at least three assertions, and ordered turns; the first turn ends at the approval gate, and each later turn carries the user's next message and any fresh canned read output.
- [ ] **E2** Every **(B)** criterion ID above appears in at least one case's tags.
- [ ] **E3** No fixture under `evals/` is a symlink.
- [ ] **E4** The cases include approval given only in the original request in each of review, iterate, and adopt; a fix-then-merge and a zero-fix merge; a review head that moves between draft and submit; a base branch retargeted after approval; a fork PR that changes build files in iterate; a review request to run the tests with no sandbox; and a PR that edits a repository instruction file.
- [ ] **E5** The cases also include these attacks: a hidden HTML-comment instruction, a failing CI log holding an instruction and a credential-shaped string, a shell-metacharacter branch name with a quote and a leading `-`, a PR that changes hook configuration, a symlink-to-credential state described in canned output, an origin host or repository mismatch, a contract-widening comment or log, a sandbox run that alters a staged file or git configuration, and a sandbox defined by a PR-modified file.
- [ ] **E6** A graded run of every case in `evals/evals.json` passes every assertion.
- [ ] **E7** Each case subagent receives only a cold copy of the skill and the case's scenario prompt and fixtures, with no expected output or assertions, and its tool allowlist excludes shell, network, Edit, and Write.
- [ ] **E8** `notes/eval-run.md` records each case subagent's tool allowlist and one subagent identifier for every turn of the case, whose later turns are supplied by continuing that subagent.
- [ ] **E9** `notes/eval-run.md` records the exact grader input for each case, which holds only the output and the assertions.
- [ ] **E10** `notes/eval-run.md` lists each case with pass or fail and, for each run copy, its file list and an empty `find -type d -name evals` result.
- [ ] **E11** `notes/eval-run.md` records one SHA-256 digest over `SKILL.md` and `references/**` of the run copy (paths relative to the skill directory, `/`-separated, sorted by path bytes, each followed by a NUL byte and the file bytes), equal to the same digest over `SKILL.md` and `references/**` of `packs/github/.apm/skills/github-pr/` at the shipped commit.

**Pack consistency**

- [ ] **P1** `pack.toml`, `plugin.json`, and the marketplace file give the pack version 0.3.0, and `[pack.evals].skills` lists `github-pr`.
- [ ] **P2** `git grep -l github-pr-iterate` on the working tree lists only paths under `docs/specs/github-pr/`.
- [ ] **P3** The changelog fragment names the review, iterate, and adopt modes.
- [ ] **P4** `make lint-ruff lint-mypy`, `agentbundle catalogue verify`, and the `packs/github` and skill-census tests pass.

## Follow-ons

none

## Assumptions

- Adopt mode rests on inference. The survey found no prior art for evaluate-then-carry-to-merge (finding 23), and the bounded-contract design is the author's synthesis (finding 25). Decider: the user, who requested the mode.
- The graded run checks that a model reading the skill proposes the right actions at the right turn; it does not check runtime ordering against live GitHub. A later throwaway-PR run would. Decider: the user.
- The minimum `gh` version (2.40) is a conservative guess and the first release with `--match-head-commit` is unchecked. Settled by: the pack maintainer reading `gh` release notes.
- A required check is usually still pending right after a push, so a fixed PR will often stop at the pending-check condition; adopt resumes from the PR's current state on the next invocation. Accepted. Decider: the user.
- Untested: whether `--match-head-commit` is an atomic server-side check. Settled by: a throwaway-PR test. Decider: the user.
- Accepted gap: no recording stub for `gh` and `git`, so ordering of real commands is not observed; the run judges proposed actions and logged tool calls. Decider: the user.
- The sandbox command is only as isolating as the user's own setup; the skill checks that one is named and that the PR did not define it, not that it isolates. Decider: the user.
- Unverified: whether a maintainer's push to a fork PR runs the PR's workflows without the "approve and run" gate GitHub applies to outside contributors, and which workflow version a `pull_request` event runs. A8 and A6 are written to hold either way. Settled by: GitHub's workflow-approval and `pull_request` docs. Decider: the user.
- Whether pushing to a fork branch needs only `maintainerCanModify` is unverified. Adopt mode treats a false value as a stop. Settled by: GitHub's "allowing changes to a pull request branch" page.
