"""Guard shared build-time code against distribution-route decisions.

This lives beside the checker it drives rather than under the engine's own test
tree: the engine's tests ship inside the sdist, and this guard reads a
repository-only `tools/` script that an adopter never receives.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "tools" / "check_distribution_route_decisions.py"
SOURCE_ROOT = REPO_ROOT / "packages" / "agentbundle" / "agentbundle"
CONTRACT = REPO_ROOT / "contracts" / "distribution-routes.toml"
RECIPES = SOURCE_ROOT / "build" / "recipes"


def _load_checker() -> ModuleType:
    """Load the repository checker through its supported Python interface."""
    spec = importlib.util.spec_from_file_location("route_decision_guard_checker", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _assert_no_route_decisions(checker: ModuleType, source_root: Path) -> None:
    """Require both decision findings and unclassified escapes to be empty."""
    result = checker.scan_tree(source_root, CONTRACT, RECIPES)
    assert result.findings == (), result.findings
    assert result.residue == (), result.residue


def test_shipped_shared_code_has_no_route_decisions_or_residue() -> None:
    """The shipped shared source tree remains route-name-free and contract-led."""
    _assert_no_route_decisions(_load_checker(), SOURCE_ROOT)


@pytest.mark.parametrize(
    ("source", "expected_failure"),
    [
        (
            'def choose(candidate):\n    return candidate == "apm"\n',
            "comparison",
        ),
        (
            'ROUTES = {"apm", "claude-plugins"}\n'
            "def choose(candidate):\n    return candidate in ROUTES\n",
            "collection-comparison",
        ),
        ('HANDLERS = {"apm": object()}\n', "dispatch-map"),
        (
            "def configure(parser):\n"
            '    parser.add_argument("--route", choices=["apm"])\n',
            "argparse-choices",
        ),
        (
            "def installed(path):\n"
            '    return path.startswith(("apm/", "claude-plugins/"))\n',
            "startswith-prefix",
        ),
        (
            "def choose(resolved: ResolvedDistributionRoute, some_key):\n"
            "    identity = resolved.identity\n"
            "    return identity == some_key\n",
            "contract-derived-value",
        ),
        (
            "def choose(resolved: ResolvedDistributionRoute, handlers):\n"
            "    return handlers[resolved.identity]\n",
            "mapping-lookup",
        ),
        (
            "from dataclasses import dataclass\n"
            "@dataclass(frozen=True)\n"
            "class Context:\n"
            "    resolved_route: ResolvedDistributionRoute\n"
            "def choose(context: Context, some_key):\n"
            "    return context.resolved_route.identity == some_key\n",
            "context.resolved_route.identity == some_key",
        ),
    ],
    ids=[
        "literal-comparison",
        "separated-literal-collection",
        "dispatch-map-key",
        "argument-choices",
        "rooted-prefix",
        "derived-alias-comparison",
        "derived-mapping-lookup",
        "dataclass-carrier-field",
    ],
)
def test_guard_rejects_recorded_route_decision_mutations(
    tmp_path: Path,
    source: str,
    expected_failure: str,
) -> None:
    """Each forbidden decision form kills the guard in an isolated source tree."""
    source_root = tmp_path / "source"
    source_root.mkdir()
    (source_root / "shared.py").write_text(source, encoding="utf-8")

    with pytest.raises(AssertionError, match=re.escape(expected_failure)):
        _assert_no_route_decisions(_load_checker(), source_root)


def test_recorded_baseline_reproduces_at_its_measuring_commit(tmp_path: Path) -> None:
    """The pinned pre-change measurement is reproducible by the shipped checker.

    Three review rounds extended the checker and each time silently invalidated
    this baseline, because nothing re-measured it. Materialising the measured
    inputs at the recorded commit and rescanning makes that failure loud: a
    change to the instrument now fails here until the baseline is re-measured.
    """
    baseline_path = (
        REPO_ROOT / "docs" / "specs" / "distribution-route-registry"
        / "route-decision-baseline.json"
    )
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    commit = baseline["measuring_commit"]

    archive = subprocess.run(
        ["git", "archive", commit, "packages/agentbundle/agentbundle", "contracts"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if archive.returncode != 0:
        pytest.skip(f"measuring commit {commit[:12]} is not available locally")
    subprocess.run(
        ["tar", "-x", "-C", str(tmp_path)], input=archive.stdout, check=True
    )

    checker = _load_checker()
    source_root = tmp_path / "packages" / "agentbundle" / "agentbundle"
    result = checker.scan_tree(
        source_root,
        tmp_path / "contracts" / "distribution-routes.toml",
        source_root / "build" / "recipes",
    )

    assert len(result.findings) == len(baseline["findings"]), (
        f"the checker now measures {len(result.findings)} decisions at {commit[:12]} "
        f"but the baseline records {len(baseline['findings'])}; re-measure it"
    )
    assert [
        (finding.path, finding.line, finding.form, finding.shape)
        for finding in result.findings
    ] == [
        (entry["path"], entry["line"], entry["form"], entry["shape"])
        for entry in baseline["findings"]
    ]
    assert len(result.residue) == len(baseline["coverage_residue"])

    # The recorded exemptions and mutation set are the checker's own account of
    # what it covers. `--verify-baseline` deliberately ignores them so a prose
    # edit cannot invalidate a measurement, which means this is the only place
    # their drift can be caught.
    artifact = checker._artifact(result, commit)
    assert artifact["limits"] == baseline["limits"], (
        "the checker's recorded limits changed; re-measure the baseline"
    )
    assert artifact["mutations"] == baseline["mutations"], (
        "the checker's recorded mutation set changed; re-measure the baseline"
    )
