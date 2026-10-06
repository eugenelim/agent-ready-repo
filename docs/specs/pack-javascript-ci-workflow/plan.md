# Plan: Pack JavaScript CI workflow

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** [ADR-0083](../../adr/0083-extend-sast-sca-gate-to-npm-with-audit-and-allowlist.md); [`docs/architecture/reference.md`](../../architecture/reference.md); [`docs/architecture/verification-graph.md`](../../architecture/verification-graph.md); [`docs/architecture/pack-layout.md`](../../architecture/pack-layout.md); `.github/workflows/test-corpus.yml` and its posture pattern; `tools/audit-npm.py`, `tools/lint-npm-allow-scripts.py`, and their self-tests; `tools/lint-pack-test-boundary.py`; the two canonical Converters npm manifests and three render-proof JavaScript suites. Named deviations: (1) repository-wide npm discovery prunes every dot-directory, so the canonical `.apm` route needs an explicit admission rather than a broader walk. (2) `tools/npm_project_discovery.py` confines its own traversal with the standard library rather than the root `AGENTS.md`-blessed `agentbundle.catalogue_tooling.file_safety`, on one ground only: `tools/AGENTS.md` requires pure-stdlib additions under `tools/`, and the two consumers this factors out — `tools/audit-npm.py` and `tools/lint-npm-allow-scripts.py` — already carry stdlib pruning that this change preserves rather than introduces. It is NOT grounded on the helper being unreachable from `tools/`: `tools/check-output-readability.py` loads `file_safety.py` by path through `importlib.util.spec_from_file_location` precisely so a `tools/` file can use it without a package import, and `tools/repo/build_gate_chain.py` already resolves `packages/agentbundle` for chain steps. Because the helper is reachable, its *confinement* refusals are stated as acceptance criteria instead of being assumed: AC-0005 and AC-0006 carry the per-route traversal rules and the regular-file-and-no-link rule for each discovered manifest and lockfile, and AC-0015 carries the `.npmrc` scan's own scope. Its *budget* refusals are not restated and are consciously accepted: `file_safety` raises `BoundExceeded` on entry count, depth, file count, per-file bytes and total bytes, and no criterion here states a ceiling. The accepted residual is that AC-0015's deliberately unpruned repository-wide walk runs unbounded inside the build-check gate on a fork `pull_request`; it is bounded only by that job's own `timeout-minutes: 25`, which this spec does not own. Revisit if that walk is ever moved to a surface with no job timeout.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/pack-javascript-ci-workflow/notes/verification-ledger.md`.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval.

## Approach

Teach one shared, standard-library discovery layer to admit lockfiles only under canonical pack skill roots while retaining the existing visible-tree walk and prune rules. Use that inventory to enforce manifest/lock parity, approved registry provenance, and the absence of repository npm configuration; commit the two current lockfiles; and keep npm audit in `make sast`. Add one separate GitHub Actions workflow whose own focused construction test pins its paths, registry configuration, posture, Node runner commands, and non-interference with existing gates; then prove the shipped route with the automatic pull-request run and a post-merge dispatch.

## Constraints

