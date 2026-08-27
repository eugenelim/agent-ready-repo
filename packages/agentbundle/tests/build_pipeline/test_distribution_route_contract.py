"""Construction tests for the public distribution-route contract."""

from __future__ import annotations

import copy
import hashlib
import json
import socket
import subprocess
import sys
import tomllib
from dataclasses import replace
from importlib.resources import files as resource_files
from pathlib import Path

import pytest
from agentbundle.build.main import (
    _parse_recipe_text,
    _resolve_distribution_route,
    load_recipe,
)
from agentbundle.build.validate import validate

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PACKAGE_ROOT.parents[1]
ROUTE_CONTRACT_PATH = PACKAGE_ROOT / "agentbundle" / "_data" / "distribution-routes.toml"
ROUTE_SCHEMA_PATH = PACKAGE_ROOT / "agentbundle" / "_data" / "distribution-routes.schema.json"
AGENT_PLUGIN_VENDOR_ROOT = REPO_ROOT / "contracts" / "vendor" / "agent-plugins" / "1.0.0"
AGENT_PLUGIN_BUNDLE_PARTS = ("_data", "vendor", "agent-plugins", "1.0.0")
AGENT_PLUGIN_UPSTREAM = "https://github.com/agentplugins/agent-plugins-spec"
AGENT_PLUGIN_COMMIT = "ff8ab5e392cc87bd88d87c060815a87490e51003"
AGENT_PLUGIN_SCHEMA_BLOBS = {
    "plugin.schema.json": "8fed0e1fe45d0464aee880d3fbab228b71ecfc1e",
    "mcp.schema.json": "a9139a4259b932c60b5351c8d9da6a5c60c97646",
}
AGENT_PLUGIN_SCHEMA_IDS = {
    "plugin.schema.json": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
    "mcp.schema.json": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
}
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


def _git_blob_id(contents: bytes) -> str:
    """Return the Git blob identity for exact contract bytes."""
    header = f"blob {len(contents)}\0".encode("ascii")
    return hashlib.sha1(header + contents, usedforsecurity=False).hexdigest()


@pytest.mark.parametrize(
    ("filename", "expected_blob"), sorted(AGENT_PLUGIN_SCHEMA_BLOBS.items())
)
def test_agent_plugin_vendor_bundle_matches_upstream_identity(
    filename: str,
    expected_blob: str,
) -> None:
    """Pin exact upstream bytes and their byte-identical packaged twins."""
    bundled = resource_files("agentbundle").joinpath(
        *AGENT_PLUGIN_BUNDLE_PARTS, filename
    ).read_bytes()

    # The authored copy is checkout-only; a published sdist carries the bundled
    # twin alone, so the upstream identity is pinned on the bytes that ship.
    if AGENT_PLUGIN_VENDOR_ROOT.is_dir():
        assert (AGENT_PLUGIN_VENDOR_ROOT / filename).read_bytes() == bundled

    assert _git_blob_id(bundled) == expected_blob
    assert json.loads(bundled)["$id"] == AGENT_PLUGIN_SCHEMA_IDS[filename]

    mutated = bundled[:-1] + bytes([bundled[-1] ^ 1])
    assert _git_blob_id(mutated) != expected_blob


def test_agent_plugin_vendor_provenance_is_complete_and_packaged() -> None:
    """Keep licence and immutable acquisition evidence beside both copies."""
    bundled_root = resource_files("agentbundle").joinpath(*AGENT_PLUGIN_BUNDLE_PARTS)
    for filename in ("LICENSE.md", "PROVENANCE.md"):
        bundled = bundled_root.joinpath(filename).read_bytes()
        # Checkout-only authored copy; the packaged twin is what ships.
        if AGENT_PLUGIN_VENDOR_ROOT.is_dir():
            assert (AGENT_PLUGIN_VENDOR_ROOT / filename).read_bytes() == bundled

    provenance = bundled_root.joinpath("PROVENANCE.md").read_text(encoding="utf-8")
    required_evidence = {
        AGENT_PLUGIN_UPSTREAM,
        AGENT_PLUGIN_COMMIT,
        "schemas/1.0.0/plugin.schema.json",
        "schemas/1.0.0/mcp.schema.json",
        "LICENSE.md",
        "b1c2f51d0884b9d5b04c960e5726ebd19b8565f4",
        "Apache-2.0",
        *AGENT_PLUGIN_SCHEMA_BLOBS.values(),
        *AGENT_PLUGIN_SCHEMA_IDS.values(),
    }
    assert all(item in provenance for item in required_evidence)


