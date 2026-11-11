# Test runner boundary completion

- **Slug:** `test-runner-boundary-completion`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **De-risked:** 2026-11-05
- **Governed by:** [spec/build-check-coverage-gaps runner-boundary follow-on](../../specs/build-check-coverage-gaps/spec.md); [spec/site-browser-quality-gate review](../../specs/site-browser-quality-gate/spec.md)

## Outcome

Every in-scope tool and end-to-end test has an invoked runner or an explicit, recorded no-runner contract.

## Opportunity

The repository has reported possible uninvoked tests, but the current orphan inventory cannot be settled from the available local evidence.

## What this absorbs

### tools-test-runner-boundary

Extend the runner/no-runner discipline to `tools/test*.py`. Re-inventory the current orphans. `tools/test_guide_typed_asides.py` is a sanctioned no-runner archival case. Every other uninvoked test needs a runner or a recorded no-runner disposition. Evidence is indeterminate because the required rule lookup was blocked before repository inspection. Unblocks when the current inventory identifies each `tools/test*.py` invocation or no-runner disposition.

### e2e-spec-runner-boundary

`docs-wayfinding.spec.ts` was reported as invoked by no Makefile line, workflow, or package script. `tools/test_browser_gate_subset.py` records it in `EXCLUDED_BY_SCOPE` with a stated reason, so it is a deliberate exclusion from the deploy gate rather than an unrecorded orphan; whether it has any other runner is open. Decide whether orphaned `web/src/test/e2e` specs receive a runner or an explicit on-demand contract. Evidence is indeterminate because the required rule lookup was blocked before repository inspection. Unblocks when the current Makefile, workflow, and package-script inventory establishes the runner or on-demand contract for every orphaned end-to-end spec.

## Assumptions

- A current inventory of `tools/test*.py`, Makefile lines, workflows, and package scripts is required to settle both reported orphan sets.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

**Riskiest assumption:** the 14 files found by basename search are true orphans, with no sweep that runs them. Agent-only test: list the files collected by the `make test` pytest lines and runners with `make -n test` and `pytest --collect-only`, and confirm none of the 14 appears.

## Non-goals

- No test is deleted to clear the inventory; each of the 14 gets a runner or a recorded no-runner reason.
- Sanctioned archival no-runner cases such as `tools/test_guide_typed_asides.py` stay as they are.
- The `docs-wayfinding.spec.ts` exclusion from the deploy gate stays; only unrecorded specs need a disposition.

## Readiness

Route: new-spec, one session.

Inventory taken 2026-11-05 by searching `Makefile`, `.github/`, `tools/repo/`, `tools/*.py`, `tests/` and the catalogue tooling for each basename: 14 `tools/test*.py` files have no named runner. Eleven `test_*.py` files pass when run directly (166 passed, 6 subtests, 22 s): `test_add_rendering_directives`, `test_agents_md_readability_floor`, `test_brief_slug_matches_filename`, `test_build_site_dry_run`, `test_check_output_readability`, `test_enterprise_rollout_playbook`, `test_lint_agents_md_progressive_disclosure`, `test_lint_harness`, `test_live_demo_guide`, `test_score_cognition` and `test_score_finding_responses`. Three hyphenated scripts are also unreferenced: `test-check-atlassian-phase3-readiness.py` (2 of 15 tests fail), `test-check-contract-drift.py` (exits 1) and `test-release-jsonl-otlp-exporter-workflow.py` (passes under pytest, 6 tests). The e2e side is settled for `docs-wayfinding.spec.ts` (recorded in `EXCLUDED_BY_SCOPE`); `docs-asides.spec.ts` and `screenshots.spec.ts` still need a recorded disposition.

First slice: a stdlib lint, modelled on `_NO_RUNNER` in `tools/lint-pack-test-boundary.py`, that fails when a `tools/test*.py` has neither a runner nor a recorded no-runner reason; wire the 12 passing files into runner lines, and give the two failing ones a fix or a recorded reason. Proof: the lint passes on the real tree and fails on a seeded unlisted test file.

## De-risk result

2026-11-05. Ran `make -n test` and `make -n build-check` and counted each of the 14 file names in the printed commands; earlier searches of `.github/`, `tools/repo/` and `tests/` found none either. Result: 0 of 14 appear in any command, so none is collected by a sweep or a runner. Verdict: the assumption holds, the 14 are true orphans. Two of them also fail when run directly (`test-check-atlassian-phase3-readiness.py` 2 of 15 tests, `test-check-contract-drift.py` exit 1), so wiring them in needs a fix or a recorded no-runner reason first.