- [ADR-0083](../../adr/0083-extend-sast-sca-gate-to-npm-with-audit-and-allowlist.md) remains unchanged: `tools/audit-npm.py` runs through `make sast`, and the new workflow never invokes it.
- Existing workflows and default local gates gain no pack dependency installation and no JavaScript test. Their existing npm policy steps may inspect the newly admitted lockfiles, and the build-check chain gains the canonical pack-project policy step this delivery adds — a repository-only static check that installs nothing and runs no JavaScript, which AC-0002 admits by name.
- `tools/AGENTS.md` requires pure-stdlib additions and shared lint/self-test harnesses for a new single-rule lint.
- `packs/AGENTS.md` keeps `.apm/` as authored source, requires a non-cosmetic Converters patch bump and eval-harness disposition, and requires a self-host build. `packs/AGENTS.local.md` requires matching pack/plugin versions, a free-standing release entry, and a `Highlights` decision.
- The workflow follows the fleet posture: SHA-pinned actions already used in the repository, read-only permissions, standard hosted runner, no secret or cache surface, finite timeout, and non-persisted checkout credentials.
- The spec/plan pair is repository-durable at `docs/specs/pack-javascript-ci-workflow/`. Its approval fingerprint is recorded by the work-loop; implementers, reviewers, CI, and close-work read it. The verification ledger becomes the stable post-closeout evidence owner and remains repository-durable.
- No external interface contract or new dependency applies.
- Grounding probe: `explore-grounding.py --phase discovery` found `Makefile` as the audit runner, no runner for either pack manifest or the render-proof test directory, and `docs/architecture/verification-graph.md` plus `docs/architecture/pack-layout.md` as current-state owners.
- Pre-review disconfirming probe: `git check-ignore -v --no-index` reports both proposed pack lockfiles ignored by `.gitignore`'s tree-wide `package-lock.json` rule and a nested dependency file ignored by `node_modules/`; T2 therefore adds a canonical-lock negation without weakening the dependency-residue rule.

## Construction tests

Most construction tests live under **Tasks** below.

**Integration tests:** Run both npm policy self-tests, their real-repository checks, the pack-project parity self-test, the pack-test-boundary self-test and lint, the workflow posture self-test, `lint-ci-parity`, Converters packaging inspection, and the repository's lightweight Python gates. The new remote workflow then runs policy, install, and all three JavaScript suites in one clean checkout.

**Manual verification:** Record the automatic pull-request run, the existing `gate-sast` run and its pack-lock audit lines, then dispatch the workflow after its definition reaches the default branch and record the run reference. Local JavaScript execution is optional and is not completion evidence when remote dispatch is available.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current verification topology in `docs/architecture/verification-graph.md` | T5 | Workflow posture and trigger tests | `close-work` compares the workflow roster and responsibility split to the shipped YAML |
| Maintainer dispatch procedure in `AGENTS.md` | T5 | Command reviewed against the workflow filename and ref contract | `close-work` verifies the command remains usable and labels the run as scoped evidence |
| Converters release history in `docs/product/changelog.md` | T2, T5 | Version-pair, marketplace regeneration, and changelog checks | `close-work` verifies a free-standing release entry and the recorded no-Highlights reason |
| Delivery evidence in `notes/verification-ledger.md` | T1-T6 | Focused gate results and remote run references | `close-work` verifies every AC mapping and the post-default-branch dispatch |

## Design (LLD)

### Design decisions

Npm audit remains an existing SAST responsibility. The new workflow owns reproducible installation and JavaScript behavior only; duplicating audit there was rejected because ADR-0083 D1 names `make sast` as its gate and the user confirmed that split. Existing jobs gain no JavaScript work. Traces to: AC-0002, AC-0005, AC-0013. Owned by: T1, T4, T6.

Canonical pack npm discovery has two inputs: the ordinary visible-tree walk and the bounded `packs/*/.apm/skills/*/` project shape. It does not turn off dot-directory pruning globally. A shared helper prevents audit, install-script policy, and parity from carrying three subtly different definitions. Traces to: AC-0004–AC-0006. Owned by: T1.

The workflow has `workflow_dispatch` and a path-scoped `pull_request` event only. Pull-request execution supplies automatic pre-merge evidence without a duplicate push run; post-merge dispatch proves the manual activation boundary. Traces to: AC-0001, AC-0013. Owned by: T3, T4, T6.

### Interfaces & contracts

The operational interface is the workflow filename and its input-free manual dispatch. It publishes no repository API, event schema, or reusable `workflow_call` contract, so no `contracts/` artifact applies. The pull-request path set is parsed by the focused construction test rather than restated in another workflow. Traces to: AC-0001, AC-0011. Owned by: T3, T4.

### Failure, edge cases & resilience

