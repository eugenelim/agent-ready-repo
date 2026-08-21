"""Construction tests for fail-closed distribution-route resolution."""

from __future__ import annotations

import copy
import tomllib
from dataclasses import replace
from importlib import import_module
from pathlib import Path

import pytest

build_main = import_module("agentbundle.build.main")


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
ROUTE_CONTRACT_PATH = PACKAGE_ROOT / "agentbundle" / "_data" / "distribution-routes.toml"
ADAPTER_CONTRACT_PATH = PACKAGE_ROOT / "agentbundle" / "_data" / "adapter.toml"


def _contract() -> dict:
    """Load the bundled route declaration used by the running build."""
    return tomllib.loads(ROUTE_CONTRACT_PATH.read_text(encoding="utf-8"))


def _adapter_contract() -> dict:
    """Load the direct-install adapter declaration used by the build."""
    return tomllib.loads(ADAPTER_CONTRACT_PATH.read_text(encoding="utf-8"))


# STUB: AC4, AC9 — a named resolver exposes only the two Phase 0 projectors.
def test_resolver_selects_only_named_phase_zero_routes() -> None:
    """Require the explicit resolver surface before dispatch migration begins."""
    resolver = getattr(build_main, "_resolve_distribution_route", None)

    assert callable(resolver), "distribution-route resolver is missing"
    apm = resolver(build_main.load_recipe("per-pack-apm-package"), _contract())
    claude = resolver(build_main.load_recipe("per-pack-claude-plugin"), _contract())

    assert (apm.identity, apm.package_projector) == ("apm", "apm-package")
    assert (claude.identity, claude.package_projector) == (
        "claude-plugins",
        "claude-plugin",
    )


# STUB: AC9 — admission policy must agree with the named projector.
def test_resolver_rejects_admission_policy_projector_conflict() -> None:
    """Fail closed when Claude's consent boundary is weakened in route data."""
    resolver = getattr(build_main, "_resolve_distribution_route", None)
    assert callable(resolver), "distribution-route resolver is missing"
    contract = copy.deepcopy(_contract())
    contract["route"]["claude-plugins"]["manifest-projector"][
        "admission-policy"
    ] = "all-packs"

    with pytest.raises(ValueError, match=r"claude-plugins.*admission-policy"):
        resolver(build_main.load_recipe("per-pack-claude-plugin"), contract)


@pytest.mark.parametrize(
    ("recipe_name", "adapter"),
    [("per-pack-apm-package", "apm"), ("per-pack-claude-plugin", None)],
)
def test_resolver_rejects_route_adapter_projector_conflict(
    recipe_name: str, adapter: str | None
) -> None:
    """Reject fabricated or missing runtime-adapter projection identity."""
    recipe = replace(build_main.load_recipe(recipe_name), adapter=adapter)

    with pytest.raises(ValueError, match=r"adapter-projector"):
        build_main._resolve_distribution_route(recipe, _contract())


def test_resolver_rejects_unknown_projector_and_route_mismatch() -> None:
    """Keep selection closed to the two declared projector combinations."""
    contract = copy.deepcopy(_contract())
    contract["route"]["apm"]["manifest-projector"]["name"] = "dynamic"
    with pytest.raises(ValueError, match=r"contract is invalid"):
        build_main._resolve_distribution_route(
            build_main.load_recipe("per-pack-apm-package"), contract
        )

    mismatched = replace(
        build_main.load_recipe("per-pack-apm-package"),
        route="claude-plugins",
        adapter="claude-code",
    )
    with pytest.raises(ValueError, match=r"output-subdir.*claude-plugins"):
        build_main._resolve_distribution_route(mismatched, _contract())


