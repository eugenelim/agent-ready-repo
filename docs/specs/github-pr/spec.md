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
- Seventeen behavioural eval cases with canned `gh` output, plus a recorded cold-context graded run — `evals/`, `notes/eval-run.md`.
- Pack metadata, README, journey, how-to guide, census, and changelog fragment describe all three modes — `packs/github/`, `guides/github/`, `docs/product/changelog.d/`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Three modes change what the pack offers | `packs/github/README.md`, `guides/github/how-to/` | pack maintainer | README and guide name all three modes and the approval rule | Both read as one story |
| Journey | Pack journey lists skills and gates | `packs/github/JOURNEY.md`, generated `web/src/content/journeys/github.md` | pack maintainer | `build-site --journeys-only` leaves no diff | Generated file matches source |
| Interface compatibility | Skill name and pack skill list change | `pack.toml`, `plugin.json`, marketplace file, skill census | pack maintainer | `catalogue verify` ok; census test green | Versions agree at 0.3.0 |
| Release history | Consumer-visible capability | `docs/product/changelog.d/66c8f467-39f7-4063-8aac-d8d60d42c4c2.md` (rewritten) | pack maintainer | `tools/changelog.py validate` ok | Fragment covers review, iterate, and adopt |
| Reusable learning | Eval method and its pilot result are reusable | `docs/specs/github-pr/notes/eval-run.md` | implementer | Recorded run with isolation evidence | Note states case results and grader inputs |
| Current architecture, decision rationale, operations | Skill content only; no new module, dependency, or service | none | n/a | n/a | n/a |

## Agent Rules

Rules for the agent building this change. How the shipped skill behaves is stated by the criteria below.

### Always do

- Update the pack's eval harness and version together with any change under `.apm/`, per `packs/AGENTS.md`.
- Record the build against the survey in `notes/github-pr-workflows-survey.md`; a command the survey marks unverified stays out of the skill.
- Rerun the graded eval run after any change to `SKILL.md` or a reference.

### Ask first

- Adding a mode beyond review, iterate, and adopt (opening a PR, auto-merge, merge queue, stacking).
- Any new dependency or any script under the skill.
- Raising the pack version beyond 0.3.0.

### Never do

- Add a new top-level directory, a new pack, or Azure DevOps support.
- Run `gh` against a real repository while building or evaluating this change, other than read-only version and help output.
- Touch the unrelated `repo-governance` journey file that `build-site` also regenerates.

## Testing Strategy

- Skill structure, trigger queries, and command safety: TDD with pytest in `packs/github/tests/skills/github-pr/`, because each rule is a string-checkable invariant over the skill text and eval files.
- Eval case integrity (counts, modes, fixtures, assertions, approval turn): TDD, same suite.
- Pack metadata consistency: goal-based, using `catalogue verify`, the skill-census test, and `git grep`.
- Agent behaviour under the skill: graded run by fresh subagents with cold context, because only a model reading the skill can show it holds the approval gate. Each case states the turn at which approval is or is not given; the grader sees only the output and the assertions and judges only actions proposed before that turn. A pilot on 2026-10-30 found the models already resist injected text and pin pushes without the skill, so the run is aimed at acting before approval, running PR code, and the adopt contract.

## Acceptance Criteria

- [ ] `SKILL.md` is at most 150 lines, counted from its first line.
- [ ] `SKILL.md` links `references/review.md`, `references/iterate.md`, and `references/adopt.md` directly.
- [ ] `SKILL.md` tells the agent to load only the reference for the chosen mode.
- [ ] Every reference over 100 lines opens with a table of contents.
- [ ] The skill description is at most 1,024 characters.
- [ ] The skill description names a trigger phrase for each of review, iterate, and adopt.
- [ ] `evals/eval_queries.json` marks review, iterate, and adopt phrasings as triggering.
- [ ] `evals/eval_queries.json` marks opening a PR, merging with no evaluation or adoption request, auto-merge, and Azure DevOps phrasings as not triggering.
- [ ] The untrusted-data rule names each of: comments, review bodies, titles and descriptions, branch names, commit messages, CI logs, the PR diff, and files the PR adds or changes.
- [ ] Every `gh` command in the skill and its references carries `--repo <owner>/<repo>` or a repository-qualified API path.
- [ ] No command block contains `--force`, `--force-with-lease`, `--amend`, `--admin`, `--auto`, `gh pr create`, `auth switch`, or `auth token`.
- [ ] `references/review.md` contains the commands that create a pending review and submit it; `references/iterate.md` contains those that push, reply to a thread, and resolve a thread; `references/adopt.md` contains those that push and merge.
- [ ] In each mode reference, every command named in the previous criterion appears after that mode's approval step.
- [ ] Each mode reference states a re-read of the PR head, equal to the recorded commit, immediately before its first mutating command.
- [ ] `gh pr merge` appears only in `references/adopt.md`.
- [ ] Every `gh pr merge` command carries `--match-head-commit`.
- [ ] Review mode creates the pending review without an event, and submits it only with an event the user named after seeing the draft.
- [ ] `references/review.md` and `references/adopt.md` check out PR code detached or in a worktree.
- [ ] The adoption contract names the starting commit, allowed fix types, push target, gates to run (stated as running PR code), merge method, and merge conditions.
- [ ] Adopt mode requires the user's explicit approval of the displayed contract, given after the evaluation and the display; approval in the original request does not count.
- [ ] Adopt mode merges only the last commit the agent itself pushed, after the contract's gates and the required checks completed and passed on that exact commit, with the head re-read equal to it.
- [ ] Adopt mode stops and asks on each of: a fix outside the allowed types, a third-party push to the head, a failing check unrelated to the change, and the end of the third push round.
- [ ] Adopt mode stops and reports, with no retry, method change, or fallback, when a merge is refused.
- [ ] Adopt mode stops with a report when the PR head is not pushable (`maintainerCanModify` false on a cross-repository PR).
- [ ] `evals/evals.json` holds seventeen cases, each with a mode tag, fixture files, expected output, at least three assertions, and the turn after which approval is or is not given.
- [ ] The cases include one per adopt stop condition above, one for a refused merge, one for approval given only in the original request in review mode, and one for the same in adopt mode.
- [ ] A graded run of all seventeen cases by fresh subagents, each given only a cold copy of the skill and its case, passes every assertion; the grader receives only the output and the assertions.
- [ ] `notes/eval-run.md` lists each case with pass or fail and, for each run copy, the kept files and an empty `find -type d -name evals` result.
- [ ] `notes/eval-run.md` shows zero shell and network tool calls in every case subagent's transcript.
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
- Whether pushing to a fork branch needs only `maintainerCanModify` is unverified. The skill treats a false value as replies-only in review and iterate and as a stop in adopt. Settled by: GitHub's "allowing changes to a pull request branch" page.
