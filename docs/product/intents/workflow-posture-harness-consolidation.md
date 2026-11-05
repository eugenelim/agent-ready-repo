# Consolidate workflow-posture harnesses without weakening their contracts

- **Slug:** `workflow-posture-harness-consolidation`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Decomposed:** 2026-11-05 brief

## Outcome

The pages workflow checks run on the shared posture harness with each check's mutation count and family coverage unchanged, and a missing `persist-credentials: false` in any workflow is caught by one dedicated guard. The build-check workflow check stays outside the harness and keeps its own regex model, as an excluded part with its own contract.

## Opportunity

The remaining posture checks duplicate driver mechanics, and the required build-check workflow check re-implements YAML structure with regular expressions, which has repeatedly created modelling bypasses.

## What this absorbs

### ci-gate-parallelization-posture-test-yaml-parser

- **Authority:** [spec/ci-gate-parallelization](../../specs/ci-gate-parallelization/spec.md)
- `tools/test-build-check-workflow.py` still models YAML with regex helpers, including `_key_re`, `_key_values`, `_sub_mapping`, `_step_key_values`, `_run_body`'s three-style folding, `_steps`, `_job_ids`, and both `*-modelled` fail-closed checks.
- Five of six adversarial review rounds found YAML-MODELLING root causes rather than security-reasoning defects: scalar folding, duplicate keys, inferred base indent, a positive substring over a block, and key-spelling encodings.
- The recorded fix is `yaml.safe_load` plus structural comparison, retiring those helpers and checks in exchange for one assumption: PyYAML resolution matches the GitHub Actions parser.
- Do not assume that equivalence. Check duplicate keys, escaped keys, explicit keys, and anchors before adopting it.
- This was deliberately excluded from the original spec because it reverses the file's stdlib-only rationale and adds an import to the job that wears the sole required check; the owner chose stdlib.

### workflow-posture-self-test-helper-extraction

- The shared posture harness already serves `tools/test-ci-security-workflow.py`, pack-evals, build-check-windows, and CodeQL. It owns the baseline-clean precondition, no-op rejection, expected-label check, family accounting, and failure and success reports.
- Each caller retains its own `audit`, `_MUTATIONS`, and predicates because they express unrelated workflow contracts. The extraction moved 188 lines from the four callers while keeping every caller's mutation count and family coverage byte-identical at that commit; re-measure rather than copying figures that later mutations can stale.
- The remaining modules are `tools/test-build-check-workflow.py`, `tools/test-pages-workflow.py`, and `tools/test-pages-concurrency.py`. The inclusion predicate is a module under `tools/` with module-level `audit()` and a `_MUTATIONS` self-test whose baseline is a real `.github/workflows/*.yml` file.
- Preserve build-check's bash differential and shape-stable fixture, pages' crafted-input predicates, and pages-concurrency's four-element `(id, expected, old, new)` mutation tuple. Decide whether that four-element tuple joins the harness or remains separate.
- `tools/test_marketplace_envelope_parity.py` is deliberately outside the set: it is a pytest-parametrized three-tuple over filesystem fixtures with no `audit()` or workflow baseline, so a bare `_MUTATIONS` search overcounts by one.
- Prove that every converged caller's mutation count and family coverage are unchanged, using the same acceptance criterion already satisfied by the four shared-harness callers.

### workflow-posture-guard-coverage-gaps

- Added 2026-08-31 by the catalogue-tooling token-posture change, this gap is registered rather than presumed covered.
- `tools/check-zizmor-excessive-permissions.py` filters only the `excessive-permissions` ident. Adding a workflow to its `WORKFLOWS` tuple makes that workflow's top-level `permissions:` durable but says nothing about checkout `persist-credentials:`.
- `persist-credentials: false` is zizmor's separate `artipacked` finding. The broad gate uses `--min-severity high`, while `artipacked` is medium, so removing the setting from any checkout in any workflow still passes.
- Decide whether this guard gains a second ident despite its scoped name and docstring, a sibling guard owns `artipacked`, or the broad gate lowers its floor for that ident alone.

## Assumptions

- PyYAML equivalence with the GitHub Actions parser must be demonstrated for duplicate keys, escaped keys, explicit keys, and anchors before a structural parser replaces the regex model.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

**Riskiest assumption:** moving the pages tests onto the shared harness keeps each caller's mutation count and family coverage unchanged. Agent-only test: record both numbers before the move and require them equal after.

## Non-goals

- The regex model in `tools/test-build-check-workflow.py` is not replaced by a YAML parser, and that file is not moved onto the shared harness.
- Callers keep their own `audit`, mutation lists and predicates; only driver mechanics are shared.
- `tools/test_marketplace_envelope_parity.py` stays outside the harness set.

## Readiness

Route: brief, [`workflow-posture-pinning-delivery`](../briefs/workflow-posture-pinning-delivery.md). Decided: keep the stdlib regex model in `tools/test-build-check-workflow.py`; the job that wears the required check does not gain a parser, so the PyYAML equivalence question is closed unless a modelling bypass recurs. The `artipacked` gap gets a sibling guard (slice P2). Moving `test-pages-workflow.py` and `test-pages-concurrency.py` onto the shared harness is slice P3, proved by unchanged mutation counts and family coverage.