Discovery fails closed on an unreadable in-scope directory, an empty canonical inventory, a manifest/lock mismatch, an unapproved or incomplete lockfile locator, or any repository `.npmrc` filename. Parity, provenance, npm-configuration, and install-script policy checks precede installation and packaging. The workflow pins and verifies the effective registry and host-replacement behavior, and installation uses `--ignore-scripts --no-audit`; a failed policy check cannot fetch dependency code, execute dependency code, or duplicate the advisory request owned by `make sast`. Each suite is a separate command, so the workflow names the failing file. A job timeout bounds registry or test stalls. Event-aware concurrency uses the platform-issued pull-request number to cancel only superseded work for that pull request and the platform-issued run ID to isolate every manual dispatch; fork-controlled inputs never form a concurrency key. Traces to: AC-0003, AC-0004, AC-0007–AC-0009, AC-0014, AC-0015. Owned by: T1, T4, T5.

### Dependencies & integration

The workflow uses the repository's Node 24 line, npm's committed-lockfile mode, standard GitHub-hosted Ubuntu, and no cache. Pack content remains under Converters ownership; repository-only discovery and workflow code remain under `tools/` and `.github/workflows/`. `lint-pack-test-boundary` reads the new workflow as a runner call site, while `lint-ci-parity` keeps the lane explicitly outside the local-parity scope. Traces to: AC-0003, AC-0008, AC-0010–AC-0012. Owned by: T2-T5.

## Tasks

### T1: Canonical pack npm projects are discovered once and fail closed on drift

**Depends on:** none

**Touches:** `tools/npm_project_discovery.py`, `tools/audit-npm.py`, `tools/test-audit-npm.py`, `tools/lint-npm-allow-scripts.py`, `tools/test-lint-npm-allow-scripts.py`, `tools/lint-pack-npm-projects.py`, `tools/test-lint-pack-npm-projects.py`, `tools/repo/build_gate_chain.py`, `tools/test_build_gate_chain.py`

**Review shape:** DEEP but localized supply-chain boundary; review the shared traversal and all three consumers together.

**Grounding:** Both existing consumers have a `discover_lockfiles(root)` seam and identical dot-directory and `node_modules` pruning. `tools/lint_harness.py` and `tools/selftest_harness.py` own new single-rule lint plumbing.

**Tests:**

- **VI-1001 (AC-0004):** `no stub (goal-based construction check)` — invoke the completed parity CLI against synthetic trees for zero projects, missing lock, orphan lock, a matched pair, a second future project admitted without roster edits, and an unrelated hidden project excluded.

- **VI-1002 (AC-0005):** `no stub (goal-based construction check)` — extend `tools/test-audit-npm.py` with positive canonical `.apm/skills/` and negative arbitrary-dot-directory, `node_modules`, symlink-directory, unreadable-directory, and visible-project cases; preserve canary and exit-code tests.
- **VI-1003 (AC-0006, AC-0007):** `no stub (goal-based construction check)` — extend `tools/test-lint-npm-allow-scripts.py` with the same traversal matrix, exact/stale/missing `allowScripts` cases, and a real-repository assertion derived from the canonical inventory.
- **VI-1004 (AC-0004, AC-0014, AC-0015):** `no stub (goal-based construction check)` — the parity, provenance, and npm-configuration self-test runs through the shared lint and self-test harnesses; covers unreadable in-scope input, approved registry plus integrity, and rejected git, file, link, non-HTTPS, another-host, missing-locator, and missing-integrity records; rejects a repository `.npmrc` by filename without reading it; and verifies stable diagnostic paths and exit codes.

**Approach:** Extract only traversal and canonical-project classification into the shared helper. Keep advisory parsing and install-script comparison in their current owners, and implement the parity rule on the shared inventory through the repository lint harness.