def test_resolver_diagnostics_name_recipe_and_offending_field() -> None:
    """Make route refusals actionable for custom recipe authors."""
    recipe = replace(
        build_main.load_recipe("per-pack-apm-package"),
        name="custom-bad-route",
        route="unknown-route",
    )
    with pytest.raises(
        ValueError, match=r"custom-bad-route.*field 'route'.*unknown-route"
    ):
        build_main._resolve_distribution_route(recipe, _contract())

    recipe = replace(
        build_main.load_recipe("per-pack-claude-plugin"),
        name="custom-bad-adapter",
        adapter="codex",
    )
    with pytest.raises(
        ValueError, match=r"custom-bad-adapter.*field 'adapter'.*codex"
    ):
        build_main._resolve_distribution_route(recipe, _contract())


def test_aggregate_requires_route_marketplace_permission_before_output(
    tmp_path: Path,
) -> None:
    """Refuse aggregation on APM's explicitly absent marketplace projector."""
    recipe = replace(
        build_main.load_recipe("marketplace"),
        name="invalid-apm-marketplace",
        route="apm",
        input_subdir="apm",
        output_file="apm/marketplace.json",
    )
    output = tmp_path / "dist"

    with pytest.raises(
        ValueError,
        match=r"invalid-apm-marketplace.*field 'route'.*marketplace-projector",
    ):
        build_main.run_recipe(
            recipe,
            [],
            output,
            _adapter_contract(),
            route_contract=_contract(),
            aggregate_scope="catalogue",
        )
    assert not output.exists()


def test_aggregate_rejects_adapter_outside_route_permission(
    tmp_path: Path,
) -> None:
    """Reject an aggregate adapter that disagrees with its named route."""
    recipe = replace(
        build_main.load_recipe("marketplace"),
        name="invalid-marketplace-adapter",
        adapter="codex",
    )
    output = tmp_path / "dist"

    with pytest.raises(
        ValueError,
        match=r"invalid-marketplace-adapter.*field 'adapter'.*codex",
    ):
        build_main.run_recipe(
            recipe,
            [],
            output,
            _adapter_contract(),
            route_contract=_contract(),
            aggregate_scope="catalogue",
        )
    assert not output.exists()


def test_distribution_routes_have_no_registration_surface() -> None:
    """Prove Phase 0 did not introduce registry or discovery dispatch."""
    assert not hasattr(build_main, "ROUTE_REGISTRY")
    assert not hasattr(build_main, "register_distribution_route")


def test_apm_has_no_fabricated_adapter_dispatch(tmp_path: Path) -> None:
    """An `adapter = apm` value cannot bypass explicit route resolution."""
    fabricated = replace(
        build_main.load_recipe("per-pack-apm-package"),
        adapter="apm",
    )
    with pytest.raises(ValueError, match=r"apm.*adapter-projector"):
        build_main.run_recipe(
            fabricated,
            [],
            tmp_path / "dist",
            _adapter_contract(),
            aggregate_scope="catalogue",
        )


def test_run_recipe_rejects_missing_route_before_output(tmp_path: Path) -> None:
    """Keep the required route invariant on programmatic callers too."""
    missing = replace(
        build_main.load_recipe("per-pack-apm-package"), route=None
    )
    output = tmp_path / "dist"
    with pytest.raises(ValueError, match=r"field 'route'.*required.*per-pack"):
        build_main.run_recipe(
            missing,
            [],
            output,
            _adapter_contract(),
            aggregate_scope="catalogue",
        )
    assert not output.exists()


def test_resolver_rejects_lifecycle_projector_conflict() -> None:
    """Lifecycle trigger selection is closed with the named projector."""
    contract = copy.deepcopy(_contract())
    contract["route"]["apm"]["lifecycle-trigger"] = "arbitrary-command"
    with pytest.raises(ValueError, match=r"contract is invalid"):
        build_main._resolve_distribution_route(
            build_main.load_recipe("per-pack-apm-package"), contract
        )


# STUB: AC5 — APM package dispatch is route-owned and has no runtime adapter.
def test_apm_route_resolves_without_a_runtime_adapter() -> None:
    """Resolve APM's writer, layout, and lifecycle from route data alone."""
    resolver = getattr(build_main, "_resolve_distribution_route", None)
    assert callable(resolver), "distribution-route resolver is missing"
    resolved = resolver(build_main.load_recipe("per-pack-apm-package"), _contract())

    assert resolved.identity == "apm"
    assert resolved.package_projector == "apm-package"
    assert resolved.adapter_projector is None
    assert resolved.output_subdir == "apm"
    assert resolved.lifecycle_trigger == "session-start-install-marker"