def test_agent_plugin_vendor_bundle_is_available_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Load every vendored resource after disabling the process network seam."""

    def refuse_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("vendored contract loading attempted network access")

    monkeypatch.setattr(socket, "create_connection", refuse_network)
    for filename in (*sorted(AGENT_PLUGIN_SCHEMA_BLOBS), "LICENSE.md", "PROVENANCE.md"):
        resource = resource_files("agentbundle").joinpath(
            *AGENT_PLUGIN_BUNDLE_PARTS, filename
        )
        assert resource.is_file()
        assert resource.read_bytes()


# STUB: AC2 — one explicit, closed Agent Plugins route is resolvable.
def test_agent_plugin_route_contract_is_closed_and_resolvable() -> None:
    """Require the third route's complete declaration and named recipe."""
    contract = tomllib.loads(ROUTE_CONTRACT_PATH.read_text(encoding="utf-8"))

    assert set(contract["route"]) == {"apm", "claude-plugins", "agent-plugin"}
    agent_plugin = contract["route"]["agent-plugin"]
    assert agent_plugin == {
        "identity": "agent-plugin",
        "package-layout": {
            "name": "agent-plugin-tree",
            "output-subdir": "agent-plugins",
        },
        "manifest-projector": {
            "name": "agent-plugin-root-manifest",
            "adapter-projector": "none",
            "admission-policy": "skills-only",
        },
        "component-capabilities": {
            "skill": {
                "status": "native",
                "mode": "direct-directory",
                "target-path": "skills/",
            },
            **{
                primitive: {
                    "status": "dropped",
                    "mode": "dropped",
                    "target-path": "none",
                }
                for primitive in PRIMITIVES - {"skill"}
            },
        },
        "marketplace-projector": "none",
        "lifecycle-trigger": "none",
    }

    recipe = load_recipe("per-pack-agent-plugin")
    resolved = _resolve_distribution_route(recipe, contract)
    assert resolved.identity == "agent-plugin"
    assert resolved.output_subdir == "agent-plugins"
    assert resolved.adapter_projector is None

    schema = json.loads(ROUTE_SCHEMA_PATH.read_text(encoding="utf-8"))
    malformed_contracts: list[dict] = []

    missing = copy.deepcopy(contract)
    del missing["route"]["agent-plugin"]
    malformed_contracts.append(missing)
    for field, invalid in (
        ("package-layout", {"name": "agent-plugin-tree", "output-subdir": "plugins"}),
        (
            "manifest-projector",
            {
                "name": "agent-plugin-root-manifest",
                "adapter-projector": "claude-code",
                "admission-policy": "skills-only",
            },
        ),
        ("marketplace-projector", "claude-marketplace"),
        ("lifecycle-trigger", "session-start-install-marker"),
    ):
        malformed = copy.deepcopy(contract)
        malformed["route"]["agent-plugin"][field] = invalid
        malformed_contracts.append(malformed)
    for primitive in ("skill", "agent"):
        malformed = copy.deepcopy(contract)
        malformed["route"]["agent-plugin"]["component-capabilities"][primitive][
            "status"
        ] = "dropped" if primitive == "skill" else "native"
        malformed_contracts.append(malformed)

    assert all(validate(item, schema) for item in malformed_contracts)

    wrong_output = replace(recipe, output_subdir="plugins")
    with pytest.raises(ValueError, match=r"output-subdir.*agent-plugins"):
        _resolve_distribution_route(wrong_output, contract)


# STUB: AC1 — the public contract declares the complete route set.
def test_route_contract_declares_exact_routes() -> None:
    """Require the bundled contract and its closed route identities."""
    assert ROUTE_CONTRACT_PATH.is_file(), "bundled distribution-route contract is missing"
    assert ROUTE_SCHEMA_PATH.is_file(), "bundled distribution-route schema is missing"
    contract = tomllib.loads(ROUTE_CONTRACT_PATH.read_text(encoding="utf-8"))
    schema = json.loads(ROUTE_SCHEMA_PATH.read_text(encoding="utf-8"))

    assert validate(contract, schema) == []
    assert contract["contract"]["version"] == "0.2"
    assert set(contract["route"]) == {"apm", "claude-plugins", "agent-plugin"}
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
        "per-pack-agent-plugin": "agent-plugin",
        "marketplace": "claude-plugins",
    }

    assert {
        recipe_name: getattr(load_recipe(recipe_name), "route", None)
        for recipe_name in expected
    } == expected
    assert load_recipe("per-pack-apm-package").adapter is None
    assert load_recipe("per-pack-claude-plugin").adapter == "claude-code"
    assert load_recipe("per-pack-agent-plugin").adapter is None

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
