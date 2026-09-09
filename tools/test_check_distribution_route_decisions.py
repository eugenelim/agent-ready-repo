"""Fixture coverage for the distribution-route decision inventory."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "tools" / "check_distribution_route_decisions.py"


def _load_checker():
    """Load the checker from its repository script path."""
    spec = importlib.util.spec_from_file_location("route_decision_checker", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def checker():
    """Return the loaded checker module."""
    return _load_checker()


@pytest.fixture
def fixture_tree(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Create the smallest contract, recipe set, and shared source tree."""
    contract = tmp_path / "distribution-routes.toml"
    contract.write_text(
        """
[route.apm]
identity = "apm"
package-layout = { output-subdir = "apm" }

[route."agent-plugin"]
identity = "agent-plugin"
package-layout = { output-subdir = "agent-plugins" }

[route."claude-plugins"]
identity = "claude-plugins"
package-layout = { output-subdir = "claude-plugins" }
""".lstrip(),
        encoding="utf-8",
    )
    recipes = tmp_path / "recipes"
    recipes.mkdir()
    (recipes / "apm.toml").write_text(
        '[recipe]\nname = "per-pack-apm-package"\nroute = "apm"\n',
        encoding="utf-8",
    )
    source = tmp_path / "source"
    source.mkdir()
    return source, contract, recipes


@pytest.mark.parametrize(
    ("source", "shape"),
    [
        ('def choose(route):\n    return route == "apm"\n', "comparison"),
        (
            'ROUTES = {"apm", "claude-plugins"}\n'
            "def choose(route):\n    return route in ROUTES\n",
            "route-collection",
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
            "def roots(base):\n"
            '    return [base / top for top in ("claude-plugins", "apm")]\n',
            "comprehension-iteration",
        ),
    ],
)
def test_route_literal_mutations_are_detected(
    checker,
    fixture_tree: tuple[Path, Path, Path],
    source: str,
    shape: str,
) -> None:
    """Each observed literal shape must produce a route-literal finding."""
    source_root, contract, recipes = fixture_tree
    (source_root / "shared.py").write_text(source, encoding="utf-8")

    result = checker.scan_tree(source_root, contract, recipes)

    assert any(
        finding.form == "route-literal" and finding.shape == shape
        for finding in result.findings
    )


def test_contract_derived_comparison_without_literal_is_detected(
    checker,
    fixture_tree: tuple[Path, Path, Path],
) -> None:
    """Aliased comparisons remain forbidden even when no route is named."""
    source_root, contract, recipes = fixture_tree
    (source_root / "shared.py").write_text(
        "def choose(resolved: ResolvedDistributionRoute, some_key: str):\n"
        "    identity = resolved.identity\n"
        "    return identity == some_key\n",
        encoding="utf-8",
    )

    result = checker.scan_tree(source_root, contract, recipes)

    assert [finding.form for finding in result.findings] == [
        "contract-derived-value"
    ]
    assert result.findings[0].detail == "identity == some_key"


def test_contract_derived_value_propagates_to_renamed_local_parameter(
    checker,
    fixture_tree: tuple[Path, Path, Path],
) -> None:
    """Direct local calls do not depend on route-like parameter names."""
    source_root, contract, recipes = fixture_tree
    (source_root / "shared.py").write_text(
        "def inner(value, key):\n"
        "    return value == key\n"
        "def outer(record: ResolvedDistributionRoute, key):\n"
        "    return inner(record.identity, key)\n",
        encoding="utf-8",
    )

    result = checker.scan_tree(source_root, contract, recipes)

    assert any(
        finding.form == "contract-derived-value"
        and finding.line == 2
        and finding.detail == "value == key"
        for finding in result.findings
    )


def test_route_return_source_is_derived_from_annotation_not_function_name(
    checker,
    fixture_tree: tuple[Path, Path, Path],
) -> None:
    """Renaming a typed route resolver does not remove its taint source."""
    source_root, contract, recipes = fixture_tree
    (source_root / "shared.py").write_text(
        "def acquire() -> ResolvedDistributionRoute:\n"
        "    raise NotImplementedError\n"
        "def choose(key):\n"
        "    item = acquire()\n"
        "    return item.identity == key\n",
        encoding="utf-8",
    )

    result = checker.scan_tree(source_root, contract, recipes)

    assert any(
        finding.form == "contract-derived-value"
        and finding.line == 5
        and finding.detail == "item.identity == key"
        for finding in result.findings
    )


def test_contract_derived_mapping_lookup_without_literal_is_detected(
    checker,
    fixture_tree: tuple[Path, Path, Path],
) -> None:
    """A contract-derived dispatch key is a decision without a comparison."""
    source_root, contract, recipes = fixture_tree
    (source_root / "shared.py").write_text(
        "def choose(record: ResolvedDistributionRoute, handlers):\n"
        "    return handlers[record.identity]\n",
        encoding="utf-8",
    )

    result = checker.scan_tree(source_root, contract, recipes)

    assert any(
        finding.form == "contract-derived-value"
        and finding.shape == "mapping-lookup"
        for finding in result.findings
    )


