# Plan: work-loop evidence modes

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (version bump, self-host, eval harness rules); the risk-trigger single-home lint in `packs/core/tests/skills/work-loop/test_work_intake_dispatch.py`; section-scoped prose pins in `packs/core/tests/pack/test_review_depth_and_verdict_contract.py` as the analogous test shape; uncertainty — none, the change is prose plus tests.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan.

## Approach

Four guidance edits that share no text, then one release task. Each guidance task adds its own section-scoped tests to one new file, `packs/core/tests/skills/work-loop/test_evidence_modes_contract.py`, so a rule that moves out of the procedure an agent follows turns a test red. The riskiest part is T3: the mode list is restated outside `work-loop` SKILL.md, so T3 replaces each closed list with a pointer to `work-loop` PLAN step 7 rather than adding two more names to every copy. T3's Touches is the one home of that file set.

## Constraints

- `packs/AGENTS.md`: bump `pack.toml` and `plugin.json` together; update the pack's eval harness; run self-host after `.apm/` edits.
- The risk-trigger block is the only home of the triggers; its existing pinned sentences stay.
- `test_review_depth_and_verdict_contract.py` pins the mechanical/judgement clauses verbatim; T4 adds beside them.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Maintainer procedure | T1, T2, T3, T4 | `test_evidence_modes_contract.py` green | suite green at the delivery commit |
| User-facing promise | T2, T3 | guide assertions in the same file | guides read as stated |
| Release history | T5 | version assertions | `catalogue verify` exit 0 |

## Design (LLD)

**Section reader.** The new test file reuses the `_section(text, start, end)` shape `test_work_intake_dispatch.py` already uses: it returns the text between two markers and fails if either is missing. Each assertion names its section's start and end markers. A read-only probe at the base commit found each marker the Tests fields name exactly once in its file.

**Mode-list owner.** `work-loop` PLAN step 7 is the one list. Every other file that names modes says "the modes `work-loop` PLAN step 7 defines" and may give examples, but no count. The `verification-modes.md` header changes from "the visual / manual-QA mode" to a reference for the modes that need doctrine beyond SKILL.md: visual / manual QA, behavior pin, and measurement.

**Proof-by-run placement.** The rule sits directly after the mechanical/judgement bullets in `adversarial-reviewer.md` § Report numbered findings, because it narrows what a mechanical behavior finding must carry. The adjudicator is unchanged: a recorded command and its output are observation evidence it already reads. Rerunning is the controller's job in `work-loop` FIX, which already has `Bash`.

**Handoff placement.** `work-loop` PLAN gains step 1b before mode selection. `bug-fix` § When to invoke gains the handoff sentence. Step 2 gains the scratch clause, step 10 names the materialized test as the one that stays, and steps 8, 9 and 11 stay as written, now binding the `work-loop` run. `bug-fix` step 2's red test keeps its content and its contract-not-implementation rule; only where it lives changes on handoff. Diagnosis runs before the mode is known, so step 2 always earns its red from disposable scratch. Full mode then records the test as the task's plan stub, as `tdd-stubs.md` already requires of every TDD stub, so no new stub path exists. Light mode writes it at its real test path during EXECUTE, which step 8's "Light mode skips stubs." already allows.

**No-stub modes.** A behavior pin passes on the base commit by design, and a measurement has no red to earn, so both record `no stub (mode)`. Step 8 and `tdd-stubs.md` name the no-stub modes by pointing at step 7's list rather than naming two of them.

## Tasks

Every test function in `packs/core/tests/skills/work-loop/test_evidence_modes_contract.py` is named for its task (`test_t1_…` to `test_t5_…`), so each `Done when` selects one task's tests with `-k tN_`. A filter that selects nothing exits 5, so a task that adds no test fails its own check. Every task here is goal-based: its checks read shipped text or data, and no task has behavior to drive red.

### T1: Spike in the Unfamiliar trigger

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/tests/skills/work-loop/test_evidence_modes_contract.py`

**Tests:** no stub (goal-based — content check)
- AC-0001: inside the risk-trigger block, the Unfamiliar bullet's text, read from `- **Unfamiliar**` to the next `- **`, contains the spike permission and each of its five limits.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_evidence_modes_contract.py -q -k t1_` exits 0.

