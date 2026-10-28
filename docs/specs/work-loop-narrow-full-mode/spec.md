# Spec: work-loop narrow full mode

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0111, ADR-0088, RFC-0099
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

An agent choosing a mode in core's `work-loop` sends a bundle of tasks that are shown independent through one unit per task, and sends a plain edit to an existing agent-guidance file through light mode with content-pin tests on the edited section. Every bundle whose independence cannot be shown, every new guidance file, and every guidance edit that changes a tool surface, an authority or gate, a security boundary, or a published schema still goes to full mode.

## What Changes

- The "Multi-feature or dependent tasks" trigger and the "prose that *is* the rule" sentence — the risk-trigger block in `packs/core/.apm/skills/work-loop/SKILL.md`.
- A bundle-splitting section and a guidance-edit section, plus a narrowed "A public or durable product behavior contract" durability row — `packs/core/.apm/skills/work-loop/references/light-mode.md`.
- The eval `risk-trigger-modify-not-touch` and nine new eval cases — `packs/core/.apm/skills/work-loop/evals/evals.json`.
- One pitfall paragraph naming both routes — `guides/core/how-to/plan-and-execute-non-trivial-work.md`.
- Content-pin tests — `packs/core/tests/skills/work-loop/test_narrow_full_mode_contract.py`, and `tests/roster/test_core_onboarding_documentation.py` for the guide.
- Core 3.1.28, a changelog fragment, and the self-hosted projections.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | The trigger block and light-mode reference are the procedure an agent follows to pick a mode | `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/work-loop/references/light-mode.md` | core pack maintainers | content-pin tests and eval cases | tests green; projections regenerated |
| User-facing promise | Adopters read when work needs a spec | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | core pack maintainers | roster guide test | the guide names both routes |
| Release history | A non-cosmetic pack change ships under a new version | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/` | core pack maintainers | both files read `3.1.28`; one fragment for core 3.1.28 | catalogue verify passes |
| Decision rationale | none — RFC-0111 records why; no ADR is needed | none | — | — | — |

## Agent Rules

### Always do

- Keep every phrase an existing test pins in the risk-trigger block and `light-mode.md`; AC-0009 and AC-0010 name what that preserves.
- Regenerate projections with `make build-self`; bump `pack.toml` and `.claude-plugin/plugin.json` together.

### Ask first

- Changing any risk trigger other than "Multi-feature or dependent tasks" and the "prose that *is* the rule" sentence, including the Unfamiliar trigger's spike paragraph.
- Adding an eligibility or durability row to `light-mode.md` rather than prose.
- Any wording that lets a split unit or a guidance edit skip a gate light mode already runs.

### Never do

- No new skill, agent, script, hook, or dependency, and no new top-level directory.
- No copy of the risk-trigger block outside its three homes, and no edit to a projection except through `make build-self`.
- No change to plan shape, review tiers after code, shaping review, or the bundled-fixes carve-out.

## Testing Strategy

- **Routing rules in the trigger block and light-mode reference (AC-0001, AC-0002, AC-0004, AC-0015, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009):** goal-based, by pytest content tests in `packs/core/tests/skills/work-loop/test_narrow_full_mode_contract.py`. Each reads one section through a `_section(...)` marker helper and asserts the backticked phrases its criterion names, so a rule removed or moved out of the procedure an agent follows turns a test red.
- **Single home of the block (AC-0003):** goal-based, by `python3 tools/lint-agents-md.py` exit status, whose check 10g compares the three homes byte for byte.
- **Regression of existing pins (AC-0010):** goal-based. The existing suites run with their files unedited, apart from the version pin AC-0010 permits removing.
- **Agent behavior on recorded cases (AC-0011):** goal-based, by the same test file reading `evals.json`; running the cases against a model is not part of this delivery.
- **User-facing guide (AC-0012):** goal-based, by a roster test, because a pack test may not read `guides/`.
- **Release and projection (AC-0013, AC-0014):** goal-based, by a pack test that both version files agree, and by command checks for the `3.1.28` value, the changelog fragment, the catalogue, and the projections, because a pack test may not read `docs/`.

## Acceptance Criteria

"The risk-trigger block" is the text between `<!-- risk-triggers:start` and `risk-triggers:end -->` in `packs/core/.apm/skills/work-loop/SKILL.md`. "The guidance sentence" is the part of the block between `Merely touching unchanged existing I/O` and the first `- **` bullet. "Light-mode.md" is `packs/core/.apm/skills/work-loop/references/light-mode.md`. "Contains" means the whitespace-flattened section contains the backticked phrase.

### Risk-trigger block

- [ ] **AC-0001.** The block's "Multi-feature or dependent tasks" bullet contains `decomposes a multi-feature brief`, `cannot show independent`, `references/light-mode.md`, `splits into one unit per task`, `faces every other trigger here on its own`, and `A bundle whose independence cannot be shown fires this trigger.`
- [ ] **AC-0002.** The guidance sentence contains `an edit to an existing agent-guidance file`, `only when the edit changes`, and the four exclusions with these definitions: `**tool surface**` with `which tools, commands, hooks, or scripts an agent may run, or how they are invoked`; `**authority or gate**` with `who or what may approve, decide, merge, or skip a gate`, `what a gate requires`, `what counts as clean`, `what evidence the finish checklist needs`, `what a finding may block`, and `which text an agent treats as instruction`; `**security boundary**` with `untrusted input, secrets, confinement, or LLM authority`; and `**published schema**` with `a format other tools or adopters parse`. It also contains `Compliance and policy prose keeps its trigger`, `still fires the structural trigger`, `An edit you cannot place outside the four is inside them.`, and `Where you cannot tell whether the change reached the thing, it did.`, and does not contain `agent guidance, policy, an interface document — is the thing itself`.
- [ ] **AC-0003.** `python3 tools/lint-agents-md.py` exits 0, so the block is byte-identical in its source, `.claude/` and `.agents/` homes and appears nowhere else.

### Light-mode reference

- [ ] **AC-0004.** Light-mode.md's `## Splitting a bundle` section contains `No dependency edge`, `Depends on:`, `No shared write set`, `Touches:`, `counts as a write to its source path`, `The diff agrees`, `touches no file in another unit's set`, `Part 3, the diff check,`, `before the first write`, and `never by itself shows independence`.
- [ ] **AC-0015.** The same section contains `every eligibility row on its own`, `its own branch and pull request`, and `a split is not parallel execution`.
- [ ] **AC-0005.** The same section contains `Expected to complete in the current session`, `Expected multi-session work`, `Queueing for later`, and `goes to full mode whole`.
- [ ] **AC-0006.** The same section contains `No light unit merges until every unit still in the bundle has a finished diff that passes the diff check.`
- [ ] **AC-0007.** The same section contains `leaves the bundle for full mode`, `its spec and plan record that set`, `run the diff check against that set`, and `without waiting for the full-mode unit`.
- [ ] **AC-0008.** The same section contains `stays whole and goes to full mode`, `stops the whole bundle`, and `kept as observed work`.
- [ ] **AC-0009.** Light-mode.md's `## Editing existing agent guidance` section contains `fires no trigger by being guidance`, `still faces every trigger on its other effects`, `does not count as a durable product contract`, `content-pin test`, and `reads only the edited section`. The durability-row table carries a row beginning `A public or durable product behavior contract` that contains `**tool surface**`, `**authority or gate**`, `**security boundary**`, and `**published schema**`, and both tables keep their current row counts.

