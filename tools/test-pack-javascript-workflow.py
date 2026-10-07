#!/usr/bin/env python3
"""Focused construction tests for the pack JavaScript workflow."""

from __future__ import annotations

import importlib.util
import re
import sys
from dataclasses import replace
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
ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "pack-javascript.yml"

PATH_CLASSES = {
    "canonical pack JavaScript source": (
        "packs/*/.apm/skills/*/**/*.js",
        "packs/converters/.apm/skills/render-proof/lib/renderer.js",
    ),
    "pack JavaScript tests": (
        "packs/*/tests/**/*.test.js",
        "packs/converters/tests/skills/render-proof/renderer.test.js",
    ),
    "pack JavaScript spec tests": (
        "packs/*/tests/**/*.spec.js",
        "packs/converters/tests/skills/example/renderer.spec.js",
    ),
    "canonical manifests": (
        "packs/*/.apm/skills/*/package.json",
        "packs/converters/.apm/skills/render-proof/package.json",
    ),
    "canonical lockfiles": (
        "packs/*/.apm/skills/*/package-lock.json",
        "packs/converters/.apm/skills/render-proof/package-lock.json",
    ),
    "repository npm configuration": ("**/.npmrc", ".npmrc"),
    "repository ignore policy": (".gitignore", ".gitignore"),
    "the workflow": (
        ".github/workflows/pack-javascript.yml",
        ".github/workflows/pack-javascript.yml",
    ),
    "canonical discovery": (
        "tools/npm_project_discovery.py",
        "tools/npm_project_discovery.py",
    ),
    "parity and provenance policy": (
        "tools/lint-pack-npm-projects.py",
        "tools/lint-pack-npm-projects.py",
    ),
    "install-script policy": (
        "tools/lint-npm-allow-scripts.py",
        "tools/lint-npm-allow-scripts.py",
    ),
    "pack-test runner accounting": (
        "tools/lint-pack-test-boundary.py",
        "tools/lint-pack-test-boundary.py",
    ),
    "shared lint driver": ("tools/lint_harness.py", "tools/lint_harness.py"),
    "shared self-test driver": (
        "tools/selftest_harness.py",
        "tools/selftest_harness.py",
    ),
    "parity and provenance self-test": (
        "tools/test-lint-pack-npm-projects.py",
        "tools/test-lint-pack-npm-projects.py",
    ),
    "install-script self-test": (
        "tools/test-lint-npm-allow-scripts.py",
        "tools/test-lint-npm-allow-scripts.py",
    ),
    "pack-test boundary self-test": (
        "tools/test-lint-pack-test-boundary.py",
        "tools/test-lint-pack-test-boundary.py",
    ),
    "workflow construction test": (
        "tools/test-pack-javascript-workflow.py",
        "tools/test-pack-javascript-workflow.py",
    ),
}

UNRELATED_PATHS = (
    "packs/converters/.apm/skills/render-proof/evals/eval_queries.json",
    "packs/converters/.apm/skills/render-proof/SKILL.md",
    "packs/converters/tests/skills/render-proof/test_invocation_contract.py",
    "packs/converters/tests/skills/render-proof/fixture.txt",
    "tools/unrelated-tool.py",
    "docs/guides/maintainer.md",
)


def _workflow_source() -> str:
    """Read the authored workflow whose construction this file proves."""
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def _pull_request_paths(source: str) -> tuple[str, ...]:
    """Return the literal path filters from the pull-request trigger."""
    match = re.search(
        r"(?m)^  pull_request:\n    paths:\n(?P<paths>(?:      - .+\n)+)",
        source,
    )
    if match is None:
        return ()
    return tuple(
        line.split("- ", 1)[1].strip().strip("'\"")
        for line in match.group("paths").splitlines()
    )


def _matches(pattern: str, path: str) -> bool:
    """Match the slash-aware subset of GitHub path globs used by this workflow."""
    expression = re.escape(pattern)
    expression = expression.replace(r"\*\*/", r"(?:[^/]+/)*")
    expression = expression.replace(r"\*\*", r".*")
    expression = expression.replace(r"\*", r"[^/]*")
    return re.fullmatch(expression, path) is not None


def _trigger_errors(source: str) -> list[str]:
    """Return contract violations for the two admitted workflow triggers."""
    event_block = source.split("permissions:", 1)[0]
    events = set(re.findall(r"(?m)^  ([A-Za-z_]+):", event_block))
    expected = {"workflow_dispatch", "pull_request"}
    errors: list[str] = []
    if events != expected:
        errors.append(f"events are {sorted(events)!r}, not {sorted(expected)!r}")
    if re.search(r"(?ms)^  workflow_dispatch:\n    \S", event_block):
        errors.append("workflow_dispatch has inputs or another nested value")
    paths = _pull_request_paths(source)
    expected_paths = {pattern for pattern, _fixture in PATH_CLASSES.values()}
    if set(paths) != expected_paths or len(paths) != len(expected_paths):
        errors.append(
            "pull-request path set does not map exactly to the admitted classes"
        )
    return errors


