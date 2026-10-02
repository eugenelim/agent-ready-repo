# Gate JavaScript shipped in pack skills

- **Slug:** `pack-javascript-ci-workflow`
- **Status:** Accepted
- **Accepted:** 2026-10-02 by eugenelim, lifecycle owner. Basis: explicit owner approval after the remote, path-scoped workflow constraint was incorporated and the resulting intent completed an independent intent-mode shaping review with no malformed findings.
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **De-risked:** no
- **Shaping-reviewed:** 2026-10-02
- **Decomposed:** 2026-10-02 spec

## Outcome

- **Input (steerable):** One dedicated remote workflow is manually dispatchable and automatically runs only for changes to pack JavaScript, its tests, manifests, lockfiles, or the workflow and policy code that governs them. It installs all 2 pack-owned npm projects from committed lockfiles and executes all 3 suites in the 1 existing pack JavaScript test directory.
- **Outcome (lagging):** Maintainers can offload pack JavaScript verification to remote CI and receive a trustworthy verdict on dependency drift, supported-severity advisories, install-script policy, and existing render-proof behavior.
- **Guardrail:** The new workflow adds no work to existing CI jobs or default local gates, unrelated changes do not trigger it automatically, and `node_modules` or cache residue never enters a catalogue or source archive.

## Opportunity

Maintainers need pack JavaScript and its dependency graph checked reproducibly without increasing baseline feedback time or consuming local machine capacity for dependency installation and the full JavaScript suite.

- **Functional job:** Change JavaScript shipped by a pack and get one trustworthy verdict for dependency installation, dependency policy, and existing behavior tests.
- **Emotional job:** Be confident that a green pull request did not skip the pack's JavaScript because its source lives under a hidden `.apm` directory.
- **Social job:** Show reviewers a repeatable, least-privilege check instead of asking them to trust an unrecorded local `npm install`.
- **Struggling moment:** Both pack npm projects lack committed lockfiles, the only pack JavaScript test directory has no CI runner, and the two repository-wide npm policy walks prune the `.apm` directory that contains both projects.

## Current evidence — 2026-10-02

- [The shipped pack-test boundary](../../specs/pack-test-boundary-remaining-packs/spec.md) moved three standalone JavaScript suites to `packs/converters/tests/skills/render-proof/`. No workflow invokes them. `tools/lint-pack-test-boundary.py` therefore carries one live `_NO_RUNNER` exemption for that directory.
- The repository has exactly two pack-owned `package.json` files: `render-proof` declares 9 caret-ranged runtime dependencies, while `markdown-to-html` pins 2 exact versions. Neither project has a `package-lock.json`.
- `.gitignore` ignores `package-lock.json` tree-wide and only re-includes the `web/` and `docs-site/` lockfiles. Those two site projects use `npm ci`; no workflow runs `npm ci`, `npm audit`, or a JavaScript suite for a pack skill.
- `tools/audit-npm.py` and `tools/lint-npm-allow-scripts.py` discover lockfiles by walking the repository, but both prune every dot-directory. A lockfile committed beside either pack `package.json` under `.apm/skills/` would therefore be invisible to both gates unless their discovery contract changes.
- `packs` is already in `Makefile`'s `SAST_DIRS`, so a pack lockfile-only diff already selects the SAST/SCA job. The missing link is audit discovery under the canonical `.apm` project roots, not another `SAST_CONFIG` entry.
- The repository already uses dispatch-only remote workflows for heavyweight corpus and roster suites. A dedicated pack JavaScript workflow can follow that offload model while adding path-scoped automatic runs for only its owned files.
- Catalogue and source-package tests already prove that `node_modules` and cache directories are pruned from archives. CI still needs to keep installs job-local so unrelated test setup does not traverse or copy dependency residue.

## What this intent requires

- Commit lockfiles for both current pack npm projects and enforce package/lockfile parity for later pack-owned npm projects, rather than relying on a hand-maintained list that can omit the next project.
- Add a new dedicated remote workflow with `workflow_dispatch` and path-scoped automatic triggers. Its automatic scope covers pack JavaScript source, JavaScript tests, package manifests, lockfiles, and the workflow or npm-policy code whose changes can alter its verdict; unrelated changes do not start it.
- Keep this work out of existing CI jobs and default local gates. Local JavaScript tests remain available for focused development feedback, but a dispatched remote run is the preferred verification path and completion evidence.
- Use the repository's Node 24 line and `npm ci --ignore-scripts --no-audit` in that workflow. Run `renderer.test.js`, `security.test.js`, and `pipeline.test.js` from their documented working directory with dependencies resolved from the `render-proof` skill.
- Extend npm audit and install-script-policy discovery only through the canonical pack project roots. Preserve pruning for unrelated hidden directories and `node_modules`, and add positive and negative tests that prove `.apm` lockfiles are included without broadening the walk to arbitrary hidden content.
- Declare every dependency install script by exact `name@version` in the sibling `allowScripts` map when the generated lockfiles show one. Do not bypass the existing install-script gate.
- Remove the render-proof `_NO_RUNNER` entry only after the real runner is present. Keep the lint's inverse check so a future exemption cannot coexist with a runner.

## Assumptions

- **Riskiest assumption:** one path filter can stay narrow enough to avoid unrelated runs while still covering every source, test, dependency, workflow, and policy change that can alter the remote JavaScript verdict.
- Both pack projects and all three existing suites are compatible with the repository's Node 24 runner once installed from generated lockfiles.
- A bounded discovery rule can admit committed lockfiles below `packs/*/.apm/skills/*/` without admitting dependency residue or unrelated hidden directories.
- **Knowledge surface:** the in-repository workflow, npm-gate, pack-boundary, package manifest, archive-test, and product-intent corpus at revision `2f33168e489345e386977012d553f26b26cdaa8f`.

## Non-goals

- JavaScript SAST coverage belongs to [`sast-scanner-coverage-expansion`](sast-scanner-coverage-expansion.md); dependency auditing and behavior tests do not substitute for it.
- Dependabot wiring remains separate from the merge-time audit gate.
- Existing required CI jobs and default local gates are not expanded with pack dependency installation or JavaScript suite execution.
- This intent does not change render-proof or markdown-to-html runtime behavior, add tests where none exist, or rewrite frozen ADR/spec history.

## Decomposition

The approved [spec](../../specs/pack-javascript-ci-workflow/spec.md) and
[plan](../../specs/pack-javascript-ci-workflow/plan.md) own this delivery as one
integration: canonical pack npm policy, reproducible dependency state, a
separate path-scoped remote workflow, and recorded GitHub execution evidence.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 2f33168e489345e386977012d553f26b26cdaa8f
