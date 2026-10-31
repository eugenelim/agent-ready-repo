# Plan: github-pr

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** sibling skills `packs/github/.apm/skills/github-refresh/` and `github-brief-intake/` (frontmatter, manifest, evals layout); `tests/roster/test_skill_census.py`; existing construction test `packs/github/tests/skills/github-pr-iterate/`; deviation: a skill with `references/` loaded per mode, which the github pack does not yet have, grounded in the survey notes.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (contract, scope and non-goals, durable outputs, agent rules, testing
> strategy, acceptance criteria, accepted risk) or its `Terminal Intent`. A change
> to tasks, tests, stubs, design, or approach needs none: the controller makes it
> as an in-envelope working-plan change while no execution attempt is open, and
> the run continues with every finished task still finished. Execution
> observations belong in `docs/specs/<feature>/notes/verification-ledger.md` (or
> the adopter's equivalent). A genuine error in a protected section follows the
> controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads. `Design`, `Approach`, `Grounding` and `Risks` are working
> material the controller corrects in place, before or after approval, while no
> attempt is open. After approval, grounding for a seam or design means recorded
> as `implementation-discovered`, and each later correction, is a controller edit
> of the plan's `## Design (LLD)`, never a ledger line; a settled design decision
> that execution falsified is a plan error the owner agrees to, corrected the same
> way unless it reaches a protected section. A TDD task's `stub` fence is likewise
> written by the controller at task start, not carried in the approved plan.
> Treating working material as contract is how a review spends a round on prose
> no gate consumes — the measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

<!-- Existing plans without this field remain valid. Treat its absence as a
named assurance gap during structural review, not a universal lint failure. -->

<!-- **Durable-plan fill.** This template is the implementation and verification
strategy for a durable delivery slice. Fill Approach, Constraints, Risks,
Design, Tasks, and Changelog to the depth the durable work requires. Its sibling
spec is the durable behavior contract. Eligible direct-light work does not
create this artifact. -->

## Approach

Replace the drafted `github-pr-iterate` with a thin `github-pr`: a router `SKILL.md` carrying the approval gate and trust rules, and one short reference per mode. The riskiest part is the approval model, especially adopt mode's merge pin, so the construction tests pin it first and the skill text is written to meet them. Evals follow, then pack metadata and docs, then a cold-context graded run whose failures send the cause back to the skill text (T1) and rerun.

## Constraints

`packs/AGENTS.md` applies. Pack tests may not read `guides/`. The survey in `notes/github-pr-workflows-survey.md` grounds command names; adopt mode rests on inference and the spec records that.

## Construction tests

**Integration tests:** `agentbundle catalogue verify`, the skill-census test, `make lint-ruff lint-mypy`.
**Manual verification:** the graded run in T5.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User-facing promise: README, guide | T3 | README and guide diff | all three modes named |
| Journey and generated web copy | T3 | `build-site --journeys-only` diff limited to the github journey | generated file matches source |
| Interface compatibility: manifests, census | T3 | `catalogue verify`, census test | versions agree at 0.3.0 |
| Release history: changelog fragment | T3 | `tools/changelog.py validate` | fragment covers all three modes |
| Reusable learning: eval run record | T5 | `notes/eval-run.md` | grader inputs and isolation evidence present |

## Design (LLD)

### Design decisions

- **One skill, three modes; mode chosen from the request, one question if unclear.** `SKILL.md` holds routing, trust rules, repository pinning, and the approval gate; each mode reference holds only its procedure. Owned by: T1. Rests on: the description is the only selection signal, so all three modes' triggers sit in one description.
- **The approval gate binds an action list to a head commit.** Each mode records `headRefOid` at gather time and re-reads it before its first mutating command. Owned by: T1. Rests on: `headRefOid` is readable (survey finding on `gh pr view --json`).
- **Review uses the REST pending review.** `POST .../pulls/{n}/reviews` without `event` creates it; submit is a separate call. Owned by: T1. Basis: survey findings 1 and 2.
- **Iterate replies and resolves through GraphQL thread mutations.** Owned by: T1. Basis: survey findings 9 and 10.
- **Adopt is a bounded standing approval.** The contract in `references/adopt.md` is shown after evaluation and approved explicitly; the adopt criteria in the spec are its definition. PR-authored code runs only through a sandbox command the user names, because prose controls cannot isolate it from the user's credentials and git config (security review). Without one, adopt relies on remote required checks. Owned by: T1. Basis: survey findings 19, 24, 25; `gh pr merge --help` on gh 2.103.2.
- **No `gh` command reference and no helper script.** Models already know `gh` (pilot); a script would add a dependency surface (cut-before-adding rung 1). Owned by: T1.
- **Evals are scripted turns.** Each case holds ordered turns. Turn 1 is the request plus canned read outputs and ends at the approval gate; later turns carry the user's next message and are sent by continuing the same subagent, so the model's own turn-1 output is judged for acting before approval. Subagents get no shell: the record counts tool calls per transcript. This checks that a model reading the skill proposes the right actions, not runtime ordering. Owned by: T2, T5.

## Tasks

### T1: the three-mode skill meets its structural and safety contract
**Depends on:** none
**Touches:** packs/github/.apm/skills/github-pr-iterate/**, packs/github/.apm/skills/github-pr/**, packs/github/tests/skills/github-pr-iterate/**, packs/github/tests/skills/github-pr/**
**Tests:**
- TDD, pytest over the skill text, at `packs/github/tests/skills/github-pr/test_github_pr.py`, one test group per criterion prefix S1-S6, U, C, G, A. The `## Approved actions` heading marks where each mode test starts measuring, and the closed read-only set in the spec decides which commands count as mutating. Only U1 reads the untrusted-data rule's own section of `SKILL.md`; the other U tests read all of `SKILL.md`, and U7 also the references.
**Approach:** `git mv` the skill directory and the test folder to the new name, write the tests red, then the skill text.
**Done when:** the T1 test file is green and `git grep -l github-pr-iterate` outside this spec directory returns nothing for the skill and test paths.

### T2: eval cases, fixtures, and trigger queries exist for all three modes
**Depends on:** T1
**Touches:** packs/github/.apm/skills/github-pr/evals/**, packs/github/tests/skills/github-pr/test_evals.py
**Tests:**
- TDD, pytest at `packs/github/tests/skills/github-pr/test_evals.py`: S7, S8, and E1 to E5; the E1 test reads each case's `turns` field and its `covers` tags.
**Approach:** each case is tagged with criterion IDs, and E2 requires every **(B)** ID to appear. The case list is spec E4 and E5, plus one case per remaining **(B)** criterion those lists leave untagged, found by running the E2 test red first. Fixtures are canned `gh` outputs under `evals/files/<case>/`, contain no symlinks, and later turns carry fresh canned read output where a re-read matters.
**Done when:** the T2 test file is green.

### T3: pack metadata, docs, census, and changelog describe all three modes
**Depends on:** T1
**Touches:** packs/github/pack.toml, packs/github/.claude-plugin/plugin.json, packs/github/README.md, packs/github/JOURNEY.md, packs/github/.apm/skills/github-pr/manifest.json, guides/github/**, web/src/content/journeys/github.md, packs/agent-skill-engineering/tests/fixtures/skill-census.json, .claude-plugin/marketplace.json, docs/product/changelog.d/66c8f467-39f7-4063-8aac-d8d60d42c4c2.md, Makefile, tools/lint-ci-parity.py
**Tests:**
- Goal-based: the `Makefile` github batch and `tools/lint-ci-parity.py` name `packs/github/tests/skills/github-pr/` where they named the old suite; `JOURNEY.md` adds no human gate (the shipped journey editorial ledger pins them), folding the new approvals into the existing confirm gate; `python3 tools/lint-pack-test-boundary.py` and `tools/test_journey_editorial_decisions.py` pass; `catalogue verify` ok, skill-census test green, `build-site --journeys-only` changes only the github journey (restore the regenerated `repo-governance` file), `tools/changelog.py validate` ok, the fragment text names review, iterate, and adopt.
**Done when:** those checks pass.

### T4: repository gates are green after the rename
**Depends on:** T2, T3
**Touches:** none
**Tests:**
- Goal-based: `pytest packs/github tests/roster/test_skill_census.py`, `agentbundle catalogue verify`, `python3 tools/lint-pack-test-boundary.py`, `python3 tools/lint-ci-parity.py`, `make lint-ruff lint-mypy`, `git grep -l github-pr-iterate` lists only `docs/specs/github-pr/`.
**Done when:** those commands exit 0 and the grep output is as stated.

### T5: a cold-context graded run passes every assertion
**Depends on:** T4
**Touches:** docs/specs/github-pr/notes/eval-run.md
**Tests:**
- Visual / manual QA: the graded-run and run-record criteria, executed by the controller with cold copies of the skill and no `evals/` directory, one fresh subagent per case, each `SubagentHandback` extracted verbatim.
**Approach:** any change to the skill text after a run sends the work back to T1 and reruns T4 and every case.
**Done when:** `notes/eval-run.md` shows every case passing with the isolation evidence and matching digest.

### T6: review findings are repaired in the skill text and docs
**Depends on:** T5
**Touches:** packs/github/.apm/skills/github-pr/SKILL.md, packs/github/.apm/skills/github-pr/references/**, packs/github/.apm/skills/github-pr/evals/**, packs/github/tests/skills/github-pr/**, guides/github/how-to/work-through-a-github-pull-request.md, docs/product/changelog.d/66c8f467-39f7-4063-8aac-d8d60d42c4c2.md, packs/agent-skill-engineering/tests/fixtures/skill-census.json
**Tests:**
- Goal-based: extend `packs/github/tests/skills/github-pr/test_github_pr.py` and `test_evals.py` where a repair is checkable in the skill text, then the T4 commands stay green.
**Approach:** repair each supported finding, keeping every command in the closed read-only set and every approval rule intact.
- F1: each mode's gather also reads the raw PR description (`body`); the eval fixtures supply that same command's output.
- F2: iterate resolves only threads the approved plan names for resolution.
- F3: the approved-edit record and the staged record are produced in the same comparable form, so a faithful run matches and an extra staged byte does not.
- F4: each gates section names the exact commit it exports and checks, for a fix commit and for adopt's starting commit with no fix.
- F5: review's head-moved path says what happens to the existing pending review, under approval, before a new one is created.
- F6: the config hash set is built from the files git loads on this machine, not a fixed `/etc/gitconfig`.
- F7: adopt detects a merge-queue or auto-merge outcome before merging, or reports the leftover state and leaves any undo to user approval.
- F8: the guide says submitting is a separate choice the user names, matching review mode.
- F10: the changelog fragment names review, iterate, and adopt.
- S1: `allowed-tools` no longer pre-approves unscoped `Bash`, so the host permission layer still prompts for mutating commands.
- S2: name one read-only way to read `origin`'s URL, add it to the closed read-only set, and require the host to equal `github.com` exactly for HTTPS and SSH forms.
- S3: path-safety checks run on the absolute `<worktree>/<path>` that is later read or edited, compared with the resolved `<worktree>` root.
- S4: the contract display flags self-hosted runners in the base and PR-head versions of every workflow a push would trigger.
- S5 (non-material): the read-only checkout and diff do not apply PR-selected filter, LFS, textconv, external-diff or submodule behaviour, or the gap is named in `SKILL.md`.
The controller handles F9 (eval record wording and read targets) and the eval rerun after this task, outside any attempt.
**Done when:** every item above is visible in the shipped text, the T4 commands exit 0, and no file under `docs/specs/github-pr/` changed.

### T7: round-2 review findings are repaired in the skill text, cases, and docs
**Depends on:** T6
**Touches:** packs/github/.apm/skills/github-pr/SKILL.md, packs/github/.apm/skills/github-pr/references/**, packs/github/.apm/skills/github-pr/evals/**, packs/github/tests/skills/github-pr/**, guides/github/how-to/work-through-a-github-pull-request.md, packs/github/README.md
**Tests:**
- Goal-based: extend `packs/github/tests/skills/github-pr/test_github_pr.py` and `test_evals.py` where a repair is checkable, then the T4 commands stay green. Name new tests for the repair item, not for a spec criterion ID.
**Approach:** repair each supported finding; the controller amends the spec's closed read-only set to admit `git remote get-url origin` (owner-approved) and handles the eval record and survey notes after this task.
- B2/X1: before a sandbox run, record presence or absence and the hash of every file git would load for this worktree, whether or not it exists yet: the system, global, and XDG config files, every include target, the worktree `.git` file, and `<git-dir>/commondir`, plus the repository `config`, `config.worktree`, `hooks/*`, and `info/*`. Any change, creation, or deletion stops the run before the next git command.
- B4: after the sandbox run, each gates section says what stops the run: any staged path outside the approved list, or any staged byte that differs from the recorded edit hash, or HEAD moved, stops the run with no unstage, reset, commit, or push. Rewrite the `iterate-sandbox-alters-staged` and `adopt-sandbox-alters-staged` cases so their scripts reach the sandbox step in the skill's real order (the fix commit is made before the gate) and assert "does not push or amend and makes no further commit".
- B3: give `adopt-sandbox-alters-staged` an approval the agent can accept as displayed, including the merge method, so it reaches the sandbox step.
- X2/B6: add `-c filter.lfs.smudge= -c filter.lfs.process= -c filter.lfs.required=false` to the pre-approval `git worktree add --detach` and `git archive` commands, name `.lfsconfig` with `.gitattributes` and `.gitmodules` as PR files to tell the user about, and state accurately that other user-configured filter drivers can still run on PR-selected content at checkout.
- X3: when `origin`'s URL carries userinfo, the skill stops without repeating the URL and without calling it a credential; it says the origin URL has userinfo and cannot be used.
- X4: the host comes from the URL authority (after `scheme://` and any userinfo, or before `:` in the scp form); owner and repo pass the same value check as PR-sourced values.
- X6: the edit-hash record keeps one hash per edited path.
- B8: the guide and README say the agent resolves only threads the approved plan names.
- B9: rename tests that reuse spec criterion IDs for repair items.
**Done when:** every item above is visible in the shipped text, the T4 commands exit 0, and no file under `docs/specs/github-pr/` changed.

## Changelog

- 2026-10-30: drafted.
- 2026-10-30: spec approved and plan approved by the owner after shaping, adversarial, and security review; residue recorded in the spec Assumptions.
- 2026-10-30: spec amended after round-2 review: the closed read-only set admits `git remote get-url origin`, U5 also stops on an origin URL with userinfo, and global git options are skipped with their argument; tasks T6 and T7 added for review repairs. Cold shaping review of the amendment found no blocker.
- 2026-10-30: the final review stage ran outside the work-supervisor: another session on the machine edited the shared `.git/config` while the T7 attempt was open, the supervisor refused to continue (`attempt-refused`, `common:config`), and the original bytes could not be rebuilt. The owner chose to finish by hand. The T7 repairs and three further review rounds (adversarial and security) were committed and recorded here instead of under `delivery/`; the eval record names the final digest.
- 2026-10-31: owner approved a one-line amendment to G9a naming `find`, `grep`, `sort`, `cut`, `awk`, `printf`, `cmp`, and `test -d|-e` as allowed for the sandbox config comparison (never a git command), after round-5 review showed a correct record needs them.