def test_route_decision_through_dataclass_carrier_field_is_detected(
    checker,
    fixture_tree: tuple[Path, Path, Path],
) -> None:
    """A typed carrier field remains visible to the value-flow pass."""
    source_root, contract, recipes = fixture_tree
    (source_root / "shared.py").write_text(
        "from dataclasses import dataclass\n"
        "@dataclass(frozen=True)\n"
        "class Context:\n"
        "    resolved_route: ResolvedDistributionRoute\n"
        "def choose(context: Context, key):\n"
        "    return context.resolved_route.identity == key\n",
        encoding="utf-8",
    )

    result = checker.scan_tree(source_root, contract, recipes)

    assert any(
        finding.form == "contract-derived-value"
        and finding.shape == "comparison"
        and finding.detail == "context.resolved_route.identity == key"
        for finding in result.findings
    )


def test_route_decision_through_transitive_dataclass_carriers_is_detected(
    checker,
    fixture_tree: tuple[Path, Path, Path],
) -> None:
    """Carrier fields annotated with another carrier resolve transitively."""
    source_root, contract, recipes = fixture_tree
    (source_root / "shared.py").write_text(
        "from dataclasses import dataclass\n"
        "@dataclass(frozen=True)\n"
        "class RouteContext:\n"
        "    resolved_route: ResolvedDistributionRoute\n"
        "@dataclass(frozen=True)\n"
        "class BuildContext:\n"
        "    route_context: RouteContext\n"
        "def choose(context: BuildContext, key):\n"
        "    return context.route_context.resolved_route.identity == key\n",
        encoding="utf-8",
    )

    result = checker.scan_tree(source_root, contract, recipes)

    assert any(
        finding.form == "contract-derived-value"
        and finding.shape == "comparison"
        and finding.detail
        == "context.route_context.resolved_route.identity == key"
        for finding in result.findings
    )


def test_carrier_construction_can_cross_a_contract_selected_dispatch(
    checker,
    fixture_tree: tuple[Path, Path, Path],
) -> None:
    """A carrier passed into route-selected behavior is classified, not residue."""
    source_root, contract, recipes = fixture_tree
    (source_root / "shared.py").write_text(
        "from dataclasses import dataclass\n"
        "@dataclass(frozen=True)\n"
        "class ResolvedDistributionRoute:\n"
        "    identity: str\n"
        "    behavior: RouteBehavior\n"
        "@dataclass(frozen=True)\n"
        "class Context:\n"
        "    resolved_route: ResolvedDistributionRoute\n"
        "def dispatch(resolved: ResolvedDistributionRoute):\n"
        "    context = Context(resolved_route=resolved)\n"
        "    return resolved.behavior.run(context)\n",
        encoding="utf-8",
    )

    result = checker.scan_tree(source_root, contract, recipes)

    assert result.residue == ()


def test_named_literal_collection_decision_sinks_are_detected(
    checker,
    fixture_tree: tuple[Path, Path, Path],
) -> None:
    """Definitions and later consumers are separate inventory sites."""
    source_root, contract, recipes = fixture_tree
    (source_root / "shared.py").write_text(
        'ROUTES = {"apm", "claude-plugins"}\n'
        "def choose(candidate):\n"
        "    return candidate in ROUTES\n",
        encoding="utf-8",
    )

    result = checker.scan_tree(source_root, contract, recipes)

    assert {(finding.line, finding.shape) for finding in result.findings} == {
        (1, "route-collection"),
        (3, "collection-comparison"),
    }


def test_write_mode_creates_a_reproducible_artifact(
    checker,
    fixture_tree: tuple[Path, Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CLI owns baseline output instead of requiring shell redirection."""
    source_root, contract, recipes = fixture_tree
    (source_root / "clean.py").write_text("VALUE = 1\n", encoding="utf-8")
    baseline = tmp_path / "baseline.json"
    monkeypatch.setattr(checker, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(checker, "_git_commit", lambda _root: "a" * 40)

    status = checker.main(
        [
            "--source-root",
            str(source_root),
            "--contract",
            str(contract),
            "--recipes",
            str(recipes),
            "--write-baseline",
            str(baseline),
        ]
    )

    assert status == 0
    document = json.loads(baseline.read_text(encoding="utf-8"))
    assert document["measuring_commit"] == "a" * 40
    assert document["findings"] == []
    assert document["coverage_residue"] == []
    assert {mutation["form"] for mutation in document["mutations"]} == {
        "shared-code-route-literal",
        "contract-derived-route-value",
    }

    monkeypatch.setattr(checker, "_git_commit", lambda _root: "b" * 40)
    monkeypatch.setattr(checker, "_sources_match_commit", lambda *_args: True)
    assert (
        checker.main(
            [
                "--source-root",
                str(source_root),
                "--contract",
                str(contract),
                "--recipes",
                str(recipes),
                "--verify-baseline",
                str(baseline),
            ]
        )
        == 0
    )