### T2: bug-fix diagnoses, work-loop fixes

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/bug-fix/SKILL.md`, `guides/core/how-to/bug-fix.md`, `guides/core/explanation/core-pack.md`, `packs/core/tests/skills/work-loop/test_evidence_modes_contract.py`

**Tests:** no stub (goal-based — content check)
- AC-0002: the parsed frontmatter `description` of `work-loop`.
- AC-0003: the PLAN section, from `## Step 1. PLAN` to `## Step 2. EXECUTE`: the `bug-fix` routing, the disposable-scratch red during diagnosis, and the full-mode and light-mode materialization branches.
- AC-0004: three regions of `bug-fix` SKILL.md, one per statement — step 2 (from `**Write the failing test (red).` to `**Investigate before narrowing.`), `## When to invoke` (to `## Procedure`), and step 10 (from `**Regression test stays.` to `**Commit body documents the root cause.`).
- AC-0005: both guide files, whole-file, because each guide states the handoff once and the three banned phrases must be absent anywhere in it.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_evidence_modes_contract.py -q -k t2_` and `python3 -m pytest packs/core/tests/skills/bug-fix -q` exit 0.

### T3: Behavior pin and measurement modes

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/work-loop/references/verification-modes.md`, `packs/core/.apm/skills/work-loop/references/tdd-stubs.md`, `packs/core/.apm/skills/work-loop/references/infra-verification.md`, `packs/core/.apm/agents/adversarial-reviewer.md`, `packs/core/.apm/agents/implementer.md`, `packs/core/.apm/skills/new-spec/SKILL.md`, `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md`, `packs/core/.apm/skills/new-spec/assets/spec.md`, `guides/core/explanation/core-pack.md`, `packs/core/tests/skills/work-loop/test_evidence_modes_contract.py`

**Tests:** no stub (goal-based — content check)
- AC-0006: PLAN step 7 (from `7. **Pick the verification mode` to `8. **Design construction tests`), EXECUTE's `Match discipline to verification mode:` list, and the conditional-reference table row.
- AC-0020: in each of three regions — PLAN step 8 (from `8. **Design construction tests` to `8a. **Anchor-test sweep`), `tdd-stubs.md`'s opening paragraph (to `## Lifecycle`), and its `Full-mode, TDD-tasks-only` bullet — the text contains `PLAN step 7` and does not contain `Goal-based and manual-QA tasks`; step 8 and the opening paragraph also name both new modes. All three regions contain the banned substring at the base commit.
- AC-0007, AC-0008: the `## Behavior pin` and `## Measurement` sections of `verification-modes.md`.
- AC-0009, sweep: every `.md` file under `packs/core/.apm/` and `guides/core/` except `work-loop/SKILL.md` has no match for a count word or numeral followed by `verification mode(s)` (optionally with `other` between), and none for `TDD` then `goal-based` joined by `/` or `,`. Reviewer modes such as quality-engineer's "three modes" do not match, because they never say "verification".
- AC-0009, named files: each of the eight files has no match for a count word followed by `modes` or for `defines` followed by a count word, and contains `PLAN step 7`.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_evidence_modes_contract.py -q -k t3_` exits 0.

### T4: Proof by a run

**Depends on:** none

**Touches:** `packs/core/.apm/agents/adversarial-reviewer.md`, `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/tests/skills/work-loop/test_evidence_modes_contract.py`

**Tests:** no stub (goal-based — content check)
- AC-0010, AC-0011, AC-0012: the `## Report numbered findings` section of `adversarial-reviewer.md`, up to `### Output format`.
- AC-0013: the `## What you do not do` section.
- AC-0014: the `## FIX` section of `work-loop` SKILL.md, up to `## Capture`.
- AC-0015: the frontmatter `tools:` value of `finding-adjudicator.md`.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_evidence_modes_contract.py -q -k t4_` and `python3 -m pytest packs/core/tests/pack/test_review_depth_and_verdict_contract.py -q` exit 0.

### T5: Evals, version, projections

**Depends on:** T1, T2, T3, T4

**Touches:** `packs/core/.apm/skills/work-loop/evals/evals.json`, `packs/core/.apm/skills/bug-fix/evals/evals.json`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `packs/core/tests/skills/work-loop/test_evidence_modes_contract.py`, `.claude/skills/**`, `.claude/agents/**`, `.agents/skills/**`, `.codex/agents/**`

**Tests:** no stub (goal-based — content and command checks)
- AC-0016: `python3 -m pytest packs/core/tests/pack/test_review_depth_and_verdict_contract.py packs/core/tests/skills/work-loop/test_work_intake_dispatch.py packs/core/tests/skills/bug-fix/test_bug_fix_skill_body.py -q`, with `git diff --quiet <base> -- ` over those three files.
- AC-0017: `test_t5_` cases read both `evals.json` files and find the five new ids, each with `id`, `prompt`, `expected_output`, and a non-empty `assertions` list; plus `python3 -m pytest packs/core/tests/skills/work-loop/test_loop_engine.py -q -k evals_json_shape`.
- AC-0018: a `test_t5_` case reads `version` from `pack.toml` with `tomllib` and from `plugin.json` with `json`, and compares each to the value AC-0018 states.
- AC-0019: the three catalogue commands, the three guide tools, and `git status --porcelain` after self-host.

**Effects:** none

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_evidence_modes_contract.py -q -k t5_` and every command in T5's `Tests:` exit 0, and `git status --porcelain` is empty after the delivery commit.

## Rollout

Ships as a core pack patch release, 3.1.26 to 3.1.27. Reversible by reverting the commit; no data or persisted state changes.

## Risks

- A content test that searches a whole file would pass after a rule moved out of its section; every test here reads one section.
- `new-spec` and `adversarial-reviewer` are loaded by other packs' specs and evals; replacing the closed mode list could break a pin elsewhere. T5's full lint and verify catch it.

## Changelog

- 2026-10-27: spec approved by eugenelim
- 2026-10-27: plan approved by eugenelim