# STUB: AC6 — Claude packaging resolves both route and adapter projectors.
def test_claude_route_resolves_package_and_adapter_projectors() -> None:
    """Resolve Claude package semantics without rewriting adapter rows."""
    resolver = getattr(build_main, "_resolve_distribution_route", None)
    assert callable(resolver), "distribution-route resolver is missing"
    resolved = resolver(build_main.load_recipe("per-pack-claude-plugin"), _contract())

    assert resolved.identity == "claude-plugins"
    assert resolved.package_projector == "claude-plugin"
    assert resolved.adapter_projector == "claude-code"
    assert resolved.admission_policy == "user-publishable-with-consent"
    assert resolved.output_subdir == "claude-plugins"
    assert resolved.component_capabilities["hook-wiring"] == {
        "status": "native",
        "mode": "compiled-manifest",
        "target-path": ".claude-plugin/plugin.json",
    }
    assert resolved.marketplace_projector == "claude-marketplace"
    assert resolved.lifecycle_trigger == "session-start-install-marker"


def test_claude_route_projection_does_not_mutate_adapter_contract() -> None:
    """Derive plugin-root adapter input while retaining direct-install rows."""
    adapter_contract = _adapter_contract()
    before = copy.deepcopy(adapter_contract)
    resolved = build_main._resolve_distribution_route(
        build_main.load_recipe("per-pack-claude-plugin"), _contract()
    )

    projected = build_main._projection_contract_for_route(
        adapter_contract, resolved
    )
    assert adapter_contract == before
    direct = {
        item["primitive"]: item
        for item in adapter_contract["adapter"]["claude-code"]["projection"]
    }
    plugin = {
        item["primitive"]: item
        for item in projected["adapter"]["claude-code"]["projection"]
    }
    assert direct["skill"]["target-path"] == ".claude/skills/"
    assert plugin["skill"]["target-path"] == "skills/"
    assert direct["hook-wiring"]["mode"] == "merge-json"
    assert plugin["hook-wiring"] == {
        "primitive": "hook-wiring",
        "mode": "dropped",
    }


# STUB: AC14 — untrusted recipe layout cannot override route-owned destinations.
@pytest.mark.parametrize("unsafe_output", ["../escape", "/absolute/escape"])
def test_route_layout_refuses_traversal_and_absolute_paths_before_output(
    tmp_path: Path,
    unsafe_output: str,
) -> None:
    """Reject route/recipe path mismatch without allocating an output tree."""
    recipe = replace(
        build_main.load_recipe("per-pack-apm-package"),
        output_subdir=unsafe_output,
    )
    output_root = tmp_path / "dist"

    with pytest.raises(ValueError, match=r"apm.*output-subdir"):
        build_main.run_recipe(
            recipe,
            [],
            output_root,
            _adapter_contract(),
            route_contract=_contract(),
            aggregate_scope="catalogue",
        )
    assert not output_root.exists()


