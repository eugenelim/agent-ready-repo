# Plan: work-loop narrow full mode

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** RFC-0111 § Proposal and § Follow-on artifacts (the authority for the wording); ADR-0088 and `tools/lint-agents-md.py` check 10g (the block's single home); `packs/AGENTS.md` (version bump, self-host, eval harness); `packs/core/tests/skills/work-loop/test_evidence_modes_contract.py` as the analogous section-scoped pin; uncertainty — none, the change is prose plus tests.

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

Two guidance edits, then evals, the guide, and the release. T1 edits the risk-trigger block and T2 edits `light-mode.md`; each adds its own section-scoped tests to one new file, `packs/core/tests/skills/work-loop/test_narrow_full_mode_contract.py`. The riskiest part is keeping existing pins green: the new light-mode rules go in as prose sections rather than table rows, because `test_the_predicate_tables_have_no_unpinned_rows` counts rows, and the durability row keeps its pinned prefix.

## Constraints

- RFC-0111 is the authority for what each rule says; this plan's wording follows its D1 and D2 text.
- ADR-0088 and lint check 10g: the block lives only in the pack source and its `.claude/` and `.agents/` projections, byte-identical.
- `packs/AGENTS.md`: bump `pack.toml` and `plugin.json` together, update the eval harness, run self-host after `.apm/` edits, and cite no internal record in shipped pack text.
- A pack test may not read `guides/`; the guide test lives in `tests/roster/`.
- This environment's `python3` has no pytest; suites run as `uv run --no-project --with pytest --with pyyaml python -m pytest …`.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Maintainer procedure | T1, T2, T3 | `test_narrow_full_mode_contract.py` green | suite green at the delivery commit |
| User-facing promise | T4 | roster guide test | the guide names both routes |
| Release history | T5 | version and fragment assertions | `catalogue verify` exit 0 |

## Design (LLD)

### Design decisions

Traces to AC-0001, AC-0002, AC-0004, AC-0015, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0011, AC-0013.
Owned by: T1, T2, T3, T5

**Section reader.** The new test file copies the `_section(text, start, end)` helper from `test_evidence_modes_contract.py`: it returns the text between two markers and fails if either is missing. Each test whitespace-flattens its section and asserts the backticked phrases its criterion names, so a re-wrap is not a failure.

**Guidance sentence.** It replaces the block's sentence beginning `Prose *about* such a thing is exempt` and keeps its place before the first bullet:

> Prose *about* such a thing is exempt; prose that *is* the rule — policy, an interface document, agent guidance — is the thing itself. For an edit to an existing agent-guidance file — a skill, an agent definition, an `AGENTS.md`, or a reference a skill loads — that holds only when the edit changes a **tool surface** (which tools, commands, hooks, or scripts an agent may run, or how they are invoked), an **authority or gate** (who or what may approve, decide, merge, or skip a gate; what a gate requires; what counts as clean; what evidence the finish checklist needs; what a finding may block; or which text an agent treats as instruction), a **security boundary** (a control the first trigger below names, including how untrusted input, secrets, confinement, or LLM authority — what an AI agent is allowed to do — are handled), or a **published schema** (a format other tools or adopters parse, such as frontmatter fields, a record grammar, a verdict schema, or a manifest). A plain edit that changes none of the four follows the guidance-edit rules in `references/light-mode.md`. Compliance and policy prose keeps its trigger, and a new skill, agent definition, hook, command, or newly loaded reference still fires the structural trigger. An edit you cannot place outside the four is inside them. Where you cannot tell whether the change reached the thing, it did.

The AC-0002 phrase `an edit to an existing agent-guidance file` matches inside "For an edit to an existing agent-guidance file"; `only when the edit changes` matches "only when the edit changes".

**Multi-feature bullet.**

> - **Multi-feature or dependent tasks** — it decomposes a multi-feature brief, or it bundles tasks that `references/light-mode.md` cannot show independent. A bundle shown independent splits into one unit per task, and each unit faces every other trigger here on its own. A bundle whose independence cannot be shown fires this trigger.

**Light-mode sections.** Two `##` sections go between `## Direct-light decision record and route` and `## Loop deltas`, so they sit after the late-trigger rule they cite. Draft text:

> ## Splitting a bundle
>
> A request that bundles several tasks may split into one light unit per task when the tasks pass all three parts of this test:
>
> 1. **No dependency edge.** No task's `Depends on:` names another task in the bundle.
> 2. **No shared write set.** Each task declares the paths it will write as a `Touches:` set, and no path or glob in one set matches a path in another. A generated projection of a source file, under `.claude/`, `.agents/`, or `.codex/`, counts as a write to its source path.
> 3. **The diff agrees.** Each unit's finished diff stays inside its own set and touches no file in another unit's set.
>
> List every task with its `Depends on:` and `Touches:` lines in the decision record, and check parts 1 and 2 there before the first write. Check part 3 on every unit's finished diff. Part 3, the diff check, is the check that counts: a declared set is a prediction, and a prediction never by itself shows independence.
>
> Each unit then faces every risk trigger and every eligibility row on its own, and ships as its own branch and pull request. Units run one at a time in this session, so a split is not parallel execution. The bundle as a whole must still pass the rows "Expected to complete in the current session", "Expected multi-session work", and "Queueing for later": a bundle whose units together need another session, or would wait in a queue, goes to full mode whole.
>
> **No light unit merges until every unit passes.** Units may be reviewed in any order. No light unit merges until every unit still in the bundle has a finished diff that passes the diff check.
>
> **A unit that fires another trigger** leaves the bundle for full mode by itself and takes its declared write set with it: its spec and plan record that set. The units still in the bundle run the diff check against that set, then merge without waiting for the full-mode unit.
>
> **The fallback.** When any part of the test fails or cannot be shown, the bundle stays whole and goes to full mode. A unit whose diff leaves its set stops the whole bundle. Nothing has merged at that point, so the bundle moves to full mode with every unit's diff kept as observed work, under the late-trigger rule above.
>
> ## Editing existing agent guidance
>
> An edit to an existing agent-guidance file that changes no **tool surface**, **authority or gate**, **security boundary**, or **published schema**, as the risk-trigger block defines them, fires no trigger by being guidance. It still faces every trigger on its other effects, and it does not count as a durable product contract for the eligibility table above. It runs light with one added obligation: each changed rule gets a new or updated content-pin test, a test that asserts the phrases the rule depends on, which reads only the edited section between two markers rather than the whole file. Adversarial review runs as light mode runs it.

**Durability row.** The first cell becomes `A public or durable product behavior contract; for an edit to an existing agent-guidance file, only one that changes a **tool surface**, an **authority or gate**, a **security boundary**, or a **published schema**`. The reason cell adds: a plain guidance edit changes how an agent carries out a step inside the same tools, authority, gates, controls, and formats.

**Eval that changes.** `risk-trigger-modify-not-touch` keeps its prompt (a test that calls an unchanged helper) and its verdict. In both `expected_output` and `assertions`, the statement that editing prose which is the rule fires the trigger becomes the narrowed rule: "editing existing agent guidance fires the trigger only when it changes a tool surface, an authority or gate, a security boundary, or a published schema". The clause that editing policy or compliance prose, or an interface document, still fires the trigger stays in both fields, because the narrowing applies only to existing agent guidance.

**Version pin.** `test_t5_pack_versions_are_3_1_27` in `test_evidence_modes_contract.py` pins the previous release, so T5 removes it. The new file's suite test asserts only that `pack.toml` and `plugin.json` agree, so the next release does not have to edit it; the `3.1.28` value is a delivery command check.

**Changelog fragment.** A pack test may not read `docs/`, so the fragment half of AC-0013 is a command check run once at delivery, not a suite test: fragments are later compacted into bundles, and a standing test would go red for reasons unrelated to this change.

### Behavior & rules

Traces to AC-0011.
Owned by: T3

Each new eval's prompt describes one concrete request; its `expected_output` gives the verdict phrase AC-0011 names and the reason, and its `assertions` restate the verdict and the deciding rule:

- `bundle-split-independent-tasks` — two edits to different reference files with no `Depends on:` edge.
- `bundle-unsplittable-shared-file` — two features that both edit one `SKILL.md`.
- `bundle-late-unit-strays` — a split unit whose finished diff touches another unit's file.
- `guidance-edit-plain-runs-light` — reordering two steps in an existing reference.
- `guidance-new-file-fires-structural` — adding a new reference a skill newly loads.
- `guidance-edit-tool-surface` — letting a skill run a new script.
- `guidance-edit-authority-or-gate` — changing what counts as a clean review round.
- `guidance-edit-security-boundary` — changing how a skill treats text from an issue body.
- `guidance-edit-published-schema` — adding a required frontmatter field.

## Tasks

Every new test function is named for its task (`test_t1_…` to `test_t5_…`), so each `Done when` selects one task's tests with `-k tN_`. A filter that selects nothing exits 5, so a task that adds no test fails its own check. Every task is goal-based: its checks read shipped text or data. `PYTEST` below means `uv run --no-project --with pytest --with pyyaml python -m pytest`.

### T1: Narrow the two rules in the risk-trigger block

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/tests/skills/work-loop/test_narrow_full_mode_contract.py`

**Tests:** no stub (goal-based — content check)
- AC-0001: the block section, then the bullet from `- **Multi-feature or dependent tasks**` to `No trigger fires`.
- AC-0002: the block section from `Merely touching unchanged existing I/O` to `- **Compliance`.

**Done when:** `PYTEST packs/core/tests/skills/work-loop/test_narrow_full_mode_contract.py -q -k t1_` exits 0.

### T2: Add the split and guidance-edit rules to light mode

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-loop/references/light-mode.md`, `packs/core/tests/skills/work-loop/test_narrow_full_mode_contract.py`

**Tests:** no stub (goal-based — content check)
- AC-0004, AC-0015, AC-0005, AC-0006, AC-0007, AC-0008: the section from `## Splitting a bundle` to `## Editing existing agent guidance`.
- AC-0009: the section from `## Editing existing agent guidance` to `## Loop deltas`, and the durability-row table read with the same row splitter `test_work_intake_dispatch.py` uses.
- AC-0010, intake half: `PYTEST packs/core/tests/skills/work-loop/test_work_intake_dispatch.py -q`, with `git diff --quiet origin/main -- packs/core/tests/skills/work-loop/test_work_intake_dispatch.py`.

**Done when:** `PYTEST packs/core/tests/skills/work-loop/test_narrow_full_mode_contract.py -q -k t2_` and every command in T2's `Tests:` exit 0.

### T3: Evals

**Depends on:** T1, T2

**Touches:** `packs/core/.apm/skills/work-loop/evals/evals.json`, `packs/core/tests/skills/work-loop/test_narrow_full_mode_contract.py`

**Tests:** no stub (goal-based — content check)
- AC-0011: a `test_t3_` case loads `evals.json` with `json`, finds the nine ids and their verdict phrases, checks the four required phrases in `risk-trigger-modify-not-touch`'s `expected_output` and `assertions`, and serializes `risk-trigger-modify-not-touch` whole to check both banned phrases are absent from every field; plus `PYTEST packs/core/tests/skills/work-loop/test_loop_engine.py -q -k evals_json_shape`.

**Done when:** `PYTEST packs/core/tests/skills/work-loop/test_narrow_full_mode_contract.py -q -k t3_` and the `test_loop_engine.py` command exit 0.

### T4: Guide

**Depends on:** T1, T2

**Touches:** `guides/core/how-to/plan-and-execute-non-trivial-work.md`, `tests/roster/test_core_onboarding_documentation.py`

**Tests:** no stub (goal-based — content check)
- AC-0012: a new roster test reads the pitfall paragraph that starts `Reaching for` and ends at the next `:::` fence.

**Done when:** `PYTEST tests/roster/test_core_onboarding_documentation.py -q` exits 0.

### T5: Version, changelog, projections

**Depends on:** T1, T2, T3, T4

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/**`, `packs/core/tests/skills/work-loop/test_evidence_modes_contract.py`, `packs/core/tests/skills/work-loop/test_narrow_full_mode_contract.py`, `.claude/skills/**`, `.agents/skills/**`, `.codex/**`

**Tests:** no stub (goal-based — content and command checks)
- AC-0013, version half: a `test_t5_` case reads `version` from `pack.toml` with `tomllib` and from `plugin.json` with `json` and asserts they are equal; a delivery command check prints both and compares them to `3.1.28`.
- AC-0013, fragment half: the fragment is created with `tools/changelog.py new`; then `git diff --name-only --diff-filter=A origin/main -- docs/product/changelog.d/` lists exactly one file, whose front matter names `core` at `3.1.28` and whose `## Highlights` has a `-` bullet; then the render command AC-0013 names, and `python3 tools/changelog.py validate`.
- AC-0010, version-pin half: `PYTEST packs/core/tests/skills/work-loop/test_evidence_modes_contract.py -q`, with `git diff origin/main` on that file showing only the removed test.
- AC-0003 and AC-0014: `python3 tools/lint-agents-md.py`, the two catalogue commands, and `git status --porcelain` after `make build-self`.

**Effects:** none

**Done when:** `PYTEST packs/core/tests/skills/work-loop/test_narrow_full_mode_contract.py -q -k t5_` and every command in T5's `Tests:` exit 0, and `git status --porcelain` is empty after the delivery commit.

## Rollout

Ships as a core pack patch release, 3.1.27 to 3.1.28. Reversible by reverting the commit; no data or persisted state changes.

## Risks

- A content test that searches a whole file would pass after a rule moved out of its section; every test here reads one section.
- The split rules could be read as permission to run units in parallel; the "one at a time" sentence and the unchanged "parallel coordination" conjunct close that reading.

## Changelog

- 2026-10-28: spec approved by eugenelim
- 2026-10-28: plan approved by eugenelim
