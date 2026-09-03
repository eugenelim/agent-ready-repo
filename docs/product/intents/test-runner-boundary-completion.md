# Test runner boundary completion

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/build-check-coverage-gaps runner-boundary follow-on](../../specs/build-check-coverage-gaps/spec.md)
- **Authority:** [spec/site-browser-quality-gate review](../../specs/site-browser-quality-gate/spec.md)

## Outcome

Every in-scope tool and end-to-end test has an invoked runner or an explicit, recorded no-runner contract.

## Opportunity

The repository has reported possible uninvoked tests, but the current orphan inventory cannot be settled from the available local evidence.

## What this absorbs

### tools-test-runner-boundary

Extend the runner/no-runner discipline to `tools/test*.py`. Re-inventory the current orphans. `tools/test_guide_typed_asides.py` is a sanctioned no-runner archival case. Every other uninvoked test needs a runner or a recorded no-runner disposition. Evidence is indeterminate because the required rule lookup was blocked before repository inspection. Unblocks when the current inventory identifies each `tools/test*.py` invocation or no-runner disposition.

### e2e-spec-runner-boundary

`docs-wayfinding.spec.ts` was reported as invoked by no Makefile line, workflow, or package script. Decide whether orphaned `web/src/test/e2e` specs receive a runner or an explicit on-demand contract. Evidence is indeterminate because the required rule lookup was blocked before repository inspection. Unblocks when the current Makefile, workflow, and package-script inventory establishes the runner or on-demand contract for every orphaned end-to-end spec.

## Assumptions

- A current inventory of `tools/test*.py`, Makefile lines, workflows, and package scripts is required to settle both reported orphan sets.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
