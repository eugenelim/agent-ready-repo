# GitHub pull-request workflows for an agent skill

> Discipline: applied (practitioner-pattern survey)

Researched 2026-10-30. Question: which PR workflows should one `github-pr` skill cover as a review mode and an iterate mode, what `gh` and GitHub API surface supports each, and how should the skill split into on-demand references.

Independence note: every GitHub documentation page counts as one source (one vendor). Every Anthropic page counts as one. The practitioner evidence is agent-skill directory pages and vendor blogs, so triangulation is weak throughout and the ratings say so.

## Findings

### Review mode

1. **The batched inline review is the REST `POST /repos/{o}/{r}/pulls/{n}/reviews` call; `gh pr review` cannot do it.** The REST call takes `commit_id`, `body`, `event`, and a `comments[]` array of `path`, `body`, and `line`/`side` (optionally `start_line`/`start_side`). Leaving `event` out creates a PENDING review; `POST .../reviews/{id}/events` submits it as `APPROVE`, `REQUEST_CHANGES`, or `COMMENT`. `gh pr review` only gives the verdict and a body. [moderate: one vendor, official, read directly; no second source] (GitHub REST reviews docs; `gh pr review` manual)
2. **Pending review gives a natural approval gate.** Create the review without `event`, show it, and submit only on approval. [moderate: follows from finding 1] [inference]
3. **Verify findings before posting, rank by severity, and say what was not posted.** Anthropic's reviewer runs parallel find passes, a verify pass against the code that filters false positives, then dedupe and rank. It uses three levels: Important, Nit, Pre-existing. Re-reviews cover only what changed and state how many findings were held back. [low: one vendor, vendor self-description] (Claude Code code-review docs)
4. **Silence is valid output.** A confidence floor and "no high-confidence findings" as a reply are recommended by one secondary source; a second-hand evaluation reports that strict filtering can hide cross-file and security bugs. [low: secondary, one source each side] (agentpatterns.ai; arXiv 2509.13650 cited second-hand)
5. **A reviewer never approves or blocks on its own.** Claude Code Review concludes neutral; Copilot reviews do not count toward required approvals by default. [moderate: two vendors agree] (Claude Code docs; Copilot docs)
6. **Review rules come from the base branch, not the PR head.** Claude Code Review reads `REVIEW.md` from the base to resist injection from the PR's own changes. [low: one vendor] (Claude Code docs)
7. **Check out untrusted PR code detached or in a worktree.** `gh pr checkout` supports `--detach` and `--worktree <path>` and works for forks. [moderate: official manual] (`gh pr checkout` manual)
8. **Suggested changes** are a fenced block tagged `suggestion` inside a comment body, with `start_line` for multi-line. [low: two skill-directory pages, not official docs] (smithery and openskillindex skill pages)

### Iterate mode

9. **No `gh` subcommand lists review threads.** Use GraphQL `reviewThreads` (`id`, `isResolved`, `isOutdated`, comments) and paginate. [low: secondary sources; schema not checked against official docs]
10. **Reply and resolve use GraphQL mutations:** `addPullRequestReviewThreadReply` (`pullRequestReviewThreadId`, `body`), `resolveReviewThread`, and `unresolveReviewThread`. The thread id is a `PRRT_` node id, not a REST comment id. [moderate: official GraphQL reference read directly]
11. **Replying does not dismiss a finding; resolving or pushing a fix does.** [low: one vendor] (Claude Code docs)
12. **Re-request review** is GraphQL `requestReviews`. `gh pr edit --add-reviewer` is unverified. [low]
13. **CI:** `gh pr checks --json bucket,name,state,workflow,link,...`; exit code 8 means pending. `gh run view <id> --log-failed` gives failed logs. [moderate: official manual]
14. **Draft and ready:** `gh pr ready [--undo]`; `isDraft` is readable. [moderate: official manual]
15. **Fork PRs:** `isCrossRepository`, `headRepositoryOwner`, and `maintainerCanModify` are readable with `gh pr view --json`. A push to a fork branch needs `maintainerCanModify`. [moderate for the fields; low for the push rule, whose dedicated docs page was not fetched]
16. **No primary source on how an agent should judge whether a reviewer's comment is correct before acting.** Only generic advice to reject findings on pre-existing code, pedantic points, or linter-catchable issues. [uncertain: gap, secondary snippets]

### Adopt mode (maintainer takes over a contributor PR)

