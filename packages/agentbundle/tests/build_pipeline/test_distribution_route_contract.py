"""Construction tests for the public distribution-route contract."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from agentbundle.build.main import _parse_recipe_text, load_recipe
from agentbundle.build.validate import validate

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PACKAGE_ROOT.parents[1]
ROUTE_CONTRACT_PATH = PACKAGE_ROOT / "agentbundle" / "_data" / "distribution-routes.toml"
ROUTE_SCHEMA_PATH = PACKAGE_ROOT / "agentbundle" / "_data" / "distribution-routes.schema.json"
ROUTE_FIELDS = {
    "identity",
    "package-layout",
    "manifest-projector",
    "component-capabilities",
    "marketplace-projector",
    "lifecycle-trigger",
}
PRIMITIVES = {
    "skill",
    "agent",
    "command",
    "hook-body",
    "hook-wiring",
    "kiro-ide-hook",
    "shared-libs",
    "adapter-root-bins",
    "user-libs",
}
CLAUDE_NATIVE = {"skill", "agent", "command", "hook-body", "hook-wiring"}


# STUB: AC1 — the public contract declares exactly the two Phase 0 routes.
def test_route_contract_declares_exact_phase_zero_routes() -> None:
    """Require the bundled contract and its closed Phase 0 route identities."""
    assert ROUTE_CONTRACT_PATH.is_file(), "bundled distribution-route contract is missing"
    assert ROUTE_SCHEMA_PATH.is_file(), "bundled distribution-route schema is missing"
    contract = tomllib.loads(ROUTE_CONTRACT_PATH.read_text(encoding="utf-8"))
    schema = json.loads(ROUTE_SCHEMA_PATH.read_text(encoding="utf-8"))

    assert validate(contract, schema) == []
    assert set(contract["route"]) == {"apm", "claude-plugins"}
    for route_name, route in contract["route"].items():
        assert set(route) == ROUTE_FIELDS
        assert route["identity"] == route_name
        assert set(route["package-layout"]) == {"name", "output-subdir"}
        assert set(route["manifest-projector"]) == {
            "name",
            "adapter-projector",
            "admission-policy",
        }
        assert set(route["component-capabilities"]) == PRIMITIVES
        assert all(
            set(capability) == {"status", "mode", "target-path"}
            for capability in route["component-capabilities"].values()
        )

    apm = contract["route"]["apm"]
    claude = contract["route"]["claude-plugins"]
    assert {name for name, item in apm["component-capabilities"].items() if item["status"] == "native"} == PRIMITIVES
    assert {name for name, item in claude["component-capabilities"].items() if item["status"] == "native"} == CLAUDE_NATIVE
    assert {name for name, item in claude["component-capabilities"].items() if item["status"] == "dropped"} == PRIMITIVES - CLAUDE_NATIVE
    assert apm["manifest-projector"] == {
        "name": "apm-package",
        "adapter-projector": "none",
        "admission-policy": "all-packs",
    }
    assert claude["manifest-projector"] == {
        "name": "claude-plugin",
        "adapter-projector": "claude-code",
        "admission-policy": "user-publishable-with-consent",
    }

    malformed = copy.deepcopy(contract)
    malformed["route"]["apm"]["unexpected"] = True
    assert validate(malformed, schema), "route objects must be closed"
    malformed = copy.deepcopy(contract)
    malformed["route"]["claude-plugins"]["component-capabilities"]["skill"][
        "mode"
    ] = "dynamic-import"
    errors = validate(malformed, schema)
    assert errors, "projector modes must fail closed"
    assert any(
        "$.route.claude-plugins.component-capabilities.skill.mode" in error
        for error in errors
    ), errors

    repository_contract_root = REPO_ROOT / "contracts"
    for filename in ("distribution-routes.toml", "distribution-routes.schema.json"):
        repository_contract = repository_contract_root / filename
        bundled_contract = PACKAGE_ROOT / "agentbundle" / "_data" / filename
        if repository_contract_root.is_dir():
            assert repository_contract.is_file()
            assert repository_contract.read_bytes() == bundled_contract.read_bytes()
        assert filename in (
            PACKAGE_ROOT / "agentbundle" / "_data" / "public-contracts.txt"
        ).read_text(encoding="utf-8").splitlines()


@pytest.mark.parametrize("field", sorted(ROUTE_FIELDS))
def test_route_contract_rejects_each_missing_concern(field: str) -> None:
    """Make every one of the six route concerns independently required."""
    contract = tomllib.loads(ROUTE_CONTRACT_PATH.read_text(encoding="utf-8"))
    schema = json.loads(ROUTE_SCHEMA_PATH.read_text(encoding="utf-8"))
    del contract["route"]["apm"][field]
    assert validate(contract, schema)


def test_route_contract_rejects_unknown_status_and_capability_omission() -> None:
    """Keep the primitive support matrix exhaustive and closed."""
    contract = tomllib.loads(ROUTE_CONTRACT_PATH.read_text(encoding="utf-8"))
    schema = json.loads(ROUTE_SCHEMA_PATH.read_text(encoding="utf-8"))
    contract["route"]["apm"]["component-capabilities"]["skill"][
        "status"
    ] = "unknown"
    assert validate(contract, schema)

    contract = tomllib.loads(ROUTE_CONTRACT_PATH.read_text(encoding="utf-8"))
    del contract["route"]["claude-plugins"]["component-capabilities"]["user-libs"]
    assert validate(contract, schema)


# STUB: AC3 — every default distribution recipe declares explicit route identity.
def test_default_distribution_recipes_declare_explicit_routes() -> None:
    """Require recipe parsing to expose route identity without inference."""
    expected = {
        "per-pack-apm-package": "apm",
        "per-pack-claude-plugin": "claude-plugins",
        "marketplace": "claude-plugins",
    }

    assert {
        recipe_name: getattr(load_recipe(recipe_name), "route", None)
        for recipe_name in expected
    } == expected
    assert load_recipe("per-pack-apm-package").adapter is None
    assert load_recipe("per-pack-claude-plugin").adapter == "claude-code"

    adapter_contract = tomllib.loads(
        (PACKAGE_ROOT / "agentbundle" / "_data" / "adapter.toml").read_text(
            encoding="utf-8"
        )
    )
    assert all(
        "install-routes" not in adapter
        for adapter in adapter_contract["adapter"].values()
    )
    assert all(
        "plugin-target-path" not in projection and "plugin-mode" not in projection
        for adapter in adapter_contract["adapter"].values()
        for projection in adapter.get("projection", [])
    )


# STUB: AC3, AC9 — non-distribution recipes cannot smuggle route-only fields.
def test_non_distribution_recipe_rejects_route_only_fields() -> None:
    """Keep overlay/composite/self-host recipes outside route dispatch."""
    assert getattr(load_recipe("per-pack-overlay"), "route", None) is None
    assert getattr(load_recipe("composite-agents-md"), "route", None) is None
    assert getattr(load_recipe("composite-marketplace"), "route", None) is None
    assert getattr(load_recipe("self-host"), "route", None) is None

    with pytest.raises(ValueError, match=r"bad-overlay.*field 'route'.*overlay"):
        _parse_recipe_text(
            '[recipe]\nname = "bad-overlay"\ntype = "overlay"\n'
            'route = "apm"\nunits = [".apm/"]\n'
        )


@pytest.mark.parametrize("recipe_type", ["per-pack", "aggregate"])
def test_distribution_recipe_requires_route_identity(recipe_type: str) -> None:
    """Refuse distribution recipes whose dispatch identity would be inferred."""
    with pytest.raises(
        ValueError,
        match=rf"missing-route.*field 'route'.*required.*{recipe_type}",
    ):
        _parse_recipe_text(
            f'[recipe]\nname = "missing-route"\ntype = "{recipe_type}"\n'
        )


def test_build_cli_reports_invalid_custom_recipe_without_traceback(
    tmp_path: Path,
) -> None:
    """Render a bad custom recipe as an ordinary CLI input refusal."""
    recipe = tmp_path / "missing-route.toml"
    recipe.write_text(
        '[recipe]\nname = "missing-route"\ntype = "per-pack"\n',
        encoding="utf-8",
    )
    packs = tmp_path / "packs"
    packs.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "agentbundle.build",
            "build",
            "--recipe",
            str(recipe),
            "--packs-dir",
            str(packs),
            "--output-dir",
            str(tmp_path / "dist"),
        ],
        cwd=PACKAGE_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "build: recipe" in result.stderr
    assert "field 'route' is required" in result.stderr
    assert "Traceback" not in result.stderr
    assert not (tmp_path / "dist").exists()
