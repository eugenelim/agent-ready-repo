# Plan: Pack test collection and isolation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

## Approach

First make the existing pack-boundary lint express source confinement and move
misplaced repository assertions to their canonical root test layer. Then
rewrite legacy standalone pack skill harnesses as native pytest cases and
migrate their callers. Finish by making the work-intake path expectations
platform-independent and running static construction checks plus the focused
test matrix.

## Tasks

### T1: Enforce pack-test source confinement

**Depends on:** none

**Touches:** `tools/lint-pack-test-boundary.py`,
`tools/test-lint-pack-test-boundary.py`

**Verification mode:** TDD.

**Tests:**

- `test_pack_test_source_confinement` — owning-pack and temporary forms pass;
  `Path(__file__)` climbs above the pack and Git-root discovery fail.
  `stub: true`

```python
# STUB: AC4 — pack tests cannot resolve checkout source above their pack
def test_pack_test_source_confinement():
    pack_test = ROOT / "packs/core/tests/pack/test_x.py"
    local = "PACK_ROOT = Path(__file__).resolve().parents[2]"
    escaped = "REPO_ROOT = Path(__file__).resolve().parents[4]"
    assert not lint._pack_test_escapes(pack_test, local)
    assert lint._pack_test_escapes(pack_test, escaped)
```

The completed self-test adds temporary-path and Git-root-discovery cases.

**Approach:** Add a sixth named lint case to the existing boundary owner. Parse
Python pack tests and report the exact file and source expression that escapes
the owning pack. Keep runtime dependency imports and temporary fixtures outside
the rule.

**Done when:** a pack test cannot regain a source-tree escape without the lint
and its falsification test failing.

### T2: Put tests at the layer whose source they inspect

**Depends on:** T1

**Touches:** Python tests under `packs/*/tests/` that currently derive the
repository root; relocated counterparts under `tests/conformance/` or
`tests/roster/`; affected root test-runner manifests, if any.

**Verification mode:** goal-based check.

**Tests:** no stub (goal-based). Exact checks:

```bash
env PYTHONDONTWRITEBYTECODE=1 \
  python3 tools/lint-pack-test-boundary.py
python3 -m pytest -p no:cacheprovider \
  tests/roster/test_adapt_reference_architecture.py \
  tests/roster/test_apm_writer_reader_journey.py \
  tests/roster/test_architect_design_reviewer_projection.py \
  tests/roster/test_core_pre_pr_hook.py \
  tests/roster/test_core_work_loop_hook.py \
  tests/roster/test_credential_broker_floor_precedence.py \
  tests/roster/test_credential_broker_source_invariants.py \
  tests/roster/test_normalized_intake_contract.py \
  tests/roster/test_work_intake_contracts.py \
  tests/roster/test_work_loop_lint_knowledge.py \
  tests/roster/test_work_loop_root_validation.py \
  tests/roster/test_workspace_entry_contract.py \
  tests/roster/test_workspace_status_projection.py \
  tests/roster/test_credential_broker_contract_docs_pack.py \
  tests/roster/test_export_catalogue_removal.py \
  tests/roster/test_product_documentation_pack.py \
  -q
```

**Approach:** Replace repository-root round trips used only to reach the owning
pack with direct `PACK_ROOT` anchors. Move whole tests that inspect contracts,
tools, packages, projections, guides, or sibling packs to the matching existing
root layer; delete only exact duplicate coverage already present there.

**Done when:** all pack tests inspect only their pack and temporary fixtures,
with repository coverage retained outside `packs/`.

### T3: Rewrite standalone pack skill harnesses as native pytest tests

**Depends on:** T2

**Touches:** all `test*.py` modules below `packs/*/tests/skills/` containing a
standalone `main()` or `unittest.main()` entry point; `tools/repo/build_gate_chain.py`,
`tools/test_build_gate_chain.py`, `tools/test-all.py`,
`packs/core/tests/skills/work-loop/test-loop-cohort.sh`, `.github/workflows/docs.yml`

**Verification mode:** goal-based check.

**Tests:** no stub (goal-based). Exact checks:

