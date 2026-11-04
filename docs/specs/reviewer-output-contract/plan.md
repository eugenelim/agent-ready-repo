# Plan: reviewer output contract

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** refusal vocabulary in `packs/core/.apm/skills/work-loop/scripts/review-artifact.py` (`_actionable_review_text`, `_classify_raw_report`, `RAW_REFUSAL_REASONS`); flagless refusal-code tests in `packs/core/tests/pack/test_finding_adjudication_contract.py` (`test_remaining_refusal_codes_are_pinned`); the template wire-format pin in `packs/core/tests/skills/work-loop/test_reviewer_lens_ownership.py` (`test_reviewer_finding_wire_format_survives`); roster schema tests in `tests/roster/test_review_gate_schemas.py`. Non-structural.

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
> attempt is open.

## Approach

The classifier change lands first because both agent files cite its new reason. Then each agent file gains its anchor rule and a concrete example line, and the experience reviewer gains a Typed report section copied in shape from the adversarial reviewer's. A roster test ties both agent files to core's parser and to the delivery schemas. Versions, fragments, and projections close the change. The riskiest part is keeping the three-reviewer template pin green while adding the rule.

## Constraints

- `packs/AGENTS.md` § Version bump rule: patch for changed content, `pack.toml` and `plugin.json` together.
- `packs/AGENTS.md` § Shipped pack content carries no internal-governance citations.
- `tools/lint-pack-test-boundary.py` check 8: a pack test may not read another pack or `contracts/`, so cross-pack assertions live in `tests/roster/`.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** run `review-artifact.py raw-classify` on the probe report that lacks anchors and record stderr in the ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Agent guidance | T2, T3 | content and round-trip tests green | projections regenerated, self-host diff empty |
| Interface compatibility | T3 | roster field-name test green | schema bytes equal the merge base |
| Maintainer procedure | T1 | refusal-reason tests green | suites green at the delivery commit |
| Release history | T4 | version-equality checks | `tools/check-core-release.py` output in the ledger |

## Design (LLD)

### Behavior & rules

- `finding-unanchored` is decided after parsing: a report with zero parsed findings and at least one line whose stripped form starts with `**<digits>.` is unanchored. The check runs only where the base reaches `sentinel-absent` (raw) or `no-actionable-result` (flagless), so a clean signal, a sentinel elsewhere in the report, or an adjudication envelope keeps its current result. Any parsed finding keeps classification `findings`, so a mixed report is unchanged. Traces to AC-0001, AC-0002, AC-0003, AC-0004.
- In `_classify_raw_report` the reason replaces `sentinel-absent` and joins `RAW_REFUSAL_REASONS`. In `_classify_report` it replaces `no-actionable-result` on the flagless path only; the strict adjudication path refuses earlier with `sustained-line-shape` and is untouched. The detector is one module-level regex reused by both sites.
- The template placeholder `` `path/to/file.ext:line` `` stays, because `test_reviewer_finding_wire_format_survives` pins it for three reviewers; it does not parse (`line` is not digits), so the rule adds a separate concrete example such as `` **1. Unvalidated input.** `src/loader.py:42`. ... Fix: ... `` that does.
- `Where:` stops at the first period, so a filename in it truncates the fingerprint location and fails the strict shape; the experience rule routes any file location to the backticked form.
- Experience-reviewer `material` means Blocker or Major whose defect something external establishes; its severities are blocker/major/minor/nit, so Major is the Concern analogue.

Owned by: T1 (rules 1–2), T2 and T3 (rules 3–5).

## Tasks

