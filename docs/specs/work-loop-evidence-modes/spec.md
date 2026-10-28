# Spec: work-loop evidence modes

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none
- **Shape:** mixed

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

## Outcome

An agent running the core pack's build loop settles an unpredictable design with one throwaway spike, diagnoses a defect with `bug-fix` before fixing it in `work-loop`, and proves refactors and performance claims with a mode built for each. A reviewer's claim about how code behaves arrives with the command that shows it whenever such a run is safe and cheap, so a disputed behavior finding is settled by rerunning it rather than by another review round.

## What Changes

- A bounded pre-trigger spike — the Unfamiliar bullet in `work-loop`'s risk-trigger block.
- `bug-fix` diagnoses, then hands the fix to `work-loop` — `bug-fix` SKILL.md, `work-loop` description and PLAN, the `bug-fix` how-to guide, and the core-pack explanation.
- Two verification modes, **behavior pin** and **measurement**, neither generating a TDD stub — `work-loop` PLAN steps 7 and 8, EXECUTE, `references/verification-modes.md`, and `references/tdd-stubs.md`.
- Every other list of verification modes points at `work-loop` PLAN step 7 instead of naming a closed set — `adversarial-reviewer`, `implementer`, the infra and verification-mode references, `new-spec` SKILL.md, its spec-and-plan contract and spec template, and the core-pack explanation.
- Proof by a run for behavior findings — `adversarial-reviewer` severity rules, and `work-loop` FIX.
- Eval cases, the core pack version, and the self-hosted projections.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | The skills and agents are the procedure an agent follows | `packs/core/.apm/skills/work-loop/`, `packs/core/.apm/skills/bug-fix/SKILL.md`, `packs/core/.apm/skills/new-spec/`, `packs/core/.apm/agents/adversarial-reviewer.md` | core pack maintainers | content contract tests and eval cases | tests green; projections regenerated |
| User-facing promise | Adopters read how bug fixing and verification modes work | `guides/core/how-to/bug-fix.md`, `guides/core/explanation/core-pack.md` | core pack maintainers | guide content tests | guides state the handoff and point at the mode list |
| Release history | A non-cosmetic pack change ships under a new version | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json` | core pack maintainers | both files read `3.1.27` | catalogue verify passes |
| Decision rationale | none — no new decision record; the change applies existing doctrine and records its reasoning in this spec's PR | none | — | — | — |

## Agent Rules

### Always do

- Keep every sentence an existing test pins; add text beside it rather than rewording it.
- Cite an owning statement instead of restating it: the risk-trigger block stays the only home of the triggers, and `new-spec` stays the only home of the side-effect-free probe rule.
- Bump `pack.toml` and `.claude-plugin/plugin.json` together, and regenerate projections with self-host rather than editing them.

### Ask first

- Changing any risk trigger other than Unfamiliar, or how light and full mode are selected.
- Changing `finding-adjudicator`'s tools or its six predicates.
- Changing `bug-fix`'s diagnosis steps (reproduce, red test, investigate, compare, falsify, trace, decide) beyond where step 2's red runs and lives, which AC-0004 states.

### Never do

- No new skill, agent, script, or dependency, and no new top-level directory.
- No edit to an adapter projection (`.claude/`, `.agents/`, `.codex/`, and the other host trees) except through self-host.
- No widening of any reviewer agent's `tools:` line.

## Testing Strategy

- **Guidance content (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0020):** goal-based, exercised by pytest content tests in `packs/core/tests/skills/work-loop/test_evidence_modes_contract.py`, each scoped to the section its rule lives in. A whole-file search would stay green if a rule moved out of the procedure an agent follows, so each test reads one bounded section.
- **Regression of pinned guidance (AC-0016):** goal-based. The existing suites that pin these files run unedited.
- **Routing behavior (AC-0017):** goal-based, by the same test file reading both `evals.json` files for the new cases; executing the cases against a model is not part of this delivery.
- **Release (AC-0018):** goal-based, by the same test file reading both version fields.
- **Projection (AC-0019):** goal-based, by the catalogue and guide commands' exit status and a clean tree after self-host.

## Acceptance Criteria

Unless a criterion names another file, "the risk-trigger block" is the text between `<!-- risk-triggers:start` and `<!-- risk-triggers:end -->` in `packs/core/.apm/skills/work-loop/SKILL.md`.

### Spike

- [x] **AC-0001.** The risk-trigger block's Unfamiliar bullet permits one spike before that trigger fires on unfamiliarity alone, and states each of these limits on it: it lives outside the tracked tree, it follows `new-spec`'s side-effect-free probe constraint, it is never committed, what it observed is recorded as the trigger's grounding, and it settles only the Unfamiliar trigger.

### Bug-fix handoff

- [x] **AC-0002.** The `work-loop` frontmatter description names a fix whose cause is established as in scope, names `bug-fix` for diagnosing a defect whose cause is not, and does not contain the substring `behavior-changing fix`.
- [x] **AC-0003.** `work-loop` PLAN states that a request reporting a defect whose cause is not established runs `bug-fix` diagnosis before mode selection, that diagnosis earns that defect's red regression test's red from disposable scratch whatever mode follows, and that mode selection then decides only how the test is materialized: full mode records it as the task's plan stub, light mode writes it at its real test path during EXECUTE, and in neither mode is it a repository test file during PLAN.
- [x] **AC-0004.** In `bug-fix` SKILL.md, step 2 states that its red is earned from disposable scratch; `## When to invoke` states that once the cause is established the fix runs through `work-loop`, whose PLAN materialization rule decides where the test lives, and that steps 8 to 11 bind that run (that rule is AC-0003, and the shipped text does not cite it); and step 10 names the test `work-loop` materializes as the one that stays in the suite.
- [x] **AC-0005.** `guides/core/how-to/bug-fix.md` and `guides/core/explanation/core-pack.md` each state that `bug-fix` hands the fix to the build loop, and neither contains `without entering the spec / loop pipeline`, `several files`, or `past one file`.