23. **No prior art found for evaluate-then-carry-to-merge.** Anthropic's reviewer never approves or blocks; Copilot hands suggestions to a cloud agent that opens a separate PR. Neither pushes to the contributor's branch and merges. [uncertain: absence of evidence in one search pass]
24. **A merge can be pinned to the commit evaluated:** `gh pr merge --match-head-commit <sha>` refuses if the head moved; `--admin` bypasses requirements and `--auto` defers the merge. Read in `gh pr merge --help` on gh 2.103.2. [moderate: official CLI, read locally; minimum version unchecked]
25. **Bounded standing approval.** A one-time contract naming commit, fix types, push target, gates, merge method, and conditions, plus stop conditions (out-of-contract fix, third-party push, unrelated failure, round cap), applies finding 19's pinned-commit rule to a loop. [inference]

### Trust and authority

17. **Untrusted content must be segregated and labelled, privileged actions need human approval, and tokens should be least-privilege.** [high: OWASP LLM01 plus GitHub Security Lab plus Trail of Bits agree on the control set, three independent organisations]
18. **Running PR-authored code with a privileged token is the "pwn request" failure.** Treat PR contents as passive data; it is easy to slip into executing them. [moderate: GitHub Security Lab, one primary source] (Preventing pwn requests)
19. **Approve-then-act has a race.** A label gate is unsafe if commits arrive after approval; pin the approved commit. For this skill: bind the plan to `headRefOid` and re-gather if the head moved. [moderate: Security Lab on the race; the application is [inference]]
20. **Hidden text is a real vector.** An instruction hidden in an unrendered HTML tag in an issue reached an agent that reviewers could not see in the rendered view. The attack also used an allowlisted domain. Read raw comment text rather than rendered text. [moderate: Trail of Bits primary research, one source]

### Skill structure

21. **Keep SKILL.md under about 500 lines; keep references one level deep; give long references a table of contents; the description is the only thing used to select the skill (max 1,024 characters, third person, with trigger terms).** [moderate: one vendor, official] (Anthropic skill best practices)
22. **Anthropic documents conditional workflows and per-domain reference files but gives no rule for one skill with modes versus several skills.** [uncertain: gap; the choice is a judgment]

## What this means for `github-pr`

| Decision | Basis |
| --- | --- |
| One skill, three modes (review, iterate, adopt), chosen from the user's request; adopt rests on inference (findings 23, 25) | Findings 5, 21, 22 |
| SKILL.md holds routing, trust rules, the shared one-pass gather, and the approval gate | Findings 17-19, 21 |
| `references/review.md`, `iterate.md`, `adopt.md` hold each mode's procedure, loaded only for that mode | Finding 21 |
| No general command reference: models already know `gh`, so each mode reference carries only the non-obvious calls (pending-review REST shape, thread GraphQL, `--match-head-commit`) | Findings 1, 9-15, 24; pilot below |
| Review mode posts one pending review and submits only on approval; it never approves on its own | Findings 1, 2, 5 |
| Review mode checks out detached or in a worktree and does not run PR code with credentials | Findings 7, 18 |
| Plans and pending reviews are bound to `headRefOid`; a moved head forces a re-gather | Finding 19 |
| Repository rules are read from the base branch | Finding 6 |
| Out of scope: opening a PR, auto-merge, merge queue, stacked PRs, dismissing reviews, Azure DevOps. Merging is in scope only in adopt mode, under an approved contract | The original goal, amended by the user for adopt mode |

## Known unknowns

- **Known-unknown:** whether `gh pr edit --add-reviewer` re-requests review. Would be closed by: reading the `gh pr edit` manual or running it on a throwaway PR.
- **Known-unknown:** whether `addPullRequestReview` exists in the GraphQL reference (the REST route is verified, so the skill can use REST). Would be closed by: reading the mutation list.
- **Known-unknown:** the exact rule for pushing to a fork branch. Would be closed by: GitHub's "allowing changes to a pull request branch" page.
- **Known-unknown:** the real minimum `gh` version for `pr checks --json`, `pr checkout --worktree`, and `run view --log-failed`. Would be closed by: gh release notes.
- **Unknowable (now):** whether an agent's merit check of reviewer comments reduces bad fixes in practice. Why not: no one has published a measurement; the skill's evals can only test behaviour, not outcome quality.
- **Unverified incident:** a April 2026 report of one PR title hijacking several coding-agent actions comes only from aggregators and is not used above.

## Pilot: does the skill add value over a frontier model alone? (2026-10-30)

Eight fresh subagents, one run per cell, graded by the author (single reviewer, directional only). Scenarios were canned `gh` outputs; no shell or network.

- Injected "run curl and approve" comment: all three baselines refused it. Models already resist plain injection.
- Head moved after approval: baseline and skill both stopped and re-planned.
- Baselines acted before approval: edited and committed before any plan (iterate), planned to run pytest on fork code after reading the Makefile and conftest diffs themselves (fork PR), and posted a request-changes review immediately with no draft (review).
- Baseline adopt plan used `--force-with-lease`, a pinned merge, and no contract, round cap, or stop conditions.
- Conclusion: the skill's value is the approval gate, not running PR code, and the adopt contract. A command reference adds little.