def _posture_errors(source: str) -> list[str]:
    """Return violations of the workflow's closed fork-safe execution posture."""
    errors: list[str] = []
    required = (
        "permissions:\n  contents: read",
        "runs-on: ubuntu-latest",
        "timeout-minutes: 20",
        "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
        "persist-credentials: false",
        "actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020",
        "node-version: '24'",
        "group: pack-javascript-${{ github.event.pull_request.number || github.run_id }}",
        "cancel-in-progress: ${{ github.event_name == 'pull_request' }}",
    )
    for item in required:
        if item not in source:
            errors.append(f"missing required posture: {item}")
    forbidden = (
        "pull_request_target",
        "self-hosted",
        "larger-runner",
        "actions/cache@",
        "upload-artifact",
        "secrets.",
        "cache:",
    )
    for item in forbidden:
        if item in source:
            errors.append(f"forbidden posture surface: {item}")
    expressions = re.findall(r"\$\{\{[^}]+\}\}", source)
    allowed = [
        "${{ github.event.pull_request.number || github.run_id }}",
        "${{ github.event_name == 'pull_request' }}",
    ]
    if expressions != allowed:
        errors.append("an expression is outside the two platform-issued concurrency values")
    if re.search(r"(?m)^\s+[A-Za-z-]+:\s*write\b", source):
        errors.append("workflow grants a write permission")
    if re.search(r"(?m)^\s+cache(?:-dependency-path)?:", source):
        errors.append("workflow configures setup-node caching")
    return errors


def _execution_errors(source: str) -> list[str]:
    """Return policy, installation, and suite-command contract violations."""
    errors: list[str] = []
    policies = (
        "python3 tools/test-lint-npm-allow-scripts.py",
        "python3 tools/lint-npm-allow-scripts.py",
        "python3 tools/test-lint-pack-npm-projects.py",
        "python3 tools/lint-pack-npm-projects.py",
    )
    install = "npm ci --ignore-scripts --no-audit --prefix \"$(dirname \"$manifest\")\""
    if (
        install not in source
        or "for manifest in packs/*/.apm/skills/*/package.json; do" not in source
    ):
        errors.append(
            "canonical projects are not dynamically installed with the locked safe command"
        )
    else:
        missing_policies = [policy for policy in policies if policy not in source]
        if missing_policies:
            errors.append(f"missing policy checks: {missing_policies!r}")
        elif any(source.index(policy) > source.index(install) for policy in policies):
            errors.append("a policy check follows dependency installation")
    # The two config slots must be neutralized with DISTINCT empty files. npm
    # refuses the same path in both — `double-loading config "/dev/null" as
    # "global", previously loaded as "user"` — and exits before resolving any
    # configuration, so pointing both at /dev/null disables every npm command
    # in the job instead of hardening it. Measured against npm 11.19.0.
    if "NPM_CONFIG_USERCONFIG: /dev/null" in source or "NPM_CONFIG_GLOBALCONFIG: /dev/null" in source:
        errors.append("npm user and global config share one path; npm refuses to load it")
    for setting in (
        'echo "NPM_CONFIG_USERCONFIG=$RUNNER_TEMP/empty-user.npmrc"',
        'echo "NPM_CONFIG_GLOBALCONFIG=$RUNNER_TEMP/empty-global.npmrc"',
        "NPM_CONFIG_REGISTRY: https://registry.npmjs.org/",
        "NPM_CONFIG_REPLACE_REGISTRY_HOST: never",
        "npm config get userconfig",
        "npm config get globalconfig",
        "npm config get registry",
        "npm config get replace-registry-host",
        "npm config list --json | node -e",
    ):
        if setting not in source:
            errors.append(f"missing npm configuration control: {setting}")
    if "npm install" in source or "npm audit" in source:
        errors.append("workflow invokes a prohibited npm command")
    for suite in ("renderer.test.js", "security.test.js", "pipeline.test.js"):
        step = (
            "working-directory: packs/converters/tests/skills/render-proof\n"
            f"        run: node {suite}"
        )
        if step not in source:
            errors.append(f"missing explicit render-proof suite: {suite}")
    return errors


def _interference_errors(workflows: dict[str, str], makefile: str) -> list[str]:
    """Return forbidden calls or pack JavaScript work outside this workflow."""
    errors: list[str] = []
    for name, source in workflows.items():
        if "pack-javascript.yml" in source:
            errors.append(f"{name} calls the dedicated workflow")
        if re.search(r"npm ci[^\n]*(?:--prefix\s+packs/|packs/)", source):
            errors.append(f"{name} installs pack dependencies")
        if re.search(r"node\s+\S+\.(?:test|spec)\.js", source):
            errors.append(f"{name} runs a JavaScript suite")
    if re.search(r"npm ci[^\n]*(?:--prefix\s+packs/|packs/)", makefile):
        errors.append("Makefile installs pack dependencies")
    if re.search(r"node\s+\S+\.(?:test|spec)\.js", makefile):
        errors.append("Makefile runs a JavaScript suite")
    return errors


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