# STUB: AC14 — a pre-existing symlink cannot turn a valid route into an escape.
def test_route_output_refuses_symlink_parent_escape(tmp_path: Path) -> None:
    """Refuse a route-layout symlink before touching its external target."""
    output_root = tmp_path / "dist"
    outside = tmp_path / "outside"
    output_root.mkdir()
    outside.mkdir()
    (output_root / "apm").symlink_to(outside, target_is_directory=True)
    fixture_pack = (
        Path(__file__).resolve().parent / "fixtures" / "packs" / "core"
    )

    with pytest.raises(ValueError, match=r"outside output root"):
        build_main.run_recipe(
            build_main.load_recipe("per-pack-apm-package"),
            [build_main.Pack(name="core", path=fixture_pack)],
            output_root,
            _adapter_contract(),
            route_contract=_contract(),
            aggregate_scope="catalogue",
        )
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize(
    ("recipe_name", "source_root"),
    [
        ("per-pack-apm-package", ".apm"),
        ("per-pack-apm-package", "seeds"),
        ("per-pack-claude-plugin", ".apm"),
        ("per-pack-claude-plugin", "seeds"),
    ],
)
def test_route_projection_refuses_symlinked_source_roots_before_output(
    tmp_path: Path, recipe_name: str, source_root: str
) -> None:
    """Never dereference a route-owned source root into package bytes."""
    pack_root = tmp_path / "pack"
    outside = tmp_path / "outside"
    pack_root.mkdir()
    outside.mkdir()
    (outside / "private.txt").write_text("outside", encoding="utf-8")
    (pack_root / source_root).symlink_to(outside, target_is_directory=True)
    (pack_root / "pack.toml").write_text(
        '[pack]\nname = "fixture"\nversion = "0.1.0"\n'
        'description = "Route source safety fixture."\n'
        '[pack.adapter-contract]\nversion = "0.18"\n'
        '[pack.install]\ndefault-scope = "user"\nallowed-scopes = ["user"]\n',
        encoding="utf-8",
    )
    plugin_manifest = pack_root / ".claude-plugin" / "plugin.json"
    plugin_manifest.parent.mkdir()
    plugin_manifest.write_text(
        '{"name":"fixture","version":"0.1.0",'
        '"description":"Route source safety fixture."}\n',
        encoding="utf-8",
    )
    output = tmp_path / "dist"

    with pytest.raises(ValueError, match=r"symlinked source root"):
        build_main.run_recipe(
            build_main.load_recipe(recipe_name),
            [build_main.Pack(name="fixture", path=pack_root)],
            output,
            _adapter_contract(),
            route_contract=_contract(),
            aggregate_scope="catalogue",
        )

    assert (outside / "private.txt").read_text(encoding="utf-8") == "outside"
    assert not output.exists()


def test_route_projection_refuses_escaping_nested_source_link(
    tmp_path: Path,
) -> None:
    """Reject nested links whose eventual consumer could follow outside the route."""
    pack_root = tmp_path / "pack"
    apm_root = pack_root / ".apm"
    outside = tmp_path / "outside.txt"
    apm_root.mkdir(parents=True)
    outside.write_text("outside", encoding="utf-8")
    (apm_root / "escape.txt").symlink_to("../../outside.txt")
    output = tmp_path / "dist"

    with pytest.raises(ValueError, match=r"source link.*escapes"):
        build_main.run_recipe(
            build_main.load_recipe("per-pack-apm-package"),
            [build_main.Pack(name="fixture", path=pack_root)],
            output,
            _adapter_contract(),
            route_contract=_contract(),
            aggregate_scope="catalogue",
        )

    assert outside.read_text(encoding="utf-8") == "outside"
    assert not output.exists()


def test_claude_preflight_ignores_pack_excluded_by_route_admission(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A repo-only pack is skipped before Claude source-tree preflight."""
    pack_root = tmp_path / "pack"
    outside = tmp_path / "outside"
    pack_root.mkdir()
    outside.mkdir()
    (pack_root / ".apm").symlink_to(outside, target_is_directory=True)
    (pack_root / "pack.toml").write_text(
        '[pack]\nname = "repo-only"\nversion = "0.1.0"\n'
        '[pack.install]\ndefault-scope = "repo"\nallowed-scopes = ["repo"]\n',
        encoding="utf-8",
    )
    output = tmp_path / "dist"

    result = build_main.run_recipe(
        build_main.load_recipe("per-pack-claude-plugin"),
        [build_main.Pack(name="repo-only", path=pack_root)],
        output,
        _adapter_contract(),
        route_contract=_contract(),
        aggregate_scope="catalogue",
    )

    assert result["produced"] == {}
    assert "skipping repo-only" in capsys.readouterr().err
    assert not output.exists()