### Verification modes

- [x] **AC-0006.** `work-loop` PLAN step 7 and EXECUTE's discipline list each name **Behavior pin** and **Measurement**, and the conditional-reference table routes a task that picks either to `references/verification-modes.md`.
- [x] **AC-0007.** The behavior-pin section of `references/verification-modes.md` states each of: the pin passes on the base commit before any structure moves; the pin stays green after each step; lint and typecheck are not a pin; a restructure that names no branch, layer, or invalid state it removed is reverted.
- [x] **AC-0008.** The measurement section of `references/verification-modes.md` states each of: the baseline comes from the base commit with the same command, data, and environment as the after run; each side runs at least 5 times, alternating; the report gives median, range, and run count; a difference inside the run-to-run range is reported as no measurable difference; the run records its error count and a count of the work done.
- [x] **AC-0020.** `work-loop` PLAN step 8 and `references/tdd-stubs.md` each state that behavior-pin and measurement tasks record `no stub (mode)`, each contains `PLAN step 7`, and neither contains `Goal-based and manual-QA tasks`.
- [x] **AC-0009.** No file under `packs/core/.apm/` or `guides/core/` other than `work-loop` SKILL.md states a count of verification modes or lists them as `TDD` followed by `goal-based` joined by `/` or `,`; and each of these files names `work-loop` PLAN step 7 as the owner of the mode list: `agents/adversarial-reviewer.md`, `agents/implementer.md`, `skills/work-loop/references/infra-verification.md`, `skills/work-loop/references/verification-modes.md`, `skills/new-spec/SKILL.md`, `skills/new-spec/references/spec-and-plan-contract.md`, and `skills/new-spec/assets/spec.md` under `packs/core/.apm/`, and `guides/core/explanation/core-pack.md`.

### Proof by a run

- [x] **AC-0010.** `adversarial-reviewer.md` states that a mechanical finding claiming what code does when it runs carries the command and the output it printed whenever the run is feasible, where feasible means all of: it runs in this checkout, writes nothing outside ignored scratch, uses no network and no credentials, and completes under a 60-second wall-clock timeout the reviewer applies; a run that hits the timeout is not feasible.
- [x] **AC-0011.** `adversarial-reviewer.md` states that a behavior finding whose run was feasible but is absent is a Concern at most, with the missing run named.
- [x] **AC-0012.** `adversarial-reviewer.md` lists exactly these cases as owing no run, and requires the finding to name the case that applies: a defect a citation already establishes; spec-stage, RFC, and intent review; prose whose only run would be a model evaluation; and a run that is not feasible.
- [x] **AC-0013.** The `What you do not do` section of `adversarial-reviewer.md` states that a targeted reproduction for one finding is not a gate run.
- [x] **AC-0014.** `work-loop` FIX states that a sustained finding carrying a command is run before the fix and recorded failing, run after the fix and recorded passing, and that a command which passes before the fix is Surfaced instead of fixed.
- [x] **AC-0015.** `finding-adjudicator.md`'s `tools:` line is `Read, Grep`, as at the base commit; this pins that the rerun lives in `work-loop` FIX rather than in the adjudicator.

### Regression, evals, release

- [x] **AC-0016.** `packs/core/tests/pack/test_review_depth_and_verdict_contract.py`, `packs/core/tests/skills/work-loop/test_work_intake_dispatch.py`, and `packs/core/tests/skills/bug-fix/test_bug_fix_skill_body.py` pass with their test files unedited.
- [x] **AC-0017.** `work-loop`'s `evals/evals.json` holds one case each for the spike, the defect handoff, behavior pin, and measurement; `bug-fix`'s `evals/evals.json` holds one handoff case; each new case carries `id`, `prompt`, `expected_output`, and a non-empty `assertions` list; and `test_evals_json_shape` in `packs/core/tests/skills/work-loop/test_loop_engine.py` passes.
- [x] **AC-0018.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` both carry version `3.1.27`.
- [x] **AC-0019.** `agentbundle catalogue lint --root . --deep`, `agentbundle catalogue verify --root .`, `python3 tools/validate_guides.py`, `python3 tools/check-guide-index.py`, and `python3 tools/lint-guide-titles.py` exit 0, and `agentbundle catalogue self-host --root . --write` leaves no tracked change after the delivery commit.

## Follow-ons

- eugenelim: none filed — merging the three spec-stage reviews into one, and thinning plan detail reviewers can only argue about, are separate work if the owner asks for them.

## Assumptions

- Product: eval cases are added but not run against a model in this delivery — the routing behavior they assert is therefore checked only by schema, not by an agent run.
- Product: every bug fix now passes through `work-loop`, at least in light mode with one adversarial review, where a single-file fix previously shipped from `bug-fix` alone — what it would change: AC-0004 and AC-0005 (settled by: the owner, at spec approval).
