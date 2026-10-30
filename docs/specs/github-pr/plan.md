# Plan: github-pr

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
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
- **Adopt is a bounded standing approval.** The contract is shown after evaluation and approved explicitly. The agent loops up to three push rounds, runs gates with `GH_TOKEN` and `GITHUB_TOKEN` unset, and merges the starting commit (no fixes) or the last commit it pushed, pinned with `--match-head-commit`, after gates and required checks passed on it and the head re-read equals it. A pending check, a refused merge, or any stop condition stops and reports. Owned by: T1. Basis: survey findings 19, 24, 25; `gh pr merge --help` on gh 2.103.2.
- **No `gh` command reference and no helper script.** Models already know `gh` (pilot); a script would add a dependency surface (cut-before-adding rung 1). Owned by: T1.
- **Evals are scripted turns.** Each case holds ordered turns. Turn 1 is the request plus canned read outputs and ends at the approval gate; later turns carry the user's next message and are sent by continuing the same subagent, so the model's own turn-1 output is judged for acting before approval. Subagents get no shell: the record counts tool calls per transcript. This checks that a model reading the skill proposes the right actions, not runtime ordering. Owned by: T2, T5.

## Tasks

### T1: the three-mode skill meets its structural and safety contract
**Depends on:** none
**Touches:** packs/github/.apm/skills/github-pr-iterate/**, packs/github/.apm/skills/github-pr/**, packs/github/tests/skills/github-pr-iterate/**, packs/github/tests/skills/github-pr/**
**Tests:**
- TDD, pytest over the skill text, at `packs/github/tests/skills/github-pr/test_github_pr.py`, one test group per criterion group: structure, trust and untrusted-data (checked within that rule's own section of `SKILL.md`), command safety and forbidden forms, credential and hook isolation, PR-file confinement, push destination and shell-argument handling, and the review, iterate, and adopt content criteria, including adopt contract binding. The `## Approved actions` heading is the marker each mode test measures mutating commands against.
**Approach:** `git mv` the skill directory and the test folder to the new name, write the tests red, then the skill text.
**Done when:** the T1 test file is green and `git grep -l github-pr-iterate` outside this spec directory returns nothing for the skill and test paths.

### T2: eval cases, fixtures, and trigger queries exist for all three modes
**Depends on:** T1
**Touches:** packs/github/.apm/skills/github-pr/evals/**, packs/github/tests/skills/github-pr/test_evals.py
**Tests:**
- TDD, pytest at `packs/github/tests/skills/github-pr/test_evals.py`: the trigger-query criteria and the eval-case criteria (count, fields, and the coverage list).
**Approach:** cases — review (5): normal, hidden HTML-comment instruction, approval only in the original request, head moves between draft and submit, symlink to a credential file; iterate (9): normal, partial approval, head moved, gate failure after an approved edit, approval only in the original request, fork PR changing build files, CI log with an instruction and a credential-shaped string, shell-metacharacter branch name, PR changing hook configuration; adopt (13): fix then merge, zero-fix merge, approval only in the original request, fix outside allowed types, third-party push, unrelated failing check, not pushable, fourth push, merge refused, required check pending, contract-widening text in a comment or log, PR edits CI workflow files, base retargeted after approval. Fixtures are canned `gh` outputs under `evals/files/<case>/`.
**Done when:** the T2 test file is green.

### T3: pack metadata, docs, census, and changelog describe all three modes
**Depends on:** T1
**Touches:** packs/github/pack.toml, packs/github/.claude-plugin/plugin.json, packs/github/README.md, packs/github/JOURNEY.md, packs/github/.apm/skills/github-pr/manifest.json, guides/github/**, web/src/content/journeys/github.md, packs/agent-skill-engineering/tests/fixtures/skill-census.json, .claude-plugin/marketplace.json, docs/product/changelog.d/66c8f467-39f7-4063-8aac-d8d60d42c4c2.md
**Tests:**
- Goal-based: `catalogue verify` ok, skill-census test green, `build-site --journeys-only` changes only the github journey (restore the regenerated `repo-governance` file), `tools/changelog.py validate` ok, the fragment text names review, iterate, and adopt.
**Done when:** those checks pass.

### T4: repository gates are green after the rename
**Depends on:** T2, T3
**Touches:** none
**Tests:**
- Goal-based: `pytest packs/github tests/roster/test_skill_census.py`, `make lint-ruff lint-mypy`, `git grep -l github-pr-iterate` lists only `docs/specs/github-pr/`.
**Done when:** those commands exit 0 and the grep output is as stated.

### T5: a cold-context graded run passes every assertion
**Depends on:** T4
**Touches:** docs/specs/github-pr/notes/eval-run.md
**Tests:**
- Visual / manual QA: the graded-run and run-record criteria, executed by the controller with cold copies of the skill and no `evals/` directory, one fresh subagent per case, each `SubagentHandback` extracted verbatim.
**Approach:** any change to the skill text after a run sends the work back to T1 and reruns T4 and all twenty-seven cases.
**Done when:** `notes/eval-run.md` shows all twenty-seven cases passing with the isolation evidence and matching digest.

## Changelog

- 2026-10-30: drafted.