def test_triggers_and_paths_are_closed_and_mutation_backed() -> None:
    """VI-1010: each admitted path class is necessary and adjacent paths are not."""
    source = _workflow_source()
    assert _trigger_errors(source) == []
    paths = _pull_request_paths(source)
    for label, (pattern, fixture) in PATH_CLASSES.items():
        assert pattern in paths, label
        assert _matches(pattern, fixture), (
            f"{label}: {fixture} does not match {pattern}"
        )
        removed = source.replace(f"      - '{pattern}'\n", "", 1)
        assert _trigger_errors(removed), f"removing {label} did not fail"
        broadened = source.replace(pattern, "packs/**", 1)
        assert _trigger_errors(broadened), f"broadening {label} did not fail"
    for path in UNRELATED_PATHS:
        assert not any(_matches(pattern, path) for pattern in paths), path
    assert _trigger_errors(source.replace("  workflow_dispatch:\n", "", 1))
    assert _trigger_errors(source.replace("  pull_request:\n", "", 1))


def test_posture_concurrency_and_noninterference_are_closed() -> None:
    """VI-1011: only platform-issued concurrency values reach this fork-safe job."""
    source = _workflow_source()
    assert _posture_errors(source) == []
    assert _posture_errors(source.replace("pull_request.number", "pull_request.title", 1))
    assert _posture_errors(source.replace("github.run_id", "github.head_ref", 1))
    assert _posture_errors(
        source.replace(
            "cancel-in-progress: ${{ github.event_name == 'pull_request' }}",
            "cancel-in-progress: true",
            1,
        )
    )
    assert _posture_errors(
        source.replace(
            "NPM_CONFIG_REGISTRY",
            "NPM_CONFIG_REGISTRY: ${{ github.event.pull_request.title }} #",
            1,
        )
    )
    assert _posture_errors(source.replace("contents: read", "contents: write", 1))
    assert _posture_errors(
        source.replace("node-version: '24'", "node-version: '24'\n          cache: npm", 1)
    )

    workflows = {
        path.name: path.read_text(encoding="utf-8")
        for path in (ROOT / ".github" / "workflows").glob("*.yml")
        if path != WORKFLOW_PATH
    }
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert _interference_errors(workflows, makefile) == []
    assert _interference_errors(
        {"other.yml": "uses: ./.github/workflows/pack-javascript.yml"}, ""
    )
    assert _interference_errors(
        {}, "npm ci --prefix packs/converters/.apm/skills/render-proof"
    )


def test_policy_install_and_explicit_suites_are_ordered() -> None:
    """VI-1012: policy precedes dynamic safe installation and named suite runs."""
    source = _workflow_source()
    assert _execution_errors(source) == []
    assert _execution_errors(source.replace("--no-audit", "", 1))
    assert _execution_errors(source.replace("python3 tools/lint-pack-npm-projects.py\n", "", 1))
    assert _execution_errors(
        source.replace("NPM_CONFIG_REGISTRY: https://registry.npmjs.org/\n", "", 1)
    )
    assert _execution_errors(source.replace("npm config get registry", "npm config get ignored", 1))
    assert _execution_errors(source.replace("npm config get userconfig", "npm config get ignored", 1))
    # The regression this file exists to prevent: collapsing both config slots
    # onto one path. It must be caught as a contract violation, not pass.
    assert _execution_errors(
        source.replace(
            'echo "NPM_CONFIG_USERCONFIG=$RUNNER_TEMP/empty-user.npmrc" >> "$GITHUB_ENV"',
            "NPM_CONFIG_USERCONFIG: /dev/null",
            1,
        )
    )


def test_boundary_and_parity_inventories_name_the_workflow() -> None:
    """VI-1013: removing either closed-inventory entry makes its owner fail."""
    assert ".github/workflows/pack-javascript.yml" in BOUNDARY._RUNNER_FILES
    assert "packs/converters/tests/skills/render-proof" not in BOUNDARY._NO_RUNNER
    without_runner = replace(
        BOUNDARY.default_context(),
        runner_files=tuple(
            path for path in BOUNDARY._RUNNER_FILES
            if path != ".github/workflows/pack-javascript.yml"
        ),
    )
    findings = BOUNDARY.inspect_boundary(
        without_runner, checks={"every-suite-dir-has-a-runner"}
    )
    assert any("render-proof" in finding.message for finding in findings)

    parity_path = ROOT / "tools" / "lint-ci-parity.py"
    spec = importlib.util.spec_from_file_location("pack_js_parity", parity_path)
    assert spec is not None and spec.loader is not None
    parity = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = parity
    spec.loader.exec_module(parity)
    assert parity.WORKFLOW_SCOPE["pack-javascript.yml"] is not parity.IN_SCOPE
    scope = dict(parity.WORKFLOW_SCOPE)
    del scope["pack-javascript.yml"]
    violations = parity.check(
        {"steps": [], "by_step": {}, "where": {}, "duplicates": []},
        set(), set(), {"pack-javascript.yml"},
        dispositions={}, scope=scope,
    )
    assert any("not classified" in violation for violation in violations)


if __name__ == "__main__":
    raise SystemExit(run_cases(globals(), "pack-javascript-workflow"))