**Done when:** VI-1001–VI-1004 are green, both existing policy tools retain their current visible-project behavior, their real-repository output names every canonical pack lockfile, and `tools/lint-pack-npm-projects.py` has a standing gate home: it is chained into the build-check gate in `tools/repo/build_gate_chain.py` as a `_script_step` pair — its self-test first, then the lint — matching the `test-lint-npm-allow-scripts` / `lint-npm-allow-scripts` precedent, with the pairing pinned in `tools/test_build_gate_chain.py`. A hyphenated `tools/test-*.py` is collected by no sweep, so without this the control would run once by hand and never again.

### T2: Converters carries reproducible npm state without dependency-script execution

**Depends on:** T1

**Touches:** `.gitignore`, `packs/converters/.apm/skills/render-proof/package.json`, `packs/converters/.apm/skills/render-proof/package-lock.json`, `packs/converters/.apm/skills/markdown-to-html/package.json`, `packs/converters/.apm/skills/markdown-to-html/package-lock.json`

**Review shape:** MIXED generated dependency state plus two small manifest edits.

**Grounding:** The two manifests are the complete canonical pack inventory before this change. `.gitignore` currently ignores every `package-lock.json` except the two site projects.

**Tests:**

- **VI-1005 (AC-0004, AC-0007, AC-0014, AC-0015):** `no stub (goal-based)` — first run the filename-only npm-configuration check, then pin and verify the approved registry and host-replacement values before any fetch. Only after both controls pass, generate each lockfile under Node 24 using `npm install --package-lock-only --ignore-scripts --no-audit`, then run parity, provenance, and install-script-policy checks over the repository.
- **VI-1006 (AC-0007):** `no stub (goal-based check)` — a lockfile-derived set comparison proves each sibling `allowScripts` map equals the exact `name@version` set for entries carrying `hasInstallScript`; an empty set produces an explicit empty map.
- **VI-1007 (AC-0012):** `no stub (goal-based check)` — `git check-ignore --no-index` reports both canonical lock paths as unignored while `node_modules` beneath either skill remains ignored.

**Approach:** Generate locks without running lifecycle scripts, inspect the resulting install-script set, then add only those exact approvals. Add one generic `.gitignore` negation for canonical pack lockfiles rather than two project-specific exceptions.

**Done when:** VI-1005–VI-1007 are green and the diff contains no direct dependency-range change.

### T3: The pack-test boundary recognizes a JavaScript workflow runner

**Depends on:** none

**Touches:** `tools/lint-pack-test-boundary.py`, `tools/test-lint-pack-test-boundary.py`, `tools/test-pack-javascript-workflow.py`

**Review shape:** DEEP parser extension with positive, negative, and stale-exemption cases.

**Grounding:** `_workflow_runner_lines` inherits a pack test working directory only for lines recognized by `_PYTEST`; `_RUNNER_FILES` does not name the new workflow, and `_NO_RUNNER` currently names render-proof.

**Tests:**

- **VI-1008 (AC-0010, stub: true):** Materialize this candidate red standalone self-test unchanged as `tools/test-pack-javascript-workflow.py`; later cases in the same file pin workflow posture and triggers.