### T1: Unanchored reports are refused as `finding-unanchored`

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/scripts/review-artifact.py`, `packs/core/tests/pack/test_finding_adjudication_contract.py`

**Tests:**
- TDD, CLI subprocess over fixture reports in `test_finding_adjudication_contract.py`, one parametrized case per report AC-0001, AC-0002, AC-0003, and AC-0004 name: the AC-0001/AC-0002 unanchored report, the four AC-0003 reports, and the AC-0004 mixed report, each written inline in the test.
- The existing `no-actionable-result` case in `test_remaining_refusal_codes_are_pinned` stays green unchanged.

**Done when:** the new cases and the whole `packs/core/tests/pack/test_finding_adjudication_contract.py` suite pass.

### T2: adversarial-reviewer states the anchor rule

**Depends on:** T1

**Touches:** `packs/core/.apm/agents/adversarial-reviewer.md`, `packs/core/.apm/agents/quality-engineer.md` (owner-approved: its `## Typed report` section is pinned byte-identical to adversarial-reviewer's, so the `evidence_refs` line changes in both), `packs/core/tests/pack/test_finding_adjudication_contract.py`, `packs/core/.apm/skills/work-loop/evals/evals.json`

**Tests:**
- Goal-based content test in `test_finding_adjudication_contract.py` over the `## Report numbered findings` through `## Typed report` sections: AC-0005's four statements.
- An eval case `unanchored-report-names-rule` and a shape check on its expected output (AC-0012).
- `test_reviewer_finding_wire_format_survives` and `test_review_depth_and_verdict_contract.py` stay green.

**Done when:** the content test, the eval shape check, and `packs/core/tests/skills/work-loop/test_reviewer_lens_ownership.py` pass.

### T3: experience-reviewer states the anchor rule and a typed report

**Depends on:** T1, T2

**Touches:** `packs/experience-design/.apm/agents/experience-reviewer.md`, `tests/roster/test_reviewer_output_contract.py`

**Tests:**
- Goal-based roster test over the experience output and Typed report sections (AC-0007, AC-0009, AC-0010, AC-0011).
- Round trip: every finding-marker line holding no `<` in either agent file parses as exactly one finding through `review-artifact.py`'s `parse_findings` and matches `STRICT_SUSTAINED_FINDING_LINE_RE`; each file carries at least one such line, and the experience file one per form (AC-0006, AC-0008).
- AC-0009's sets are read from the schemas, not copied into the test.

**Done when:** `python3 -m pytest tests/roster/test_reviewer_output_contract.py -q` passes locally and on the dispatched `test-roster.yml` run.

### T4: Release and projections

**Depends on:** T2, T3

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `packs/experience-design/pack.toml`, `packs/experience-design/.claude-plugin/plugin.json`, `docs/product/changelog.d/*.md`, adapter projections

**Tests:**
- Goal-based, at delivery against the merge base with freshly fetched `origin/main`: both version pairs (AC-0013), both fragments (AC-0014), `tools/check-core-release.py --base <merge-base>` (AC-0015), `git diff --exit-code <merge-base> -- contracts/delivery/review-report.v1.schema.json contracts/delivery/finding.v1.schema.json` (AC-0016), and an empty self-host diff (AC-0017).

**Done when:** each command above exits 0 and its output is recorded in `notes/verification-ledger.md`.

### T5: The unanchored-report eval surfaces and stops

**Depends on:** T4

**Touches:** `packs/core/.apm/skills/work-loop/evals/evals.json`

**Tests:**
- The `unanchored-report-names-rule` case's expected output and assertions follow the skill's `invalid` route: the controller surfaces and stops, names `finding-unanchored` and the backticked `path:line` anchor rule as the recovery, and waits for direction instead of redispatching the reviewer or recording the round (AC-0012). `test_unanchored_report_eval_names_the_rule` stays green.

**Done when:** `packs/core/tests/pack/test_finding_adjudication_contract.py` passes and the case's text names no redispatch.

## Rollout

Pure guidance and classifier-diagnostic change; ships with the pack versions. Rollback is a revert. No persisted state changes, because the reason is not stored in records.

## Risks

- Task E also bumps Core; whichever merges second re-derives the version at rebase.
- `test-roster.yml` is dispatch-only, so T3's suite gates nothing on the PR; its dispatched run is the evidence.

## Changelog

- 2026-11-04: spec approved by eugenelim (scope).
- 2026-11-04: plan approved by eugenelim (build strategy).