```bash
env PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest \
  tools.test_build_gate_chain.PackSkillPytestShapeTest \
  tools.test_build_gate_chain.BuildCheckChainTest
python3 -m pytest -p no:cacheprovider \
  packs/core/tests/skills/work-loop/ -q
python3 -m pytest -p no:cacheprovider \
  packs/core/tests/skills/receive-brief/ -q
python3 -m pytest -p no:cacheprovider \
  packs/governance-extras/tests/skills/new-adr/ -q
python3 -m pytest -p no:cacheprovider \
  packs/governance-extras/tests/skills/new-rfc/ -q
python3 -m pytest -p no:cacheprovider \
  packs/atlassian/tests/skills/confluence-crawler/ -q
python3 -m pytest -p no:cacheprovider \
  packs/atlassian/tests/skills/confluence-publisher/ -q
python3 -m pytest -p no:cacheprovider \
  packs/atlassian/tests/skills/jira/ -q
python3 -m pytest -p no:cacheprovider \
  packs/atlassian/tests/skills/jira-align/ -q
python3 -m pytest -p no:cacheprovider \
  packs/atlassian/tests/skills/jira-team-status/ -q
python3 -m pytest -p no:cacheprovider \
  packs/figma/tests/skills/figma/ -q
python3 -m pytest -p no:cacheprovider \
  packs/desk-research/tests/skills/desk-research/ -q
python3 -m pytest -p no:cacheprovider \
  packs/desk-research/tests/skills/desk-research-project-start/ -q
```

**Approach:** Rename legacy cases into pytest's namespace, replace manual
temporary-directory injection with pytest fixtures, turn optional-capability
branches into pytest skips, remove aggregate state and entry points, and change
live callers to `python -m pytest <path> -q`.

**Done when:** pytest owns every case lifecycle and no affected gate can pass
without collecting the intended tests.

### T4: Make repository-relative fixture path checks host-independent

**Depends on:** T2

**Touches:** the relocated work-intake and workspace-entry contract tests.

**Verification mode:** TDD.

**Tests:**

- `test_repository_relative_plan_path_is_posix` — a Windows path object must
  serialize to the fixture's POSIX value. `stub: true`

```python
# STUB: AC6 — repository-relative contract paths are host-independent
from pathlib import PureWindowsPath


def test_repository_relative_plan_path_is_posix():
    entry = PureWindowsPath("docs/specs/example/spec.md")
    assert str(entry.with_name("plan.md")) == "docs/specs/example/plan.md"
```

The red stub exposes the backslash mismatch; green replaces native `str(Path)`
serialization with `.as_posix()` and the focused contract tests verify it.

**Approach:** Serialize expected relative fixture paths with `.as_posix()` while
leaving filesystem paths platform-native for actual I/O.

**Done when:** the same contract fixtures compare identically on Windows,
Linux, and macOS.

### T5: Audit the final diff against the requested surface

**Depends on:** T1, T2, T3, T4

**Touches:** none beyond the preceding tasks.

**Verification mode:** goal-based check; no stub (diff audit).

**Tests:** no stub (goal-based). Exact audit:

```bash
git diff --name-status
git diff --exit-code -- \
  'packs/*/.apm/**' \
  'packs/*/pack.toml' \
  'packs/*/.claude-plugin/plugin.json' \
  'packages/*/pyproject.toml' \
  'packages/*/requirements*.txt' \
  pyproject.toml requirements.txt uv.lock poetry.lock
git diff --name-only -- \
  'packs/*/tests/**/*.sh' \
  'packs/*/tests/**/*.js' \
  'packs/*/tests/**/*.ts'
```

The last command may name only
`packs/core/tests/skills/work-loop/test-loop-cohort.sh`; its diff is limited to
pytest argv, renamed Python paths, and matching diagnostics.

**Approach:** Classify every changed path before handoff and reject surplus
runtime, metadata, dependency, generated projection, or non-Python test edits.

**Done when:** the diff contains only spec/plan, Python tests, their existing
runner/caller contracts, and the approved shell/workflow invocation updates.

## Declined patterns

- Compatibility wrappers around `main()`: declined by explicit user direction
  and because they preserve aggregate false-pass behavior.
- Copy repository contracts or tools into pack fixtures: declined because it
  duplicates the source of truth and hides ownership rather than correcting it.
- Ban temporary paths or installed dependencies: declined because neither is a
  checkout source-tree escape.
- Add a second boundary tool: declined because
  `tools/lint-pack-test-boundary.py` already owns this policy.

## Resolve-vs-surface record

- Resolved: direct invocations are in scope because otherwise migrated modules
  would silently stop executing.
- Resolved: otherwise-collectable `unittest` modules lose their script guards
  so every Python pack skill test has one runner contract.
- Resolved: cross-boundary tests move intact where practical; splitting is used
  only when it avoids moving unrelated pack-local coverage.
- Applied: restored the legacy loop-engine suite's temporary Git repository and
  working-directory fixture after runtime execution exposed setup formerly
  hidden in `main()`.
- Applied: removed the last aggregate `RAN` mutations after independently
  collected roster tests exposed the stale harness state.
- Applied: closed review findings for function-local path aliases, helper-shaped
  Git-root discovery, linked test sources, and stale relocated-test prose.
- Surface: none.