```python
#!/usr/bin/env python3
"""Focused construction tests for the pack JavaScript workflow."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from selftest_harness import run_cases


BOUNDARY_PATH = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "lint-pack-test-boundary.py"
)


def _load_boundary():
    # NOT `selftest_harness.load`: that helper never registers the module in
    # `sys.modules`, and `lint-pack-test-boundary.py` declares a frozen
    # dataclass at import time, which CPython resolves through
    # `sys.modules[cls.__module__]`. The shared loader therefore raises
    # `AttributeError: 'NoneType' object has no attribute '__dict__'` on this
    # subject. The registration line below is the whole difference.
    spec = importlib.util.spec_from_file_location("pack_js_boundary", BOUNDARY_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BOUNDARY = _load_boundary()


# STUB: AC-0010
def test_node_runner_inherits_pack_test_working_directory() -> None:
    workflow = """
steps:
  - name: renderer suite
    working-directory: packs/converters/tests/skills/render-proof
    run: node renderer.test.js
"""
    runners = BOUNDARY._workflow_runner_lines("pack-javascript.yml", workflow)

    assert any(
        "packs/converters/tests/skills/render-proof" in runner.tokens
        for runner in runners
    )


if __name__ == "__main__":
    raise SystemExit(run_cases(globals(), "pack-javascript-workflow"))
```

  Validation on 2026-10-02: `python3 -m py_compile` exits 0, and direct execution from disposable scratch reports the one case red because the current parser ignores explicit Node test commands.

  Loader deviation measured 2026-10-05, after spec-stage review asked why the stub does not use the shared loader. Substituting `selftest_harness.load("lint-pack-test-boundary.py")` and running from disposable scratch raises `AttributeError: 'NoneType' object has no attribute '__dict__'` at `tools/lint-pack-test-boundary.py:315`, because `load()` omits the `sys.modules` registration that CPython's `dataclasses._is_type` needs to resolve a frozen dataclass declared at import time. The shared loader serves subjects without that shape; it cannot serve this one. The local `_load_boundary` is kept with the reason recorded at the line.

- **VI-1009 (AC-0010):** `no stub (goal-based construction check)` — extend the existing boundary self-test so a Node step without a pack-test working directory is not a runner, each explicit Node suite line is recognized, a missing runner without an exemption fails, and a runner plus exemption fails.

**Approach:** Generalize workflow runner recognition only far enough to admit explicit `node <name>.test.js` or `node <name>.spec.js` commands. Keep pytest compatibility-class checks unchanged and add the new workflow to the closed runner-file inventory only when T4 creates it.

**Done when:** VI-1008 and VI-1009 are green and the render-proof exemption can be removed without weakening the inverse check.

### T4: A dedicated workflow installs pack projects and runs all render-proof suites

**Depends on:** T1, T2, T3

**Touches:** `.github/workflows/pack-javascript.yml`, `tools/test-pack-javascript-workflow.py`, `tools/lint-pack-test-boundary.py`, `tools/lint-ci-parity.py`, `tools/test-lint-ci-parity.py`

**Review shape:** MIXED workflow configuration and its focused mutation-backed construction test.

**Grounding:** `test-corpus.yml` supplies the repository's dispatch posture, Node 24 line, SHA-pinned checkout/setup actions, read-only permissions, and non-persisted credential pattern. `lint-ci-parity.py` requires every new workflow to receive an explicit scope disposition.

**Tests:**

- **VI-1010 (AC-0001):** `no stub (goal-based)` — the focused self-test parses the trigger set and path list, maps every pattern to an enumerated verdict-changing class, applies one positive fixture per admitted class, rejects unrelated pack source, skill documentation, non-JavaScript tests, unrelated tooling, and unrelated documentation, and mutates away each required trigger/path class or broadens a pattern to a parent selector.
- **VI-1011 (AC-0002, AC-0003):** `no stub (goal-based)` — the same test asserts the closed posture set, proves pull-request concurrency groups by platform-issued PR number with cancellation while manual dispatch groups by platform-issued run ID without cancellation, rejects fork-controlled key components, and scans pre-existing workflow/Make entry points for a call to the new workflow or a pack npm install/test command.
- **VI-1012 (AC-0008, AC-0009, AC-0014, AC-0015):** `no stub (goal-based integration)` — the workflow sets and verifies the approved registry and host-replacement values, runs parity, provenance, npm-configuration, and install-script policy first, dynamically installs every canonical project with `npm ci --ignore-scripts --no-audit`, and has three explicit Node suite steps under the render-proof working directory. The construction test rejects an install command that omits either flag, precedes a policy check, lacks either job-level registry setting, or lacks the effective-value preflight.
- **VI-1013 (AC-0010, AC-0011):** `no stub (goal-based integration check)` — the pack boundary lint, its self-test, the workflow self-test, and `lint-ci-parity.py` all exit 0; a mutation removing the workflow from either closed inventory fails its owning check.