### Regression, evals, guide, release

- [ ] **AC-0010.** `packs/core/tests/skills/work-loop/test_work_intake_dispatch.py` passes unedited, and `packs/core/tests/skills/work-loop/test_evidence_modes_contract.py` passes with only `test_t5_pack_versions_are_3_1_27` removed.
- [ ] **AC-0011.** `work-loop`'s `evals/evals.json` holds these nine new cases, each with `id`, `prompt`, `expected_output`, and a non-empty `assertions` list, and each `expected_output` containing its verdict phrase: `bundle-split-independent-tasks` (`one unit per task`), `bundle-unsplittable-shared-file` (`full mode`), `bundle-late-unit-strays` (`whole bundle`), `guidance-edit-plain-runs-light` (`light mode`), `guidance-new-file-fires-structural` (`structural trigger`), `guidance-edit-tool-surface`, `guidance-edit-authority-or-gate`, `guidance-edit-security-boundary`, and `guidance-edit-published-schema` (each `full mode`). In the case `risk-trigger-modify-not-touch`, `expected_output` and at least one `assertions` entry each contain `existing agent guidance`, `only when it changes`, `policy`, and `interface document`, and no field contains `so editing it fires the trigger` or `agent guidance, policy, an interface document -- fires the trigger`, and `test_evals_json_shape` in `packs/core/tests/skills/work-loop/test_loop_engine.py` passes.
- [ ] **AC-0012.** `guides/core/how-to/plan-and-execute-non-trivial-work.md`'s pitfall on reaching for `new-spec` contains `one unit per task`, `existing agent-guidance file`, `tool surface`, `authority or gate`, `security boundary`, and `published schema`.
- [ ] **AC-0013.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` both carry version `3.1.28`; exactly one file under `docs/product/changelog.d/` added by this change names package `core` at version `3.1.28` and has a `-` bullet under `## Highlights`; and `python3 tools/changelog.py render --output .context/changelog-render.md` exits 0.
- [ ] **AC-0014.** `agentbundle catalogue lint --root . --deep` and `agentbundle catalogue verify --root .` exit 0, and `make build-self` leaves no tracked change after the delivery commit.

## Follow-ons

- eugenelim: none filed — the experiment RFC-0111 describes (the first 10 pack changes after release) is the owner's to run.

## Assumptions

none