**Approach:** Use one standard Ubuntu job. A bounded shell loop consumes the canonical manifest glob after parity has proved it non-empty and paired; the workflow never hand-lists current projects. Keep the three suite commands explicit so GitHub logs and the pack-test-boundary parser identify the failing suite.

**Done when:** VI-1010–VI-1013 are green and no existing workflow or local gate contains new JavaScript work.

### T5: Pack release state and current documentation match the shipped route

**Depends on:** T4

**Touches:** `packs/converters/pack.toml`, `packs/converters/.claude-plugin/plugin.json`, `marketplace.json`, `docs/product/changelog.md`, `docs/architecture/verification-graph.md`, `AGENTS.md`, `docs/specs/pack-javascript-ci-workflow/notes/verification-ledger.md`

**Review shape:** WIDE but mechanical release and documentation reconciliation after behavior is fixed.

**Grounding:** Converters is currently at 0.9.6 in both manifests. The root command list is the only current dispatch procedure, and `verification-graph.md` owns the remote workflow fleet.

**Tests:**

- **VI-1014 (AC-0012, AC-0014, AC-0015):** `no stub (goal-based)` — run manifest/lock parity, lockfile provenance, npm-configuration, and install-script policy before packaging; bump the Converters manifests together; run the required self-host build; inspect the built Converters artifact for both lockfiles and the absence of dependency/cache residue; and run catalogue verification.
- **VI-1015 (durable outputs):** `no stub (goal-based documentation check)` — the verification graph's workflow roster and responsibility text match the shipped workflow; the root command list dispatches the exact filename; documentation and link checks pass.
- **VI-1016 (release history):** `no stub (goal-based release check)` — the free-standing Converters release entry matches the version pair. Record no `Highlights` because the delivery changes maintainer verification and dependency reproducibility, not a skill outcome or user task.
- **VI-1017 (pack eval rule):** `no stub (owner decision)` — either a meaningful eval-harness change is verified, or the owner-approved no-change waiver records that no prompt, activation surface, rendering behavior, or output contract changed.

**Done when:** VI-1014–VI-1017 are green, generated outputs match their sources, and the durable-output rows are current.

### T6: Remote runs prove automatic scope, existing audit coverage, and dispatch

**Depends on:** T5

**Touches:** `docs/specs/pack-javascript-ci-workflow/notes/verification-ledger.md`

**Review shape:** external evidence capture only.

**Tests:**

- **VI-1018 (AC-0013):** `no stub (manual QA)` — record the successful pull-request run of `pack-javascript.yml` and confirm an unrelated documentation-only change does not start it.
- **VI-1019 (AC-0013):** `no stub (manual QA)` — record the existing `gate-sast` run and the audit wrapper's pack-lockfile lines; confirm the pack JavaScript workflow log contains no npm-audit invocation.
- **VI-1020 (AC-0013):** `no stub (manual QA)` — after the workflow definition exists on the default branch, dispatch it against the implementation ref and record the successful run URL, commit SHA, and job conclusion.

**Done when:** VI-1018–VI-1020 are recorded against the same implementation revision or an explicitly reconciled successor, and AC-0013 is checked.

## Rollout

- **Delivery:** additive and reversible. Reverting the workflow removes the remote lane; reverting discovery and lockfiles restores the prior dependency-policy scope. No data migration or deployment occurs.
- **Infrastructure:** one standard `ubuntu-latest` GitHub-hosted job, read-only token, no secrets, caches, environments, artifacts, or self-hosted capacity.
- **External-system integration:** npm registry access is required for `npm ci`; npm advisory access remains in the existing `gate-sast` job.
- **Deployment sequencing:** pre-merge construction tests and the automatic path-scoped run establish the workflow shape. GitHub manual dispatch is proved only after the workflow exists on the default branch, so the spec remains `Implementing` until T6 records that run.

## Risks

- A caret-ranged direct dependency may resolve to a transitive tree incompatible with Node 24. T2 records the resolved lock; T4 and T6 fail on the clean remote runner rather than treating a local install as proof.
- The path allowlist may omit a future verdict-changing policy file or overmatch an unrelated neighbor. The workflow construction test owns a closed set of semantic path classes, proves every pattern maps to one, and rejects representative adjacent files; the architecture record names that test rather than copying its patterns.
- Running with `--ignore-scripts` may expose a dependency that requires a vetted build step. The workflow stays fail-closed; removing the flag requires owner approval and a spec amendment rather than an inline workaround.
- Extending shared discovery makes the existing npm policy gates inspect more repository inputs. That is deliberate ADR-0083 coverage, but no new step or JavaScript runtime work is added to those jobs.
- The manual dispatch cannot be demonstrated before the workflow reaches the default branch. T6 keeps the spec open instead of substituting a local YAML check for activation evidence.

## Changelog

- 2026-10-02: spec approved by eugenelim.
- 2026-10-02: plan approved by eugenelim.
- 2026-10-05: revised from nine sustained pre-EXECUTE review findings (one
  Blocker, eight Concerns) across an adversarial and a secure-design pass, both
  adjudicated. Spec: AC-0014 gained a vacuous-pass guard and a `sha512`
  integrity floor; AC-0015 gained a stated scan scope and user/global/scoped
  /auth configuration neutralization; AC-0003 gained an expression-interpolation
  prohibition; AC-0001 gained the two shared harness drivers as a path class;
  two Agent Rules and two Testing Strategy lines were walked to match. Plan: T1
  gained its build-check gate home and the two chain files in `Touches`; the
  named-deviation line records why `tools/npm_project_discovery.py` confines
  with the standard library rather than the blessed helper; VI-1008 records the
  measured reason the shared self-test loader cannot load this subject. The
  change set needs re-approval before `plan-locked`.
- 2026-10-05: round 2 revised from four further sustained Concerns, both passes
  adjudicated; round 2's two reported Blockers were both refuted on evidence.
  AC-0002's unbounded "adding a step is not" contradicted the gate home round 1
  had just mandated, so it is now bounded to pack dependency-installation and
  JavaScript-suite steps, with the matching `Ask first` rule and the plan's
  Constraints line aligned. AC-0005 and AC-0006 gained a regular-file-and-no-
  link requirement for each discovered manifest and lockfile, which the
  existing walk does not supply because it admits a symlinked file by design.
  AC-0014 gained a locator-to-identity binding, because npm verifies integrity
  against the bytes it fetched rather than the name it requested. The named-
  deviation line dropped a `packages/`-import claim the repository contradicts
  and now rests on the `tools/AGENTS.md` pure-stdlib rule alone.
- 2026-10-05: round 3 revised from one sustained Concern and one sustained
  advisory; three further findings were refuted. Round 2's regular-file rule
  had collided with AC-0005's own prune rule — a canonical lockfile under a
  symlinked directory segment fell in both classes, so the two self-tests the
  criterion mandates would have asserted opposite exit codes. AC-0005 now
  partitions by route: the visible-tree walk prunes silently, the canonical
  `.apm/skills/` route is an explicit admission where nothing is pruned and a
  refusal fails closed naming the path. The matching `Never do` rule and
  Testing Strategy line were walked to the same partition, and the
  symlinked-directory fixture now appears on both routes with opposite expected
  exit codes. Separately, the named deviation's "every refusal is restated"
  claim was narrowed: `file_safety`'s `BoundExceeded` budgets are NOT restated,
  and the residual — AC-0015's unpruned walk running unbounded in build-check,
  held only by that job's own 25-minute timeout — is now recorded as
  consciously accepted with a revisit trigger, rather than covered by an
  overbroad sentence.
- 2026-10-05: revised spec re-approved by eugenelim after four adversarial and
  four secure-design rounds, every report adjudicated, both round-4 reviewers
  returning the direct-clean sentinel.
- 2026-10-05: revised plan re-approved by eugenelim in the same decision.
